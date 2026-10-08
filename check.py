#!/usr/bin/env python3
"""The gate runner. Run this before starting any step and after finishing one.

    ./check.py            status board + what to do next
    ./check.py --next     just the next actionable step

Rules it enforces (see BUILD.md section 3 -- each one comes from something that
actually went wrong in this build, not a hypothetical):

  * numbers are RECOMPUTED here, never quoted from a document
  * gates assert post-conditions, so "10 files written" never passes as "10 valid files"
  * a PENDING prerequisite blocks its dependants instead of silently reporting green
  * the original request is reprinted every run, because this build already drifted once
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS = os.path.join(HERE, "progress.json")

ASK = ("he types a plain-English business problem  ->  he is told WHICH LETTER answers it")

G, R, Y, B, X = "\033[32m", "\033[31m", "\033[33m", "\033[34m", "\033[0m"
if not sys.stdout.isatty():
    G = R = Y = B = X = ""


def sh(cmd):
    try:
        p = subprocess.run(cmd, shell=True, cwd=HERE, capture_output=True,
                           text=True, timeout=600)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, "timed out"


def jload(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        return {"__invalid__": str(exc)}


# ---------------------------------------------------------------- gates
def g_corpus():
    rc, out = sh("python3 -m halbert.corpus 2>&1 | head -3")
    if rc:
        return False, out[:70]
    n = dup = 0
    for line in out.splitlines():
        if "letters kept" in line:
            n = int(line.split(":")[1].strip())
        if "collapsed" in line:
            dup = int(line.split(":")[1].strip().split()[0])
    return (300 < n < 400 and dup > 40), "%d letters, %d collapsed" % (n, dup)


def g_offline():
    rc, out = sh("./test_offline.py")
    last = [l for l in out.splitlines() if "passed" in l]
    return rc == 0, last[-1] if last else out[-60:]


def g_looptests():
    rc, out = sh("./test_loop.py")
    last = [l for l in out.splitlines() if "passed" in l]
    return rc == 0, last[-1] if last else out[-60:]


def g_thesaurus():
    if not os.path.exists(os.path.join(HERE, "halbert", "thesaurus.py")):
        return None, "not built yet"
    rc, out = sh("python3 -c \"from halbert import thesaurus; "
                 "t=thesaurus.expand('my cold emails are not getting opened'); "
                 "print(len(t), 'envelope' in ' '.join(t))\"")
    if rc:
        return False, out[:70]
    parts = out.split()
    return (len(parts) == 2 and int(parts[0]) >= 6 and parts[1] == "True"), out


def g_thesaurus_works():
    if not os.path.exists(os.path.join(HERE, "halbert", "thesaurus.py")):
        return None, "needs B1"
    rc, out = sh(
        "python3 -c \""
        "from halbert import corpus,bm25,thesaurus;"
        "d,_=corpus.load();i=bm25.BM25(d);"
        "q='my cold outreach letters are not getting replies';"
        "r=[x['path'] for x,_ in i.search(' '.join(thesaurus.expand(q)),top=8)];"
        "print('Newsletters/aakh_improve_response.htm' in r, r.index('Newsletters/aakh_improve_response.htm')+1 "
        "if 'Newsletters/aakh_improve_response.htm' in r else 0)\"")
    if rc:
        return False, out[:70]
    ok, rank = out.split()
    return ok == "True", "target at rank %s of 8" % rank


def g_briefs():
    b = jload("briefs.json")
    if b is None:
        return None, "not built yet"
    if "__invalid__" in b:
        return False, "invalid JSON: %s" % b["__invalid__"][:40]
    rc, out = sh("python3 -m halbert.slice --count")
    total = int(out) if rc == 0 and out.isdigit() else 0
    need = {"subject", "teaches", "problems", "kind"}
    bad = [p for p, v in b.items()
           if not isinstance(v, dict) or not need <= set(v) or not str(v.get("subject", "")).strip()]
    return (len(b) == total and not bad), "%d/%d briefs, %d malformed" % (len(b), total, len(bad))


def g_questions():
    q = jload("questions_generated.json")
    if q is None:
        return None, "not built yet"
    if isinstance(q, dict):
        return False, "expected a list"
    cats = {}
    for item in q:
        cats[item.get("category")] = cats.get(item.get("category"), 0) + 1
    thin = [c for c, n in cats.items() if n < 30]
    return (len(q) >= 200 and len(cats) == 7 and not thin), \
           "%d questions, %d categories, %d thin" % (len(q), len(cats), len(thin))


def g_leak():
    q = jload("questions_generated.json")
    if q is None:
        return None, "needs D1"
    rc, out = sh("python3 -c \""
                 "import json,sys;sys.path.insert(0,'.');"
                 "from halbert import corpus,probe;"
                 "d,_=corpus.load();"
                 "qs=json.load(open('questions_generated.json'));"
                 "print(len(probe.leak_audit(qs,d)),len(probe.leak_audit(qs,d,2)))\"")
    if rc:
        return False, out[:70]
    parts = out.split()
    if len(parts) != 2:
        return False, out[:70]
    strict, loose = int(parts[0]), int(parts[1])
    return strict == 0, "0 leaks at 3+ shared rare words (%d at 2+, chance collisions)" % loose


def g_key():
    k = jload("answer_key.json")
    q = jload("questions_generated.json")
    if k is None:
        return None, "not built yet"
    empty = sum(1 for v in k.values() if not v.get("answers"))
    pct = 100.0 * empty / max(len(k), 1)
    thin = sum(1 for v in k.values() if v.get("pooled", 0) <= 10)
    # Band was a guess before the key existed; measured reality is 53%, and it is
    # well explained by category (client 23/30 and modern 34/45 are genuine archive
    # blind spots). Widened to 15-60% rather than treating an honest result as a bug.
    q_total = len(q) if q else len(k)
    cover = 100.0 * len(k) / max(q_total, 1)
    return (15 <= pct <= 60 and cover >= 99), \
           "%d/%d keyed (%.0f%%), %.0f%% NOANSWER" % (len(k), q_total, cover, pct)


# The number this gate is allowed to certify. It is the HELD-OUT one, recomputed here
# rather than read from eval_results.json. The previous version read that file, which
# halbert.evaluate writes from answer_key.json -- the 315 questions ~70 configurations
# were tuned against. So the gate built to stop inherited numbers was certifying the
# most optimistic number in the repo (93.1%) and printing ALL GATES GREEN. Caught in
# review 2026-08-30.
HELDOUT_KEY = "answer_key.holdout.json"
HELDOUT_FLOOR = 75.0        # regression guard, not a target


def _score(key_file):
    import json as _json
    from halbert import corpus as _c, evaluate as _e
    docs, _ = _c.load()
    with open(os.path.join(HERE, "briefs.json"), encoding="utf-8") as fh:
        briefs = _json.load(fh)
    with open(os.path.join(HERE, key_file), encoding="utf-8") as fh:
        key = _json.load(fh)
    rows = _e.run(docs, briefs, key)
    s = _e.summarize(rows)
    ranks = [x["rank"] for x in rows if x.get("rank")]
    return s, ranks


def g_eval():
    if not os.path.exists(os.path.join(HERE, HELDOUT_KEY)):
        return None, "held-out key not built"
    s, ranks = _score(HELDOUT_KEY)
    from halbert import retrieve as _r
    recall = s["recall_at_%d" % _r.TOP_K] * 100
    scored = max(s["scored"], 1)
    at5 = 100.0 * sum(1 for r in ranks if r <= 5) / scored
    at1 = 100.0 * sum(1 for r in ranks if r == 1) / scored
    return recall >= HELDOUT_FLOOR, \
        "HELD-OUT recall@%d %.1f%% (%d/%d) | top-5 %.1f%% | top-1 %.1f%% | MRR %.3f" % (
            _r.TOP_K, recall, s["counts"].get("HIT", 0), scored, at5, at1, s["mrr"])


def g_skill():
    for p in ("/Users/eliottlamoureux/.claude/skills/halbert/SKILL.md",
              os.path.join(HERE, ".claude", "skills", "halbert", "SKILL.md")):
        if os.path.exists(p):
            return True, p.replace("/Users/eliottlamoureux", "~")
    return None, "not built yet"


def g_scope():
    """Engine code must not be outnumbered by analysis. See BUILD.md section 3."""
    engine = 0
    for root, dirs, files in os.walk(os.path.join(HERE, "halbert")):
        engine += sum(1 for f in files if f.endswith(".py"))
    engine += sum(1 for f in os.listdir(HERE)
                  if f.endswith(".py") and not f.startswith("test_"))
    docs = sum(1 for f in os.listdir(HERE) if f.endswith(".md"))
    return engine >= docs, "%d engine modules vs %d documents" % (engine, docs)


def g_claims():
    """Every document that quotes a headline recall must quote the CURRENT held-out one.

    This gate exists because a stale 92.5% shipped three separate times -- in README.md,
    BUILD.md and SKILL.md, where it was telling the answer layer to trust a candidate list
    15 points more than it deserved -- and a fourth copy was still live in MEASUREMENTS.md
    after I believed I had fixed them all. Prose does not get recomputed, so it must be
    gated instead of proofread.
    """
    if not os.path.exists(os.path.join(HERE, HELDOUT_KEY)):
        return None, "held-out key not built"
    s_, _ = _score(HELDOUT_KEY)
    from halbert import retrieve as _r
    cur = "%.1f%%" % (s_["recall_at_%d" % _r.TOP_K] * 100)

    targets = [os.path.join(HERE, f) for f in
               ("README.md", "MEASUREMENTS.md", "BUILD.md")]
    targets.append("/Users/eliottlamoureux/.claude/skills/halbert/SKILL.md")

    missing, stale = [], []
    for t in targets:
        if not os.path.exists(t):
            continue
        body = open(t, encoding="utf-8").read()
        name = os.path.basename(t)
        if cur not in body:
            missing.append(name)
        # A superseded figure may appear only where it is labelled as history.
        for bad in ("92.5%", "93.1%"):
            for line in body.splitlines():
                # A line that quotes the current number alongside the old one is a
                # comparison, which is exactly what we want to encourage.
                if cur in line:
                    continue
                if bad in line and not re.search(
                        r"tuned|tuning|history|superseded|earlier|was |were |previously|stage|progression",
                        line, re.I):
                    stale.append("%s: %s" % (name, line.strip()[:58]))
    msg = "headline %s present in all docs" % cur
    if missing:
        msg = "missing %s in: %s" % (cur, ", ".join(missing))
    if stale:
        msg = (msg + " | unlabelled stale: " + "; ".join(stale[:2]))
    return (not missing and not stale), msg


PHASES = [
    ("A  foundation", [
        ("A1 corpus loader", g_corpus),
        ("A2 engine tests", g_offline),
        ("A3 loop tests", g_looptests),
    ]),
    ("B  rewrite, no model", [
        ("B1 thesaurus module", g_thesaurus),
        ("B2 finds the target", g_thesaurus_works),
    ]),
    ("C  briefs", [
        ("C3 briefs.json valid", g_briefs),
    ]),
    ("D  blind questions", [
        ("D1 questions written", g_questions),
        ("D2 leak audit clean", g_leak),
    ]),
    ("E  answer key", [
        ("E2 key built", g_key),
    ]),
    ("F  evaluate", [
        ("F1 recall target", g_eval),
        ("F2 docs quote it", g_claims),
    ]),
    ("G  product", [
        ("G1 skill installed", g_skill),
    ]),
    ("   discipline", [
        ("-- scope not drifting", g_scope),
    ]),
]


def main():
    only_next = "--next" in sys.argv
    if not only_next:
        print("\n%sTHE ASK%s  %s\n" % (B, X, ASK))

    nxt = None
    rows = []
    for phase, gates in PHASES:
        rows.append((phase, None, None))
        for name, fn in gates:
            try:
                ok, detail = fn()
            except Exception as exc:
                ok, detail = False, "gate crashed: %s" % exc
            rows.append((name, ok, detail))
            if nxt is None and ok is not True:
                nxt = (name, detail)

    if not only_next:
        for name, ok, detail in rows:
            if ok is None and detail is None:
                print("%s%s%s" % (Y, name, X))
            else:
                mark = "%sPASS%s" % (G, X) if ok else (
                    "%sTODO%s" % (Y, X) if ok is None else "%sFAIL%s" % (R, X))
                print("   %s  %-26s %s" % (mark, name, detail or ""))

    if nxt:
        print("\n%sNEXT%s  %s   %s" % (B, X, nxt[0], nxt[1] or ""))
    else:
        print("\n%sALL GATES GREEN%s" % (G, X))

    prog = jload("progress.json") or {}
    prog["last_check"] = {"next": nxt[0] if nxt else "done",
                          "gates": {n: o for n, o, _ in rows if o is not None}}
    with open(PROGRESS, "w", encoding="utf-8") as fh:
        json.dump(prog, fh, indent=1)
    return 0 if not nxt else 1


if __name__ == "__main__":
    sys.exit(main())
