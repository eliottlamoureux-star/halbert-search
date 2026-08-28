# Corpus measurements

Every number in `STRUCTURE.md`, and how it was measured. Independently reproduced by more than
one pass except where noted. Measured 2026-08-28 against `letters.json` + `site/`.

## Size and shape

| | |
|---|---|
| Records in `letters.json` | **413** (README says 410 — README is stale) |
| Words | 876,372 (`letters.json` field) / 877,504 by correct extraction |
| Tokens, stripped text | ~1.22M — **exceeds a 1M context window** |
| Length | min 34 · p25 449 · median 1,572 · p75 3,137 · p95 5,978 · max 14,651 |
| Letters > 1,500w | 214 · **> 6,000w: 21** |
| Sub-collections | 228 Newsletters · 66 HOTD (34–400w) · 48 Boron · 27 `new/b` |
| Dated | 181/413 — **232 NULL**. 108 of the 181 fall in one 24-month window (2004–05) |
| Titles that are filename slugs | 96 |

## The vocabulary cliff

Document frequency across 413 letters — the reason plain search fails:

```
cold email 0 · autoresponder 0 · funnel 1 · landing page 1 · facebook 2
open rate 4 · SEO 8 · conversion rate 8
```

BM25 over raw text: ~43% hit rate on 7 plausible questions. `"nobody opens my cold emails"`
returns a seminar ad.

**The rewrite result** (reproduced exactly, twice):

```
"my cold outreach letters are not getting replies"     -> aakh_improve_response.htm  #51
"response rate direct mail nixies test list envelope"  -> aakh_improve_response.htm  #1
```

Absolute BM25 scores vary by implementation (27.4/23.7 vs 17.6/11.5 in two passes); the rank
move is what reproduces.

## Defects

| Defect | Measurement |
|---|---|
| Near-duplicates | **53 removable** (42 groups, 95 letters involved) at 8-gram containment > 0.90. README's "0 duplicate groups" is **false** |
| Dedup threshold | Jaccard is the wrong measure — `TChapter1`↔`BoronLetterCh1` is J=0.395 but containment=0.983. Use containment |
| Non-letter pages in the item set | ~38 (`index.html`, `index3.html`, `Signup.html`, `Become-An-Affiliate.htm`, archive pages, `Boron Template.htm`, `bullet test.htm`) |
| Not valid UTF-8 | 345/481 files (71%). 349 declare windows-1252 |
| C1-byte letters | **57** — `latin-1` renders these as invisible controls (`driver\x92s`); `cp1252` gives `driver's` |
| gzip streams named `.htm` | 2 — `zkkk_killer_headlines.htm` (598w indexed → **2,766 real**), `2005/07-13-05.htm` (152w → **1,622**). Both have intact twins already in the corpus |
| Boilerplate share | 22% of tokens in letters < 200w · 0.9% in letters > 3,000w · worst 43% |
| Multi-author | 64 of 273 letters > 800w reference another author. **Of the 6 letters > 8,000w, zero are clean Gary teaching letters.** Largest (14,651w) is reader condolences; 2nd (12,391w) is Scott Haines |
| Boron 2.0 | Written by **Bond** Halbert; chapter numbers do **not** correspond to Boron 1.0. Not rewrites |
| Drafts/templates indexed as letters | `DRAFT 11-21-05 Version 2.htm`, `Boron Template.htm`, `bullet test.htm` |
| Split letter | `f04/{4,5,6,7}.html` are contiguous fragments of `zaza_interesting_facts.htm` at word offsets 1101/1629/1940/2321 |
| Dead image refs | 112 of 1,255 (README says 49). 75 letters are mostly-image with < 250w of text |
| Truncated | 83 letters end mid-sentence after footer removal |

## Structure signals

| | |
|---|---|
| `<a name=>` anchors | **33/413** · `id=` on a content block: **8** → paragraph deep-linking is not possible |
| Bold elements per letter | median 7 · mean 18 · **max 228** |
| Letters > 1,500w with 3+ plausible subheads | 150–154 of 214 (~71%) |
| Inversion at the top | `rememberinggary.htm` 14,651w → **2** bold · `shortcutcopycourse.htm` 12,391w → **228** |
| First bold line as title | fails — 84 letters have no bold; 15 lead with "Click Here To View Our Newsletter Archive"; **61 of 96** slug letters get junk |
| Cross-references to other letters | 62–74 depending on phrase set (an earlier pass said 33 — that understated) |
| Link graph | 1,496 internal links, but 4 nav strings account for 823 (55%). Editorial residue ~50–100. **No usable authority signal** |

## Hazards to gate at output

- `aakh_improve_response.htm` — item #12 is a 1990s phone number, item #21 invites you to mail
  Gary your control package. He died in 2007.
- `a_yellow_pages.htm` — model advertorial invents a chiropractic technique claiming 375% pain
  reduction. Halbert says outright he fabricated it.
- `976_Numbers.htm` — roughly a third is a directory of 1987 adult chat lines.
- 138/413 letters contain a phone number (116 distinct).
- The corpus's core play — cold mail to rented lists — is unlawful in its email form in Canada
  without consent (CASL). Relevant if you lift tactics into live outreach.

## Known-stale claims in `README.md`

"0 duplicate groups" (53 removable) · "410 letters" (413) · "163 dated" (181) · "49 dead image
refs" (112) · "48 Boron chapters" (the 48 `Boron/` records include `976_Numbers.htm` and
`Boron Template.htm`; and Boron 1.0 ch. 2 lives at `Newsletters/BoronLetterCh2.htm` with
`boron: false`).

## Search quality (2026-08-28)

Measured on 315 corpus-blind questions with an independently-judged answer key
(159 answerable, 156 with no answer in the archive).

| stage | recall |
|---|---|
| letter-text BM25 only | 54.8% @8 |
| + brief index fused | 70.4% @8 |
| + `b=0.35` letter length normalisation | 72.2% @8 |
| + demote pitch/aside/admin/memorial | 80.0% @12 |
| + fuse raw question with expanded | **92.5% @20** |

Depth curve at the final setting: @5 61% · @8 72% · @12 81% · @20 **92.5%** · @30 95%.

By category: offer 100% · copy 95% · client 93% · market 93% · outreach 93% ·
modern 91% · testing 82%.

Remaining failures: QUERY_BAD 3 (1.9%), BRIEF_BAD 9 (5.7%).
