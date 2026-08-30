#!/usr/bin/env python3
"""The fusion says min-max in its docstring and does divide-by-max in the code.
A pass's 40th-ranked document currently keeps 34-45% of the winner's credit."""
import json, sys
sys.path.insert(0,'.')
from halbert import corpus, bm25, retrieve, thesaurus
docs,_=corpus.load(); key=json.load(open('answer_key.json',encoding='utf-8'))
briefs=json.load(open('briefs.json',encoding='utf-8'))
ans=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
bt={p:retrieve.brief_text(b) for p,b in briefs.items()}
Ia=bm25.BM25([{"path":d['path'],"text":d['text']+' '+bt.get(d['path'],''),
               "title":d['title'],"words":d['words']} for d in docs], b=retrieve.B_LETTER)
Ib=bm25.BM25([{"path":p,"text":t,"title":"","words":0} for p,t in bt.items() if t.strip()], b=retrieve.B_BRIEF)
DEM=retrieve.DEMOTE

def run(norm, dem_pitch=0.40, pool=40, top=20):
    d=dict(DEM); d['pitch']=dem_pitch
    hit5=hit=0; mrr=0.0
    for q,want in ans:
        terms=thesaurus.expand(q); comb={}
        for query in (' '.join(terms), q):
            for idx in (Ia,Ib):
                h=idx.search(query,top=pool)
                if not h: continue
                hi=h[0][1]; lo=h[-1][1]
                for dd,s in h:
                    if norm=='max':    v=s/(hi or 1.0)
                    elif norm=='minmax': v=(s-lo)/((hi-lo) or 1.0)
                    elif norm=='z':
                        import statistics as st
                        vals=[x[1] for x in h]; m=st.mean(vals); sd=st.pstdev(vals) or 1.0
                        v=(s-m)/sd
                    comb[dd['path']]=comb.get(dd['path'],0.0)+v
        sc=sorted(((p,v*d.get((briefs.get(p) or {}).get('kind','teaching'),1.0))
                   for p,v in comb.items()),key=lambda kv:-kv[1])
        paths=[p for p,_ in sc]
        for i,p in enumerate(paths[:top],1):
            if p in want: hit+=1; mrr+=1.0/i; break
        if want & set(paths[:5]): hit5+=1
    n=len(ans); return 100.0*hit5/n, 100.0*hit/n, mrr/n

print("%-28s %9s %10s %8s" % ("normalisation","recall@5","recall@20","MRR"))
for norm in ('max','minmax','z'):
    r5,r20,m=run(norm)
    tag=" <- current (buggy)" if norm=='max' else ""
    print("%-28s %8.1f%% %9.1f%% %8.3f%s" % (norm,r5,r20,m,tag))
print()
print("min-max + independently varying the pitch demotion:")
for pv in (0.40,0.55,0.70,0.85,1.00):
    r5,r20,m=run('minmax',dem_pitch=pv)
    print("   pitch=%.2f              %8.1f%% %9.1f%% %8.3f" % (pv,r5,r20,m))
