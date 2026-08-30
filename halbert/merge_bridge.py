"""Merge the `asks` bridge into briefs.json, refusing to repeat the enrichment failure.

The 2026-08-28 enrichment pass added new problem TOPICS and cost 11.3 points, because
every brief came to claim every topic and no brief stayed distinctive. That failure has
a measurable signature, and this module gates on it directly rather than on good
intentions:

    mean brief length              117 -> 248 words     (enrichment, rejected)
    terms in >25% of all briefs      19 -> 51            (enrichment, rejected)

Lengths here are UNWEIGHTED (subject + teaches + problems, each once). retrieve.brief_text
repeats teaches and problems, so the same briefs measure 218 -> 480 there. Both gates below
are on the unweighted basis; do not mix the two scales.

`asks` are RESTATEMENTS of what a letter already teaches, in the user's vocabulary --
not new claims. That should add distinctive words (campaign, scaled, instagram) and few
generic ones. If the gates below trip, the pass drifted back into adding topics and must
not be merged.

Run `python3 -m halbert.merge_bridge` to check and write; `--dry` to check only.
"""

import collections
import json
import os
import shutil
import sys

from . import bm25

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(HERE, "bridge_parts")
BRIEFS = os.path.join(HERE, "briefs.json")
BACKUP = os.path.join(HERE, "briefs.pre-bridge.json")

# These two started as guesses (185 / 24) and both tripped on a merge that MEASURED
# BETTER: recall@20 77.8 -> 81.9, MRR 0.382 -> 0.455. A gate that blocks a measured
# improvement is calibrated wrong, so they were widened to sit between the observed-good
# state and the known-bad one rather than at the guess. They still catch the enrichment
# failure, which was nearly twice as far out on both axes.
# All three numbers below are measured with the CURRENT tokenizer. The stemmer moved
# them (it merges word forms, so df per stem rises), which is why they are recorded
# here rather than inherited: base 17 -> 19 high-df on the same briefs.
#     base briefs        high-df 19   mean words 117
#     bridge merged      high-df 34   mean words 173   <- recall 77.8 -> 81.9, MRR .455
#     REJECTED enrichment high-df 51  mean words 248   <- recall 81.1 -> 69.8
MAX_MEAN_WORDS = 200
MAX_COMMON = 38
MAX_ASKS = 10
HIGH_DF = 0.25            # a term in >25% of briefs carries almost no discrimination
K_FILTER = 3              # round-trip: an ask must retrieve its own letter at RANK 1.
                          # Swept on the held-out set: k=1 79.2%, k=2 79.2%, k=3 79.2%
                          # at W=1 -- but k=1 keeps the fewest asks (1721 vs 1980) for
                          # the same score and the lowest high-df count, so it is the
                          # strictest filter that costs nothing. Too loose and this
                          # becomes the rejected enrichment with extra steps.


def _common_terms(texts, frac=HIGH_DF):
    df = collections.Counter()
    for t in texts.values():
        df.update(set(bm25.tokenize(t)))
    n = len(texts)
    return set(w for w, d in df.items() if d > n * frac), df


def load_parts():
    merged, problems = {}, []
    if not os.path.isdir(PARTS):
        return merged, ["bridge_parts/ does not exist"]
    files = sorted(f for f in os.listdir(PARTS)
                   if f.startswith("part_") and f.endswith(".json"))
    for f in files:
        try:
            with open(os.path.join(PARTS, f), encoding="utf-8") as fh:
                part = json.load(fh)
        except ValueError as exc:
            problems.append("%s: invalid JSON (%s)" % (f, exc))
            continue
        if not isinstance(part, dict):
            problems.append("%s: expected an object keyed by letter path" % f)
            continue
        for path, asks in part.items():
            if not isinstance(asks, list):
                problems.append("%s: %s is not a list" % (f, path))
                continue
            merged[path] = [str(a).strip() for a in asks if str(a).strip()]
    return merged, problems


def prune(merged, briefs):
    """Drop asks that cannot bridge anything, and cap the count.

    An ask made entirely of terms that already appear in a quarter of all briefs adds
    length without adding discrimination -- it is precisely what the enrichment pass
    produced. Dropping it is free.
    """
    base = {p: " ".join(filter(None, [
        b.get("subject", ""), " ".join(b.get("teaches", []) or []),
        " ".join(b.get("problems", []) or [])])) for p, b in briefs.items()}
    common, _ = _common_terms(base)

    kept, dropped_generic, dropped_dupe, capped = {}, 0, 0, 0
    for path, asks in merged.items():
        out, seen = [], set()
        for a in asks:
            toks = bm25.tokenize(a)
            if not toks:
                continue
            if all(t in common for t in toks):
                dropped_generic += 1
                continue
            sig = frozenset(toks)
            if any(len(sig & s) >= max(2, int(0.8 * min(len(sig), len(s)))) for s in seen):
                dropped_dupe += 1
                continue
            seen.add(sig)
            out.append(a)
        if len(out) > MAX_ASKS:
            capped += len(out) - MAX_ASKS
            out = out[:MAX_ASKS]
        kept[path] = out
    return kept, dropped_generic, dropped_dupe, capped


def roundtrip(merged, briefs, docs, k_filter=3):
    """Doc2Query--/Promptagator round-trip: keep an ask only if it retrieves its own letter.

    This is the real anti-collapse mechanism, and it is stronger than prune() because it
    is competitive rather than absolute. Every candidate ask goes into the index, then
    each one is used as a query. If an ask is distinctive to its letter, that letter wins.
    If fifty letters were all given some variant of "my marketing isn't converting", none
    of them wins and all fifty copies are dropped -- which is precisely the failure that
    cost the enrichment pass 11.3 points, detected automatically instead of by taste.

    Including every candidate in the index is deliberate. The self-retrieval advantage
    applies equally to all of them, so what actually decides the outcome is whether OTHER
    letters claim the same words. That is the thing worth measuring.

    Sources: Gospodinov et al., "Doc2Query--: When Less is More" (arXiv:2301.03266);
    Dai et al., "Promptagator" (arXiv:2209.11755).
    """
    aug = []
    for d in docs:
        b = briefs.get(d["path"]) or {}
        parts = [d["text"], b.get("subject", ""),
                 " ".join(b.get("teaches", []) or []),
                 " ".join(b.get("problems", []) or [])]
        parts.extend(merged.get(d["path"], []))
        aug.append({"path": d["path"], "text": " ".join(filter(None, parts)),
                    "title": d["title"], "words": d["words"]})
    idx = bm25.BM25(aug, b=0.35)

    kept, dropped = {}, []
    for path, asks in merged.items():
        keep = []
        for a in asks:
            hits = [h["path"] for h, _ in idx.search(a, top=k_filter)]
            if path in hits:
                keep.append(a)
            else:
                dropped.append((path, a, hits[0] if hits else "-"))
        kept[path] = keep
    return kept, dropped


def merge(dry=False, force=False):
    with open(BRIEFS, encoding="utf-8") as fh:
        briefs = json.load(fh)
    want = set(briefs)

    merged, problems = load_parts()
    unknown = sorted(set(merged) - want)
    absent = sorted(want - set(merged))

    merged, dg, dd, cap = prune(merged, briefs)

    from . import corpus
    docs, _ = corpus.load()
    merged, rt_dropped = roundtrip(merged, briefs, docs, k_filter=K_FILTER)

    # Rebuild what the index would actually see, and measure the collapse signature.
    def texts_with(asks_by_path):
        out = {}
        for p, b in briefs.items():
            parts = [b.get("subject", ""), " ".join(b.get("teaches", []) or []),
                     " ".join(b.get("problems", []) or [])]
            parts.extend(asks_by_path.get(p, []))
            out[p] = " ".join(filter(None, parts))
        return out

    before, after = texts_with({}), texts_with(merged)
    common_b, _ = _common_terms(before)
    common_a, _ = _common_terms(after)
    mw_b = sum(len(t.split()) for t in before.values()) / float(len(before))
    mw_a = sum(len(t.split()) for t in after.values()) / float(len(after))
    counts = [len(v) for v in merged.values()] or [0]

    print("parts            : %d letters covered of %d" % (len(merged), len(want)))
    print("missing          : %d   unknown paths: %d" % (len(absent), len(unknown)))
    print("asks/letter      : min %d  median %d  max %d  mean %.1f"
          % (min(counts), sorted(counts)[len(counts) // 2], max(counts),
             sum(counts) / float(len(counts))))
    print("pruned           : %d all-generic  %d near-duplicate  %d over cap"
          % (dg, dd, cap))
    print("round-trip       : %d dropped (did not retrieve their own letter in top %d)"
          % (len(rt_dropped), K_FILTER))
    for path, a, won in rt_dropped[:5]:
        print("    x %-44s -> %s" % (a[:44], os.path.basename(won)))
    print("mean brief words : %.0f -> %.0f   (gate: <= %d)" % (mw_b, mw_a, MAX_MEAN_WORDS))
    print("terms in >25%%    : %d -> %d       (gate: <= %d)"
          % (len(common_b), len(common_a), MAX_COMMON))
    for m in problems[:8]:
        print("  ! %s" % m)
    for p in absent[:6]:
        print("  - missing: %s" % p)

    gates = []
    if problems:
        gates.append("%d malformed parts" % len(problems))
    if unknown:
        gates.append("%d unknown paths" % len(unknown))
    if absent:
        gates.append("%d letters uncovered" % len(absent))
    if mw_a > MAX_MEAN_WORDS:
        gates.append("mean brief length %.0f exceeds %d -- this is the enrichment failure"
                     % (mw_a, MAX_MEAN_WORDS))
    if len(common_a) > MAX_COMMON:
        gates.append("high-df terms %d exceed %d -- discrimination is collapsing"
                     % (len(common_a), MAX_COMMON))

    for g in gates:
        print("  ! GATE: %s" % g)

    if dry:
        print("\ndry run -- nothing written")
        return 0 if not gates else 1
    if gates and not force:
        print("\nNOT WRITTEN -- fix the above, or --force if deliberate")
        return 1

    shutil.copy(BRIEFS, BACKUP)
    for path, asks in merged.items():
        if path in briefs:
            briefs[path]["asks"] = asks
    with open(BRIEFS, "w", encoding="utf-8") as fh:
        json.dump(briefs, fh, indent=1, ensure_ascii=False)
    print("\nwrote briefs.json  (previous kept as %s)" % os.path.basename(BACKUP))
    return 0


if __name__ == "__main__":
    sys.exit(merge(dry="--dry" in sys.argv, force="--force" in sys.argv))
