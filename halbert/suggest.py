"""Turn the `asks` catalogue into search suggestions.

The archive answers questions, not keywords. Typing `guarantee` into a BM25 index over
1984-2013 direct mail returns the letters that say "guarantee" most often, which are a
legal-compliance rant and a male-enhancement sales letter -- not the letter that teaches
risk reversal, which ranks 14th. That is not a bug in the scoring; it is what term
frequency means. A keyword names a topic, and this corpus is organised by problem.

Every letter already carries 4-8 `asks` -- the questions it answers, written the way a
reader types (see TASK_BRIDGE.md). That is 2,130 real questions. This module makes them
searchable, so a keyword becomes a menu of questions instead of a guess at phrasing:

    guarantee  ->  "should i hold off charging their card until a month after i ship"
                   "how do i stop people from taking it and never paying"
                   ...

Pure Python, reuses halbert.bm25, no index build beyond the one BM25 object.
"""

import os

from . import bm25

MIN_PREFIX = 3          # below this, prefix expansion matches too much to be useful
MAX_EXPAND = 40         # cap vocabulary terms pulled in by one prefix


class Suggester(object):
    def __init__(self, briefs):
        """briefs: the loaded briefs.json. Only `asks` and `subject` are used."""
        self.items = []                 # [(question, path, subject)]
        for path, b in (briefs or {}).items():
            subject = b.get("subject", "") or ""
            for a in (b.get("asks") or []):
                self.items.append((a, path, subject))

        # Each ask is its own document. They are short and uniform, so the default
        # b=0.75 length normalisation is right here -- unlike the letters, which span
        # 34 to 14,651 words and need b=0.35.
        self.index = bm25.BM25(
            [{"path": str(i), "text": q, "title": "", "words": 0}
             for i, (q, _, _) in enumerate(self.items)]) if self.items else None

        self.vocab = set()
        for q, _, _ in self.items:
            self.vocab.update(bm25.tokenize(q))

    def _expand_prefix(self, text):
        """Let a half-typed last word match. `guar` -> `guarantee`, `guaranteed`.

        Only the final token expands: the earlier words are ones the user finished
        typing, and expanding those turns a specific query back into a vague one.
        """
        raw = text.rstrip()
        if not raw or raw.endswith(" "):
            return text
        parts = raw.split()
        last = bm25.tokenize(parts[-1])
        if not last:
            return text
        stub = last[-1]
        if len(stub) < MIN_PREFIX or stub in self.vocab:
            return text
        hits = [w for w in self.vocab if w.startswith(stub)][:MAX_EXPAND]
        return text + " " + " ".join(hits) if hits else text

    def suggest(self, text, top=8):
        """Partial query -> [{question, path, subject}], best first, deduplicated."""
        if not self.index or not (text or "").strip():
            return []
        query = self._expand_prefix(text)
        out, seen_q, seen_path = [], set(), {}
        for doc, score in self.index.search(query, top=top * 6):
            q, path, subject = self.items[int(doc["path"])]
            key = q.lower()
            if key in seen_q:
                continue
            # At most 2 suggestions from any one letter, so a letter with 8 asks
            # cannot fill the whole menu and hide the rest of the archive.
            if seen_path.get(path, 0) >= 2:
                continue
            seen_q.add(key)
            seen_path[path] = seen_path.get(path, 0) + 1
            out.append({"q": q, "path": path, "subject": subject,
                        "score": round(score, 3)})
            if len(out) >= top:
                break
        return out
