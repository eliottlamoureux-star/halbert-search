# Search structure for this archive

Ask a plain-English question about a problem you have. Get told which letter answers it.

## The answer

Halbert's vocabulary and yours don't overlap, so **every design here is a bridge between the
two.** There are two ways to build that bridge, they cost wildly different amounts, and the
cheap one goes first:

1. **Rewrite the question into his vocabulary, then search the raw text.** One model call.
   Works tonight.
2. **Attach modern problem phrasings to each lesson, then search those.** Costs an extraction
   pass over the whole archive. Build it only where (1) is measurably failing.

The answer is always **a letter**, with the passage quoted in full — never a bare passage, and
never a link into the middle of a file (see *Deep links*).

## Why the bridge is the whole problem

```
df across 413 letters:  cold email 0 · autoresponder 0 · funnel 1 · landing page 1
                        open rate 4 · SEO 8 · conversion rate 8
```

Measured on this archive, same index, same corpus — only the question changed:

```
"my cold outreach letters are not getting replies"     -> right letter ranks #51
"response rate direct mail nixies test list envelope"  -> same letter ranks #1
```

That rewrite **is** the bridge.

### The rewrite is the highest-leverage thing in this file

It is one model call and everything depends on it. Give it his actual vocabulary:

| yours | his |
|---|---|
| cold email, outreach, DM | sales letter, direct mail, mailing piece |
| open rate, deliverability | getting it opened, the A-pile, the envelope |
| reply rate, response | response rate, pull, nixies |
| audience, ICP, targeting | the list, the market, a starving crowd |
| landing page, funnel | the offer, the order card, the sales piece |
| hook, angle | the grabber, the headline |
| testing, A/B | split-run, test mailing, rollout |
| lead magnet | free recorded message, free report |
| social proof | testimonials, endorsements |

Instruct it to emit 8–15 terms, no sentences, and to keep any proper nouns from your question.

## Round one — tonight

```
halbert "my outreach letters aren't getting replies"
```

One Python file (`pip install rank-bm25`), no database:

1. Model rewrites your question using the table above.
2. **Strip tags first, then index.** Indexing raw HTML inflates document length ~1.9x and
   measurably degrades the top 5.
3. **Decode `utf-8`, fall back to `cp1252` — never `latin-1`.** 57 letters carry bytes in
   0x80–0x9F; latin-1 turns those into invisible control characters, so you print
   `driver\x92s test` instead of `driver's test`. You are quoting these passages verbatim,
   so this is user-visible, not archive hygiene.
4. BM25, top 20. Drop `index.html`, `index3.html`, `Copy of index.html` — they are in
   `letters.json` as letters.
5. Collapse results with >90% text overlap. ~53 of 413 letters are near-duplicates; without
   this, one cluster eats three of your top five.
6. Model reads the **top 8** full letters (~10k tokens typical, ~80k worst case).
7. Print the block below. `--save` appends the quote to `swipe.md`.

**Titles: don't take the first bold line.** It fails on exactly the letters that need it —
84 letters have no bold at all, 15 lead with *"Click Here To View Our Newsletter Archive"*,
and **61 of the 96 slug-titled letters get junk** (nav chrome, `&nbsp;`, `From:`, drop-cap
fragments like `'A'`). Instead: take the first bold run that is on its own line, is 3–12 words,
sits *after* the salutation, and isn't on a nav denylist — and if none qualifies, let the model
name the letter from its content at answer time. It has already read it.

## What an answer looks like

```
$ halbert "my outreach letters aren't getting replies"

THE LETTER
  20 Ways To Increase Response · 3,047w · Gary Halbert
  open http://localhost:8848/site/Newsletters/aakh_improve_response.htm

WHY
  It's 21 numbered fixes for exactly this, and none of them touch your copy.

HE SAYS
  "Last month I promised you that this month I was going to reveal unto you
   20-ways to increase the response of your direct mail without changing a
   word of your copy. I am now about to keep that promise."

ALSO
  Boron Ch. 11 — the root cause: your envelope is landing in the B-pile
  HOTD/45 — one paragraph, same point

CAUTION
  Items #12 and #21 give a dead phone number and invite you to mail Gary
  your control package. He died in 2007.
```

And the case that earns trust:

```
NOTHING HERE
  The archive has no useful coverage of this. Closest is <letter>, and it's
  a stretch. Halbert didn't write about CRMs.
```

Without that path it hands you a mediocre letter every time and you stop believing it.

## "Some correlate, some don't"

Both halves are answers, and the second is the more useful one.

- **Correlated** → the `ALSO` block. Same lesson, other letters, ranked.
- **Not correlated** → *"only one letter in the archive covers this."* A **feature, not low
  confidence.** A lesson taught exactly once is the one you'd never stumble onto by browsing.
- **Sequenced** → **62–74 letters explicitly reference another** ("as I promised you last
  week," "part two," "continued"). Boron especially: Ch. 11's payoff is in Ch. 12. The phrases
  are backward-looking, so detect and store `previous`, and print `NEXT` by inverting the edge.

## Deep links: don't

Only **33 of 413** letters have `<a name=>` anchors; 8 have `id=` on a content block.
Paragraph-level linking would require rewriting the mirror, and this archive's README promises
the opposite: *"zero HTML rewriting — byte-identical to the origin."* So quote the passage
verbatim and link to the letter. Quote long enough that the anchor isn't missed.

## The escalation trigger

Round two is justified only when round one measurably fails, so **write 15–20 real questions
down first** — the ones you'd actually type mid-campaign — and keep them in `questions.txt`.
Without them "measurably failing" is unmeasurable and you'll rebuild on vibes.

## Round two — only what round one proves you need

Round one's weakness is long letters: right letter, wrong half. 21 letters run past 6,000 words.

**Section boundaries: bold alone is emphasis, not structure.** Median letter has 7 bold
elements, mean 18, max 228 — and it inverts exactly where you need it. `rememberinggary.htm`
(14,651w) has **2**; `shortcutcopycourse.htm` (12,391w) has **228**, which would yield ~54-word
fragments. Treat a bold run as a boundary only if it is on its own line, 3–12 words, and
**≥400 words since the last boundary**. Paragraph windows for the letters that still yield none.

```sql
CREATE TABLE letters  (id, path, title, author, date, series, seq, previous, text);
CREATE TABLE sections (id, letter_id, heading, start_ch, end_ch, text);
CREATE TABLE cards    (section_id PRIMARY KEY, kind, principle);
CREATE TABLE symptoms (section_id, text);   -- bridge #2: 10-15 per section, in YOUR words
CREATE TABLE quotables(section_id, text);   -- feeds the HE SAYS block

CREATE VIRTUAL TABLE symptoms_fts USING fts5(text, content='symptoms', content_rowid='rowid');
CREATE VIRTUAL TABLE letters_fts  USING fts5(text, content='letters',  content_rowid='id');
-- external-content tables index nothing until you populate them:
INSERT INTO symptoms_fts(symptoms_fts) VALUES('rebuild');
INSERT INTO letters_fts(letters_fts)   VALUES('rebuild');
```

Query path: question → rewrite → BM25 over `symptoms_fts` **and** `letters_fts` → union top 12
sections → drop `kind IN ('pitch','aside','admin')` → max 2 sections per letter → collapse to
3–5 letters → read in full → the answer block.

`cards.principle` drives `ALSO` (group size > 1) and the rare-lesson flag (group size = 1).
`date` is NULL for 232 letters — **never rank on it.** `series` is the subdirectory; `seq` is
reliable only for Boron and HOTD, which are the only numbered runs.

## Cleanup, when it earns its place

Three repairs are in round one because you see them: correct decoding, duplicate collapse,
title handling. Everything else is archive hygiene — the 2 gzip-corrupted files have intact
twins already in the corpus, and the 3 orphaned letters and 4 fragments are 9 documents out of
413. Fix them when the archive matters to you as an archive, not as a precondition for
searching it.

## Deliberately not building

Embeddings or a vector store — both bridges are lexical. A principle graph with typed edges —
nothing in the query path would read them. LLM boundary segmentation — the boundaries move on
re-run and break stored offsets. An NDCG eval harness — `questions.txt` and your own eyes are
the harness. Content-safety filters — this is a private study copy with one reader; the
`CAUTION` line handles the dead contacts.

---
Numbers here are verified against the corpus: `MEASUREMENTS.md`.
