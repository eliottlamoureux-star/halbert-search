#!/usr/bin/env python3
"""Does proximity rerank help? Measured on the 315-question set (tuning set)."""
import json, sys
sys.path.insert(0,'.')
from halbert import corpus, retrieve, proximity
docs,_=corpus.load(); key=json.load(open('answer_key.json',encoding='utf-8'))
ans=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
r=retrieve.Retriever(docs)
CAND=40

base=[]
for q,want in ans:
    base.append((q,want,r.search(q,top=CAND)))

def metrics(rer, top):
    hit=0; mrr=0.0
    for q,want,hits in base:
        h = rer(q,hits) if rer else hits
        paths=[d['path'] for d,_ in h][:top]
        for i,p in enumerate(paths,1):
            if p in want:
                hit+=1; mrr+=1.0/i; break
    n=len(base)
    return 100.0*hit/n, mrr/n

b20,bm=metrics(None,20); b5,b5m=metrics(None,5)
print("baseline            recall@5 %.1f%%  recall@20 %.1f%%  MRR %.3f" % (b5,b20,bm))
print()
print("%-22s %9s %10s %8s" % ("proximity weight/window","recall@5","recall@20","MRR"))
for w in (0.10,0.20,0.35,0.50,0.80):
    for win in (8,12,20):
        f=lambda q,h,w=w,win=win: proximity.rerank(h,q,weight=w,window=win)
        r5,_=metrics(f,5); r20,m=metrics(f,20)
        flag=" <--" if m>bm+0.005 else ""
        print("%-22s %8.1f%% %9.1f%% %8.3f%s" % ("w=%.2f win=%d"%(w,win), r5, r20, m, flag))
