"""Assemble answer_key.test.json from BOTH judging routes, and report their agreement.

Two independent routes decide what answers what:

  engine-pool judges  read key_pools_test/ -- candidates the engine surfaced. Fast, but
                      structurally blind to any letter the engine never ranked, so on its
                      own it measures the engine against itself.
  document-side       read all 346 letters and say which questions each answers, never
                      seeing a search result. Blind to the engine, so it can find exactly
                      what the engine misses.

The union is the key. The DISAGREEMENT is the more interesting output: on the previous
key the two routes agreed at Cohen kappa = 0.34, which means that key was a union of two
noisy samples rather than a ground truth, and every number derived from it inherited that.
This module prints kappa so the same thing cannot happen silently twice.

    python3 -m halbert.key_test          # check and write
    python3 -m halbert.key_test --dry    # check only
"""

import json
import os
import sys

from . import corpus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(HERE, "questions_test.json")
POOLS = os.path.join(HERE, "key_pools_test")
JUDGE_PARTS = os.path.join(HERE, "key_parts_test")
DOC_PARTS = os.path.join(HERE, "docside_test_parts")
KEY = os.path.join(HERE, "answer_key.test.json")


def _load_dir(path, prefix="part_"):
    out, problems = [], []
    if not os.path.isdir(path):
        return out, ["%s does not exist" % os.path.basename(path)]
    for f in sorted(x for x in os.listdir(path)
                    if x.startswith(prefix) and x.endswith(".json")):
        try:
            with open(os.path.join(path, f), encoding="utf-8") as fh:
                out.append((f, json.load(fh)))
        except ValueError as exc:
            problems.append("%s: invalid JSON (%s)" % (f, exc))
    return out, problems


def _kappa(a_yes, b_yes, universe):
    """Cohen's kappa over a shared decision universe of (question, letter) pairs."""
    both = len(a_yes & b_yes)
    a_only = len(a_yes - b_yes)
    b_only = len(b_yes - a_yes)
    neither = len(universe) - both - a_only - b_only
    n = float(max(len(universe), 1))
    po = (both + neither) / n
    pa1, pb1 = (both + a_only) / n, (both + b_only) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    k = (po - pe) / (1 - pe) if pe < 1 else 0.0
    return k, both, a_only, b_only


def build(dry=False):
    with open(QUESTIONS, encoding="utf-8") as fh:
        questions = json.load(fh)
    qtext = [q["q"] for q in questions]
    qindex = {q: i for i, q in enumerate(qtext)}
    cat = {q["q"]: q.get("category", "") for q in questions}

    docs, _ = corpus.load()
    valid = set(d["path"] for d in docs)

    judged, p1 = _load_dir(JUDGE_PARTS)
    docside, p2 = _load_dir(DOC_PARTS)
    problems = p1 + p2

    # route 1: engine-pool judges
    jyes, seen_q = set(), set()
    for fname, part in judged:
        for row in part:
            q = row.get("q", "")
            if q not in qindex:
                problems.append("%s: unknown question %r" % (fname, q[:40]))
                continue
            seen_q.add(q)
            for p in row.get("answers", []) or []:
                if p in valid:
                    jyes.add((q, p))
                else:
                    problems.append("%s: unknown path %s" % (fname, p))

    # route 2: document-side readers
    dyes, seen_docs = set(), set()
    for fname, part in docside:
        for path, idxs in part.items():
            if path not in valid:
                problems.append("%s: unknown path %s" % (fname, path))
                continue
            seen_docs.add(path)
            for i in idxs or []:
                if isinstance(i, int) and 0 <= i < len(qtext):
                    dyes.add((qtext[i], path))
                else:
                    problems.append("%s: bad question index %r" % (fname, i))

    # Agreement is only meaningful where BOTH routes could have said yes: a letter the
    # engine never pooled was never offered to the judge, so counting it as a judge "no"
    # would manufacture agreement out of the engine's blind spot.
    pools, p3 = _load_dir(POOLS, prefix="pool_")
    problems += p3
    universe = set()
    for _, part in pools:
        for row in part:
            q = row.get("q", "")
            if q in qindex:
                for c in row.get("candidates", []):
                    universe.add((q, c["path"]))
    k, both, jonly, donly = _kappa(jyes & universe, dyes & universe, universe)

    key = {}
    for q in qtext:
        ans = sorted(set(p for (qq, p) in (jyes | dyes) if qq == q))
        key[q] = {"answers": ans, "category": cat.get(q, "")}

    empty = sum(1 for v in key.values() if not v["answers"])
    pct = 100.0 * empty / max(len(key), 1)
    sizes = [len(v["answers"]) for v in key.values() if v["answers"]]

    print("questions        : %d" % len(key))
    print("judge parts      : %d files, %d questions covered" % (len(judged), len(seen_q)))
    print("docside parts    : %d files, %d letters covered of %d"
          % (len(docside), len(seen_docs), len(valid)))
    print("answers          : %d from judges, %d from docside, %d in the union"
          % (len(jyes), len(dyes), len(jyes | dyes)))
    print("NOANSWER         : %d (%.0f%%)" % (empty, pct))
    if sizes:
        print("answers/question : min %d median %d max %d"
              % (min(sizes), sorted(sizes)[len(sizes) // 2], max(sizes)))
    print("route agreement  : kappa %.3f  (both %d, judge-only %d, docside-only %d)"
          % (k, both, jonly, donly))
    if k < 0.45:
        print("    ! the two routes largely disagree. The key is a union of two noisy")
        print("      samples, not a ground truth. Treat every number from it as a band.")

    missing_q = [q for q in qtext if q not in seen_q]
    missing_d = sorted(valid - seen_docs)
    for m in problems[:8]:
        print("  ! %s" % m)
    for q in missing_q[:4]:
        print("  - unjudged: %s" % q[:58])
    for d in missing_d[:4]:
        print("  - unread letter: %s" % d)

    ok = (not problems and not missing_q and not missing_d and 15 <= pct <= 65)
    if not ok:
        print("\nNOT WRITTEN -- fix the above first (NOANSWER band is 15-65%)")
        return 1
    if dry:
        print("\ndry run -- nothing written")
        return 0
    with open(KEY, "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=1, ensure_ascii=False)
    print("\nwrote answer_key.test.json")
    return 0


if __name__ == "__main__":
    sys.exit(build(dry="--dry" in sys.argv))
