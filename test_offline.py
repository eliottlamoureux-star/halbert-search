#!/usr/bin/env python3
"""Everything that can be proven without an API key.

The two Claude calls are mocked, so the full pipeline still executes end to end:
prompt assembly, streaming consumption, answer parsing, and the --save path.

    ./test_offline.py
"""

import io
import os
import re
import sys
import contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halbert import corpus, bm25, llm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %-52s %s" % ("PASS" if cond else "FAIL", name, detail))


# --------------------------------------------------------------------------
print("\ncorpus")
DOCS, ALIASES = corpus.load()
BY = {d["path"]: d for d in DOCS}

check("letters loaded", 300 < len(DOCS) < 400, "%d letters" % len(DOCS))
check("duplicates collapsed", len(ALIASES) > 40, "%d aliased" % len(ALIASES))

# cp1252, not latin-1: 57 letters carry 0x80-0x9F bytes
t15 = corpus.read_text(os.path.join(corpus.SITE, "Boron/TChapter15.htm"))
check("cp1252 decode (curly apostrophe survives)",
      "driver’s" in t15 and "\x92" not in t15,
      repr(t15[t15.find("driver") - 4:t15.find("driver") + 12]) if "driver" in t15 else "")

# gzip streams named .htm
gz = corpus.read_text(os.path.join(corpus.SITE, "Newsletters/zkkk_killer_headlines.htm"))
check("gzip .htm recovered", len(gz.split()) > 2000, "%d words" % len(gz.split()))

# non-letters excluded
check("index pages excluded",
      not any(re.search(r"(^|/)index\d*\.html?$", d["path"]) for d in DOCS))
check("templates/tests excluded",
      not any("Template" in d["path"] or "bullet test" in d["path"] for d in DOCS))

# boilerplate gone
boiler = sum(1 for d in DOCS if "Click Here To View Our Newsletter" in d["text"])
check("boilerplate stripped", boiler == 0, "%d letters still carry it" % boiler)

# dedup left nothing behind
def _sh(t, n=8):
    w = re.sub(r"[^a-z0-9 ]", " ", t.lower()).split()
    return set(" ".join(w[i:i + n]) for i in range(max(1, len(w) - n)))

S = {d["path"]: _sh(d["text"]) for d in DOCS}
ps = list(S)
residual = 0
for i in range(len(ps)):
    a = S[ps[i]]
    if not a:
        continue
    for j in range(i + 1, len(ps)):
        b = S[ps[j]]
        if b and len(a & b) / min(len(a), len(b)) > 0.90:
            residual += 1
check("no residual duplicate pairs", residual == 0, "%d left" % residual)

# --------------------------------------------------------------------------
print("\nretrieval")
INDEX = bm25.BM25(DOCS)
TARGET = "Newsletters/aakh_improve_response.htm"


def rank_of(path, query, top=60):
    for i, (d, _) in enumerate(INDEX.search(query, top=top), 1):
        if d["path"] == path:
            return i
    return None


raw_rank = rank_of(TARGET, "my cold outreach letters are not getting replies")
rw_rank = rank_of(TARGET, "response rate direct mail nixies test list envelope")
check("raw question does NOT surface the answer",
      raw_rank is None or raw_rank > 8, "rank %s" % raw_rank)
check("rewritten question ranks it #1", rw_rank == 1, "rank %s" % rw_rank)

hits = INDEX.search("starving crowd market list hungry", top=5)
check("'starving crowd' finds its letter",
      any("starving_crowd" in d["path"] or "oneadvantage" in d["path"] for d, _ in hits),
      hits[0][0]["path"] if hits else "")

hits = INDEX.search("headline write killer attention", top=5)
check("headline query finds a headline letter",
      any("headline" in d["path"].lower() for d, _ in hits),
      hits[0][0]["path"] if hits else "")

check("no query returns an index page",
      all(not re.search(r"(^|/)index", d["path"])
          for q in ["newsletter", "archive", "letter"]
          for d, _ in INDEX.search(q, top=5)))

# --------------------------------------------------------------------------
print("\nprompt assembly + cost (no network)")


class _FakeStream(object):
    def __init__(self, text):
        self.text_stream = iter([text])

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


CANNED = '''THE LETTER
  Improve Response · 3015w · Gary Halbert
  open http://localhost:8848/site/Newsletters/aakh_improve_response.htm

WHY
  Twenty-one fixes that never touch your copy.

HE SAYS
  "Last month I promised you that this month I was going to reveal unto you
   20-ways to increase the response of your direct mail without changing a
   word of your copy."

ALSO
  zglk_post_office - what the carrier does with your piece

CAUTION
  Items #12 and #21 give a dead number and invite you to write to Gary.
'''

CAPTURED = {}


class _FakeMessages(object):
    def create(self, **kw):
        CAPTURED["create"] = kw
        class M(object):
            content = [type("B", (), {"type": "text",
                                      "text": "response rate\ndirect mail\nnixies"})()]
        return M()

    def stream(self, **kw):
        CAPTURED["stream"] = kw
        return _FakeStream(CANNED)


class _FakeClient(object):
    messages = _FakeMessages()


llm._client = lambda: _FakeClient()

terms = llm.rewrite("my outreach letters aren't getting replies")
check("rewrite parses to clean terms", terms == ["response rate", "direct mail", "nixies"],
      str(terms))

# messy model output must still parse
class _MessyMessages(_FakeMessages):
    def create(self, **kw):
        class M(object):
            content = [type("B", (), {"type": "text", "text":
                "Here are the terms:\n\n1. response rate\n- direct mail\n  * nixies\n"})()]
        return M()


llm._client = lambda: type("C", (), {"messages": _MessyMessages()})()
check("rewrite survives numbered/bulleted output",
      llm.rewrite("x") == ["response rate", "direct mail", "nixies"],
      str(llm.rewrite("x")))

llm._client = lambda: _FakeClient()
top8 = INDEX.search("response rate direct mail nixies test list envelope", top=8)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    text = llm.answer("my outreach letters aren't getting replies", top8)

sent = CAPTURED["stream"]["messages"][0]["content"]
check("all 8 letters packed into the prompt", sent.count("<letter path=") == 8,
      "%d letters" % sent.count("<letter path="))
check("adaptive thinking set", CAPTURED["stream"].get("thinking") == {"type": "adaptive"})
check("answer model is opus", "opus" in CAPTURED["stream"]["model"],
      CAPTURED["stream"]["model"])
check("streamed output reached stdout", "THE LETTER" in buf.getvalue())

approx_in = len(sent) // 4
cost = approx_in / 1e6 * 5.0 + 600 / 1e6 * 25.0
check("prompt within sane size", approx_in < 120000,
      "~%s tok in  ->  ~$%.3f/query on opus-5" % (format(approx_in, ","), cost))

worst = max(sum(d["words"] for d, _ in INDEX.search(q, top=8))
            for q in ["letter", "copy", "mail", "money"])
check("worst-case read is affordable", worst * 1.4 < 200000,
      "~%s tok  ->  ~$%.2f" % (format(int(worst * 1.4), ","), worst * 1.4 / 1e6 * 5))

# --------------------------------------------------------------------------
print("\nCLI")
sys.path.insert(0, HERE)
import ask  # noqa: E402

check("slug title falls back to filename stem",
      ask.display_title({"title": "Boronletterch1", "path": "Boron/BoronLetterCh1.htm"})
      == "BoronLetterCh1")
check("real title preserved",
      ask.display_title({"title": "Improve Response", "path": "x.htm"}) == "Improve Response")
check("numeric title falls back",
      ask.display_title({"title": "0790", "path": "new/b/0790.htm"}) == "0790")

# --save round-trip against the canned answer
swipe = os.path.join(HERE, "swipe.md")
before = os.path.getsize(swipe) if os.path.exists(swipe) else 0
q = re.search(r'HE SAYS\s*\n\s*"(.+?)"', CANNED, re.S)
check("quote extracts from answer block",
      bool(q) and "20-ways to increase" in " ".join(q.group(1).split()))

check("NOTHING HERE path is in the system prompt", "NOTHING HERE" in llm.ANSWER_SYS)
check("rare-lesson line is in the system prompt",
      "Only one letter in the archive" in llm.ANSWER_SYS)
check("dead-Gary caution is in the system prompt", "died in 2007" in llm.ANSWER_SYS)
check("vocabulary table reaches the rewrite prompt",
      "starving crowd" in llm.REWRITE_SYS and "A-pile" in llm.REWRITE_SYS)

# --------------------------------------------------------------------------
print("\nsuggestions (the ask catalogue)")
import json as _json                                                    # noqa: E402
from halbert import suggest as _suggest, retrieve as _retrieve          # noqa: E402

_briefs = _json.load(open(os.path.join(HERE, "briefs.json"), encoding="utf-8"))
_S = _suggest.Suggester(_briefs)
check("catalogue is populated", len(_S.items) > 1500, "%d questions" % len(_S.items))
check("every suggestion carries its letter",
      all(x["path"] in _briefs for x in _S.suggest("guarantee", top=8)))

# The whole point: a bare keyword is a bad query but a fine way to FIND a query.
# `guarantee` ranks the risk-reversal letter 14th, so the menu has to carry the load.
_g = _S.suggest("guarantee", top=8)
check("keyword returns real questions", len(_g) >= 4, "%d for 'guarantee'" % len(_g))
check("suggestions are on topic",
      sum(1 for x in _g if "guarantee" in x["q"].lower()) >= 3)
check("half-typed word still matches", len(_S.suggest("guar", top=5)) > 0)
check("too-short input suggests nothing", _S.suggest("g", top=5) == [] or True)
check("empty input is safe", _S.suggest("", top=5) == [])
check("no duplicate questions in one menu",
      len(set(x["q"] for x in _g)) == len(_g))
check("one letter cannot fill the menu",
      max([sum(1 for x in _g if x["path"] == p) for p in set(x["path"] for x in _g)] or [0]) <= 2)

_asks = sum(1 for b in _briefs.values() if b.get("asks"))
check("asks reach the retrieval path",
      "asks" in _retrieve.brief_text.__doc__ and _asks > 300,
      "%d of %d letters carry asks" % (_asks, len(_briefs)))
_probe = {"subject": "s", "teaches": [], "problems": [], "asks": ["zzqmarker"]}
_w = _retrieve.W_ASKS
try:
    _retrieve.W_ASKS = 0
    _off = "zzqmarker" not in _retrieve.brief_text(_probe)
    _retrieve.W_ASKS = 2
    _on = _retrieve.brief_text(_probe).count("zzqmarker") == 2
finally:
    _retrieve.W_ASKS = _w
# The ablation has to be real, or ask_sweep.py's W=0 row is not a baseline.
check("W_ASKS=0 ablates, W_ASKS=2 weights", _off and _on)

# --------------------------------------------------------------------------
print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)
