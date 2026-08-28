#!/usr/bin/env python3
"""The tuning loop. No API key -- diagnosis and review are subagents, not calls.

    ./loop.py                 evaluate, attribute failures, write diagnosis.json
    ./loop.py --apply FILE    append reviewed mappings to vocab_extra.txt, re-evaluate
    ./loop.py --status        round history

One round:
  1. score retrieval against the answer key
  2. split failures: QUERY_BAD (the thesaurus is wrong) vs BRIEF_BAD (the brief is wrong)
  3. write diagnosis.json -- the failing questions, their expanded terms, what came back
     instead, and an excerpt of the letter that SHOULD have won
  4. a subagent proposes mappings; a SECOND subagent reviews them before they land
  5. --apply writes them to vocab_extra.txt and re-scores

Step 4 is not optional. An unreviewed tuning loop optimizes the wrong thing for hours
and reports progress the entire time.

Stops at recall@8 >= TARGET, two rounds with no gain, or MAX_ROUNDS.
"""

import json
import os
import sys
import time

from halbert import corpus, evaluate, key as keymod, thesaurus

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "loop_state.json")
DIAGNOSIS = os.path.join(HERE, "diagnosis.json")
VOCAB_EXTRA = os.path.join(HERE, "vocab_extra.txt")
BRIEFS = os.path.join(HERE, "briefs.json")

TARGET = 0.85
MAX_ROUNDS = 6
NO_GAIN_LIMIT = 2


def _state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"rounds": []}


def _save(s):
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1)


def _load():
    docs, _ = corpus.load()
    with open(BRIEFS, encoding="utf-8") as fh:
        briefs = json.load(fh)
    with open(keymod.KEY, encoding="utf-8") as fh:
        key = json.load(fh)
    return docs, briefs, key


def diagnose(rows, docs, limit=25):
    """Write the evidence a proposing subagent needs. No judgement here."""
    by_path = {d["path"]: d for d in docs}
    out = {"QUERY_BAD": [], "BRIEF_BAD": []}
    for r in rows:
        v = r["verdict"]
        if v not in out or len(out[v]) >= limit:
            continue
        want = r.get("want") or []
        excerpts = []
        for p in want[:2]:
            d = by_path.get(p)
            if d:
                excerpts.append({"path": p, "title": d["title"],
                                 "excerpt": d["text"][:1400]})
        out[v].append({
            "question": r["q"],
            "expanded_terms": r.get("terms"),
            "should_have_found": want,
            "actually_returned": r.get("top"),
            "letter_excerpts": excerpts,
        })
    with open(DIAGNOSIS, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


def apply_mappings(path):
    """Append reviewed `modern -> his, his` lines. Rejects unknown target terms."""
    docs, _ = corpus.load()
    vocab = set()
    for d in docs:
        vocab.update(w.lower() for w in d["text"].split())
    vocab = set(w.strip(".,;:!?\"'()") for w in vocab)

    with open(path, encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if "->" in l and not l.startswith("#")]

    good, rejected = [], []
    for line in lines:
        src, dst = line.split("->", 1)
        targets = [t.strip(".,;:!?\"'()") for t in dst.strip().lower().split()]
        missing = [t for t in targets if t and t not in vocab]
        if missing:
            rejected.append((line, missing))
        else:
            good.append(line)

    if good:
        with open(VOCAB_EXTRA, "a", encoding="utf-8") as fh:
            fh.write("\n".join(good) + "\n")
    print("applied   : %d mappings" % len(good))
    print("rejected  : %d (target term absent from the corpus)" % len(rejected))
    for line, missing in rejected[:6]:
        print("   ! %-46s missing %s" % (line[:46], missing))
    return len(good)


def main():
    if "--status" in sys.argv:
        for r in _state()["rounds"]:
            print("round %d  recall %5.1f%%  QUERY_BAD %3d  BRIEF_BAD %3d  %s"
                  % (r["round"], r["recall"] * 100,
                     r["counts"].get("QUERY_BAD", 0), r["counts"].get("BRIEF_BAD", 0),
                     r.get("action", "")))
        return

    if "--apply" in sys.argv:
        apply_mappings(sys.argv[sys.argv.index("--apply") + 1])
        # force a reload so the new mappings take effect in this process
        import importlib
        importlib.reload(thesaurus)

    docs, briefs, key = _load()
    rows = evaluate.run(docs, briefs, key)
    s = evaluate.report(rows)
    recall = s["recall_at_%d" % evaluate.TOP_K]

    with open(os.path.join(HERE, "eval_results.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)

    state = _state()
    prev = [r["recall"] for r in state["rounds"]]
    rnd = len(state["rounds"]) + 1
    entry = {"round": rnd, "recall": recall, "counts": s["counts"],
             "ts": time.strftime("%Y-%m-%d %H:%M")}

    if recall >= TARGET:
        entry["action"] = "TARGET MET"
    elif len(prev) >= NO_GAIN_LIMIT and all(recall <= p + 0.005 for p in prev[-NO_GAIN_LIMIT:]):
        entry["action"] = "STOP: no gain in %d rounds" % NO_GAIN_LIMIT
    elif rnd >= MAX_ROUNDS:
        entry["action"] = "STOP: round limit"
    else:
        dominant = max(("QUERY_BAD", "BRIEF_BAD"), key=lambda v: s["counts"].get(v, 0))
        entry["action"] = "diagnose %s" % dominant
        diagnose(rows, docs)
        print("\ndominant failure : %s (%d)" % (dominant, s["counts"].get(dominant, 0)))
        print("evidence written : diagnosis.json")
        print("next             : have a subagent propose mappings, a second review them,")
        print("                   then ./loop.py --apply <reviewed-file>")

    state["rounds"].append(entry)
    _save(state)
    print("\nround %d: %s" % (rnd, entry["action"]))


if __name__ == "__main__":
    main()
