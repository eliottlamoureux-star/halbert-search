#!/usr/bin/env python3
"""Two free ideas for pulling ranks 9-20 into the top 8.

  AUGMENT  index each letter as its own text PLUS its brief -- one index, both vocabularies
  PRF      pseudo-relevance feedback: search briefs, harvest the top hits' distinctive
           terms, add them to the query, search again. Classic RM3. No model, no cost.
"""
import json, sys, re, collections
sys.path.insert(0,'.')
from halbert import corpus, bm25, thesaurus, retrieve

docs,_=corpus.load()
key=json.load(open('answer_key.json',encoding='utf-8'))
briefs=json.load(open('briefs.json',encoding='utf-8'))
answerable=[(q,set(v['answers'])) for q,v in key.items() if v['answers']]
DEMOTE={"pitch":0.55,"aside":0.45,"admin":0.25,"memorial":0.20}
def kf(p): return DEMOTE.get((briefs.get(p) or {}).get('kind','teaching'),1.0)

I_letter=bm25.BM25(docs)
I_brief =bm25.BM25([{"path":p,"text":retrieve.brief_text(b),"title":"","words":0}
                    for p,b in briefs.items() if retrieve.brief_text(b).strip()])
I_aug   =bm25.BM25([{"path":d['path'],
                     "text":d['text']+' '+retrieve.brief_text(briefs.get(d['path'],{})),
                     "title":d['title'],"words":d['words']} for d in docs])

def fuse(hitsets, top):
    comb={}
    for hits,w in hitsets:
        if not hits: continue
        best=hits[0][1] or 1.0
        for d,s in hits: comb[d['path']]=comb.get(d['path'],0.0)+w*(s/best)
    return [p for p,_ in sorted(((p,s*kf(p)) for p,s in comb.items()),key=lambda kv:-kv[1])[:top]]

def prf_terms(q, n_docs=5, n_terms=12):
    """Harvest discriminative terms from the top brief hits."""
    seed=' '.join(thesaurus.expand(q))
    hits=I_brief.search(seed, top=n_docs)
    cnt=collections.Counter()
    for d,_ in hits:
        for t in set(bm25.tokenize(d['text'])):
            if I_brief.idf.get(t,0)>1.5: cnt[t]+=1
    return [t for t,_ in cnt.most_common(n_terms)]

def score(mode, top=8):
    hit=0
    for q,want in answerable:
        terms=' '.join(thesaurus.expand(q))
        if mode=='fuse':
            got=fuse([(I_letter.search(terms,top=40),0.6),(I_brief.search(terms,top=40),1.0)],top)
        elif mode=='aug':
            got=[d['path'] for d,_ in I_aug.search(terms,top=top*3)][:top]
        elif mode=='aug+brief':
            got=fuse([(I_aug.search(terms,top=40),1.0),(I_brief.search(terms,top=40),1.0)],top)
        elif mode=='prf':
            exp=terms+' '+' '.join(prf_terms(q))
            got=fuse([(I_letter.search(exp,top=40),0.6),(I_brief.search(exp,top=40),1.0)],top)
        elif mode=='prf+aug':
            exp=terms+' '+' '.join(prf_terms(q))
            got=fuse([(I_aug.search(exp,top=40),1.0),(I_brief.search(exp,top=40),1.0)],top)
        if want & set(got): hit+=1
    return 100.0*hit/len(answerable)

print("%-14s %8s %8s %8s" % ("mode","@8","@12","@20"))
for m in ('fuse','aug','aug+brief','prf','prf+aug'):
    print("%-14s %7.1f%% %7.1f%% %7.1f%%" % (m, score(m,8), score(m,12), score(m,20)))
