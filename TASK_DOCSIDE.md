# Task: document-side pooling — which questions does each letter answer?

This closes the last known bias in the evaluation. The existing answer key was built by
showing a judge the *search engine's own top results* for each question. A letter the engine
never surfaced could not be judged relevant, so it silently became "no answer." That makes
the key partly a description of the engine rather than of the archive.

This task runs the other direction: you read the LETTERS and decide which questions they
answer. Nothing you do here depends on what the search engine returned, so it can find
exactly what the engine is blind to.

## Input

- Your slice of letters: `python3 -m halbert.slice START END /tmp/docside_NN.txt`
- All the questions: `holdout_questions_numbered.json` — a JSON array of
  `{"i": 0, "q": "...", "category": "..."}`. Read it once; it is short.

## What to do

Read each letter in your slice **in full**. Then, for that letter, list the `i` values of
every question it **genuinely answers**.

## The standard — this is the whole job

**Be strict. Topical adjacency is NOT an answer.** Would someone with that exact problem,
reading this letter, get real, actionable help? If not, it is not an answer.

**Most letters answer NO questions, and that is the expected result.** There are ~125
questions and 346 letters; a typical letter will answer zero, one, or two. A letter that
"sort of relates" to eight questions is answering none of them — you are being too generous,
and a loose key is worse than no key because it makes a bad engine look good.

Be especially careful with letters that are mostly a sales pitch, a joke, a rant, a memorial,
or site housekeeping. Those usually answer nothing even when they mention the topic.

Do NOT run the search engine. Do NOT look at any existing answer key. Judge only from the
letter text in front of you.

## Output

Write `docside_parts/part_NN.json` — a JSON object keyed by the exact letter path:

```json
{"Boron/TChapter11.htm": [3, 47], "Newsletters/some_joke.htm": []}
```

Every letter in your slice must appear, even with an empty list. Use a python3 heredoc with
`json.dump(d, fh, indent=1, ensure_ascii=False)`.

Verify before replying:
`python3 -c "import json;d=json.load(open('docside_parts/part_NN.json'));print(len(d), sum(len(v) for v in d.values()))"`
First number = your letter count. Second = total judgments (expect roughly 10-40, not 200).

**Do NOT spawn subagents. Do this work yourself.** Write the file BEFORE replying.

Reply with: letters read, total judgments made, and any letter you found genuinely borderline.
