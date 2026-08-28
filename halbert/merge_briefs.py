"""Merge briefs_parts/*.json into briefs.json, validating as we go.

Asserts post-conditions, not completion. "10 files written" is not "346 valid briefs" --
an earlier step in this build reported success while silently dropping 40 duplicate pairs,
so every batch merge here checks what actually landed.
"""

import json
import os
import sys

from . import corpus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(HERE, "briefs_parts")
OUT = os.path.join(HERE, "briefs.json")

REQUIRED = {"subject", "teaches", "problems", "kind"}
KINDS = {"teaching", "pitch", "aside", "memorial", "guest", "admin"}


def merge():
    docs, _ = corpus.load()
    want = set(d["path"] for d in docs)

    merged, problems = {}, []
    files = sorted(f for f in os.listdir(PARTS) if f.startswith("part_") and f.endswith(".json"))
    for f in files:
        p = os.path.join(PARTS, f)
        try:
            with open(p, encoding="utf-8") as fh:
                part = json.load(fh)
        except ValueError as exc:
            problems.append("%s: invalid JSON (%s)" % (f, exc))
            continue
        if not isinstance(part, dict):
            problems.append("%s: expected an object keyed by path" % f)
            continue
        for path, brief in part.items():
            if path in merged:
                problems.append("%s: duplicate key %s" % (f, path))
            merged[path] = brief

    # validate every brief
    bad = []
    for path, b in list(merged.items()):
        if not isinstance(b, dict):
            bad.append((path, "not an object"))
            continue
        missing = REQUIRED - set(b)
        if missing:
            bad.append((path, "missing %s" % ",".join(sorted(missing))))
        elif not str(b.get("subject", "")).strip():
            bad.append((path, "empty subject"))
        elif b.get("kind") not in KINDS:
            bad.append((path, "bad kind %r" % b.get("kind")))
        elif not isinstance(b.get("problems"), list):
            bad.append((path, "problems is not a list"))

    unknown = set(merged) - want
    absent = want - set(merged)

    print("parts merged     : %d files" % len(files))
    print("briefs           : %d" % len(merged))
    print("letters expected : %d" % len(want))
    print("missing          : %d" % len(absent))
    print("unknown paths    : %d" % len(unknown))
    print("malformed        : %d" % len(bad))
    for msg in problems[:10]:
        print("  ! %s" % msg)
    for path, why in bad[:10]:
        print("  ! %s -- %s" % (path, why))
    for path in sorted(absent)[:10]:
        print("  - missing brief: %s" % path)

    ok = not absent and not unknown and not bad and not problems
    if ok:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=1, ensure_ascii=False)
        teaching = sum(1 for b in merged.values() if b.get("kind") == "teaching")
        nonGary = sorted(set(b.get("author", "") for b in merged.values()
                             if b.get("author") and "gary" not in b["author"].lower()))
        print("\nwrote %s" % os.path.basename(OUT))
        print("  teaching letters : %d of %d" % (teaching, len(merged)))
        print("  other authors    : %s" % (", ".join(nonGary[:8]) or "none detected"))
    else:
        print("\nNOT WRITTEN -- fix the above first")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(merge())
