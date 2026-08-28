"""Dump a contiguous slice of letters as plain text.

Used by the brief-writing agents so each one reads only its own share and never
has to load the whole corpus.

    python3 -m halbert.slice 0 35            -> letters 0..34 to stdout
    python3 -m halbert.slice 0 35 out.txt    -> same, to a file
    python3 -m halbert.slice --paths         -> every path, one per line, indexed
"""

import sys

from . import corpus


def main():
    docs, _ = corpus.load()
    if "--paths" in sys.argv:
        for i, d in enumerate(docs):
            print("%d\t%s\t%d" % (i, d["path"], d["words"]))
        return
    if "--count" in sys.argv:
        print(len(docs))
        return
    if "--path" in sys.argv:
        want = sys.argv[sys.argv.index("--path") + 1]
        for d in docs:
            if d["path"] == want:
                print("path: %s\ntitle: %s\nwords: %d\n" % (d["path"], d["title"], d["words"]))
                print(d["text"])
                return
        print("no such letter: %s" % want, file=sys.stderr)
        sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])
    out = open(sys.argv[3], "w", encoding="utf-8") if len(sys.argv) > 3 else sys.stdout
    for i, d in enumerate(docs[start:end], start):
        out.write("\n\n===== LETTER %d =====\n" % i)
        out.write("path: %s\ntitle: %s\ndate: %s\nwords: %d\n\n"
                  % (d["path"], d["title"], d.get("date") or "unknown", d["words"]))
        out.write(d["text"])
    if out is not sys.stdout:
        out.close()
        print("wrote letters %d..%d" % (start, end - 1), file=sys.stderr)


if __name__ == "__main__":
    main()
