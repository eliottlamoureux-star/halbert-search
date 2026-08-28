#!/usr/bin/env python3
"""BM25 length-normalisation and kind-demotion, tuned by measurement."""
import json, sys
sys.path.insert(0,'.')
from halbert import corpus, bm25, thesaurus, retrieve

docs,_=corpus.load()
key=json.load(open('answer_key.json',encoding='utf-8'))
briefs=json.load(open('briefs.json',encoding='utf-8'))
ans=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
BT={p:retrieve.brief_text(b) for p,b in briefs.items()}

def build(b_letter, b_brief, k1=1.2):
    aug=bm25.BM25([{"path":d['path'],"text":d['text']+' '+BT.get(d['path'],''),
                    "title":d['title'],"words":d['words']} for d in docs], k1=k1, b=b_letter)
    br =bm25.BM25([{"path":p,"text":t,"title":"","words":0}
                   for p,t in BT.items() if t.strip()], k1=k1, b=b_brief)
    return aug, br

def score(aug, br, dem, top=8):
    hit=0
    for q,want in ans:
        terms=' '.join(thesaurus.expand(q)); comb={}
        for idx,w in ((aug,1.0),(br,1.0)):
            hits=idx.search(terms,top=40)
            if not hits: continue
            best=hits[0][1] or 1.0
            for d,s in hits: comb[d['path']]=comb.get(d['path'],0.0)+w*(s/best)
        got=[p for p,_ in sorted(((p,s*dem.get((briefs.get(p) or {}).get('kind','teaching'),1.0))
             for p,s in comb.items()),key=lambda kv:-kv[1])[:top]]
        if want & set(got): hit+=1
    return 100.0*hit/len(ans)

D0={"pitch":0.55,"aside":0.45,"admin":0.25,"memorial":0.20}
print("length normalisation (b) -- lower means less penalty for long letters")
print("%-22s %7s %7s" % ("b_letter : b_brief","@8","@12"))
best=(0,None)
for bl in (0.35,0.5,0.65,0.75):
    for bb in (0.5,0.75):
        aug,br=build(bl,bb)
        s8=score(aug,br,D0); s12=score(aug,br,D0,12)
        print("%-22s %6.1f%% %6.1f%%" % ("%g : %g"%(bl,bb), s8, s12))
        if s8>best[0]: best=(s8,(bl,bb))
bl,bb=best[1]; print("\nbest b = %g : %g" % (bl,bb))

aug,br=build(bl,bb)
print("\ndemotion strength at that setting")
for name,D in [("none",{}),("mild",{"pitch":0.8,"aside":0.7,"admin":0.4,"memorial":0.3}),
               ("current",D0),("hard",{"pitch":0.4,"aside":0.3,"admin":0.1,"memorial":0.1})]:
    print("  %-9s @8 %5.1f%%   @12 %5.1f%%" % (name, score(aug,br,D), score(aug,br,D,12)))
