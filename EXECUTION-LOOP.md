# The self-tuning loop

Tests the search engine without anyone hand-writing questions, and — when it fails — says
*why*, which is the part that makes it fixable.

**No API key.** Every model call is a Claude Code subagent. Cost is the subscription,
not per-token.

## Why it is built this way

The obvious design — summarize each letter, write questions from the summary, check that the
question finds its letter — **cannot measure anything.** A question written from a summary
inherits the letter's vocabulary, so retrieval succeeds on words the real user would never
type. It hands the test its own answer.

So the two jobs are split, and the split is the whole point:

| role | sees | produces |
|---|---|---|
| **writer** | only *who the user is and what the tool is for* — never a letter, never a brief | 315 questions |
| **judge** | the corpus | which letters actually answer each question |

The writer cannot leak vocabulary it was never shown. The judge builds the key independently
of the question. Generation and judgment being separate roles is what makes the result valid.

### Blindness is audited, not trusted

The writer agent reported it never opened the archive. That claim was verified independently:

```
0 questions share 3+ rare corpus words with any letter   (315 questions)
5 questions share 2+                                     (1.6%, all chance)
```

The 5 are ordinary English colliding by accident — `frozen`(df 9), `maker`(9), `bundle`(7),
`batch`, `performed`. A genuine leak looks different: a question written while reading
`aakh_improve_response.htm` surfaces `nixies`(5) **and** `lettershop`(10) together. The
threshold of 3 is calibrated on that contrast, not guessed.

## The answer key

Candidates are pooled from **four routes** — letter-BM25 and brief-BM25, each with the raw
question and the thesaurus-expanded one. The union matters: if one route defined the pool it
would also define the ceiling, and the evaluation could never see what that route misses.
Judging agents shortlist from the candidates' briefs, then verify against full letter text.

**A question with no answering letter is a valid result**, not a failure. Those are the only
real test of the `NOTHING HERE` path — and they exist only because the writer was blind
enough to ask about CRMs and attribution, which Halbert never wrote about. Target: 15–45%.

## What a failure means

| verdict | what happened | fix |
|---|---|---|
| `HIT` | a key letter came back in the top 8 | — |
| `QUERY_BAD` | the letter's **brief** matched but its **text** did not | the rewrite emits terms absent from the corpus → extend `thesaurus.py` |
| `BRIEF_BAD` | neither matched | the brief does not describe what the letter covers → regenerate that brief |
| `NOANSWER` | the key found nothing | scored separately; tests whether the engine declines instead of guessing |

That split is why the loop can improve itself. "Recall is 61%" tells you nothing about what to
change. "61%, and 80% of misses are QUERY_BAD" says touch the thesaurus and leave briefs alone.

## The review gate

Each round proposes one fix, and **a reviewer sees the evidence and the proposal before
anything is written.** It rejects diagnoses that confuse correlation with cause, fixes aimed at
a symptom rather than the dominant failure, and vocabulary that does not actually occur in the
excerpts shown. A rejected round changes nothing and records why.

This exists because an unreviewed tuning loop will optimize the wrong thing for hours and
report progress the whole time.

## Stopping

`recall@8 ≥ 85%`, or two consecutive rounds with no gain, or six rounds — whichever is first.
Thesaurus additions append to `vocab_extra.txt`, never to source, so a bad round is reverted
by deleting one file.

## Tests

`./test_loop.py` — 21 checks, every model call mocked: leak calibration, writer blindness,
pooled key construction, three-way attribution, the review gate including rejection, and the
stop conditions. `./test_offline.py` — 29 checks on the engine itself.

Both write only to temp paths. An earlier run left 28 mock questions in
`questions_generated.json` and `check.py` scored them as real — tests now cannot touch a live
artifact.
