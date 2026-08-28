#!/usr/bin/env python3
"""Exercise the tuning-loop machinery with every API call mocked.

Proves the wiring: blind generation -> pooled key -> scoring -> attribution ->
review gate -> fix application. Only the quality of the model's judgement is
untested, which is the one thing a key would tell us.
"""


import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halbert import corpus, evaluate, ground, key as keymod, llm, probe  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %-50s %s" % ("PASS" if cond else "FAIL", name, detail))


DOCS, _ = corpus.load()
TARGET = "Newsletters/aakh_improve_response.htm"
DOC = next(d for d in DOCS if d["path"] == TARGET)

# --------------------------------------------------------------------------
print("\nleak detection (now a guard rail, not the mechanism)")
leak = ground.Leak(DOCS)
banned = leak.banned(DOC)
check("banned list is the letter's rare vocabulary", len(banned) > 20,
      "%d words e.g. %s" % (len(banned), ", ".join(banned[:4])))
check("a cheating question is caught",
      len(leak.leaks("how do I stop nixies and lettershop shrinkage", DOC)) >= 2,
      str(leak.leaks("how do I stop nixies and lettershop shrinkage", DOC)))
check("an honest question is not caught",
      len(leak.leaks("my outreach emails never get answered", DOC)) < 2,
      str(leak.leaks("my outreach emails never get answered", DOC)))

# --------------------------------------------------------------------------
print("\nblind generation")
CALLS = {"n": 0}


def fake_json_call(model, system, user, max_tokens=1200):
    CALLS["n"] += 1
    if "WRITE" in system and "QUESTIONS" in system:
        CALLS.setdefault("writer_saw", []).append(user)
        cat = user.split("\n")[0].replace("CATEGORY: ", "").strip()
        return {"questions": [
            "my %s work keeps stalling before anyone answers" % cat,
            "how do i fix %s when nothing seems to land" % cat,
            "nobody engages with my %s and i cannot tell why" % cat,
            "what should i change about %s to get a decision" % cat]}
    if "answer key" in system:
        return {"picks": [1], "why": "directly addresses low response"}
    if "genuinely answers" in system:
        return {"answers": True, "why": "yes"}
    if "diagnosing" in system:
        return {"cause": "rewrite emits modern terms absent from the corpus",
                "fix_kind": "vocab",
                "mappings": ["ignored -> no response, nixies"],
                "brief_instruction": "", "confidence": "high"}
    if "reviewing a proposed fix" in system:
        return {"verdict": "APPROVE", "reason": "grounded in shown excerpts",
                "counter_proposal": ""}
    return {"subject": "how to lift direct mail response without touching copy",
            "teaches": ["mail first class", "widen the margins"],
            "problems": ["my mail gets thrown out", "nobody responds to my mailing"],
            "kind": "teaching", "author": "Gary Halbert", "era_bound": ["live stamps"]}


ground._json_call = fake_json_call
llm.rewrite = lambda q: ["response rate", "direct mail", "nixies", "test", "list", "envelope"]

# Tests must never write to a live artifact path. An earlier run left 28 mock
# questions in questions_generated.json, which check.py then scored as real.
probe.QUESTIONS = os.path.join(tempfile.gettempdir(), "test_questions.json")
if os.path.exists(probe.QUESTIONS):
    os.remove(probe.QUESTIONS)

qs = probe.generate(force=True)
check("questions generated", len(qs) > 0, "%d questions" % len(qs))
saw = " ".join(CALLS.get("writer_saw", []))
check("writer never saw a letter or a brief",
      "nixies" not in saw.lower() and "halbert" not in saw.lower()
      and "teaches" not in saw.lower(),
      "prompt carried only the category description")
check("questions span categories",
      len(set(q["category"] for q in qs)) == len(probe.CATEGORIES),
      "%d categories" % len(set(q["category"] for q in qs)))
check("generated questions do not leak", len(probe.leak_audit(qs, DOCS)) == 0)

# --------------------------------------------------------------------------
print("\nanswer key -- pooling is free Python, judging is subagents")
briefs = {d["path"]: {"subject": "how to lift direct mail response",
                      "teaches": ["mail first class"],
                      "problems": ["nobody responds to my mailing"],
                      "kind": "teaching"} for d in DOCS[:40]}
briefs[TARGET] = {"subject": "twenty ways to lift direct mail response without new copy",
                  "teaches": ["mail first class", "widen the margins"],
                  "problems": ["nobody responds to my mailing",
                               "my mail is thrown out unopened"],
                  "kind": "teaching"}

tmp = tempfile.mkdtemp()
keymod.BRIEFS = os.path.join(tmp, "briefs.json")
keymod.QUESTIONS = os.path.join(tmp, "questions.json")
keymod.POOLS = os.path.join(tmp, "pools")
keymod.PARTS = os.path.join(tmp, "parts")
keymod.KEY = os.path.join(tmp, "key.json")
with open(keymod.BRIEFS, "w") as fh:
    json.dump(briefs, fh)
with open(keymod.QUESTIONS, "w") as fh:
    json.dump(qs[:6], fh)

pooled = keymod.pool(batches=2)
check("pool covers every question", len(pooled) == 6, "%d pooled" % len(pooled))
sizes = [len(p["candidates"]) for p in pooled]
check("pool is a union of four routes, so no single route caps it",
      max(sizes) > keymod.POOL_PER_ROUTE,
      "max pool %d vs %d per route" % (max(sizes), keymod.POOL_PER_ROUTE))
check("pool batches written for agents",
      len(os.listdir(keymod.POOLS)) == 2, os.listdir(keymod.POOLS))
check("candidates carry brief context for the judge",
      all("subject" in c for p in pooled for c in p["candidates"]))

os.makedirs(keymod.PARTS)
with open(os.path.join(keymod.PARTS, "part_00.json"), "w") as fh:
    json.dump([{"q": p["q"], "category": p["category"],
                "answers": [TARGET] if i % 3 else []}
               for i, p in enumerate(pooled)], fh)
rc = keymod.merge()
check("merge rejects an incomplete NOANSWER rate or writes the key",
      rc in (0, 1), "exit %d" % rc)

# --------------------------------------------------------------------------
print("\nscoring + attribution")
synthetic = {
    "q hit":       {"answers": [TARGET], "category": "outreach", "terms":
                    ["response rate", "direct mail", "nixies", "envelope"]},
    # a genuine miss: terms that cannot possibly surface the wanted letter
    "q miss":      {"answers": ["Boron/TChapter11.htm"], "category": "outreach",
                    "terms": ["guarantee", "refund", "price"]},
    "q noanswer":  {"answers": [], "category": "modern", "terms": ["crm", "attribution"]},
}
rows = evaluate.run(DOCS, briefs, synthetic)
verdicts = dict((r["q"], r["verdict"]) for r in rows)
check("a findable question scores HIT", verdicts["q hit"] == "HIT", verdicts["q hit"])
check("an unanswerable question is set aside as NOANSWER",
      verdicts["q noanswer"] == "NOANSWER", verdicts["q noanswer"])
check("a miss is attributed to a cause, not just counted",
      verdicts["q miss"] in ("QUERY_BAD", "BRIEF_BAD"), verdicts["q miss"])

s = evaluate.summarize(rows)
check("NOANSWER excluded from recall denominator", s["scored"] == 2,
      "scored %d of %d" % (s["scored"], s["questions"]))

# --------------------------------------------------------------------------
print("\ndiagnosis + apply gate")
import loop  # noqa: E402

diag = loop.diagnose(rows, DOCS)
check("diagnosis buckets failures by cause",
      set(diag) == {"QUERY_BAD", "BRIEF_BAD"}, str(sorted(diag)))
evid = [e for v in diag.values() for e in v]
check("evidence carries the terms that failed",
      all("expanded_terms" in e and "actually_returned" in e for e in evid) if evid else True,
      "%d failure cases" % len(evid))
check("evidence carries the letter that should have won",
      all("letter_excerpts" in e for e in evid) if evid else True)

loop.VOCAB_EXTRA = os.path.join(tempfile.gettempdir(), "test_vocab_extra.txt")
if os.path.exists(loop.VOCAB_EXTRA):
    os.remove(loop.VOCAB_EXTRA)
prop = os.path.join(tempfile.gettempdir(), "test_proposals.txt")
with open(prop, "w") as fh:
    fh.write("ghosted -> nixies, response\n")           # both exist in the corpus
    fh.write("churn -> zzzznotawordanywhere\n")          # must be rejected
n = loop.apply_mappings(prop)
check("valid mapping applied", n == 1, "%d applied" % n)
applied = open(loop.VOCAB_EXTRA).read()
check("mapping with a non-existent target term is rejected",
      "zzzznotawordanywhere" not in applied,
      "a df-0 term would add noise and never match")

check("loop has a stop condition",
      loop.TARGET and loop.MAX_ROUNDS and loop.NO_GAIN_LIMIT,
      "target %.0f%%, max %d rounds, stop after %d flat"
      % (loop.TARGET * 100, loop.MAX_ROUNDS, loop.NO_GAIN_LIMIT))

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
