#!/usr/bin/env python3
"""Sweep the weight of the `asks` bridge, and ablate it.

W_ASKS=0 is the ablation: it removes the bridge entirely and must reproduce the
pre-bridge number exactly. If it does not, something else changed and the sweep is
measuring the wrong thing.

Reports on the DEV set (answer_key.holdout.json). The test set is scored once, at the
end, by check.py -- never here. Tuning against a set is what makes it a dev set.

    ./ask_sweep.py                 # sweep 0..4 on the dev set
    ./ask_sweep.py --key FILE      # score a different key
"""

import json
import sys

sys.path.insert(0, ".")
from halbert import corpus, evaluate, retrieve   # noqa: E402


def main():
    key_path = "answer_key.holdout.json"
    if "--key" in sys.argv:
        key_path = sys.argv[sys.argv.index("--key") + 1]

    docs, _ = corpus.load()
    with open("briefs.json", encoding="utf-8") as fh:
        briefs = json.load(fh)
    with open(key_path, encoding="utf-8") as fh:
        key = json.load(fh)

    have = sum(1 for b in briefs.values() if b.get("asks"))
    print("key: %s   letters carrying asks: %d/%d\n" % (key_path, have, len(briefs)))
    print("  %-8s %-10s %-8s %-8s %s" % ("W_ASKS", "recall@20", "MRR", "r@5", "counts"))

    original = retrieve.W_ASKS
    try:
        for w in (0, 1, 2, 3, 4):
            retrieve.W_ASKS = w
            rows = evaluate.run(docs, briefs, key)
            s = evaluate.summarize(rows)
            ranks = [r["rank"] for r in rows if r.get("rank")]
            at5 = sum(1 for r in ranks if r <= 5) / float(max(s["scored"], 1))
            c = s["counts"]
            print("  %-8d %-10.1f %-8.3f %-8.1f HIT %d  QUERY_BAD %d  BRIEF_BAD %d"
                  % (w, s["recall_at_20"] * 100, s["mrr"], at5 * 100,
                     c.get("HIT", 0), c.get("QUERY_BAD", 0), c.get("BRIEF_BAD", 0)))
    finally:
        retrieve.W_ASKS = original


if __name__ == "__main__":
    main()
