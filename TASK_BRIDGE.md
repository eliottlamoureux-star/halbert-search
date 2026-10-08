# Task: write the `asks` bridge for a slice of letters

You are closing the last measured failure in a private search engine over Gary Halbert's
letters. A user types a plain-English business problem; the engine names the letter that
answers it.

## Why this task exists — read this, it determines whether you succeed

Retrieval is at 77.8%. Every remaining failure has the SAME cause, and it is not what you
would guess. **The briefs are not missing content.** Measured: for all 16 failures, the
correct letter ranks #1 when you search using its own brief's wording. The content is there.

What fails is the **translation**. Example, verbatim from the evaluation:

```
USER TYPED : "my campaign worked at 100 emails and died at 1000"
RIGHT LETTER: Newsletters/azkh_starving_crowd.htm
ITS BRIEF ALREADY SAYS: "My small test of a new list did great but the full rollout
                         completely tanked"
```

Same problem. **Zero shared words.** `campaign/emails/100/1000` vs `test/list/rollout/tanked`.
The engine matches words, so it never connects them.

Your job is to write the missing half of that bridge: the way **the user** says it.

## What NOT to do — an earlier attempt at this failed badly

A previous pass added 12-18 *new problem topics* per letter. Recall fell from 81.1% to 69.8%,
and it fell monotonically as more was added. Cause: every brief came to claim every topic, so
no brief was distinctive any more. Brief length went 218 -> 480 words and the number of terms
appearing in over a quarter of all briefs went 17 -> 41.

**So: you are NOT adding topics. You are RESTATING topics the letter already covers, in the
user's words.** If you find yourself writing about something the letter does not actually
teach, stop — that is the failure mode that lost 11 points.

## Input

1. Dump your slice: `python3 -m halbert.slice START END /tmp/bridge_NN.txt`
2. Read each letter in your slice **in full**.
3. Read its existing brief:
   `python3 -c "import json;d=json.load(open('briefs.json'));print(json.dumps(d['THE/PATH'],indent=1))"`

## What to write

For each letter, **6 to 10 `asks`** — search queries, in the user's register, that this letter
genuinely answers.

### Who the user is
A solo operator running a small design/marketing studio in Québec. Cold outreach to local
business owners (property managers, contractors, small service firms). Writes his own copy in
French and English, builds his own offers, buys or scrapes his own lists. No team, no budget.
He searches when he is stuck on a specific piece of work, late at night.

### The rules that matter

1. **Every ask must restate something the letter ACTUALLY teaches.** Trace each one to a
   specific passage or to an existing `problems`/`teaches` entry. No new topics. Ever.

2. **Write it in 2026 words, including modern channel words** where the underlying problem is
   genuinely the same. The letter says "mail a test of 5,000 pieces then roll out" — the user
   types "my campaign worked small and died when i scaled it". Use `campaign`, `email`,
   `landing page`, `dm`, `ads`, `subscribers`, `clients` when the mechanism transfers. This is
   the entire point of the task: those words are the bridge.
   **But do not claim a modern mechanic the letter does not cover.** A letter about mailing
   lists can bridge to "my email list"; it cannot bridge to "my facebook ad account got banned".

3. **Be specific to THIS letter.** Test every ask: *would this be equally true of 20 other
   letters in a direct-marketing archive?* If yes, delete it. "my marketing isn't working" is
   worthless. "the client keeps adding people to the decision and it never closes" is useful.
   Each ask should carry at least two words tied to this letter's actual mechanism.

4. **Lowercase, 6-18 words, first person, the way he types.** Symptoms, not topics. Some
   blunt: "nobody's replying". Some how-do-I. Some frustrated.

5. **Vary the vocabulary ACROSS the 6-10 asks.** They are bridges to different phrasings, so
   near-duplicates waste a slot. If two asks share most of their words, replace one.

6. **Do not use Halbert's jargon.** No "A-pile", no "starving crowd", no "unique selling
   proposition". Those words are already in the letter text — repeating them adds nothing. Your
   value is entirely in the words that are NOT already there.

7. **A thin letter gets fewer asks.** Short admin notes, pitches and asides may only support
   2-4 honest asks. Write fewer rather than padding. Padding is the failure mode above.

## Output

Write `bridge_parts/part_NN.json` — a JSON object keyed by the exact letter path:

```json
{
  "Newsletters/azkh_starving_crowd.htm": [
    "my campaign worked small and died when i scaled it",
    "how do i pick which list to test first",
    "i think my list broker is giving me their best names then swapping them",
    "how do i tell if a list is worth paying for before i spend",
    "my own past clients vs a bought list, which converts better"
  ],
  "Newsletters/next_one.htm": ["..."]
}
```

Cover **every** letter in your slice. Use the exact paths from the slice dump.

## Before you submit — verify, do not assume

1. Re-read rule 1: does every single ask trace to something the letter actually teaches?
2. Re-read rule 3: delete every ask that would be true of 20 other letters.
3. Count: 6-10 per teaching letter, 2-4 for thin ones. Never more than 10.
4. Confirm your JSON parses and every key is an exact path from your slice.

Do **NOT** spawn subagents. Do the reading yourself. A previous run delegated and returned
before its children finished, reporting success with no output file.
