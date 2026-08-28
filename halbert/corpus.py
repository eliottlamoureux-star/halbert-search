"""Load the letter mirror into clean, searchable text.

Decoding order is utf-8 then cp1252 -- never latin-1, which turns the 0x80-0x9F
bytes in 57 letters into invisible control characters (`driver\x92s` instead of
`driver's`). We quote these passages verbatim, so that damage would be on screen.
"""

import gzip
import html
import os
import pickle
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(HERE, "site")
CACHE = os.path.join(HERE, "corpus.pkl")

# Pages that are in letters.json but are not letters.
EXCLUDE = re.compile(
    r"(?i)(^|/)(index\d*\.html?|copy of .*|.*template.*|.*\btest\b.*|signup.*|"
    r"signupthankyou.*|.*archives?\.html?|.*newsletter-archives.*|become-an-affiliate.*|"
    r"lettersmainframe.*|.*mainframe.*|.*seal_of_approval.*|thank[_ ]?you.*)$"
)

# Boilerplate that appears on nearly every letter and would otherwise make every
# document look like every other document.
BOILER = [
    r"(?i)click\s+here\s+to\s+view\s+our\s+newsletter\s+archives?",
    r"(?i)click\s+here\s+if\s+you\s+want\s+to\s+be\s+on\s+my\s+newsletter\s+announcement\s+list",
    r"(?i)click\s+here\s+to\s+e-?mail\s+us",
    r"(?i)copyright\s*.{0,4}\s*(19|20)\d\d\s+gary\s+c?\.?\s*halbert.*?reserved\.?",
    r"(?i)copyright\s*.{0,4}\s*gary\s+c?\.?\s*halbert.*?reserved\.?",
    r"(?i)all\s+rights\s+reserved\.?",
    r"(?i)the\s+gary\s+halbert\s+letter\s*$",
    r"(?i)^\s*[vw<>]\s*(previous|next)\s*[vw<>]?\s*$",
    r"(?i)begin\s+web-?stat\s+code.*?end\s+web-?stat\s+code",
    r"(?i)/?\s*aweber\s+web\s+form\s+generator[\d\. ]*",
    r"(?i)7510\s+sunset\s+blvd.*?90046",
]
BOILER = [re.compile(p, re.S | re.M) for p in BOILER]


def read_text(path):
    """Bytes on disk -> clean text. Handles the two gzip files named .htm."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:2] == b"\x1f\x8b":  # gzip stream with an .htm extension
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            s = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        s = raw.decode("utf-8", "replace")

    s = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?i)<(br|/p|/div|/tr|/td|/h[1-6]|/li)\b[^>]*>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    for pat in BOILER:
        s = pat.sub(" ", s)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def _shingles(text, n=8):
    # Stride 1. Subsampling makes the sets too sparse for containment to be
    # reliable -- at stride 3 this silently missed 40 genuine duplicate pairs.
    w = re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
    return set(" ".join(w[i:i + n]) for i in range(max(1, len(w) - n)))


def _dedupe(docs, thresh=0.90):
    """Collapse near-duplicates by 8-gram containment.

    Jaccard is the wrong measure here: TChapter1 is a fragment of BoronLetterCh1
    at J=0.395 but containment=0.983. Keeps the copy with the most content and
    the least chrome, then inherits the best title from the group.
    """
    sh = {d["path"]: _shingles(d["text"]) for d in docs}
    parent = {d["path"]: d["path"] for d in docs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    paths = [d["path"] for d in docs]
    for i in range(len(paths)):
        a = sh[paths[i]]
        if not a:
            continue
        for j in range(i + 1, len(paths)):
            b = sh[paths[j]]
            if not b:
                continue
            if len(a & b) / min(len(a), len(b)) > thresh:
                ra, rb = find(paths[i]), find(paths[j])
                if ra != rb:
                    parent[rb] = ra

    groups = {}
    for d in docs:
        groups.setdefault(find(d["path"]), []).append(d)

    kept, aliases = [], {}
    for members in groups.values():
        best = max(members, key=_quality)
        titled = max(members, key=lambda d: _title_score(d["title"]))
        if _title_score(titled["title"]) > _title_score(best["title"]):
            best = dict(best, title=titled["title"])
        dated = [m for m in members if m.get("date")]
        if dated and not best.get("date"):
            best = dict(best, date=dated[0]["date"])
        kept.append(best)
        for m in members:
            if m["path"] != best["path"]:
                aliases[m["path"]] = best["path"]
    return kept, aliases


def _quality(d):
    """Prefer real content over chrome; punish files that look like artifacts."""
    s = len(d["text"].split())
    p = d["path"].lower()
    if re.search(r"template|copy of|\bold\b|draft|bodytextonly|mobil|index", p):
        s -= 1200
    s += 400 if _title_score(d["title"]) > 1 else 0
    s += 200 if d.get("date") else 0
    return s


def _title_score(t):
    t = (t or "").strip()
    if not t or t.isdigit():
        return 0
    if re.fullmatch(r"[A-Z][a-z]+[a-z0-9]*", t):  # 'Boronletterch1', 'Oneadvantage'
        return 1
    return 2 + min(len(t.split()), 8)


def load(force=False):
    """Return (docs, aliases). Cached -- delete corpus.pkl to rebuild."""
    if not force and os.path.exists(CACHE):
        with open(CACHE, "rb") as fh:
            return pickle.load(fh)

    import json
    with open(os.path.join(HERE, "letters.json"), encoding="utf-8") as fh:
        records = json.load(fh)

    docs = []
    for r in records:
        if EXCLUDE.search(r["path"]):
            continue
        full = os.path.join(SITE, r["path"])
        if not os.path.exists(full):
            continue
        text = read_text(full)
        if len(text.split()) < 25:
            continue
        docs.append({
            "path": r["path"],
            "title": r.get("title") or "",
            "date": r.get("date"),
            "series": r["path"].split("/")[0],
            "words": len(text.split()),
            "text": text,
        })

    docs, aliases = _dedupe(docs)
    docs.sort(key=lambda d: d["path"])
    with open(CACHE, "wb") as fh:
        pickle.dump((docs, aliases), fh)
    return docs, aliases


if __name__ == "__main__":
    docs, aliases = load(force=True)
    print("letters kept : %d" % len(docs))
    print("collapsed    : %d near-duplicates" % len(aliases))
    print("words        : %s" % format(sum(d["words"] for d in docs), ","))
    print("longest      : %s (%dw)" % max(
        ((d["path"], d["words"]) for d in docs), key=lambda x: x[1]))
