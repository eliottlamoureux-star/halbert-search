"""Merge enriched `problems` lists back into briefs.json.

Keeps a backup and refuses to write on incomplete or degraded input -- an enrichment
pass that produced FEWER phrasings than it replaced would silently lower recall, and
that failure is invisible in a diff of 346 records.
"""

import json
import os
import shutil
import sys

from . import corpus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(HERE, "problems_parts")
BRIEFS = os.path.join(HERE, "briefs.json")
BACKUP = os.path.join(HERE, "briefs.pre-enrich.json")

MIN_MEAN = 9.0          # the enrichment brief asks for 12-18; below 9 something went wrong


def merge(force=False):
    docs, _ = corpus.load()
    want = set(d["path"] for d in docs)
    with open(BRIEFS, encoding="utf-8") as fh:
        briefs = json.load(fh)

    merged, problems = {}, []
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
            problems.append("%s: expected an object keyed by path" % f)
            continue
        for path, plist in part.items():
            if not isinstance(plist, list):
                problems.append("%s: %s is not a list" % (f, path))
                continue
            merged[path] = [str(x).strip() for x in plist if str(x).strip()]

    unknown = set(merged) - want
    absent = want - set(merged)

    old_mean = sum(len(b.get("problems") or []) for b in briefs.values()) / float(len(briefs))
    new_counts = [len(v) for v in merged.values()]
    new_mean = (sum(new_counts) / float(len(new_counts))) if new_counts else 0.0
    thin = [p for p, v in merged.items() if len(v) < 4
            and (briefs.get(p, {}).get("kind") == "teaching")]

    print("parts            : %d files" % len(files))
    print("letters enriched : %d of %d" % (len(merged), len(want)))
    print("missing          : %d   unknown paths: %d" % (len(absent), len(unknown)))
    print("phrasings/letter : %.1f  ->  %.1f" % (old_mean, new_mean))
    print("thin teaching    : %d (<4 phrasings)" % len(thin))
    for m in problems[:8]:
        print("  ! %s" % m)
    for p in sorted(absent)[:6]:
        print("  - missing: %s" % p)

    ok = (not absent and not unknown and not problems and new_mean >= MIN_MEAN
          and new_mean > old_mean)
    if not ok and not force:
        print("\nNOT WRITTEN -- fix the above, or pass --force if this is deliberate")
        return 1

    shutil.copy(BRIEFS, BACKUP)
    for path, plist in merged.items():
        if path in briefs:
            briefs[path]["problems"] = plist
    with open(BRIEFS, "w", encoding="utf-8") as fh:
        json.dump(briefs, fh, indent=1, ensure_ascii=False)
    print("\nwrote briefs.json  (previous kept as %s)" % os.path.basename(BACKUP))
    return 0


if __name__ == "__main__":
    sys.exit(merge(force="--force" in sys.argv))
