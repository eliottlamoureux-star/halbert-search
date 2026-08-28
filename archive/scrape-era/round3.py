#!/usr/bin/env python3
"""Round 3: close the reviewer's remaining gaps.
  a) the specific paths it named
  b) anything from letter-paths.txt no longer on disk (covers retry.py's
     unlogged word-count purge, which could have deleted short real letters)
"""
import os, re, time, json, html, hashlib, urllib.parse, urllib.request

ROOT=os.path.dirname(os.path.abspath(__file__)); SITE=os.path.join(ROOT,"site")
UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOST="https://www.thegaryhalbertletter.com"

NAMED = [
 "/EnvelopeTitles/Gary Girlfriend In Motion.htm",
 "/newsletters/EnvelopeTitles/Gary Girlfriend In Motion.htm",
 "/GaryHalbertAudio/GaryHalbertAudio.htm",
 "/Friends/JoePolish2/JoePolishLetter2.html",
 "/newsletters/Friends/JoePolish/JoePolish.htm",
 "/newsletters/Friends/JoePolish/JoePolishNewsletter_7_1_09.htm",
 "/newsletters/Friends/JoePolish/Joe_and_Frank.html",
 "/12-MonthMillionaireOcalaOnly.htm", "/iraqisecret.htm", "/TheresaFarewell.htm",
 "/Goodbye 04-05-05.htm", "/Goodbye 04-06-05.htm",
 "/newsletters/SeminarPush05-18-05.htm", "/newsletters/TheresaFarewell.htm",
 "/newsletters/12-MonthMillionaireOcalaOnly.htm",
 "/newsletters/Goodbye 04-05-05.htm", "/newsletters/Goodbye 04-06-05.htm",
 "/newsletters/WhatsNew/1WhatsNew.html",
 "/newsletters/MarkJoyner/hp1.htm",
 "/newsletters/MilloinDollarRolodex/1MillionDollarRolodex.html",
 "/goldbox/sleazypitch.htm", "/newsletters/goldbox/sleazypitch.htm",
]

def textof(raw):
    if isinstance(raw,bytes): raw=raw.decode('utf-8','ignore')
    t=re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>',' ',raw)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'(?s)<[^>]+>',' ',t))).strip()
def sig(raw):
    return hashlib.md5(re.sub(r'[^a-z0-9 ]+','',textof(raw).lower())
                       .encode()).hexdigest()
def shingle(raw):
    w=re.sub(r'[^a-z0-9 ]+','',textof(raw).lower()).split()[:600]
    return hashlib.md5(' '.join(w).encode()).hexdigest() if len(w)>=100 else None

have_sig, have_sh = {}, {}
for dp,_,fs in os.walk(SITE):
    for fn in fs:
        if not fn.lower().endswith(('.htm','.html')): continue
        p=os.path.join(dp,fn)
        try: raw=open(p,'rb').read()
        except Exception: continue
        rel=os.path.relpath(p,SITE)
        have_sig[sig(raw)]=rel
        s=shingle(raw)
        if s: have_sh[s]=rel

def fetch(u,t=40):
    r=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html,*/*;q=0.8"})
    with urllib.request.urlopen(r,timeout=t) as x: return x.read()
def wayback(u):
    try:
        api="https://archive.org/wayback/available?url="+urllib.parse.quote(u,safe="")
        s=json.loads(fetch(api,25)).get("archived_snapshots",{}).get("closest")
        if not s: return None
        return fetch(f"https://web.archive.org/web/{s['timestamp']}id_/{u}",50)
    except Exception: return None

# NOTE: no minimum-length gate here — that bug is exactly what let retry.py
# delete short real letters and then refuse to re-accept them.
LETTER=re.compile(r'(?i)(gary\s+halbert|dear\s+friend|jewfish\s+creek|halbertism)')
kept=[]; dup=[]; skip=[]; miss=[]

def consider(path,raw,src):
    if not raw or len(raw)<600: miss.append(path); return
    t=textof(raw); w=len(t.split())
    if w<150 or not LETTER.search(t[:6000]): skip.append((path,w)); return
    s,sh=sig(raw),shingle(raw)
    if s in have_sig or (sh and sh in have_sh):
        dup.append((path, have_sig.get(s) or have_sh.get(sh))); return
    local=os.path.join(SITE,path.lstrip('/'))
    os.makedirs(os.path.dirname(local),exist_ok=True)
    open(local,'wb').write(raw)
    have_sig[s]=os.path.relpath(local,SITE)
    if sh: have_sh[sh]=os.path.relpath(local,SITE)
    kept.append((path,w,src)); print(f"  KEEP {w:>6}w {src:<8} {path}",flush=True)

def grab(path):
    url=HOST+urllib.parse.quote(path,safe="/%")
    try: raw,src=fetch(url),"live"
    except Exception: raw,src=wayback(url),"wayback"
    consider(path,raw,src)
    time.sleep(0.25)

print("(a) reviewer's named paths")
for p in NAMED: grab(p)

print("\n(b) anything from the original list now missing from disk")
gone=[l.strip() for l in open(os.path.join(ROOT,"letter-paths.txt"))
      if l.strip() and not os.path.exists(os.path.join(SITE,l.strip().lstrip('/')))]
print(f"    {len(gone)} paths to re-check")
for p in gone: grab(p)

print(f"\n=== round 3 ===\n  kept {len(kept)}  dup {len(dup)}  "
      f"not-letters {len(skip)}  unreachable {len(miss)}")
json.dump({"kept":kept,"dup":dup[:40],"skip":skip[:40]},
          open(os.path.join(ROOT,"round3-result.json"),"w"),indent=1)
