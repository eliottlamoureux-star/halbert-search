"""THE retrieval path. Both ask.py and evaluate.py call this and nothing else.

If the tool and the evaluation use different code, the evaluation measures a system
nobody uses. That is not hypothetical -- the first version searched only letter text
while the briefs sat unused as a diagnostic, and 27% of all failures were letters the
brief index would have found immediately. Wiring the briefs in moved recall@8 from
54.8% to 70.4% with no other change.

Two arms, because there are two vocabularies:

  augmented   each letter's own text PLUS its brief. His words and yours in one index.
  brief       the brief alone. Short, dense, entirely in modern reader vocabulary.

Every constant below was set by measurement, not taste -- see fuse_sweep.py,
arm_sweep.py, prf_sweep.py, param_sweep.py. Things that were tried and REJECTED:

  * splitting the brief into `problems` and `subject+teaches` arms   68.7% vs 70.4%
    (short docs lose BM25 discrimination; the parts are worse than the whole)
  * pseudo-relevance feedback / RM3                                  62.6% vs 70.4%
    (amplifies noise when the seed retrieval is itself mediocre)
  * reciprocal rank fusion instead of normalised sum                 no gain at 2 arms
  * enriching briefs to 12-18 problem phrasings each                 REJECTED 69.8% vs 81.1%
    More surface area destroyed discrimination: every brief came to claim every topic,
    IDF collapsed, and recall fell monotonically as phrasings grew (cap 3 -> 79.2%,
    cap 10 -> 73.6%, uncapped -> 69.8%). The rejected set is kept as
    briefs.enriched-rejected.json. Do not retry without a different mechanism.

The query is issued TWICE and fused: once thesaurus-expanded, once raw. The raw question
carries signal the expansion discards, and keeping both is worth +4.4 points at 20
(88.1% -> 92.5%).
"""

import json
import os

from . import bm25, thesaurus

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFS = os.path.join(HERE, "briefs.json")

TOP_K = 20          # candidates handed to the answer layer.
                    # Depth on the TUNED set: @12 81.1% · @20 92.5% · @30 95.0%.
                    # Held out with an independent key it is 77.8% @20 -- see MEASUREMENTS.md.
                    # The answer layer triages 20 cheaply by subject, then reads 4-6 in full.

# b is BM25 length normalisation. 0.35 on letters rather than the usual 0.75 because
# this corpus spans 34 to 14,651 words and the standard penalty buries long letters.
B_LETTER = 0.35
B_BRIEF = 0.75
W_AUG = 1.0
W_BRIEF = 1.0

# How many times the `asks` block is repeated in the indexed brief text. Repetition is
# how term weight is expressed to BM25 here, matching the 1:2:2 subject:teaches:problems
# scheme above. Swept by ask_sweep.py; 0 disables the bridge entirely for ablation.
W_ASKS = 1

# Non-teaching letters otherwise occupy top-K slots. Tuned: this beats no demotion
# (77.4% -> 80.0% @12) and beats milder settings.
DEMOTE = {"pitch": 0.40, "aside": 0.30, "admin": 0.10, "memorial": 0.10}


def brief_text(b):
    """What of a brief gets indexed. `problems` is the modern-vocabulary bridge and
    is doubled so it carries more weight than the letter's own framing.

    `asks` is the second half of that bridge: the same problems restated the way a user
    types them. Motivation: all 16 held-out failures rank #1 when queried with their own
    brief's wording, so those briefs are discriminative and the index can reach them --
    what is missing is the user's register, not the content.

    That is NOT true of every failure, and the first version of this comment said it was.
    Inspecting all 16 individually: some are genuine translation gaps (a brief saying
    "the full rollout completely tanked" never matches "died at 1000"), some are real
    coverage gaps where the brief omits the facet asked about, and some are simply wrong
    key entries. `asks` addresses only the first group. See MEASUREMENTS.md for the split.

    Gated by halbert/merge_bridge.py, which uses a round-trip filter (Doc2Query--,
    arXiv:2301.03266) so a phrasing survives only if it retrieves its own letter.
    """
    teaches = " ".join(b.get("teaches", []) or [])
    problems = " ".join(b.get("problems", []) or [])
    asks = " ".join(b.get("asks", []) or [])
    # subject:teaches:problems weighted 1:2:2 -- measured, see text_sweep.py
    parts = [b.get("subject", ""), teaches, teaches, problems, problems]
    parts.extend([asks] * W_ASKS)
    return " ".join(filter(None, parts))


class Retriever(object):
    def __init__(self, docs, briefs=None, demote=True):
        self.docs = docs
        self.by_path = {d["path"]: d for d in docs}

        if briefs is None and os.path.exists(BRIEFS):
            with open(BRIEFS, encoding="utf-8") as fh:
                briefs = json.load(fh)
        self.briefs = briefs or {}
        bt = {p: brief_text(b) for p, b in self.briefs.items()}

        self.aug_index = bm25.BM25(
            [{"path": d["path"], "text": d["text"] + " " + bt.get(d["path"], ""),
              "title": d["title"], "words": d["words"]} for d in docs], b=B_LETTER)
        bd = [{"path": p, "text": t, "title": "", "words": 0}
              for p, t in bt.items() if t.strip()]
        self.brief_index = bm25.BM25(bd, b=B_BRIEF) if bd else None
        self.demote = demote

    def _kind_factor(self, path):
        if not self.demote:
            return 1.0
        kind = (self.briefs.get(path) or {}).get("kind", "teaching")
        return DEMOTE.get(kind, 1.0)

    def search(self, question, top=None, pool=40, terms=None):
        """Question -> ranked letters.

        Four passes: {expanded query, raw question} x {augmented index, brief index}.
        Each pass is min-max normalised before fusion so no arm's raw BM25 scale can
        dominate. Dropping the raw pass costs 4.4 points at top-20.
        """
        top = TOP_K if top is None else top
        terms = terms or thesaurus.expand(question)
        queries = [" ".join(terms), question]

        combined = {}
        for query in queries:
            for index, weight in ((self.aug_index, W_AUG), (self.brief_index, W_BRIEF)):
                if index is None or weight == 0:
                    continue
                hits = index.search(query, top=pool)
                if not hits:
                    continue
                hi, lo = hits[0][1], hits[-1][1]
                span = hi - lo
                for d, s in hits:
                    # A pass with one hit, or with every score tied, has no spread to
                    # normalise. It used to compute (s-lo)/1.0 = 0, so a pass that
                    # uniquely surfaced a document gave that document ZERO credit --
                    # the strongest evidence available, discarded. Full credit instead.
                    norm = 1.0 if span <= 0 else (s - lo) / span
                    # TRUE min-max. Dividing by the max alone left the pool's last
                    # document holding 34-45% of the winner's credit, so the fusion
                    # rewarded breadth of mediocrity over depth of match -- which is
                    # exactly the profile it produced: recall@20 92.5%, MRR 0.42.
                    # Subtracting the floor: recall@5 61.6% -> 64.8%, MRR -> 0.434.
                    # (z-score was also tried and is worse: 88.7% / 0.413.)
                    combined[d["path"]] = combined.get(d["path"], 0.0) + weight * norm

        ranked = sorted(((p, s * self._kind_factor(p)) for p, s in combined.items()),
                        key=lambda kv: -kv[1])[:top]
        return [(self.by_path[p], s) for p, s in ranked if p in self.by_path]
