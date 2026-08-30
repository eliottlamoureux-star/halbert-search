# What the 16 held-out failures actually are

Hand-classified 2026-08-30 by reading each question against its keyed letter's brief.
This exists because my first diagnosis — "all 16 are translation gaps" — was wrong. I had
generalised from two clean examples. The real split decides what the `asks` bridge can and
cannot deliver, and therefore whether 92% is reachable at all.

Baseline: 56/72 = 77.8% recall@20 on `answer_key.holdout.json`.

## TRANSLATION — the brief covers the facet, in different words (10)

The bridge (`asks`) targets exactly these.

| question | keyed letter | the brief already says |
|---|---|---|
| my campaign worked at 100 emails and died at 1000 | azkh_starving_crowd | "My small test of a new list did great but the full rollout completely tanked" |
| nobody opens my emails, is it the subject line or the list | azkh_starving_crowd | list choice by recency/frequency/spend |
| i hate cold calling, is there a way around it | Gary-Halbert-Personal-Ad | "My cold outreach feels awkward and confrontational" |
| how do i price a website project without pulling a number out of nowhere | zskl_price_is_relative | "I don't know what price to charge and I'm basically guessing" |
| how do i add extras without making the whole thing look cheap | zszd_didn't_masturbate | "make my bonuses feel more valuable" |
| how do i know property managers actually need what i sell | Boron/TChapter5 | demand from purchase behaviour, not surveys |
| how do i check an offer with twenty conversations before building it | zakj_lesser_brethren | market understanding comes from customer contact |
| how do i scale something that's working without breaking it | Boron/TChapter22 | the 7-step test-then-roll-out sequence |
| my instagram posts get likes and zero clients | zjll_most_valuable_skill | "looks great but visitors don't stick around" |
| should i take all the risk myself just to get the first yes | 5 letters | risk reversal / guarantees |

Shared shape: **zero content-word overlap, total semantic overlap.** BM25 cannot cross it.

## COVERAGE — the brief genuinely omits the facet (1)

| question | keyed letter | why |
|---|---|---|
| how do i track which version a lead actually came from | zglk_post_office | brief covers response rates and mail fraud; keying/coding responses is not in it |

Only a rewrite of that brief fixes this. The bridge cannot, and should not be asked to —
inventing an `ask` for a facet the brief does not carry is the enrichment failure again.

## BAD KEY — the letter does not answer the question (5)

These are not engine failures. They are judge errors in the answer key, and they mean the
true 77.8% is a *floor*, not a point estimate.

| question | keyed letter | why it is wrong |
|---|---|---|
| what do i do with a client who wants to design it himself | Boron/TChapter7 | TChapter7 is recency/frequency/unit-of-sale list selection. Unrelated. |
| how do i position myself when cheaper options are everywhere | 2011/hiringcopywriters | letter is about *hiring* a cheap copywriter — the buyer's side, inverted from the question |
| prospects say the price is fine and then never sign | Boron/TChapter8 | a profit model plus "trust behaviour over stated preference"; adjacent at best |
| my cold emails never get a reply, not even a no | seminar.htm | a *pitch*, "you cannot multiply by zero" — real but very loose |
| the decision keeps stalling because they keep adding more people | asza_another_issue | targeting affluent decisive buyers ≠ committee decision-making |

## What this implies for the 92% target

If the bridge converts all 10 translation cases: 66/72 = **91.7%**. That is the ceiling of
this approach on this key, and it lands almost exactly on the target — which means there is
no slack. Anything less than ~10/10 misses.

Two rules follow, and they matter more than the number:

1. **Do not hand-fix the 5 bad key entries on this set.** Correcting the ruler to make the
   engine look better is the pooling bias again, in a more embarrassing form. They stay.
2. **The fresh test set (`questions_test.json`, 164 questions) is where the honest number
   comes from.** Its key is built stricter, and the dev set above is now a tuning set. Any
   number quoted from the dev set after this point is a tuned number and must be labelled so.
