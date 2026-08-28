# Execution plan

What to build, in what order, and how you know when to stop. Design rationale is in
`STRUCTURE.md`; every number is sourced in `MEASUREMENTS.md`.

The governing rule: **round one is the whole product until your own failure log says otherwise.**
Everything expensive is gated behind a measurement you have not taken yet.

---

## Step 0 — `questions.txt` · you · 20 minutes · BLOCKING

Write 15–20 questions you'd actually type mid-campaign. Real ones, in your words, not
search-engine phrasing. Ballpark spread:

- 10 diagnostic — *"my outreach letters aren't getting replies"*
- 4 conceptual — *"what makes a good guarantee"*
- 3 locate — *"the letter with the coat-of-arms story"*
- 3 swipe — *"give me P.S. structures that close"*

This is first because it is the only input I cannot generate, and because it becomes the
acceptance test in Step 2 and the escalation trigger in Step 4. Without it, "round one is
failing" is unfalsifiable and you will rebuild on instinct.

---

## Step 1 — `ask.py` · one evening · ~150 lines

```
pip install rank-bm25 anthropic
halbert "my outreach letters aren't getting replies"
```

Five modules, in dependency order:

**`corpus.py`** — walk `site/`, decode **`utf-8` → `cp1252`** (never `latin-1`; 57 letters
break), strip tags, cache to `corpus.pkl`. Exclude by path: `index*.html`, `Copy of *`,
`*Template*`, `*test*`, `Signup*`, `*archives*`, `Become-An-Affiliate*`. ~375 letters survive.

**`index.py`** — BM25 over **stripped** text (raw HTML inflates length 1.9× and degrades top-5).

**`rewrite.py`** — one Claude call, question → 8–15 of his terms, using the vocabulary table in
`STRUCTURE.md`. No sentences. Preserve proper nouns from the question. `claude-sonnet-5` is
plenty here.

**`answer.py`** — read the top 8 letters in full, emit the answer block. `claude-opus-5`,
streamed — this is the only part where quality is worth paying for.

**`ask.py`** — wire it: rewrite → BM25 top 20 → collapse >90% overlap → top 8 → answer.
`--save` appends the quote to `swipe.md`.

Three things that are easy to skip and shouldn't be:

- **Collapse near-duplicates.** 53 of 413 are dupes; one cluster otherwise eats three of your top five.
- **The `NOTHING HERE` path.** Without it the tool bluffs, and you stop trusting the good answers.
- **Titles.** 96 are filename slugs. First-bold-line does *not* work (61 of 96 return junk) —
  let the model name the letter from content it has already read.

**Cost**, measured across all 20 questions in `questions.txt` (reading the top 8 in full —
median 38,693 tokens, max 63,573):

| | median | worst |
|---|---|---|
| `claude-opus-5` (default) | **$0.211** | $0.335 |
| `claude-sonnet-5` | $0.084 | $0.134 |

Switch with `export HALBERT_ANSWER_MODEL=claude-sonnet-5`. Start on Opus — answer quality is
the entire product and $0.21 is not a real constraint at a few queries a day. Drop to Sonnet
only if you're running the batch repeatedly.

**Latency** 30–60s, so the answer streams or it reads as hung.

---

## Step 2 — baseline · 30 minutes

Run all of `questions.txt`. For each, record one line in `results.md`:

```
Q  my outreach letters aren't getting replies
A  aakh_improve_response          HIT
```

`HIT` / `MISS` / `WRONG-HALF` (right letter, answer buried in a 6,000-word letter) /
`NOTHING` (it declined, correctly or not).

**This number is the whole point of Step 0.** Every later decision is measured against it.
My expectation is 60–75% HIT. If you're above 80%, round two is probably never worth building.

---

## Step 3 — two weeks of real use

Use it. Don't improve it. `--save` accumulates `swipe.md`; append any new failing question to
`questions.txt` as you hit it.

Resist the urge to tune the rewrite table on a single bad result — one query is noise, and the
table is the one component where overfitting is invisible.

---

## Step 4 — round two, scoped to your log · only if Step 2/3 warrant it

Three failure modes, three different fixes. **Build only the one your log actually shows.**

| Dominant failure | Fix | Cost |
|---|---|---|
| `MISS` — wrong letter entirely | Extend the vocabulary table; add 2–3 rewrite variants and union the results | 1 hour |
| `WRONG-HALF` — right letter, wrong part | Section indexing: split on own-line bold, 3–12 words, ≥400 words apart | 1 day |
| `NOTHING` — found nothing, but the letter exists | Bridge #2: extract `symptoms[]` per section, add `symptoms_fts` | 1 day + ~$3 |

Schema and query path for all three are in `STRUCTURE.md`. Do not build the SQLite layer until
one of these fires — `corpus.pkl` plus BM25 in memory is sufficient for round one and there is
no migration cost, because extraction re-reads the letters either way.

---

## Deferred until the archive matters as an archive

None of this changes which letter answers your question:

- 2 gzip-corrupted files (`zkkk_killer_headlines.htm`, `2005/07-13-05.htm`) — both already have
  intact twins in the corpus
- 3 orphaned letters, 4 split fragments, `boron: false` on Boron ch. 2
- `author` / `author_spans` — matters for attribution, not retrieval
- The 5 stale claims in `README.md` (see `MEASUREMENTS.md`)
- 112 dead image refs, 83 truncated letters

---

## Not building, and why

**Embeddings / vector store** — both bridges are lexical; the symptom phrasings are already in
your vocabulary, so BM25 matches them directly. **Principle graph with typed edges** — nothing
in the query path would read the edges. **LLM boundary segmentation** — boundaries move on
re-run and break stored offsets; his own bold runs are stable. **NDCG eval harness** —
`questions.txt` plus your eyes is the harness; you will not instrument your own tool.
**Content-safety filtering** — private study copy, one reader; the `CAUTION` line covers the
dead contacts and the fabricated health claim.

---

## Definition of done

Round one is done when you can type a real problem and get the right letter, with a quote worth
keeping, in under a minute — and when it tells you plainly on the questions the archive can't
answer. Everything past that is earned by `results.md`, not chosen up front.
