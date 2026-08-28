"""Deterministic modern -> Halbert-era term expansion. No model, no API, no cost.

`cold email` appears in 0 of 413 letters. `funnel` in 1. So a question typed in 2026
vocabulary has nothing to match on, and BM25 over the raw question returns noise. This
module is the cheap half of the bridge: a hand-built map, applied by string match.

Every target term below was checked against the corpus -- `verify()` fails the build if
any of them has a document frequency of zero, because a term that appears nowhere adds
nothing but noise to the query.
"""

import os
import re

# Multi-word first: longest phrases are matched before their component words, so
# "cold email" does not get shredded into "cold" + "email".
PHRASES = [
    ("cold email", "sales letter direct mail envelope prospect"),
    ("cold outreach", "sales letter direct mail mailing prospect names"),
    ("cold call", "telephone prospect pitch"),
    ("cold list", "list names mailing prospect"),
    ("email list", "list names subscribers mailing"),
    ("mailing list", "list names mailing"),
    ("open rate", "opened envelope response"),
    ("click through", "response reply coupon"),
    ("click rate", "response reply"),
    ("reply rate", "response rate pull reply"),
    ("response rate", "response rate pull nixies"),
    ("conversion rate", "response rate pull sales"),
    ("landing page", "sales letter offer order coupon"),
    ("sales page", "sales letter offer order"),
    ("squeeze page", "coupon free report offer"),
    ("lead magnet", "free report free recorded message coupon offer"),
    ("lead gen", "inquiry coupon prospect list"),
    ("follow up", "follow up second notice telephone letter"),
    ("social proof", "testimonials endorsement proof"),
    ("case study", "testimonials proof results"),
    ("target audience", "list market prospects buyers"),
    ("ideal customer", "list market buyers prospects"),
    ("target market", "market list starving crowd buyers"),
    ("product market fit", "market starving crowd demand buyers"),
    ("split test", "split run test mailing control"),
    ("a b test", "split run test mailing control"),
    ("ab test", "split run test mailing control"),
    ("scale up", "roll out rollout mailing quantity"),
    ("scaling up", "roll out rollout mailing quantity"),
    ("price point", "price unit of sale offer"),
    ("value proposition", "offer benefit promise"),
    ("call to action", "order coupon act now respond"),
    ("subject line", "headline envelope teaser opening"),
    ("email deliverability", "delivered post office mail opened"),
    ("spam folder", "thrown away discarded opened"),
    ("bounce rate", "nixies returned bad address"),
    ("churn rate", "repeat buyers back end renewal"),
    ("customer retention", "repeat buyers back end customers"),
    ("upsell", "back end additional order"),
    ("sales funnel", "front end back end offer order"),
    ("ad copy", "copy advertisement headline"),
    ("ad spend", "advertising cost media budget"),
    ("cost per lead", "cost per inquiry advertising"),
    ("free trial", "free examination guarantee trial"),
    ("money back", "guarantee refund risk"),
    ("brand awareness", "image reputation recognition"),
    ("web traffic", "inquiries responses visitors"),
    ("search engine", "advertising directory listing"),
]

WORDS = {
    "email": "letter mail sales letter",
    "emails": "letters mail mailing",
    "outreach": "direct mail sales letter prospect",
    "dm": "direct mail letter",
    "inbox": "mailbox envelope mail",
    "spam": "junk thrown away discarded",
    "prospect": "prospect inquiry name list",
    "prospects": "prospects inquiries names list",
    "lead": "inquiry prospect name",
    "leads": "inquiries prospects names",
    "funnel": "front end back end offer",
    "conversion": "response sales order",
    "converts": "pulls sells responds",
    "copy": "copy letter advertisement",
    "copywriting": "copy writing advertisement",
    "headline": "headline attention opening",
    "hook": "grabber headline attention",
    "angle": "appeal approach idea",
    "offer": "offer deal proposition price",
    "pricing": "price unit of sale",
    "guarantee": "guarantee refund risk",
    "testimonial": "testimonials endorsement proof",
    "audience": "market list readers buyers",
    "niche": "market field specialty",
    "targeting": "list selection market",
    "segment": "list selection names",
    "list": "list names mailing",
    "testing": "test split run control",
    "metrics": "results figures numbers",
    "analytics": "results records figures",
    "roi": "profit return cost",
    "crm": "records customer file",
    "seo": "advertising listing directory",
    "ads": "advertisement advertising space",
    "advert": "advertisement advertising",
    "campaign": "mailing promotion advertising",
    "newsletter": "newsletter issue letter",
    "webinar": "seminar presentation",
    "subscribe": "subscription order",
    "unsubscribe": "remove name cancel",
    "engagement": "response interest attention",
    "retention": "repeat buyers renewal",
    "referral": "referral recommendation friend",
    "objection": "objection excuse doubt",
    "credibility": "believability proof reputation",
    "urgency": "deadline act now limited",
    "scarcity": "limited supply deadline",
    "onboarding": "welcome first order new customer",
    "client": "client customer account",
    "clients": "clients customers accounts",
    "closing": "close order sale",
    "pitch": "pitch presentation offer",
    "deck": "presentation material",
    "brand": "image reputation name",
    "website": "advertisement sales letter",
    "page": "letter advertisement",
    "traffic": "inquiries responses",
    "opened": "opened envelope read",
    "ignored": "thrown away discarded no response",
    "ignoring": "thrown away discarded",
    "replies": "response reply answer",
    "reply": "response reply answer",
    "respond": "respond response order",
    "buy": "buy order purchase",
    "buying": "buying ordering purchase",
    "sell": "sell sale order",
    "selling": "selling sales order",
    "expensive": "price expensive cost",
    "cheap": "cheap price inexpensive",
    "market": "market list buyers demand",
}

# Dropped before matching: too common in the corpus to discriminate.
NOISE = set("""a an the my your our their his her its i me we you they it this that these
those is are was were be been being am do does did doing have has had having will would
shall should can could may might must of in on at by for with from to into onto out up
down over under about as if then than so but or and not no nor too very just only own
same how what when where which who whom why get getting got keep keeps keeping make makes
making go goes going come comes any some more most much many few need needs want wants
try trying seem seems look looks feel feels think thinks know knows tell tells say says
aren isn doesn don won can didn hasn haven wasn weren shouldn wouldn couldn ain
ive youre theyre thats whats dont cant wont im ill""".split())


# Learned mappings from the tuning loop live in a separate file, never in this
# source, so a bad round is reverted by deleting one file.
_EXTRA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "vocab_extra.txt")
if os.path.exists(_EXTRA):
    with open(_EXTRA, encoding="utf-8") as _fh:
        for _line in _fh:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "->" not in _line:
                continue
            _src, _dst = _line.split("->", 1)
            _src, _dst = _src.strip().lower(), _dst.strip().lower()
            if " " in _src:
                PHRASES.append((_src, _dst))
            elif _src in WORDS:
                WORDS[_src] = WORDS[_src] + " " + _dst
            else:
                WORDS[_src] = _dst


def _clean(q):
    return re.sub(r"[^a-z0-9 ]", " ", q.lower())


def expand(question, keep_original=True):
    """Question -> search terms. Deterministic, instant, free."""
    text = _clean(question)
    out, consumed = [], text

    for phrase, repl in sorted(PHRASES, key=lambda p: -len(p[0])):
        if phrase in consumed:
            out.extend(repl.split())
            consumed = consumed.replace(phrase, " ")

    for w in consumed.split():
        if w in NOISE or len(w) < 3:
            continue
        if w in WORDS:
            out.extend(WORDS[w].split())
        elif keep_original:
            out.append(w)

    seen, terms = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            terms.append(t)
    return terms


def verify(docs):
    """Every mapped target must exist in the corpus. A df-0 term is pure noise."""
    vocab = set()
    for d in docs:
        vocab.update(re.findall(r"[a-z]+", d["text"].lower()))
    missing = set()
    for _, repl in PHRASES:
        missing |= {t for t in repl.split() if t not in vocab}
    for repl in WORDS.values():
        missing |= {t for t in repl.split() if t not in vocab}
    return sorted(missing)


if __name__ == "__main__":
    from . import corpus
    docs, _ = corpus.load()
    missing = verify(docs)
    print("mapped targets absent from the corpus: %d %s"
          % (len(missing), missing if missing else ""))
    for q in ("my cold outreach letters are not getting replies",
              "my cold emails are not getting opened",
              "how do I find a market before I write anything",
              "what makes a guarantee actually work"):
        print("\n%s\n  -> %s" % (q, ", ".join(expand(q))))
