#!/usr/bin/env python3
"""Export the retrieval index to search-index.json so index.html can search in the browser.

    python3 build_search.py

GitHub Pages serves static files only, so the page cannot call retrieve.py. Instead this
dumps the exact state retrieve.Retriever builds -- both BM25 arms' postings, lengths and
b, plus the thesaurus tables -- and search.js replays the same arithmetic over it.
IDF is not stored: it is a pure function of document frequency and is recomputed in JS.

test_static_search.py checks the JS ranking against retrieve.py on every question we
have. Re-run both after any change to briefs.json, the corpus, bm25.py or thesaurus.py.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from halbert import bm25, corpus, retrieve, thesaurus   # noqa: E402

OUT = os.path.join(HERE, "search-index.json")


def arm(index, paths, pos):
    """One BM25 index -> {b, k1, avgdl, doc ids, lengths, postings as [doc, tf, ...]}."""
    post = {}
    for i, tf in enumerate(index.tf):
        for t, f in tf.items():
            post.setdefault(t, []).extend((i, f))
    # Posting order must match Python's (doc order), so score accumulation -- and so
    # tie-breaking between equal scores -- replays identically in the browser.
    # search.js keys fused scores by letter, so a brief for a letter the corpus dropped
    # (a dedup casualty) would collide with every other one. Fail loudly instead.
    orphans = [p for p in paths if p not in pos]
    if orphans:
        sys.exit("briefs without a letter in the corpus: %s" % orphans[:5])
    return {"k1": index.k1, "b": index.b, "avgdl": index.avgdl,
            "doc": [pos[p] for p in paths], "len": index.len, "post": post}


def main():
    docs, _ = corpus.load()
    R = retrieve.Retriever(docs)
    pos = {d["path"]: i for i, d in enumerate(docs)}

    meta = []
    for d in docs:
        b = R.briefs.get(d["path"]) or {}
        meta.append({"p": d["path"], "t": d["title"] or d["path"], "w": d["words"],
                     "d": d.get("date") or "", "s": b.get("subject", ""),
                     "k": b.get("kind", ""), "a": b.get("author", "")})

    out = {
        "docs": meta,
        "aug": arm(R.aug_index, [d["path"] for d in R.aug_index.docs], pos),
        "brief": arm(R.brief_index, [d["path"] for d in R.brief_index.docs], pos),
        "fuse": {"pool": 40, "top": retrieve.TOP_K, "w_aug": retrieve.W_AUG,
                 "w_brief": retrieve.W_BRIEF, "demote": retrieve.DEMOTE},
        "stop": sorted(bm25.STOP),
        "thes": {"phrases": thesaurus.PHRASES, "words": thesaurus.WORDS,
                 "noise": sorted(thesaurus.NOISE)},
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"), ensure_ascii=False)
    print("search-index.json — %d letters, %.1f MB"
          % (len(docs), os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
