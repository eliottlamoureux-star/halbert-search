"""Okapi BM25 over the letter text. No dependencies.

Indexes stripped text, never raw HTML -- markup inflates document length ~1.9x
and measurably degrades the top 5.
"""

import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9']+")

# Halbert writes in contractions and the corpus is small, so we stem lightly and
# keep almost everything. A big stopword list costs recall here.
STOP = set("""a an the and or but if of to in on at by for with from as is are was were
be been being it its this that these those i you he she they we my your his her their our
me him them us do does did not no so then than there here what which who whom when where
how all any both each few more most other some such only own same too very s t can will
just don should now""".split())


def tokenize(text):
    return [w for w in TOKEN.findall(text.lower()) if w not in STOP and len(w) > 1]


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
