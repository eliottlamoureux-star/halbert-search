"""The answer key: which letters actually answer each blind question.

Split into a free half and a judged half, so no API is needed:

  pool()   pure Python. Candidates from FOUR routes -- letter-BM25 and brief-BM25,
           each with the raw question and the thesaurus-expanded one. The union
           matters: if one route defined the pool it would also define the ceiling,
           and the evaluation could never see what that route misses.
  judge    subagents read pool_NN.json and decide which candidates truly answer the
           question, verifying against full letter text. Written back as key_parts/.
  merge()  validates and assembles answer_key.json.

A question with zero answering letters is a valid result, not a failure. Those are
the only real test of the NOTHING HERE path.
"""

import json
import os
import sys

from . import bm25, corpus, thesaurus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFS = os.path.join(HERE, "briefs.json")
QUESTIONS = os.path.join(HERE, "questions_generated.json")
POOLS = os.path.join(HERE, "key_pools")
PARTS = os.path.join(HERE, "key_parts")
KEY = os.path.join(HERE, "answer_key.json")
POOL_PER_ROUTE = 10


def brief_text(b):
    return " ".join(filter(None, [
        b.get("subject", ""),
        " ".join(b.get("teaches", []) or []),
        " ".join(b.get("problems", []) or []),
    ]))


def pool(batches=8):
    """Free. Writes key_pools/pool_NN.json for the judging agents to consume."""
    docs, _ = corpus.load()
    by_path = {d["path"]: d for d in docs}
    with open(BRIEFS, encoding="utf-8") as fh:
        briefs = json.load(fh)
    with open(QUESTIONS, encoding="utf-8") as fh:
        questions = json.load(fh)

    letter_index = bm25.BM25(docs)
    brief_docs = [{"path": p, "text": brief_text(b), "title": "", "words": 0}
                  for p, b in briefs.items() if brief_text(b).strip()]
    brief_index = bm25.BM25(brief_docs)

    out = []
    for item in questions:
        q = item["q"]
        terms = thesaurus.expand(q)
        seen, cands = set(), []
        for idx in (letter_index, brief_index):
            for query in (q, " ".join(terms)):
                for d, _ in idx.search(query, top=POOL_PER_ROUTE):
                    if d["path"] not in seen:
                        seen.add(d["path"])
                        cands.append(d["path"])
        out.append({
            "q": q, "category": item.get("category", ""), "terms": terms,
            "candidates": [
                {"path": p,
                 "title": by_path[p]["title"] if p in by_path else "",
                 "subject": (briefs.get(p) or {}).get("subject", ""),
                 "teaches": (briefs.get(p) or {}).get("teaches", [])[:3],
                 "problems": (briefs.get(p) or {}).get("problems", [])[:4]}
                for p in cands],
        })

    if not os.path.exists(POOLS):
        os.makedirs(POOLS)
    step = (len(out) + batches - 1) // batches
    for i in range(batches):
        chunk = out[i * step:(i + 1) * step]
        if not chunk:
            continue
        with open(os.path.join(POOLS, "pool_%02d.json" % i), "w", encoding="utf-8") as fh:
            json.dump(chunk, fh, indent=1, ensure_ascii=False)
    sizes = [len(x["candidates"]) for x in out]
    print("pooled %d questions into %d batches" % (len(out), batches))
    print("  candidates per question: min %d  median %d  max %d"
          % (min(sizes), sorted(sizes)[len(sizes) // 2], max(sizes)))
    thin = sum(1 for s in sizes if s <= POOL_PER_ROUTE)
    print("  thin pools (<=%d, means the routes agreed too much): %d"
          % (POOL_PER_ROUTE, thin))
    return out


def merge():
    """Assemble key_parts/*.json into answer_key.json, validating."""
    with open(QUESTIONS, encoding="utf-8") as fh:
        questions = [x["q"] for x in json.load(fh)]
    docs, _ = corpus.load()
    valid = set(d["path"] for d in docs)

    key, problems = {}, []
    files = sorted(f for f in os.listdir(PARTS)
                   if f.startswith("part_") and f.endswith(".json"))
    for f in files:
        try:
            with open(os.path.join(PARTS, f), encoding="utf-8") as fh:
                part = json.load(fh)
        except ValueError as exc:
            problems.append("%s: invalid JSON (%s)" % (f, exc))
            continue
        for row in (part if isinstance(part, list) else part.items()):
            q = row["q"] if isinstance(row, dict) else row[0]
            ans = row.get("answers", []) if isinstance(row, dict) else row[1]
            bad = [p for p in ans if p not in valid]
            if bad:
                problems.append("%s: %d unknown paths for %r" % (f, len(bad), q[:40]))
            key[q] = {"answers": [p for p in ans if p in valid],
                      "category": row.get("category", "") if isinstance(row, dict) else ""}

    missing = [q for q in questions if q not in key]
    empty = sum(1 for v in key.values() if not v["answers"])
    pct = 100.0 * empty / max(len(key), 1)

    print("parts        : %d" % len(files))
    print("keyed        : %d of %d questions" % (len(key), len(questions)))
    print("NOANSWER     : %d (%.0f%%) -- want 15-45%%" % (empty, pct))
    for m in problems[:8]:
        print("  ! %s" % m)
    for q in missing[:5]:
        print("  - unkeyed: %s" % q[:60])

    ok = not missing and not problems and 15 <= pct <= 45
    if ok:
        with open(KEY, "w", encoding="utf-8") as fh:
            json.dump(key, fh, indent=1, ensure_ascii=False)
        print("\nwrote answer_key.json")
    else:
        print("\nNOT WRITTEN -- fix the above first")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--merge" in sys.argv:
        sys.exit(merge())
    pool()
