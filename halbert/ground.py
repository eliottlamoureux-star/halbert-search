"""Ground truth: a brief per letter, and probe questions generated from it.

The briefs are what the search engine is tested against AND what bridge #2 would
use if it is ever built. The probes are how we test without needing anyone to
hand-write questions.

The hard part is that probes must not cheat. A question written from a brief will
naturally reuse the letter's own vocabulary, which hands retrieval the answer and
measures nothing. `leaks()` enforces that mechanically -- see EXECUTION-LOOP.md.
"""

import json
import os
import re
import sys
import time

from . import corpus, llm

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFS = os.path.join(HERE, "briefs.json")
PROBES = os.path.join(HERE, "probes.json")

BRIEF_MODEL = os.environ.get("HALBERT_BRIEF_MODEL", "claude-sonnet-5")

BRIEF_SYS = """\
You summarize one letter from Gary Halbert's direct-mail newsletter archive (1984-2013).

Return JSON only, this exact shape:

{"subject": "<8-15 words: what this letter is actually ABOUT>",
 "teaches": ["<a concrete lesson the letter delivers>", "..."],
 "problems": ["<a business problem a reader would have that this letter solves>", "..."],
 "kind": "teaching|pitch|aside|memorial|guest|admin",
 "author": "<who wrote it, if the text makes that clear; else Gary Halbert>",
 "era_bound": ["<any tactic here that cannot be executed in 2026>"]}

Rules:
- `subject` must describe the DOMINANT topic. Many letters open on an unrelated anecdote
  before pivoting -- do not let the opening story decide the subject.
- `teaches`: 2 to 6 items. Concrete and specific. "Attach a dollar bill to the top of the
  letter and reference it in a phone follow-up", not "use attention-getting devices".
- `problems`: 3 to 8 items. Write these as the READER'S problem in their own words, not as
  the letter's solution. "My mail gets thrown out before it's opened", not "the A-pile".
- `kind`: `pitch` if it mostly sells something, `aside` if it is a joke or a rant with no
  lesson, `memorial` for tributes, `guest` if someone other than Gary wrote the bulk of it,
  `admin` for site/housekeeping pages.
- If the letter teaches nothing, say so: empty `teaches`, and `kind` other than `teaching`.
Output JSON and nothing else."""

PROBE_SYS = """\
You write realistic questions that a working marketer would type into a search box.

You will be given a brief describing ONE letter, plus a list of BANNED WORDS.

Write %d questions that this letter would genuinely answer.

Hard rules:
- Write as somebody describing a PROBLEM THEY HAVE, in 2026 business vocabulary.
  "my cold emails aren't getting opened" -- NOT "how do I use the A-pile principle".
- NEVER use any banned word, or an obvious morphological variant of one. The banned list is
  the letter's own distinctive vocabulary; using it would make the test meaningless.
- Vary the framing across your questions: some diagnostic ("why is X happening"), some
  advice-seeking ("how do I X"), some blunt ("my X is broken").
- No question may name Gary Halbert, a letter, or direct mail as a medium unless the
  reader's own problem is literally about physical mail.
- 6 to 18 words each.

Return JSON only: {"questions": ["...", "..."]}"""


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


class Leak(object):
    """Detects probe questions that reuse the target letter's rare vocabulary."""

    def __init__(self, docs, rare_df=10):
        # df <= 10 of 346 documents (~3%). Calibrated, not guessed: it catches the
        # genuinely distinctive vocabulary (cheshire 1, nixies 5, indicia 5,
        # sugarman 8, lettershop 10) while ignoring ordinary words that are merely
        # uneven in a small corpus (land 16, testing 27, keeps 30, answers 39).
        # Note df alone cannot do this job at any higher cutoff -- "jewfish" sits at
        # 173 because it is in the masthead, so a wider net catches the boilerplate
        # and misses the point.
        self.df = {}
        self.words = {}
        for d in docs:
            ws = set(_norm(w) for w in re.findall(r"[A-Za-z']+", d["text"]))
            ws.discard("")
            self.words[d["path"]] = ws
            for t in ws:
                self.df[t] = self.df.get(t, 0) + 1
        self.rare_df = rare_df
        self.n = len(docs)

    def banned(self, doc, limit=60):
        """The letter's distinctive words -- what a probe must not say."""
        seen, out = set(), []
        for w in re.findall(r"[A-Za-z']+", doc["text"]):
            t = _norm(w)
            if len(t) < 4 or t in seen:
                continue
            seen.add(t)
            if 0 < self.df.get(t, 0) <= self.rare_df:
                out.append(w.lower())
        out.sort(key=lambda w: self.df.get(_norm(w), 0))
        return out[:limit]

    def leaks(self, question, doc):
        """Rare words shared by the question and the letter. >=2 means it cheats."""
        letter = self.words.get(doc["path"])
        if letter is None:
            letter = set(_norm(w) for w in re.findall(r"[A-Za-z']+", doc["text"]))
        hits = []
        for w in re.findall(r"[A-Za-z']+", question):
            t = _norm(w)
            if len(t) < 4:
                continue
            if t in letter and 0 < self.df.get(t, 0) <= self.rare_df:
                hits.append(w.lower())
        return sorted(set(hits))


def _json_call(model, system, user, max_tokens=1200):
    msg = llm._client().messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in response: %r" % text[:200])
    return json.loads(m.group(0))


def build_briefs(docs, force=False, limit=None):
    """One brief per letter. Resumable -- rerun after an interruption."""
    out = {}
    if os.path.exists(BRIEFS) and not force:
        with open(BRIEFS, encoding="utf-8") as fh:
            out = json.load(fh)
    todo = [d for d in docs if d["path"] not in out]
    if limit:
        todo = todo[:limit]
    for i, d in enumerate(todo, 1):
        body = d["text"][:24000]
        try:
            out[d["path"]] = _json_call(
                BRIEF_MODEL, BRIEF_SYS,
                "Title: %s\nPath: %s\n\n%s" % (d["title"], d["path"], body))
        except Exception as exc:
            print("  brief failed %s: %s" % (d["path"], exc), file=sys.stderr)
            continue
        if i % 20 == 0:
            with open(BRIEFS, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1, ensure_ascii=False)
            print("  briefs %d/%d" % (i, len(todo)), file=sys.stderr)
            time.sleep(0.2)
    with open(BRIEFS, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


def build_probes(docs, briefs, per_letter=3, force=False, max_retries=2):
    """Probe questions per letter, rejected and regenerated if they leak."""
    out = {}
    if os.path.exists(PROBES) and not force:
        with open(PROBES, encoding="utf-8") as fh:
            out = json.load(fh)

    leak = Leak(docs)
    by_path = {d["path"]: d for d in docs}
    todo = [p for p in briefs if p not in out and p in by_path]

    for i, path in enumerate(todo, 1):
        doc, brief = by_path[path], briefs[path]
        if brief.get("kind") not in ("teaching", None) and not brief.get("teaches"):
            out[path] = []          # nothing to ask about; excluded from scoring
            continue
        banned = leak.banned(doc)
        accepted = []
        for attempt in range(max_retries + 1):
            need = per_letter - len(accepted)
            if need <= 0:
                break
            user = ("BRIEF:\n%s\n\nBANNED WORDS (never use these):\n%s"
                    % (json.dumps(brief, ensure_ascii=False), ", ".join(banned)))
            try:
                qs = _json_call(BRIEF_MODEL, PROBE_SYS % need, user).get("questions", [])
            except Exception as exc:
                print("  probe failed %s: %s" % (path, exc), file=sys.stderr)
                break
            for q in qs:
                lk = leak.leaks(q, doc)
                if len(lk) < 2 and 4 <= len(q.split()) <= 24:
                    accepted.append({"q": q, "leaks": lk})
        out[path] = accepted[:per_letter]
        if i % 20 == 0:
            with open(PROBES, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1, ensure_ascii=False)
            print("  probes %d/%d" % (i, len(todo)), file=sys.stderr)
    with open(PROBES, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


if __name__ == "__main__":
    docs, _ = corpus.load()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    briefs = build_briefs(docs, limit=n)
    print("briefs: %d" % len(briefs))
    probes = build_probes(docs, briefs)
    print("probes: %d questions across %d letters"
          % (sum(len(v) for v in probes.values()), len(probes)))
