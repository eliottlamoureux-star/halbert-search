# Task: build the answer key for one pool (test set)

Read `key_pools_test/pool_NN.json` — a JSON array. Each entry has a question and a list of
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

## Five ways the last key was wrong — do not repeat these

Every one of these was found by hand-auditing the previous answer key. They are the reason
this file exists. Check your own shortlist against each before you keep anything.

1. **Inverted perspective.** The question asks how to handle X *from the seller's side*; the
   letter covers X *from the buyer's side*. Real example: *"how do i position myself when
   cheaper options are everywhere"* was keyed to a letter about how to *hire* a cheap
   copywriter. Same words, opposite role. **Reject.**

2. **Shared vocabulary, unrelated mechanism.** Real example: *"what do i do with a client who
   wants to design it himself"* was keyed to a chapter on recency/frequency/unit-of-sale list
   selection. The letter never discusses clients or design at all. If you cannot point to the
   specific passage that helps, there isn't one. **Reject.**

3. **Adjacent-but-not-answering.** Real example: *"prospects say the price is fine and then
   never sign"* keyed to a letter containing a profit model and a remark that behaviour beats
   stated preference. Genuinely about pricing, does not address stalling after agreement.
   **Reject.**

4. **A pitch that mentions the topic.** Real example: *"my cold emails never get a reply"* keyed
   to a seminar advertisement whose argument is that weak copy can't be saved by tactics. It is
   selling a seminar, not teaching the fix. Sales letters, event ads, memorials, rants and site
   housekeeping almost always answer nothing even when they name the topic. **Reject.**

5. **Right theme, wrong problem.** Real example: *"the decision keeps stalling because they keep
   adding more people"* keyed to a letter on targeting affluent, decisive buyers. Both concern
   decisiveness; one is about who to mail, the other about committee dynamics. **Reject.**

The test: **name the passage that helps.** If you cannot quote a specific line or section that
someone with that exact problem would act on, it is not an answer. Write nothing rather than
something defensible-sounding.

## Output

Write `key_parts_test/part_NN.json` — a JSON array, one entry per question, same order as input:

```json
[{"q": "<the question, copied exactly>", "category": "<copied>", "answers": ["path/one.htm"]}]
```

`"answers": []` is a valid and common result. Copy the question text **exactly** — it is the
join key, and a reworded question silently drops the row.

Verify before replying:
`python3 -c "import json;d=json.load(open('key_parts_test/part_NN.json'));print(len(d), sum(1 for x in d if x['answers']))"`

**Do NOT spawn subagents. Do this work yourself.** A previous run delegated and returned before
its children finished, reporting success with no output file. Write the file BEFORE replying.

Reply with: questions judged, how many got at least one answer, and any you found genuinely
borderline.
