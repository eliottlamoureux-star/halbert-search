#!/usr/bin/env python3
"""The browser search must rank exactly like retrieve.py, or the measured recall
(MEASUREMENTS.md) says nothing about the page people actually use.

    python3 build_search.py && python3 test_static_search.py

Runs every question we have (training key + held-out set) through both retrieve.py and
search.js under node, and fails on any difference in terms, order or score.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from halbert import corpus, retrieve, thesaurus   # noqa: E402

NODE = r"""
const fs = require('fs'), Searcher = require(process.argv[1]);
const s = new Searcher(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')));
const qs = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(qs.map(q => {
  const r = s.search(q);
  return {terms: r.terms, hits: r.results.map(h => [h.doc.p, h.score])};
})));
"""


def questions():
    with open(os.path.join(HERE, "answer_key.json"), encoding="utf-8") as fh:
        qs = list(json.load(fh))
    with open(os.path.join(HERE, "questions_holdout.json"), encoding="utf-8") as fh:
        qs += [q["q"] for q in json.load(fh)]
    # the page's example links, plus inputs that stress tokenising and phrase matching
    qs += ["my outreach letters aren't getting replies",
           "how do i find a market that actually wants this",
           "prospects say my price is too high", "what makes a guarantee actually work",
           "cold email cold email A/B test!!", "  ", "zzzz", "Boron", "the the the",
           "Écrire une lettre de vente", "split-test my landing page's headline"]
    return qs


def main():
    docs, _ = corpus.load()
    R = retrieve.Retriever(docs)
    qs = questions()

    js = subprocess.run(
        ["node", "-e", NODE, os.path.join(HERE, "search.js"),
         os.path.join(HERE, "search-index.json")],
        input=json.dumps(qs), capture_output=True, text=True, check=True)
    got = json.loads(js.stdout)

    bad = 0
    for q, g in zip(qs, got):
        terms = thesaurus.expand(q)
        want = [(d["path"], s) for d, s in R.search(q, terms=terms)] if q.strip() else []
        if not q.strip():
            g["hits"] = []   # the page never searches a blank box; neither does serve.py
        same = (g["terms"] == terms and len(g["hits"]) == len(want) and all(
            gp == wp and abs(gs - ws) < 1e-9 for (gp, gs), (wp, ws) in zip(g["hits"], want)))
        if not same:
            bad += 1
            if bad <= 5:
                print("MISMATCH %r\n  py: %s\n  js: %s" % (
                    q, [p for p, _ in want[:5]], [p for p, _ in g["hits"][:5]]))
    print("%d/%d questions rank identically" % (len(qs) - bad, len(qs)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
