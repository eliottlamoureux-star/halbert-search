#!/usr/bin/env python3
"""Round 2: fetch every remaining candidate, keep only genuine unheld letters.

Dedup is on NORMALIZED TEXT (markup stripped, whitespace/case collapsed), so the
same letter served under different markup or path collapses to one copy.
"""
import os, re, sys, time, json, html, hashlib, urllib.parse, urllib.request
import threading, queue, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
UA   = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOST = "https://www.thegaryhalbertletter.com"
WB_OK = re.compile(r'(?i)^/(newsletters?|boron|hotd|new)/|^/[^/]+\.html?$')  # worth a wayback try

def textof(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', 'ignore')
    t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', raw)
    t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', t))
    return re.sub(r'\s+', ' ', t).strip()

def sig(raw):
    """Normalized-text fingerprint for dedup."""
    t = textof(raw).lower()
    t = re.sub(r'[^a-z0-9 ]+', '', t)
    return hashlib.md5(t.encode()).hexdigest()

# ---- fingerprint everything we already hold ------------------------------
have = {}
for dp, _, fs in os.walk(SITE):
    for fn in fs:
        if not fn.lower().endswith(('.htm', '.html')): continue
        p = os.path.join(dp, fn)
        try: have[sig(open(p, 'rb').read())] = os.path.relpath(p, SITE)
        except Exception: pass
print(f"already holding {len(have)} distinct letters (by text fingerprint)", flush=True)

def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
          "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def wayback(url):
    try:
        api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
        snap = json.loads(fetch(api, 25)).get("archived_snapshots", {}).get("closest")
        if not snap: return None
        return fetch(f"https://web.archive.org/web/{snap['timestamp']}id_/{url}", 50)
    except Exception:
        return None

LETTER = re.compile(r'(?i)(gary\s+halbert|dear\s+friend|jewfish\s+creek|halbert\s+letter)')
lock = threading.Lock()
kept, dupes, rejected, failed = [], [], [], []

def consider(path, raw, src):
    if not raw or len(raw) < 1200:
        with lock: failed.append(path); return
    txt = textof(raw)
    words = len(txt.split())
    if words < 300 or not LETTER.search(txt[:6000]):
        with lock: rejected.append((path, words)); return
    s = sig(raw)
    with lock:
        if s in have:
            dupes.append((path, have[s])); return
        local = os.path.join(SITE, path.lstrip('/'))
        os.makedirs(os.path.dirname(local), exist_ok=True)
        open(local, 'wb').write(raw)
        have[s] = os.path.relpath(local, SITE)
        kept.append((path, words, src))
        print(f"  KEEP {words:>6}w  {src:<8} {path}", flush=True)

def worker(q):
    while True:
        try: path = q.get_nowait()
        except queue.Empty: return
        url = HOST + urllib.parse.quote(path, safe="/%")
        raw, src = None, "live"
        try: raw = fetch(url)
        except Exception: raw = None
        if raw is None and WB_OK.search(path):
            raw, src = wayback(url), "wayback"
        consider(path, raw, src)
        time.sleep(0.25)

cands = [l.strip() for l in open(os.path.join(ROOT, "candidates-round2.txt")) if l.strip()]
print(f"probing {len(cands)} candidates ...\n", flush=True)
q = queue.Queue()
for c in cands: q.put(c)
ts = [threading.Thread(target=worker, args=(q,), daemon=True) for _ in range(6)]
for t in ts: t.start()
for t in ts: t.join()

print(f"\n=== round 2 ===")
print(f"  new letters kept : {len(kept)}")
print(f"  exact duplicates : {len(dupes)}")
print(f"  not letters      : {len(rejected)}")
print(f"  unreachable      : {len(failed)}")
json.dump({"kept": kept, "dupes": dupes[:50]},
          open(os.path.join(ROOT, "round2-result.json"), "w"), indent=1)
