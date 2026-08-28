#!/usr/bin/env python3
"""Round 4: enumerate the sequential naming schemes exhaustively."""
import os, re, time, html, hashlib, urllib.parse, urllib.request, threading, queue, json

ROOT=os.path.dirname(os.path.abspath(__file__)); SITE=os.path.join(ROOT,"site")
UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOST="https://www.thegaryhalbertletter.com"

def textof(raw):
    if isinstance(raw,bytes): raw=raw.decode('utf-8','ignore')
    t=re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>',' ',raw)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'(?s)<[^>]+>',' ',t))).strip()
def wordsof(raw): return re.sub(r'[^a-z0-9 ]+','',textof(raw).lower()).split()
def shing(ws,k=8): return {' '.join(ws[i:i+k]) for i in range(max(0,len(ws)-k+1))}

have={}
for dp,_,fs in os.walk(SITE):
    for fn in fs:
        if not fn.lower().endswith(('.htm','.html')): continue
        p=os.path.join(dp,fn)
        try: w=wordsof(open(p,'rb').read())
        except Exception: continue
        if len(w)>=40: have[hashlib.md5(' '.join(w).encode()).hexdigest()]=os.path.relpath(p,SITE)
print(f"baseline: {len(have)} distinct texts held",flush=True)

# ---- candidate space ----------------------------------------------------
cands=[]
for yy in list(range(85,100))+list(range(0,7)):          # 1985-2006
    for mm in range(1,13):
        cands.append(f"/new/b/{mm:02d}{yy:02d}.htm")
for n in range(1,60):                                     # /fNN/N.html|HTM
    for d in range(1,51):
        cands.append(f"/f{d:02d}/{n}.html")
        cands.append(f"/f{d:02d}/{n}.HTM")
    if n>14: break
for n in range(67,131): cands.append(f"/HOTD/{n}.htm")    # confirm HOTD ceiling
cands=[c for c in cands if not os.path.exists(os.path.join(SITE,c.lstrip('/')))]
print(f"probing {len(cands)} candidate URLs\n",flush=True)

LETTER=re.compile(r'(?i)(gary\s+halbert|dear\s+friend|jewfish\s+creek|halbertism)')
lock=threading.Lock(); kept=[]; dup=[]; skip=0; miss=0

def worker(q):
    global skip,miss
    while True:
        try: path=q.get_nowait()
        except queue.Empty: return
        url=HOST+urllib.parse.quote(path,safe="/%")
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*;q=0.8"})
            with urllib.request.urlopen(r,timeout=25) as x: raw=x.read()
        except Exception:
            with lock: miss+=1
            time.sleep(0.15); continue
        t=textof(raw); w=len(t.split())
        if w<40 or not LETTER.search(t[:6000]):
            with lock: skip+=1
            time.sleep(0.15); continue
        ws=wordsof(raw); h=hashlib.md5(' '.join(ws).encode()).hexdigest()
        with lock:
            if h in have:
                dup.append((path,have[h]))
            else:
                loc=os.path.join(SITE,path.lstrip('/'))
                os.makedirs(os.path.dirname(loc),exist_ok=True)
                open(loc,'wb').write(raw)
                have[h]=os.path.relpath(loc,SITE); kept.append((path,w))
                print(f"  KEEP {w:>6}w  {path}",flush=True)
        time.sleep(0.15)

q=queue.Queue()
for c in cands: q.put(c)
ts=[threading.Thread(target=worker,args=(q,),daemon=True) for _ in range(8)]
for t in ts: t.start()
for t in ts: t.join()
print(f"\n=== round 4 ===\n  new {len(kept)}   dup {len(dup)}   not-letters {skip}   404 {miss}")
json.dump({"kept":kept,"dup":dup[:40]},open(os.path.join(ROOT,"round4-result.json"),"w"),indent=1)
