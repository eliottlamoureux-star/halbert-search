#!/usr/bin/env python3
"""Second pass: retry failures across path/host variants, and purge stub files."""
import os, re, time, json, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
UA   = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOSTS = ["https://www.thegaryhalbertletter.com", "https://thegaryhalbertletter.com"]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
          "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def wayback(url):
    try:
        api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
        snap = json.loads(fetch(api)).get("archived_snapshots", {}).get("closest")
        if not snap: return None
        return fetch(f"https://web.archive.org/web/{snap['timestamp']}id_/{url}")
    except Exception:
        return None

def variants(path):
    """Path spellings the live server might actually answer to."""
    seen, out = set(), []
    cands = [path]
    # case: the live tree is lowercase for these dirs
    cands.append(re.sub(r'(?i)^/Newsletters/', '/newsletters/', path))
    cands.append(re.sub(r'(?i)^/Boron/', '/Boron/', path))
    # the archived "protected" mirror
    for c in list(cands):
        if not re.match(r'(?i)^/Newletter-archives-protected', c):
            cands.append('/Newletter-archives-protected' + c)
    # stray space before the extension
    for c in list(cands):
        if ' .htm' in c:
            cands.append(c.replace(' .htm', '.htm'))
        if ' ' in c:
            cands.append(c.replace(' ', '_'))
    for c in cands:
        if c not in seen:
            seen.add(c); out.append(c)
    return out

def try_all(path):
    for cand in variants(path):
        for host in HOSTS:
            url = host + urllib.parse.quote(cand, safe="/%")
            try:
                body = fetch(url)
                if body and len(body) > 400:
                    return body, f"live{'' if cand==path else ' ('+cand+')'}"
            except Exception:
                pass
            time.sleep(0.2)
    for cand in variants(path):
        body = wayback(HOSTS[0] + urllib.parse.quote(cand, safe="/%"))
        if body and len(body) > 400:
            return body, f"wayback ({cand})"
        time.sleep(0.2)
    return None, None

# ---- purge stubs/empties so they can be retried cleanly -------------------
STUB = re.compile(rb'(?i)(login|password|not found|404|access denied|has moved)')
purged = []
for dp, _, fs in os.walk(SITE):
    for fn in fs:
        if not fn.lower().endswith(('.htm', '.html')): continue
        full = os.path.join(dp, fn)
        n = os.path.getsize(full)
        if n == 0:
            purged.append(os.path.relpath(full, SITE)); os.remove(full); continue
        if n < 2048:
            raw = open(full, 'rb').read()
            text = re.sub(rb'(?s)<[^>]+>', b' ', raw)
            # purge ONLY on a positive stub match. A short page is not a stub:
            # some real letters are genuinely brief, and the old word-count
            # condition deleted them with no way to re-acquire.
            if STUB.search(text):
                purged.append(os.path.relpath(full, SITE)); os.remove(full)
print(f"purged {len(purged)} stub/empty files")
with open(os.path.join(ROOT, "purged.txt"), "w") as fh:
    fh.write("\n".join(purged) + ("\n" if purged else ""))

# ---- retry every path that has no file on disk ---------------------------
wanted = [l.strip() for l in open(os.path.join(ROOT, "letter-paths.txt")) if l.strip()]
missing = [p for p in wanted if not os.path.exists(os.path.join(SITE, p.lstrip('/')))]
print(f"retrying {len(missing)} missing letters ...")

recovered, dead = 0, []
for p in missing:
    body, how = try_all(p)
    if body:
        local = os.path.join(SITE, p.lstrip('/'))
        os.makedirs(os.path.dirname(local), exist_ok=True)
        open(local, 'wb').write(body)
        recovered += 1
        print(f"  OK   {p}  <- {how}", flush=True)
    else:
        dead.append(p)
        print(f"  DEAD {p}", flush=True)

print(f"\nrecovered {recovered}, unrecoverable {len(dead)}")
open(os.path.join(ROOT, "unrecoverable.txt"), "w").write('\n'.join(dead) + ('\n' if dead else ''))
