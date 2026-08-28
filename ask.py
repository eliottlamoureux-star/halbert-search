#!/usr/bin/env python3
"""Ask the Gary Halbert archive a plain-English question.

    ./ask.py "my outreach letters aren't getting replies"
    ./ask.py --dry "..."      retrieval only, no API key needed
    ./ask.py --save "..."     append the quote to swipe.md
    ./ask.py --batch questions.txt > results.md

Design: STRUCTURE.md   Numbers: MEASUREMENTS.md   Plan: EXECUTION.md
"""

import argparse
import os
import re
import sys
import time

from halbert import corpus, llm, retrieve, thesaurus

HERE = os.path.dirname(os.path.abspath(__file__))
READ_TOP = retrieve.TOP_K   # what the answer layer reads; recall@12 79.1% vs @8 72.2%
CAND = 20


def display_title(doc):
    """96 titles in letters.json are filename slugs.

    First-bold-line does NOT work as a fallback -- 84 letters have no bold at all,
    15 lead with nav chrome, and 61 of the 96 slugs return junk. So we surface the
    slug honestly and let the answering model name the letter from content.
    """
    t = (doc["title"] or "").strip()
    if not t or t.isdigit() or re.fullmatch(r"[A-Z][a-z]+[a-z0-9]*", t):
        return os.path.basename(doc["path"]).rsplit(".", 1)[0]
    return t


def get_hits(r, terms, question):
    hits = r.search(question, top=READ_TOP, terms=terms)
    if not hits:
        hits = r.search(question, top=READ_TOP)
    return hits


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("question", nargs="*")
    ap.add_argument("--dry", action="store_true", help="retrieval only, no model calls")
    ap.add_argument("--model-rewrite", action="store_true",
                    help="use a model to rewrite the question instead of the thesaurus")
    ap.add_argument("--save", action="store_true", help="append the quote to swipe.md")
    ap.add_argument("--batch", metavar="FILE", help="run a question file, print results")
    ap.add_argument("--rebuild", action="store_true", help="rebuild corpus.pkl")
    args = ap.parse_args()

    t0 = time.time()
    docs, aliases = corpus.load(force=args.rebuild)
    r = retrieve.Retriever(docs)
    if args.rebuild or args.dry:
        print("# %d letters, %d duplicates collapsed, index in %.1fs"
              % (len(docs), len(aliases), time.time() - t0), file=sys.stderr)

    if args.batch:
        with open(args.batch, encoding="utf-8") as fh:
            qs = [l.strip() for l in fh
                  if l.strip() and not l.lstrip().startswith("#")]
        for q in qs:
            terms = llm.rewrite(q) if args.model_rewrite else thesaurus.expand(q)
            hits = get_hits(r, terms, q)
            print("Q  %s" % q)
            for doc, score in hits[:3]:
                print("A  %-46s %6.2f" % (display_title(doc)[:46], score))
            print("   -> HIT / MISS / WRONG-HALF / NOTHING")
            print()
        return

    question = " ".join(args.question).strip()
    if not question:
        ap.print_help()
        return

    terms = llm.rewrite(question) if args.model_rewrite else thesaurus.expand(question)
    if args.dry:
        print("terms: %s\n" % ", ".join(terms))
    hits = get_hits(r, terms, question)

    if not hits:
        print("NOTHING HERE\n  No letter scored on this question at all.")
        return

    if args.dry:
        # subject line comes from the brief, so 20 candidates can be triaged without
        # opening any of them; read only the few that look right.
        for i, (doc, score) in enumerate(hits, 1):
            b = r.briefs.get(doc["path"]) or {}
            kind = b.get("kind", "")
            print("%2d. %5.2f  %-40s %5dw  %s" %
                  (i, score, display_title(doc)[:40], doc["words"], doc["path"]))
            subj = b.get("subject", "")
            if subj:
                print("           %s%s" % (("[%s] " % kind) if kind != "teaching" else "", subj[:88]))
        return

    text = llm.answer(question, hits)

    if args.save:
        quote = re.search(r'HE SAYS\s*\n\s*"(.+?)"', text, re.S)
        letter = re.search(r"THE LETTER\s*\n\s*(.+)", text)
        if quote:
            with open(os.path.join(HERE, "swipe.md"), "a", encoding="utf-8") as fh:
                fh.write("\n## %s\n_%s_\n\n> %s\n"
                         % (question,
                            letter.group(1).strip() if letter else "",
                            " ".join(quote.group(1).split())))
            print("\n[saved to swipe.md]")


if __name__ == "__main__":
    main()
