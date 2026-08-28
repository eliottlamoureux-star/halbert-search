#!/usr/bin/env python3
"""Round 5: mine EVERY historical version of the site's index/archive pages.

The index page was rewritten many times; each old version links letters the
current one dropped. This reads them all out of Wayback.
"""
import json, re, os, urllib.parse, urllib.request, time, collections, threading, queue

ROOT=os.path.dirname(os.path.abspath(__file__)); SITE=os.path.join(ROOT,'site')
UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
def get(u,t=40):
    r=urllib.request.Request(u,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=t) as x: return x.read().decode('utf-8','ignore')

PAGES=["thegaryhalbertletter.com/",
       "thegaryhalbertletter.com/newsletter-archives.htm",
       "thegaryhalbertletter.com/newsletters/",
       "thegaryhalbertletter.com/index.html",
       "thegaryhalbertletter.com/Newletter-archives-protected/newsletter-archives.htm",
       "thegaryhalbertletter.com/1FOTGHLOutermainFrame.html",
       "thegaryhalbertletter.com/WhatsNew/1WhatsNew.html"]
snaps=[]
for p in PAGES:
    try:
        raw=get("http://web.archive.org/cdx/search/cdx?url="+urllib.parse.quote(p)
                +"&output=text&fl=timestamp&collapse=digest&limit=300")
        ts=[l.strip() for l in raw.splitlines() if l.strip()]
        snaps+=[(p,t) for t in ts]
        print(f"  {len(ts):>4} snapshots  {p}",flush=True)
    except Exception as e: print("  ERR",p,e,flush=True)
    time.sleep(0.4)
print(f"\nmining {len(snaps)} snapshots\n",flush=True)

lock=threading.Lock(); found=collections.Counter(); newp=set(); done=[0]
def worker(q):
    while True:
        try: p,ts=q.get_nowait()
        except queue.Empty: return
        try: h_=get(f"https://web.archive.org/web/{ts}id_/http://{p}")
        except Exception:
            with lock: done[0]+=1
            time.sleep(0.2); continue
        loc=[]
        for m in re.finditer(r'(?i)href\s*=\s*["\']([^"\']+)["\']',h_):
            h=re.sub(r'^https?://web\.archive\.org/web/\d+(?:id_)?/','',m.group(1))
            pr=urllib.parse.urlparse(h)
            if pr.netloc and 'thegaryhalbertletter' not in pr.netloc.lower(): continue
            path=urllib.parse.unquote(pr.path)
            if not path.lower().endswith(('.htm','.html')): continue
            if not path.startswith('/'): path='/'+path
            loc.append(path)
        with lock:
            for path in loc:
                found[path]+=1
                if not os.path.exists(os.path.join(SITE,path.lstrip('/'))): newp.add(path)
            done[0]+=1
            if done[0]%40==0:
                print(f"    {done[0]}/{len(snaps)} snapshots, {len(newp)} unheld",flush=True)
        time.sleep(0.2)

q=queue.Queue()
for s in snaps: q.put(s)
ts_=[threading.Thread(target=worker,args=(q,),daemon=True) for _ in range(6)]
for t in ts_: t.start()
for t in ts_: t.join()

print(f"\n  distinct .htm links across all historical versions: {len(found)}")
print(f"  NOT currently held: {len(newp)}")
open(os.path.join(ROOT,'histindex-candidates.txt'),'w').write('\n'.join(sorted(newp))+'\n')
