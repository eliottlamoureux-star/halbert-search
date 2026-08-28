#!/usr/bin/env python3
"""Mirror the publicly-readable Gary Halbert Letter archive for local offline study.

Live site first, Wayback (raw `id_` mode, no toolbar injection) as fallback.
Directory structure is mirrored exactly so the pages' relative asset links
(../images/foo.jpg) resolve without rewriting a single byte of HTML.
"""
import os, re, sys, time, json, urllib.parse, urllib.request, urllib.error
import collections, threading, queue

ROOT   = os.path.dirname(os.path.abspath(__file__))
SITE   = os.path.join(ROOT, "site")
HOST   = "https://www.thegaryhalbertletter.com"
UA     = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
DELAY  = 0.35          # politeness delay per worker
WORKERS= 4
TIMEOUT= 45

_lock = threading.Lock()
manifest = []

def fetch(url, referer=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        **({"Referer": referer} if referer else {}),
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), r.headers.get_content_type(), r.status

def wayback(url):
    """Newest archived snapshot, raw mode (no Wayback chrome injected)."""
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        raw, _, _ = fetch(api)
        snap = json.loads(raw).get("archived_snapshots", {}).get("closest")
        if not snap:
            return None, None
        ts = snap["timestamp"]
        return fetch(f"https://web.archive.org/web/{ts}id_/{url}")[:2]
    except Exception:
        return None, None

def save(path, data):
    local = os.path.join(SITE, path.lstrip("/"))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    with open(local, "wb") as f:
        f.write(data)
    return local

def get_one(path):
    """Fetch one site path; returns (status, source, bytes) and writes to disk."""
    url = HOST + urllib.parse.quote(path, safe="/%")
    body = ctype = None
    src  = "live"
    for attempt in range(3):
        try:
            body, ctype, _ = fetch(url)
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 500, 502, 503) and attempt < 2:
                time.sleep(1.5 * (attempt + 1)); continue
            body = None; break
        except Exception:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1)); continue
            body = None; break
    if body is None:
        body, ctype = wayback(url)
        src = "wayback"
    if body is None:
        return ("FAIL", None, 0)
    # a "soft 404" / login wall is far smaller than a real letter
    save(path, body)
    return ("OK", src, len(body))

def worker(q, results):
    while True:
        try: path = q.get_nowait()
        except queue.Empty: return
        status, src, n = get_one(path)
        with _lock:
            results.append((path, status, src, n))
            done = len(results)
            if done % 25 == 0:
                print(f"  ... {done} fetched", flush=True)
        time.sleep(DELAY)
        q.task_done()

def run(paths, label):
    print(f"\n=== {label}: {len(paths)} URLs ===", flush=True)
    q = queue.Queue()
    for p in paths: q.put(p)
    results = []
    threads = [threading.Thread(target=worker, args=(q, results), daemon=True)
               for _ in range(WORKERS)]
    for t in threads: t.start()
    for t in threads: t.join()
    ok   = [r for r in results if r[1] == "OK"]
    fail = [r for r in results if r[1] != "OK"]
    wb   = [r for r in ok if r[2] == "wayback"]
    print(f"  {len(ok)} ok ({len(wb)} via wayback), {len(fail)} failed", flush=True)
    return results

# ---- pass 1: the letters -------------------------------------------------
paths = [l.strip() for l in open(os.path.join(ROOT, "letter-paths.txt")) if l.strip()]
res1 = run(paths, "letters")

# ---- pass 2: assets referenced by whatever we just saved -----------------
ASSET_RE = re.compile(rb'''(?i)(?:src|background)\s*=\s*["']([^"'>]+)''')
CSS_RE   = re.compile(rb'''(?i)url\(\s*["']?([^"')]+)''')
assets = set()
for dirpath, _, files in os.walk(SITE):
    for fn in files:
        if not fn.lower().endswith((".htm", ".html")): continue
        full = os.path.join(dirpath, fn)
        page_path = "/" + os.path.relpath(full, SITE).replace(os.sep, "/")
        try: raw = open(full, "rb").read()
        except Exception: continue
        for m in list(ASSET_RE.findall(raw)) + list(CSS_RE.findall(raw)):
            ref = m.decode("utf-8", "ignore").strip()
            if not ref or ref.startswith(("data:", "#", "mailto:", "javascript:")): continue
            absu = urllib.parse.urljoin(HOST + page_path, ref)
            pr = urllib.parse.urlparse(absu)
            if pr.netloc.replace("www.", "") != "thegaryhalbertletter.com": continue
            if not re.search(r'(?i)\.(jpe?g|gif|png|bmp|css|js|ico|swf|mp3|pdf)$', pr.path): continue
            assets.add(urllib.parse.unquote(pr.path))
assets = sorted(a for a in assets
                if not os.path.exists(os.path.join(SITE, a.lstrip("/"))))
res2 = run(assets, "assets") if assets else []

# ---- report --------------------------------------------------------------
with open(os.path.join(ROOT, "manifest.tsv"), "w") as f:
    f.write("path\tstatus\tsource\tbytes\n")
    for path, status, src, n in sorted(res1 + res2):
        f.write(f"{path}\t{status}\t{src}\t{n}\n")
print("\nmanifest.tsv written", flush=True)
