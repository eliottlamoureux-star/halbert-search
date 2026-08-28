# Task: enrich the `problems` list for a slice of letters

You are improving the search index for a private Gary Halbert letter archive. A user types a
plain-English business problem; the engine must return the right letter.

Measured recall is 80%. The remaining failures share one cause: each letter's `problems` list
is too short (3-5 entries) and covers only ONE facet of the letter. Real example — a letter
teaching joint-venture deal structuring has problems all about *"I have no audience to sell
to"*, so the question *"my contracts are too loose and i keep paying for it"* never finds it,
even though the letter answers it directly.

## What to do

1. Dump your slice: `python3 -m halbert.slice START END /tmp/enrich_NN.txt`
2. Read each letter in full.
3. Read the existing brief for context: `python3 -c "import json;d=json.load(open('briefs.json'));print(json.dumps(d['THE/PATH'],indent=1))"`
4. Write **12 to 18** problem phrasings per letter.

## The rules that matter

- **Write the READER'S symptom, in 2026 words.** "my mail gets thrown out before anyone opens
  it" — NOT "the A-pile principle". Never use Halbert's jargon; that is the whole point.
- **Cover EVERY facet the letter touches**, not just its headline lesson. A letter usually
  carries a main lesson, one or two secondary lessons, and several incidental points. Each
  deserves its own phrasing. This is the single biggest fix — thin, single-facet lists are why
  retrieval misses.
- **Vary the surface form.** Mix symptoms ("nobody replies to my second email"), how-do-I
  ("how do i price a retainer"), and blunt frustration ("my landing page is garbage").
- **Vary the vocabulary.** The same facet phrased two ways doubles the chance of a match:
  "my emails don't get opened" and "my subject lines are being ignored".
- **Include the modern analog.** If a letter teaches a postal tactic, phrase the problem in
  the terms someone would use for email, ads, or DMs today — that is how it will be searched.
- Do NOT invent coverage. If the letter genuinely does not address something, leave it out.
  A letter that teaches nothing (a joke, a rant, a memorial, a pure pitch) can have 2-3
  entries or an empty list.

## Output

Write `problems_parts/part_NN.json` — a JSON object keyed by the exact letter path:

```json
{"Boron/TChapter11.htm": ["my mail gets thrown out unopened", "..."]}
```

Use a python3 heredoc with `json.dump(d, fh, indent=1, ensure_ascii=False)`. Do not hand-write JSON.

Verify before replying:
`python3 -c "import json;d=json.load(open('problems_parts/part_NN.json'));print(len(d), sum(len(v) for v in d.values())//max(len(d),1))"`
First number = your letter count. Second = mean phrasings, should be 12+.

**Do NOT spawn subagents. Do this work yourself.** Write the file BEFORE replying, and reply
only after the verification command passes.

Reply with: letter count, mean phrasings per letter.
