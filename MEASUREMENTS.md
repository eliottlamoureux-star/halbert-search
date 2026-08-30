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

## Search quality (2026-08-30)

**Headline: recall@20 = 77.8% (56/72), Wilson 95% CI 66.9-85.8.** Share of *answerable*
held-out questions where at least one letter the key marks correct appears in the 20 shown.

Read this before quoting it. It is an **upper bound**, for three measured reasons:

| what a user would call it | value | n |
|---|---|---|
| top-1 correct | **23.6%** | 17/72 |
| top-5 contains a right letter | **55.6%** | 40/72 |
| top-20 contains a right letter | **77.8%** | 56/72 |
| per-answer recall@20 (each gold letter counted separately) | **50.2%** | 114/227 |

- **Pooling bias was diluted, not removed.** 55% of the key's 227 answers still sit inside
  the engine's own candidate pool. Split by pool visibility: questions with >=1 gold answer
  in the pool score **90.3%** (56/62); questions with none score **0.0%** (0/10). The engine
  finds almost nothing its own pooling routes did not already surface.
- **The key is annotator-noise-limited.** The two judging routes (engine-pool judges vs
  document-side readers) agree at **Cohen kappa = 0.34** over 3,236 co-judged pairs.
  The key is a union of two noisy samples, not a ground truth.
- **NOANSWER labels are contaminated.** 53 of 125 questions are labelled unanswerable and
  are *dropped from the denominator*, so a mislabel converts a retrieval failure into a free
  pass. Hand-probing 11 of them found answering letters in the archive for **11 of 11**.
  Folding those back in puts the defensible band at **64-74%**.

Sensitivity to that last point:

| mislabelled NOANSWER | n | recall@20 |
|---|---|---|
| 0 (as claimed) | 72 | 77.8% [66.9-85.8] |
| 11 (probed) | 83 | 73.5% [63.1-81.8] |
| 39 (all non-`modern`) | 111 | 66.7% [57.5-74.7] |

**Nothing here measures the product.** Every number is retrieval-only: does a right letter
appear in the candidate list. Whether the answer layer then names the right one and quotes it
accurately has never been measured.

### Recall depends on how many letters answer the question

1-answer questions **56.7%** (n=30) · 2-3 answers 90.5% · 4-6 90.9% · 7+ 100%. The aggregate
is flattered by broad questions. Hardest half (1-3 answers, n=51): **70.6%**.

### How it got here (TUNED set, 315 questions — history, not current performance)

These are the stage-by-stage gains measured on the same 315 questions that ~70 configurations
were selected against. They are **superseded** by the held-out numbers above; they are kept
because they record which change bought what.

| stage | recall (tuned) |
|---|---|
| letter-text BM25 only | 54.8% @8 |
| + brief index fused | 70.4% @8 |
| + `b=0.35` letter length normalisation | 72.2% @8 |
| + demote pitch/aside/admin/memorial | 80.0% @12 |
| + complete answer key | 81.1% @12 |
| + fuse raw question with expanded | 92.5% @20 (tuned) |
| + true min-max fusion normalisation | 93.1% @20 (tuned) |

Depth on the tuned set: @5 64.8% · @12 81.1% · @20 93.1% · @30 95.0%.
Held out, the same depths are @5 55.6% · @12 68.1% · @20 77.8% · @30 83.3%.

### Known measurement defects, unfixed

- **n=72 cannot resolve a 1-3 point tuning decision.** ~70 configurations were selected on
  differences that size. Exact McNemar on min-max vs z-score normalisation: p=0.688 at k=20.
  On held-out data z-score actually scores higher (80.6% vs 77.8%); the shipped choice is
  min-max because it was chosen on the tuned set. Neither is significant.
- **The held-out set paraphrases the tuning set.** Same writer prompt, same 7 categories:
  18 pairs at Jaccard >= 0.6, 55 of 126 at >= 0.4. Measured effect on score: none detectable
  (near-dups 76.5% vs non-near-dups 78.2%), but the sets are not independent.
- **6.6% of gold answers are letters the engine deliberately demotes** (15 of 227 are
  `kind: pitch`, x0.40). `DEMOTE` was tuned against a key whose judge saw only engine-pool
  candidates, so it was tuned partly to suppress letters an independent reader calls answers.
- **The abstain threshold in SKILL.md never fires.** Minimum top-1 fused score over all 125
  held-out questions is 1.12, above the documented ~1.0 cutoff. Abstain AUC is 0.583; the best
  single threshold reaches 60.8% accuracy against a 57.6% always-answer baseline.
