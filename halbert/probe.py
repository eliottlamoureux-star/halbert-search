"""Question generation, deliberately blind to the corpus.

The writer agent never sees a letter, a brief, or a search result. It is told only
what the tool is FOR and who uses it, then writes questions that person would type.
Corpus vocabulary cannot leak because it was never in context.

That blindness costs us the answer key -- a question no longer knows which letter
answers it. `key.py` rebuilds the key with a separate judge. Generation and judgment
must be different roles; collapsing them is what made the earlier design need a
banned-word filter to compensate.

A side benefit: some questions will be about things Halbert never wrote about
(CRMs, SEO, attribution). Those are the only real test of the NOTHING HERE path.
"""

import json
import os
import re
import sys

from . import ground

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(HERE, "questions_generated.json")

WRITER_SYS = """\
You are generating a realistic test set of search questions. You have NOT been shown the
archive being searched, and you must not speculate about its contents. Write only from your
own knowledge of what this person struggles with day to day.

WHO IS ASKING
A solo operator running a small design/marketing studio in Québec. He does cold outreach to
local business owners (property managers, contractors, small service firms), writes his own
sales copy in French and English, builds his own offers, and buys or scrapes his own lists.
He is not a big-budget advertiser. He has no team. He works late and searches when he is
stuck on a specific piece of work.

WHAT HE IS SEARCHING
A private archive of direct-response marketing and copywriting writing. He wants to be told
which single document solves the problem he has right now.

WRITE %d QUESTIONS in the category below. Rules:
- First person, describing a problem or asking for something concrete. His words, 2026
  vocabulary, the way he would actually type it -- lowercase, sometimes clipped.
- 6 to 18 words.
- Concrete, not abstract. "my follow-up emails get ignored" not "how does one build rapport".
- Vary the surface: some are symptoms, some are how-do-I, some are blunt frustration.
- Do NOT invent jargon. Do NOT reference any specific author, book, letter, or document.
- Some of these SHOULD be things a 1980s-2000s direct-mail archive would have no answer for.
  Do not avoid modern topics; write what he would genuinely ask.

Return JSON only: {"questions": ["...", "..."]}"""

CATEGORIES = [
    ("outreach", "Getting a cold prospect to respond at all -- first contact, follow-up, "
                 "being ignored, gatekeepers, timing, channel."),
    ("copy", "Writing the thing -- headlines, openings, length, structure, tone, editing, "
             "getting unstuck, knowing if it is any good."),
    ("offer", "What he is actually selling -- pricing, packaging, guarantees, risk, bonuses, "
              "objections, why people stall."),
    ("market", "Who to sell to -- picking a niche, list quality, targeting, whether demand "
               "exists, testing a market before committing."),
    ("testing", "Knowing what works -- testing, scaling something that worked, results that "
                "collapse at volume, measuring, deciding what to change."),
    ("client", "Running the business -- clients who won't decide, scope, referrals, "
               "positioning against cheaper competitors, retention."),
    ("modern", "Channels and mechanics that did not exist before 2005 -- landing pages, "
               "email deliverability, ads platforms, SEO, CRM, analytics, social."),
]


def generate(per_category=45, force=False):
    """~300 questions across 7 categories, written blind."""
    if os.path.exists(QUESTIONS) and not force:
        with open(QUESTIONS, encoding="utf-8") as fh:
            return json.load(fh)

    out = []
    seen = set()
    for name, desc in CATEGORIES:
        got = []
        for attempt in range(3):
            need = per_category - len(got)
            if need <= 0:
                break
            try:
                r = ground._json_call(
                    ground.BRIEF_MODEL, WRITER_SYS % need,
                    "CATEGORY: %s\n%s" % (name, desc), max_tokens=3000)
            except Exception as exc:
                print("  writer failed (%s): %s" % (name, exc), file=sys.stderr)
                break
            for q in r.get("questions", []):
                q = " ".join(q.split())
                k = re.sub(r"[^a-z ]", "", q.lower())
                if k in seen or not (4 <= len(q.split()) <= 24):
                    continue
                seen.add(k)
                got.append(q)
        out.extend({"q": q, "category": name} for q in got)
        print("  %-9s %d questions" % (name, len(got)), file=sys.stderr)

    with open(QUESTIONS, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


def leak_audit(questions, docs, min_shared=3):
    """Should be 0 by construction. Non-zero means the blindness failed somewhere.

    min_shared=3 is calibrated, not guessed. At 2, ~1.6% of a genuinely blind set
    flags on ordinary English colliding by chance (`frozen` df=9, `maker` df=9,
    `bundle` df=7). At 3, a blind set flags 0. A real leak -- a question written
    while looking at a letter -- surfaces distinctive vocabulary like `nixies`(5)
    and `lettershop`(10) together, which clears 3 easily.
    """
    leak = ground.Leak(docs)
    worst = []
    for item in questions:
        # the question's own rare words, computed once rather than per document
        qrare = set()
        for w in re.findall(r"[A-Za-z']+", item["q"]):
            t = ground._norm(w)
            if len(t) >= 4 and 0 < leak.df.get(t, 0) <= leak.rare_df:
                qrare.add(t)
        if len(qrare) < min_shared:
            continue
        for d in docs:
            shared = qrare & leak.words[d["path"]]
            if len(shared) >= min_shared:
                worst.append((item["q"], d["path"], sorted(shared)))
                break
    return worst


if __name__ == "__main__":
    from . import corpus
    docs, _ = corpus.load()
    qs = generate(force="--force" in sys.argv)
    print("generated %d questions" % len(qs))
    bad = leak_audit(qs, docs)
    print("leak audit: %d questions share rare vocabulary with a letter" % len(bad))
    for q, p, lk in bad[:5]:
        print("   %-52s %s %s" % (q[:52], os.path.basename(p), lk))
