"""The two Claude calls: rewrite the question, then answer from the letters.

The rewrite is the whole design. Halbert's vocabulary and a 2026 marketer's do
not overlap -- "cold email" appears in 0 of 413 letters -- so searching the raw
question finds nothing. Measured: the right letter moves from rank #51 to #1
on nothing but this rewrite.
"""

import os
import re

REWRITE_MODEL = os.environ.get("HALBERT_REWRITE_MODEL", "claude-sonnet-5")
ANSWER_MODEL = os.environ.get("HALBERT_ANSWER_MODEL", "claude-opus-5")

VOCAB = """\
cold email, outreach, DM      -> sales letter, direct mail, mailing piece
open rate, deliverability     -> getting it opened, the A-pile, the B-pile, the envelope
reply rate, response, conv.   -> response rate, pull, nixies
audience, ICP, targeting      -> the list, the market, a starving crowd
landing page, funnel, website -> the offer, the order card, the sales piece
hook, angle, thumbnail        -> the grabber, the headline, the teaser
testing, A/B, experiment      -> split-run, test mailing, rollout, control
lead magnet, opt-in           -> free recorded message, free report, coupon
social proof, reviews         -> testimonials, endorsements
copywriter, agency            -> copy cub, ad agency
price, pricing                -> unit of sale, front-end, back-end
churn, retention              -> repeat buyers, multi-buyers, the back-end
"""

REWRITE_SYS = """\
You translate a modern marketer's question into the vocabulary of Gary Halbert's
direct-mail newsletters, written 1984-2013. The archive predates the internet for
the most part: it has no word for "funnel", "landing page" or "cold email".

Reference mappings:
%s
Output ONLY search terms, one per line, 8 to 15 of them. No sentences, no numbering,
no commentary. Include any proper nouns from the question verbatim. Prefer his concrete
nouns over abstractions. Do not output a term that is merely topical -- every term should
be one he would plausibly have typed.""" % VOCAB

# The tuning loop appends learned mappings here rather than editing this file, so a
# bad round can be reverted by deleting one text file.
_EXTRA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "vocab_extra.txt")
if os.path.exists(_EXTRA):
    with open(_EXTRA, encoding="utf-8") as _fh:
        _learned = _fh.read().strip()
    if _learned:
        REWRITE_SYS += "\n\nAdditional mappings learned from failed searches:\n" + _learned

ANSWER_SYS = """\
You answer questions about direct-response marketing using ONLY the Gary Halbert letters
provided. You are talking to a working copywriter who runs real outreach campaigns. He wants
to know which letter solves his problem, and he wants the line he can keep.

Output EXACTLY this shape, no markdown, no preamble:

THE LETTER
  <title> · <words>w · <author if not Gary>
  open http://localhost:8848/site/<path>

WHY
  <2 lines. Why this letter answers HIS question. Name the mechanism in his terms,
   then in Halbert's. Do not summarize the letter.>

HE SAYS
  "<a verbatim quote from the letter, 25-70 words, that carries the actual lesson.
    Copy it exactly. Never paraphrase inside the quotes.>"

ALSO
  <up to 3 other letters that cover the same ground, one line each: filename stem
   then a 6-10 word note on what that one adds. Omit this block entirely if only one
   letter covers it, and instead write:>
  Only one letter in the archive covers this.

CAUTION
  <Only if warranted. Gary Halbert died in 2007. Flag: tactics that cannot be executed
   today (postal tricks, 976 numbers, yellow pages, fax broadcast); dead phone numbers and
   addresses; any invitation to contact or mail Gary; claims he admits inventing.
   Always say what still transfers.>

Rules:
- Name exactly ONE letter as THE LETTER. Choose the one that best answers HIS question,
  not the longest or the most famous.
- If the letters genuinely do not cover his question, output only:
    NOTHING HERE
      <one line on what the archive has instead, and say plainly it is a stretch.>
  Do this rather than reaching. A confident wrong answer costs more than an honest miss.
- Some documents in this archive are by other authors (Bond Halbert, Kevin Halbert,
  Scott Haines, James Sheridan) or are memorial pages. If the letter you pick is not by
  Gary, say so on the title line."""


def _client():
    try:
        import anthropic
    except ImportError:
        raise SystemExit("pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Retrieval works without it: try  ask.py --dry 'your question'"
        )
    return anthropic.Anthropic()


def rewrite(question):
    """Modern question -> Halbert-era search terms."""
    msg = _client().messages.create(
        model=REWRITE_MODEL,
        max_tokens=400,
        system=REWRITE_SYS,
        messages=[{"role": "user", "content": question}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    terms = []
    for line in text.splitlines():
        line = re.sub(r"^\s*[-*\d.)\s]+", "", line).strip().strip('"')
        if line and len(line) < 60 and not line.endswith(":"):
            terms.append(line)
    return terms or [question]


def answer(question, hits, stream=True):
    """hits: [(doc, score)]. Reads the letters in full and prints the block."""
    parts = []
    for doc, _ in hits:
        parts.append(
            "<letter path=\"%s\" title=\"%s\" words=\"%d\" date=\"%s\">\n%s\n</letter>"
            % (doc["path"], doc["title"], doc["words"], doc.get("date") or "unknown",
               doc["text"])
        )
    user = "His question: %s\n\nThe candidate letters:\n\n%s" % (
        question, "\n\n".join(parts))

    client = _client()
    if not stream:
        msg = client.messages.create(
            model=ANSWER_MODEL, max_tokens=2000,
            thinking={"type": "adaptive"},
            system=ANSWER_SYS, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if b.type == "text")

    out = []
    with client.messages.stream(
        model=ANSWER_MODEL, max_tokens=2000,
        thinking={"type": "adaptive"},
        system=ANSWER_SYS, messages=[{"role": "user", "content": user}],
    ) as s:
        for chunk in s.text_stream:
            out.append(chunk)
            print(chunk, end="", flush=True)
    print()
    return "".join(out)
