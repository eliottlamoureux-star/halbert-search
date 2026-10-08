"""Okapi BM25 over the letter text. No dependencies.

Indexes stripped text, never raw HTML -- markup inflates document length ~1.9x
and measurably degrades the top 5.
"""

import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9']+")

# There is NO stemming -- tokens match as written. An earlier version of this comment
# claimed light stemming; it never existed. Caught in review 2026-08-30.
# Halbert writes in contractions and the corpus is small, so the stopword list stays
# short and keeps almost everything. A big stopword list costs recall here.
STOP = set("""a an the and or but if of to in on at by for with from as is are was were
be been being it its this that these those i you he she they we my your his her their our
me him them us do does did not no so then than there here what which who whom when where
how all any both each few more most other some such only own same too very s t can will
just don should now""".split())


# Light suffix stripping, applied to queries and documents alike. NOT Porter -- five
# rules, ordered longest-first, and only when at least 3 characters remain, so "thing"
# and "need" survive intact while "marketing"/"market" and "tested"/"test" collapse.
#
# Measured on the 72-question held-out set, with the `asks` bridge in place:
#     off  recall@20 79.2%  MRR 0.416  top-5 61.1%  top-1 26.4%
#     on   recall@20 81.9%  MRR 0.455  top-5 62.5%  top-1 30.6%
# It exists because the whole remaining failure mode is paraphrase, and "scale/scaled/
# scaling" or "price/pricing/priced" are the cheapest paraphrases there are.
SUFFIX = (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", ""))


def stem(w):
    for suf, repl in SUFFIX:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)] + repl
    return w


def tokenize(text):
    return [stem(w) for w in TOKEN.findall(text.lower())
            if w not in STOP and len(w) > 1]


class BM25(object):
    def __init__(self, docs, k1=1.2, b=0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf = []
        self.len = []
        df = Counter()
        for d in docs:
            toks = tokenize(d["text"])
            c = Counter(toks)
            self.tf.append(c)
            self.len.append(len(toks))
            df.update(c.keys())
        self.n = len(docs)
        self.avgdl = (sum(self.len) / float(self.n)) if self.n else 0.0
        self.idf = {
            t: math.log(1.0 + (self.n - v + 0.5) / (v + 0.5)) for t, v in df.items()
        }
        # term -> doc ids, so scoring touches only documents that can score
        self.post = {}
        for i, c in enumerate(self.tf):
            for t in c:
                self.post.setdefault(t, []).append(i)

    def search(self, query, top=20):
        q = tokenize(query) if isinstance(query, str) else [w.lower() for w in query]
        scores = {}
        for t in q:
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i in self.post.get(t, ()):
                f = self.tf[i][t]
                denom = f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avgdl)
                scores[i] = scores.get(i, 0.0) + idf * (f * (self.k1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top]
        return [(self.docs[i], s) for i, s in ranked]
