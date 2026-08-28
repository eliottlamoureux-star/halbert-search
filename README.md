# The Gary Halbert Letter — local archive

Offline mirror of the publicly-readable letters at thegaryhalbertletter.com,
kept in the site's original markup so each letter looks exactly as it does live.

## Run it

    ./serve.sh            # http://localhost:8848
    ./serve.sh 9000       # or pick a port

`index.html` is the navigation page; `site/` is the untouched mirror.

## What's here

| | |
|---|---|
| Letters | 413 indexed, 346 after full dedup |
| Words | ~875,000 |
| Newsletters & other | 269 |
| Halbertisms (`/HOTD/`) | 66 |
| Boron Letters | 48 (chapters 1–25, incl. the 2.0 rewrites) |
| `/new/b/` letters | 27 |

## How it was built

1. `scrape.py` — fetches every candidate path, live site first, Wayback
   (`id_` raw mode, no toolbar injection) as fallback. The directory tree is
   mirrored exactly, so relative `../images/…` links resolve with **zero HTML
   rewriting** — the markup on disk is byte-identical to the origin.
2. `retry.py` — retries failures across path spellings (case variants, the
   `Newletter-archives-protected` prefix, filenames with stray spaces).
3. `round2.py` / `round3.py` — discovery sweeps beyond the first candidate list
   (see below).
4. `build_index.py` — regenerates `index.html` + `letters.json` from whatever is
   on disk. Safe to re-run any time.

## How coverage was widened

The first pass only looked under `/newsletters/` and `/boron/` and found 370.
A review pass found letters living outside both. Three further sources:

- **Broad CDX** — re-queried Wayback with no `statuscode:200` filter and no
  directory restriction, catching root-level letters and redirect-only captures.
- **The site's original archive index** — recovered at
  `/Newletter-archives-protected/newsletter-archives.htm`; it links letters the
  current landing page dropped.
- **Internal link crawl** — parsed every downloaded letter for links to siblings.

That surfaced the unlinked `/new/b/` directory, the `/HOTD/` Halbertisms, and
`sleazypitch` / `Gary Girlfriend In Motion`, all previously listed as lost.

## Deduplication

Four stages, because each catches what the last misses:

1. exact byte hash
2. normalized-text hash (markup stripped, whitespace/case collapsed)
3. opening-600-word shingle
4. **fuzzy pass** — among records sharing a date or title, collapse pairs whose
   8-word shingle sets overlap >75%, keeping the longer text

Stage 4 exists because copies of one letter can differ in nav markup just enough
to defeat all three hashes — four such pairs scored 89–99% similar. Verified
result: **0 duplicate groups, 0 broken links.**

## Known gaps

- **2 letters genuinely lost**: `hopkinshalbert`, `clayton_makepeace_vsl_snippet`.
  (`976-Numbers-Update` is held under other paths.)
- **112 inline image refs** dead on the origin server too (the earlier figure of 49 undercounted).
- **Titles**: letters carry no headline in the body (masthead → "From:" →
  location → salutation → copy), so titles come from the site's own index labels
  where available, else a cleaned-up filename slug. Titles that would collide are
  disambiguated by date or path.
- **Dates**: only where the letter states one or the path encodes one (**181 of 413**).

## Two bugs found and fixed during the review

- `retry.py` deleted any page under 2048 bytes **and** 120 words even when the
  stub regex did *not* match, and `try_all()` then refused to re-accept anything
  under 1500 bytes — so a genuinely short letter was deleted permanently. Now it
  purges only on a positive stub match, logs what it purged to `purged.txt`, and
  accepts short re-fetches.
- `build_index.py`'s 120-word floor discarded 54 of 66 Halbertisms (they run
  34–400 words). The floor is now content-aware: a positive content marker
  overrides it.

Personal offline copy for study. Not for redistribution.


## Search

This archive is searchable. See `STRUCTURE.md` for the design, `BUILD.md` for build state,
`MEASUREMENTS.md` for every number and how it was measured.

    ./ask.py --dry "my outreach letters aren't getting replies"

or, in Claude Code, `/halbert <your problem>` — which retrieves, reads the letters, and
answers with a verbatim quote. Measured recall@20: **92.5%**.
