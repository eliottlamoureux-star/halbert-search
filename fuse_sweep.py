#!/usr/bin/env python3
"""Pick fusion weights and the kind-demotion by measurement, not taste."""
import json, sys, itertools
sys.path.insert(0, '.')
from halbert import corpus, retrieve

docs, _ = corpus.load()
key = json.load(open('answer_key.json', encoding='utf-8'))
briefs = json.load(open('briefs.json', encoding='utf-8'))
answerable = [(q, set(v['answers'])) for q, v in key.items() if v['answers']]
print("answerable questions: %d\n" % len(answerable))

def score(r, wl, wb, top=8):
    hit = 0
    for q, want in answerable:
        got = [d['path'] for d, _ in r.search(q, top=top, w_letter=wl, w_brief=wb)]
        if want & set(got):
            hit += 1
    return 100.0 * hit / len(answerable)

r_plain  = retrieve.Retriever(docs, briefs, demote=False)
r_demote = retrieve.Retriever(docs, briefs, demote=True)

print("%-28s %8s %8s" % ("arms (letter:brief)", "no dem", "demote"))
for wl, wb in [(1,0), (0,1), (1,1), (1,0.6), (0.6,1), (1,1.5), (1,2), (1,3)]:
    a = score(r_plain, wl, wb)
    b = score(r_demote, wl, wb)
    print("%-28s %7.1f%% %7.1f%%" % ("%g : %g" % (wl, wb), a, b))

print("\nheadroom at the best setting (1:2, demote):")
for k in (5, 8, 12, 20):
    print("   recall@%-3d %.1f%%" % (k, score(r_demote, 1, 2, top=k)))
