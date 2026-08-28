#!/usr/bin/env python3
"""How much should each brief field weigh inside the indexed text?"""
import json, sys
sys.path.insert(0,'.')
from halbert import corpus, bm25, thesaurus
docs,_=corpus.load(); key=json.load(open('answer_key.json',encoding='utf-8'))
briefs=json.load(open('briefs.json',encoding='utf-8'))
ans=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
DEM={"pitch":0.40,"aside":0.30,"admin":0.10,"memorial":0.10}

def mk(ns,nt,np_):
    return {p:' '.join([b.get('subject','')]*ns
                       +[' '.join(b.get('teaches',[]) or [])]*nt
                       +[' '.join(b.get('problems',[]) or [])]*np_) for p,b in briefs.items()}

def score(bt, top=12):
    aug=bm25.BM25([{"path":d['path'],"text":d['text']+' '+bt.get(d['path'],''),
                    "title":d['title'],"words":d['words']} for d in docs], b=0.35)
    br =bm25.BM25([{"path":p,"text":t,"title":"","words":0} for p,t in bt.items() if t.strip()], b=0.75)
    hit=0
    for q,want in ans:
        terms=' '.join(thesaurus.expand(q)); comb={}
        for idx in (aug,br):
            hits=idx.search(terms,top=40)
            if not hits: continue
            best=hits[0][1] or 1.0
            for d,s in hits: comb[d['path']]=comb.get(d['path'],0.0)+s/best
        got=[p for p,_ in sorted(((p,s*DEM.get((briefs.get(p) or {}).get('kind','teaching'),1.0))
             for p,s in comb.items()),key=lambda kv:-kv[1])[:top]]
        if want & set(got): hit+=1
    return 100.0*hit/len(ans)

print("%-24s %7s %7s" % ("subject:teaches:problems","@8","@12"))
for ns,nt,np_ in [(1,1,1),(1,1,2),(1,1,3),(1,2,2),(1,1,4),(2,1,3),(1,0,2),(0,1,2)]:
    bt=mk(ns,nt,np_)
    print("%-24s %6.1f%% %6.1f%%" % ("%d : %d : %d"%(ns,nt,np_), score(bt,8), score(bt,12)))
