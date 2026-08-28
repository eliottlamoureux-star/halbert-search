"""Score retrieval against the answer key, and attribute every failure to a cause.

Questions come from a corpus-blind writer; the key comes from a separate judge. So a
miss here is a real miss, not an artifact of the test set. Bad questions were already
removed at key-build time -- the judge simply found nothing that answers them, which
makes them NOANSWER cases rather than noise.

Failures split two ways, and they need different fixes:

  QUERY_BAD  a key letter's BRIEF matches the query, but its TEXT does not
             -> the rewrite is not producing terms that exist in the letters
  BRIEF_BAD  neither matches
             -> the brief does not describe what the letter actually covers

NOANSWER questions (the key found nothing) are scored separately: they test whether
the engine correctly declines instead of confidently returning its best bad guess.
"""

import json
import os
import sys

from . import bm25, corpus, ground, retrieve, thesaurus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "eval_results.json")
TOP_K = retrieve.TOP_K

JUDGE_SYS = """\
You decide whether a document genuinely answers a question. You are quality-controlling an
evaluation set, so be strict: the question must be substantively addressed, not merely adjacent.

Return JSON only: {"answers": true|false, "why": "<12 words>"}

`true` only if someone with that exact problem would find real help here. Topical overlap is
not enough. If the document only mentions the area in passing, it is false."""


def _judge(question, doc):
    try:
        r = ground._json_call(
            ground.BRIEF_MODEL, JUDGE_SYS,
            "QUESTION: %s\n\nDOCUMENT (%s):\n%s"
            % (question, doc["title"], doc["text"][:18000]), max_tokens=200)
        return bool(r.get("answers")), r.get("why", "")
    except Exception as exc:
        return False, "judge failed: %s" % exc


def brief_text(brief):
    return " ".join(filter(None, [
        brief.get("subject", ""),
        " ".join(brief.get("teaches", []) or []),
        " ".join(brief.get("problems", []) or []),
    ]))


def run(docs, briefs, key, limit=None):
    r = retrieve.Retriever(docs, briefs)
    brief_index = r.brief_index

    items = list(key.items())
    if limit:
        items = items[:limit]

    rows = []
    for i, (q, meta) in enumerate(items, 1):
        want = set(meta["answers"])
        terms = meta.get("terms") or thesaurus.expand(q)
        query = " ".join(terms)
        hits = r.search(q, top=TOP_K, terms=terms)
        got = [d["path"] for d, _ in hits]
        topscore = hits[0][1] if hits else 0.0

        if not want:
            rows.append({"q": q, "verdict": "NOANSWER", "category": meta.get("category"),
                         "top": got[:3], "topscore": round(topscore, 2)})
            continue

        found = [p for p in got if p in want]
        if found:
            rows.append({"q": q, "verdict": "HIT", "category": meta.get("category"),
                         "rank": got.index(found[0]) + 1, "want": sorted(want)})
        else:
            gotb = set(d["path"] for d, _ in brief_index.search(query, top=TOP_K))
            verdict = "QUERY_BAD" if (want & gotb) else "BRIEF_BAD"
            rows.append({"q": q, "verdict": verdict, "category": meta.get("category"),
                         "want": sorted(want), "top": got[:3], "terms": terms})

        if i % 50 == 0:
            print("  evaluated %d/%d" % (i, len(items)), file=sys.stderr)
    return rows


def summarize(rows):
    c = {}
    for r in rows:
        c[r["verdict"]] = c.get(r["verdict"], 0) + 1
    scored = sum(v for k, v in c.items() if k != "NOANSWER")
    hits = c.get("HIT", 0)
    ranks = [r["rank"] for r in rows if r.get("rank")]
    return {
        "questions": len(rows),
        "scored": scored,
        "recall_at_%d" % TOP_K: round(hits / float(scored), 4) if scored else 0.0,
        "mrr": round(sum(1.0 / r for r in ranks) / scored, 4) if scored else 0.0,
        "counts": c,
    }


def report(rows):
    s = summarize(rows)
    k = "recall_at_%d" % TOP_K
    print("\nquestions %d   answerable %d   NOANSWER %d"
          % (s["questions"], s["scored"], s["counts"].get("NOANSWER", 0)))
    print("recall@%d  %.1f%%      MRR %.3f" % (TOP_K, s[k] * 100, s["mrr"]))
    for v in ("HIT", "QUERY_BAD", "BRIEF_BAD"):
        n = s["counts"].get(v, 0)
        print("  %-10s %4d  %5.1f%% of answerable"
              % (v, n, 100.0 * n / max(s["scored"], 1)))

    bycat = {}
    for r in rows:
        if r["verdict"] == "NOANSWER":
            continue
        d = bycat.setdefault(r.get("category") or "?", [0, 0])
        d[0] += 1
        d[1] += r["verdict"] == "HIT"
    print("\n  by category:")
    for cat, (tot, hit) in sorted(bycat.items()):
        print("    %-9s %5.1f%%  (%d/%d)" % (cat, 100.0 * hit / max(tot, 1), hit, tot))
    return s


if __name__ == "__main__":
    from . import key as keymod
    docs, _ = corpus.load()
    with open(ground.BRIEFS, encoding="utf-8") as fh:
        briefs = json.load(fh)
    with open(keymod.KEY, encoding="utf-8") as fh:
        key = json.load(fh)
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = run(docs, briefs, key, limit=lim)
    with open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    report(rows)
