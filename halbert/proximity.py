"""Term-proximity rerank of an already-retrieved candidate list.

Sequential-dependence idea (Metzler & Croft): documents where the query's terms appear
NEAR each other are more likely to be about the query than documents where the same terms
appear scattered. Reported to help most on small homogeneous collections with long queries,
which is exactly this corpus.

Two deliberate choices:

  * Proximity is computed on the RAW question's terms, never the thesaurus-expanded ones.
    The expansion is a bag of loosely-associated words -- `cold email` becomes
    `sales letter direct mail envelope prospect` -- and word order among those is an
    artifact of how the table was written, not a signal about the document. Scoring
    adjacency over that would be measuring the thesaurus, not the letter.

  * It runs ONLY as a rerank over candidates already retrieved. Recall cannot regress,
    so the experiment is bounded: the worst case is that ordering does not improve.
"""

import re
from collections import defaultdict

from . import bm25

WINDOW = 12          # tokens; ordered pairs inside this span count
ORDERED_BONUS = 1.0
UNORDERED_BONUS = 0.4


def _positions(tokens, wanted):
    pos = defaultdict(list)
    for i, t in enumerate(tokens):
        if t in wanted:
            pos[t].append(i)
    return pos


def score(text, question, window=WINDOW):
    """Proximity score for one document against the raw question.

    Counts, for each adjacent pair of query terms, how often they occur within `window`
    tokens -- crediting the query's own order more than the reverse. Normalised by the
    number of pairs so long questions do not automatically outscore short ones.
    """
    qterms = bm25.tokenize(question)
    if len(qterms) < 2:
        return 0.0
    pairs = [(qterms[i], qterms[i + 1]) for i in range(len(qterms) - 1)
             if qterms[i] != qterms[i + 1]]
    if not pairs:
        return 0.0

    tokens = bm25.tokenize(text)
    pos = _positions(tokens, set(qterms))
    if not pos:
        return 0.0

    total = 0.0
    for a, b in pairs:
        pa, pb = pos.get(a), pos.get(b)
        if not pa or not pb:
            continue
        best = 0.0
        for i in pa:
            for j in pb:
                d = j - i
                if 0 < d <= window:
                    best = max(best, ORDERED_BONUS * (1.0 - (d - 1) / float(window)))
                elif -window <= d < 0:
                    best = max(best, UNORDERED_BONUS * (1.0 - (-d - 1) / float(window)))
        total += best
    return total / len(pairs)


def rerank(hits, question, weight=0.25, window=WINDOW):
    """hits: [(doc, score)] already ranked. Returns the list reordered.

    The proximity term is added to the existing normalised fusion score, scaled by
    `weight`. Because both are on a comparable 0-1-ish scale, `weight` is roughly
    "how many points of fusion score a perfect phrase match is worth".
    """
    if not hits:
        return hits
    best = hits[0][1] or 1.0
    out = []
    for doc, s in hits:
        p = score(doc["text"], question, window)
        out.append((doc, (s / best) + weight * p))
    out.sort(key=lambda kv: -kv[1])
    return out
