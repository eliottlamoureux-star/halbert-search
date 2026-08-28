#!/usr/bin/env python3
"""7 of 12 remaining failures are `pitch` letters we demote. Is the demotion too hard?"""
import json, sys
sys.path.insert(0,'.')
from halbert import corpus, retrieve
docs,_=corpus.load(); key=json.load(open('answer_key.json',encoding='utf-8'))
briefs=json.load(open('briefs.json',encoding='utf-8'))
ans=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
r=retrieve.Retriever(docs,briefs,demote=False)   # score once without demotion
raw={q:r.search(q,top=60) for q,_ in ans}

def metrics(dem, top):
    hit=0; mrr=0.0
    for q,want in ans:
        sc=[(d['path'], s*dem.get((briefs.get(d['path']) or {}).get('kind','teaching'),1.0))
            for d,s in raw[q]]
        sc.sort(key=lambda kv:-kv[1])
        for i,(p,_) in enumerate(sc[:top],1):
            if p in want: hit+=1; mrr+=1.0/i; break
    n=len(ans); return 100.0*hit/n, mrr/n

cur={"pitch":0.40,"aside":0.30,"admin":0.10,"memorial":0.10}
print("%-34s %9s %10s %8s" % ("demotion","recall@5","recall@20","MRR"))
c5,_=metrics(cur,5); c20,cm=metrics(cur,20)
print("%-34s %8.1f%% %9.1f%% %8.3f   <- current" % ("pitch .40", c5,c20,cm))
for pv in (0.55,0.70,0.85,1.0):
    d=dict(cur); d['pitch']=pv
    r5,_=metrics(d,5); r20,m=metrics(d,20)
    print("%-34s %8.1f%% %9.1f%% %8.3f%s" % ("pitch %.2f"%pv, r5,r20,m, "  <--" if m>cm+0.004 else ""))
print()
for name,d in [("no demotion at all",{}),
               ("only admin/memorial killed",{"admin":0.10,"memorial":0.10}),
               ("guest also demoted 0.7",{**cur,"pitch":0.7,"guest":0.7})]:
    r5,_=metrics(d,5); r20,m=metrics(d,20)
    print("%-34s %8.1f%% %9.1f%% %8.3f" % (name, r5,r20,m))
