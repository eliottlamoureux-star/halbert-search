#!/usr/bin/env python3
"""Three arms instead of two: his framing, your symptoms, his raw text."""
import json, sys
sys.path.insert(0, '.')
from halbert import corpus, bm25, thesaurus

docs, _ = corpus.load()
key = json.load(open('answer_key.json', encoding='utf-8'))
briefs = json.load(open('briefs.json', encoding='utf-8'))
answerable = [(q, set(v['answers'])) for q, v in key.items() if v['answers']]
by_path = {d['path']: d for d in docs}
DEMOTE = {"pitch":0.55,"aside":0.45,"admin":0.25,"memorial":0.20}

def mk(fn):
    ds=[{"path":p,"text":fn(b),"title":"","words":0} for p,b in briefs.items() if fn(b).strip()]
    return bm25.BM25(ds)

I_letter  = bm25.BM25(docs)
I_about   = mk(lambda b: (b.get('subject','')+' '+' '.join(b.get('teaches',[]) or [])))
I_problem = mk(lambda b: ' '.join(b.get('problems',[]) or []))

def search(q, arms, top=8, pool=40, rrf=False, demote=True):
    terms=' '.join(thesaurus.expand(q)); comb={}
    for idx,w in arms:
        if w==0: continue
        hits=idx.search(terms, top=pool)
        if not hits: continue
        best=hits[0][1] or 1.0
        for rank,(d,s) in enumerate(hits,1):
            add = w*(1.0/(60+rank)) if rrf else w*(s/best)
            comb[d['path']]=comb.get(d['path'],0.0)+add
    if demote:
        comb={p:s*DEMOTE.get((briefs.get(p) or {}).get('kind','teaching'),1.0) for p,s in comb.items()}
    return [p for p,_ in sorted(comb.items(), key=lambda kv:-kv[1])[:top]]

def score(arms, top=8, rrf=False, demote=True):
    return 100.0*sum(1 for q,w in answerable if w & set(search(q,arms,top,rrf=rrf,demote=demote)))/len(answerable)

print("%-34s %7s %7s" % ("letter : about : problems","norm","rrf"))
for wl,wa,wp in [(1,1,1),(1,0,1),(0,1,1),(0,0,1),(0.5,1,2),(0.5,0.5,2),(1,1,2),(0.5,1,3),(0.3,1,3),(0.5,0.5,3)]:
    arms=[(I_letter,wl),(I_about,wa),(I_problem,wp)]
    print("%-34s %6.1f%% %6.1f%%" % ("%g : %g : %g"%(wl,wa,wp),
          score(arms), score(arms,rrf=True)))

best=[(I_letter,0.5),(I_about,1),(I_problem,2)]
print("\nheadroom, 0.5:1:2 normalised + demote")
for k in (5,8,12,20): print("   recall@%-3d %.1f%%" % (k, score(best,top=k)))
