#!/usr/bin/env python3
"""Build a local navigation index for the mirrored archive.

Only metadata is emitted here — title, dateline, word count, link.
The letters themselves are served untouched, exactly as fetched.
"""
import os, re, html, json, urllib.parse, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")

# ---- 1. titles harvested from the site's own index page -------------------
TITLE_MAP = {}
idx_src = os.path.join(ROOT, "index-source.html")
if os.path.exists(idx_src):
    raw = open(idx_src, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'(?is)<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
        href, text = m.group(1), m.group(2)
        text = re.sub(r'(?s)<[^>]+>', ' ', text)
        text = html.unescape(re.sub(r'\s+', ' ', text)).strip()
        if not text or len(text) < 4:
            continue
        path = urllib.parse.unquote(urllib.parse.urlparse(href).path).lower()
        if path.endswith((".htm", ".html")):
            key = os.path.basename(path)
            # keep the longest/most descriptive label seen for a file
            if len(text) > len(TITLE_MAP.get(key, "")):
                TITLE_MAP[key] = text

SORTCODE = re.compile(r'^[a-z]{4}_')
DATEFILE = re.compile(r'^(?:\d{2}-\d{2}-\d{2}|(?:19|20)\d\d[-_]\d{2}[-_]\d{2})')
MONTHS = ["January","February","March","April","May","June","July",
          "August","September","October","November","December"]

def prettify(slug, rel=""):
    s = os.path.splitext(slug)[0]
    # Boron Letters get a proper chapter name
    h = re.match(r'^(\d{1,3})$', s)
    if h and re.search(r'(?i)/hotd/', '/' + rel):
        return f"Halbertism #{int(h.group(1))}"
    b = re.match(r'(?i)^T?Chapter\s*_?(\d+)([a-z]?)$', s)
    if b or '/boron/' in ('/' + rel).lower():
        m = re.search(r'(?i)chapter\s*_?(\d+)\s*([a-z]?)', s)
        if m:
            two = ' 2.0' if '2.0' in s else ''
            return f"Boron Letters{two} — Chapter {int(m.group(1))}{m.group(2).upper()}"
    s = s.lstrip('_')
    s = SORTCODE.sub('', s)                      # strip zfkj_ / zszs_ sort codes
    s = s.lstrip('_')
    s = re.sub(r'(?i)(original|copy)$', '', s)
    s = re.sub(r'[_\-]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.title() if s else os.path.splitext(slug)[0]

DATE_RE  = re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b')
PATH_DATE= re.compile(r'/(\d{2})-(\d{2})-(\d{2})(?:[^/]*)\.html?$', re.I)
ISO_FILE = re.compile(r'/((?:19|20)\d\d)[-_](\d{2})[-_](\d{2})(?:[^/]*)\.html?$', re.I)
LONGDATE = re.compile(r'(?i)\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+((?:19|20)\d\d)\b')
YEAR_DIR = re.compile(r'/(19|20)(\d\d)/')

def norm_year(y):
    y = int(y)
    if y < 100:
        y += 1900 if y >= 60 else 2000
    return y

records = []
for dirpath, _, files in os.walk(SITE):
    for fn in sorted(files):
        if not fn.lower().endswith((".htm", ".html")):
            continue
        full = os.path.join(dirpath, fn)
        rel  = os.path.relpath(full, SITE).replace(os.sep, "/")
        try:
            raw = open(full, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue

        text = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', raw)
        text = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', text))
        words = len(text.split())
        # A short page is not automatically a stub. Halbertisms run 34-400
        # words and are genuine content, so a positive content marker
        # overrides the length floor; the floor only screens unmarked pages.
        marked = re.search(r'(?i)halbertism\s*#?\s*\d+', text[:3000])
        if words < 120 and not marked:       # nav stubs / redirect shims
            continue
        if re.search(r'(?i)/(StorePages|MarketingMovieNight)/', '/' + rel):
            continue                          # store index / event flyer, not a letter

        title = TITLE_MAP.get(fn.lower()) or prettify(fn, rel)

        # dateline: the letter's own M/D/YY, else the year in its path
        date_s, year = None, None
        m = DATE_RE.search(text[:9000])
        if m:
            mo, dy, yr = int(m.group(1)), int(m.group(2)), norm_year(m.group(3))
            if 1 <= mo <= 12 and 1 <= dy <= 31 and 1960 <= yr <= 2026:
                date_s, year = f"{yr:04d}-{mo:02d}-{dy:02d}", yr
        if not year:
            pm = PATH_DATE.search("/" + rel)
            if pm:
                mo, dy, yr = int(pm.group(1)), int(pm.group(2)), norm_year(pm.group(3))
                if 1 <= mo <= 12 and 1 <= dy <= 31:
                    date_s, year = f"{yr:04d}-{mo:02d}-{dy:02d}", yr
        if not year:
            im = ISO_FILE.search("/" + rel)
            if im:
                yr, mo, dy = int(im.group(1)), int(im.group(2)), int(im.group(3))
                if 1 <= mo <= 12 and 1 <= dy <= 31:
                    date_s, year = f"{yr:04d}-{mo:02d}-{dy:02d}", yr
        if not year:
            lm = LONGDATE.search(text[:9000])
            if lm:
                mo = MONTHS.index(
                    next(x for x in MONTHS if x.lower().startswith(lm.group(1)[:3].lower()))) + 1
                dy, yr = int(lm.group(2)), norm_year(lm.group(3))
                if 1 <= dy <= 31 and 1960 <= yr <= 2026:
                    date_s, year = f"{yr:04d}-{mo:02d}-{dy:02d}", yr
        if not year:
            ym = YEAR_DIR.search("/" + rel)
            if ym:
                year = int(ym.group(1) + ym.group(2))

        # a bare date-named file has no real title in it — name it by its date
        if DATEFILE.match(fn) and date_s:
            y, mo, dy = date_s.split("-")
            nice = f"{MONTHS[int(mo)-1]} {int(dy)}, {y}"
            extra = re.sub(r'^(?:\d{2}-\d{2}-\d{2}|(?:19|20)\d\d[-_]\d{2}[-_]\d{2})[-_]?', '',
                           os.path.splitext(fn)[0])
            extra = re.sub(r'[_\-]+', ' ', extra).strip()
            title = f"Letter — {nice}" + (f" ({extra})" if extra else "")

        records.append({"path": rel, "title": title, "date": date_s,
                        "year": year, "words": words,
                        "boron": "/boron/" in ("/" + rel).lower()})

# one entry per distinct letter; prefer the shortest, cleanest path
import hashlib
_seen = {}
for r in records:
    try:
        _raw = open(os.path.join(SITE, r["path"]), "rb").read().decode("utf-8", "ignore")
        _t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', _raw)
        _t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', _t))
        _w = re.sub(r'[^a-z0-9 ]+', '', re.sub(r'\s+', ' ', _t).strip().lower()).split()
        # opening shingle collapses copies that differ only in trailing markup
        d = hashlib.md5(' '.join(_w[:600]).encode()).hexdigest() if len(_w) >= 100 \
            else hashlib.md5(' '.join(_w).encode()).hexdigest()
    except Exception:
        d = r["path"]
    cur = _seen.get(d)
    score = (("protected" in r["path"].lower()), len(r["path"]))
    if cur is None or score < cur[0]:
        _seen[d] = (score, r)
records = [v[1] for v in _seen.values()]

# Hash-based dedup misses copies whose nav markup differs just enough to change
# the hash. Final fuzzy pass: among records sharing a date or a title, collapse
# pairs whose 8-word shingle sets overlap >75%. Keep the longer text.
def _wordset(rec):
    try:
        _r = open(os.path.join(SITE, rec["path"]), encoding="utf-8", errors="ignore").read()
    except Exception:
        return []
    _t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', _r)
    _t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', _t))
    return re.sub(r'[^a-z0-9 ]+', '', re.sub(r'\s+', ' ', _t).strip().lower()).split()

def _shingles(ws, k=8):
    return {' '.join(ws[i:i+k]) for i in range(max(0, len(ws) - k + 1))}

# a record may land in several buckets, but never twice in the SAME bucket -
# doing so makes it compare against itself, score 1.0, and delete itself.
_buckets = collections.defaultdict(dict)
for r in records:
    if r["date"]:
        _buckets[("d", r["date"])][id(r)] = r
    _buckets[("t", r["title"].lower())][id(r)] = r

_drop, _cache = set(), {}
for _key, _bucket in _buckets.items():
    _group = [r for r in _bucket.values()]
    if len(_group) < 2:
        continue
    for _i in range(len(_group)):
        for _j in range(_i + 1, len(_group)):
            _a, _b = _group[_i], _group[_j]
            if _a is _b or id(_a) in _drop or id(_b) in _drop:
                continue
            for _r in (_a, _b):
                if id(_r) not in _cache:
                    _cache[id(_r)] = _shingles(_wordset(_r))
            _sa, _sb = _cache[id(_a)], _cache[id(_b)]
            if not _sa or not _sb:
                continue
            if len(_sa & _sb) / len(_sa | _sb) > 0.75:
                _drop.add(id(_a if _a["words"] < _b["words"] else _b))
if _drop:
    records = [r for r in records if id(r) not in _drop]

# Distinct letters can prettify to the same title (e.g. four different
# "976 Numbers" letters). Disambiguate so the index never *looks* duplicated.
_bytitle = collections.defaultdict(list)
for r in records:
    _bytitle[r["title"].lower()].append(r)
for _t, _group in _bytitle.items():
    if len(_group) < 2:
        continue
    for r in _group:
        if r["date"]:
            r["title"] += f" ({r['date']})"
        else:
            _hint = os.path.dirname(r["path"]).split("/")[-1] or "root"
            _stem = os.path.splitext(os.path.basename(r["path"]))[0]
            r["title"] += f" ({_hint}/{_stem})"

records.sort(key=lambda r: (r["date"] or "9999", r["title"].lower()))
json.dump(records, open(os.path.join(ROOT, "letters.json"), "w"), indent=1)

# ---- 2. render the index --------------------------------------------------
by_year = collections.defaultdict(list)
for r in records:
    by_year[r["year"] or "Undated"].append(r)
years = sorted((y for y in by_year if y != "Undated")) + (["Undated"] if "Undated" in by_year else [])
total_w = sum(r["words"] for r in records)

rows = []
for y in years:
    items = sorted(by_year[y], key=lambda r: (r["date"] or "9999", r["title"].lower()))
    rows.append(f'<h2 id="y{y}">{y} <span class="c">{len(items)}</span></h2><ul>')
    for r in items:
        d = f'<span class="d">{r["date"]}</span>' if r["date"] else '<span class="d nd">—</span>'
        b = ' <span class="tag">Boron</span>' if r["boron"] else ''
        rows.append(
            f'<li>{d}<a href="site/{urllib.parse.quote(r["path"])}">{html.escape(r["title"])}</a>'
            f'{b}<span class="w">{r["words"]:,}w</span></li>')
    rows.append("</ul>")

nav = " · ".join(f'<a href="#y{y}">{y}</a>' for y in years)
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Gary Halbert Letter — Local Archive</title><style>
:root{{--bg:#f4f1ea;--fg:#1c1a17;--mut:#6b6459;--line:#ddd6c8;--acc:#8c2f16}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--fg);font:16px/1.55 Georgia,"Times New Roman",serif;
margin:0;padding:2.5rem 1.25rem 5rem}}
.wrap{{max-width:60rem;margin:0 auto}}
h1{{font-size:1.9rem;margin:0 0 .25rem;letter-spacing:-.01em}}
.sub{{color:var(--mut);margin:0 0 1.5rem;font-size:.95rem}}
.nav{{border-top:1px solid var(--line);border-bottom:1px solid var(--line);
padding:.7rem 0;margin-bottom:2rem;font-size:.85rem;color:var(--mut);line-height:2}}
.nav a{{color:var(--acc);text-decoration:none}}.nav a:hover{{text-decoration:underline}}
h2{{font-size:1.15rem;margin:2.2rem 0 .5rem;padding-bottom:.3rem;
border-bottom:1px solid var(--line)}}
h2 .c{{color:var(--mut);font-size:.8rem;font-weight:400}}
ul{{list-style:none;margin:0;padding:0}}
li{{display:flex;align-items:baseline;gap:.7rem;padding:.28rem 0;
border-bottom:1px dotted var(--line)}}
li a{{color:var(--fg);text-decoration:none;flex:1}}
li a:hover{{color:var(--acc);text-decoration:underline}}
.d{{color:var(--mut);font:400 .78rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;
min-width:5.6rem;flex:none}}
.d.nd{{opacity:.45}}
.w{{color:var(--mut);font-size:.75rem;flex:none;font-variant-numeric:tabular-nums}}
.tag{{background:#e6dfd0;color:var(--mut);font-size:.65rem;padding:.1rem .4rem;
border-radius:3px;flex:none;letter-spacing:.03em}}
.note{{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);
color:var(--mut);font-size:.8rem}}
@media(max-width:620px){{.d{{min-width:0}}.w{{display:none}}}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#171614;--fg:#e8e3d8;
--mut:#948c7e;--line:#332f28;--acc:#e0714c}}.tag{{background:#2a261f}}}}
</style></head><body><div class="wrap">
<h1>The Gary Halbert Letter</h1>
<p class="sub">Local mirror · {len(records)} letters · {total_w:,} words · served from disk</p>
<div class="nav">{nav}</div>
{''.join(rows)}
<p class="note">Personal offline copy of publicly-readable pages, kept in the
site's original markup. Not for redistribution.</p>
</div></body></html>"""
open(os.path.join(ROOT, "index.html"), "w").write(page)
print(f"index.html — {len(records)} letters, {total_w:,} words, {len(years)} groups")
