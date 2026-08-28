# Task: build the answer key for one pool

Read `key_pools/pool_NN.json` — a JSON array. Each entry has a question and a list of
candidate letters (pre-filtered search results; most are wrong, that is expected).

For each question:

1. **Shortlist** at most 4 candidates whose `subject`/`teaches`/`problems` suggest a real match.
2. **Verify** each by reading the actual letter: `python3 -m halbert.slice --path "<exact path>"`
   Keep it only if the full text really addresses the asker's problem. Keep at most 3, best first.

## The standard

**Be strict. Topical adjacency is NOT an answer.** Would someone with this exact problem,
reading this letter, get real help? If not, it is not an answer.

**Picking nothing is correct and expected.** This archive is direct-response marketing,
1984-2013. It has near-zero coverage of SaaS, subscriptions, CRM, attribution, analytics, SEO,
social platforms, ad-platform mechanics, B2B enterprise sales. Roughly half of all questions
have no answer at all. If nearly every question gets an answer, you are being too generous and
you are corrupting the evaluation this key exists to support. Never stretch to fill a slot.

## Output

Write `key_parts/part_NN.json` — a JSON array, one entry per question, same order as input:

```json
[{"q": "<question verbatim>", "category": "<from input>",
  "answers": ["<exact path>", "..."], "why": "<12 words>"}]
```

`answers` is 0-3 exact `path` strings copied from that question's own candidates. Use a
python3 heredoc with `json.dump(...)`. Do not hand-write JSON.

Verify: `python3 -c "import json;d=json.load(open('key_parts/part_NN.json'));print(len(d))"`
must equal the number of questions in your pool.

**Do NOT spawn subagents. Do this work yourself.** Write the file BEFORE replying.

Reply with: questions judged, how many got zero answers.
