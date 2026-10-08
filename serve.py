#!/usr/bin/env python3
"""Serve the archive with a search bar, on the same port the mirror already used.

    ./serve.py            http://localhost:8848
    ./serve.py 9000       pick a port

Routes:
    /                     the search page
    /api/search?q=...     JSON results
    /api/suggest?q=...    JSON question suggestions (the ask catalogue)
    /index.html           the original chronological index
    /site/...             the untouched mirror

Search calls halbert/retrieve.py -- the same code the CLI and the /halbert skill use.
Nothing here reimplements retrieval, so the page cannot drift from the measured number.

The suggestion route exists because keywords do not work well on this corpus, and that is
not fixable by scoring. Typing `guarantee` returns the letters that say the word most
often -- a compliance rant and a male-enhancement sales letter -- while the letter that
actually teaches risk reversal ranks 14th. The archive is organised by problem, not by
topic, so the page turns a keyword into a menu of real questions instead.

Indexes are built once at startup (~2s) and reused.
"""

import json
import os
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from halbert import bm25, corpus, retrieve, suggest, thesaurus   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R = None
S = None

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Gary Halbert Letter — Search</title><style>
:root{--bg:#f4f1ea;--fg:#1c1a17;--mut:#6b6459;--line:#ddd6c8;--acc:#8c2f16;--hit:#f0e6cf;
--card:#fffdf8}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:16px/1.55 Georgia,"Times New Roman",serif;
margin:0;padding:2.5rem 1.25rem 5rem}
.wrap{max-width:52rem;margin:0 auto}
h1{font-size:1.7rem;margin:0 0 .2rem;letter-spacing:-.01em}
.sub{color:var(--mut);margin:0 0 1.6rem;font-size:.9rem}
.sub a{color:var(--acc)}
form{display:flex;gap:.5rem;margin-bottom:.6rem}
.field{flex:1;position:relative}
input[type=search]{width:100%;font:inherit;padding:.7rem .85rem;border:1px solid var(--line);
background:var(--card);color:var(--fg);border-radius:3px}
input[type=search]:focus{outline:2px solid var(--acc);outline-offset:-1px}
button{font:inherit;padding:.7rem 1.2rem;border:0;background:var(--acc);color:#fff;
border-radius:3px;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
#sug{position:absolute;left:0;right:0;top:calc(100% + 3px);background:var(--card);
border:1px solid var(--line);border-radius:3px;z-index:20;display:none;
box-shadow:0 6px 22px rgba(28,26,23,.13);max-height:22rem;overflow-y:auto}
#sug.on{display:block}
#sug .h{font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);
padding:.5rem .8rem .3rem;border-bottom:1px solid var(--line)}
#sug ul{margin:0;padding:0}
#sug li{list-style:none;padding:.5rem .8rem;cursor:pointer;font-size:.93rem}
#sug li small{display:block;color:var(--mut);font-size:.72rem;margin-top:.1rem}
#sug li:hover,#sug li.sel{background:var(--hit)}
.terms{color:var(--mut);font-size:.78rem;margin:0 0 1.8rem;min-height:1.2em}
.terms b{color:var(--fg);font-weight:400;background:var(--hit);padding:.05rem .25rem}
.ex{color:var(--mut);font-size:.82rem;margin:-.2rem 0 1.8rem}
.ex a{color:var(--acc);text-decoration:none;border-bottom:1px dotted var(--line)}
.r{border-top:1px solid var(--line);padding:.95rem 0}
.r:last-child{border-bottom:1px solid var(--line)}
.r h2{font-size:1.02rem;margin:0 0 .2rem;font-weight:400}
.r h2 a{color:var(--fg);text-decoration:none}
.r h2 a:hover{color:var(--acc);text-decoration:underline}
.r .meta{color:var(--mut);font-size:.75rem;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.r .subj{color:var(--mut);font-size:.87rem;margin:.25rem 0 0}
.r .ask{font-size:.83rem;margin:.35rem 0 0;color:var(--fg);border-left:2px solid var(--acc);
padding-left:.55rem}
.r .ask span{color:var(--mut)}
.tag{background:#e6dfd0;color:var(--mut);font-size:.63rem;padding:.08rem .38rem;
border-radius:3px;letter-spacing:.03em;text-transform:uppercase}
.none{color:var(--mut);padding:2rem 0;text-align:center}
.rank{color:var(--mut);font-size:.72rem;font-family:ui-monospace,Menlo,monospace;min-width:1.6rem;
display:inline-block}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);
color:var(--mut);font-size:.76rem}
</style></head><body><div class="wrap">
<h1>The Gary Halbert Letter</h1>
<p class="sub">__N__ letters · __A__ questions they answer · <a href="/index.html">browse by date</a></p>
<form id="f" autocomplete="off"><div class="field">
<input type="search" id="q" name="q" autofocus autocomplete="off"
 placeholder="describe the problem — or type a word and pick a question"
 aria-label="Search" role="combobox" aria-expanded="false" aria-controls="sug">
<div id="sug" role="listbox"></div></div><button id="go">Search</button></form>
<p class="terms" id="terms"></p>
<p class="ex">Try:
<a href="#" data-q="my outreach letters aren&#39;t getting replies">outreach getting ignored</a> ·
<a href="#" data-q="how do i find a market that actually wants this">finding a market</a> ·
<a href="#" data-q="prospects say my price is too high">price objections</a> ·
<a href="#" data-q="guarantee">the word &ldquo;guarantee&rdquo;</a></p>
<div id="out"></div>
<footer>Searches the letters, a structured summary of each, and __A__ questions written
from them — in his vocabulary and yours. Keywords work, but this archive is organised by
problem, so typing a word and picking a question gets a much better answer. The right
letter is in the results roughly 4 times in 5, and is the top result about 1 time in 3.
Private study copy.</footer>
</div><script>
var out=document.getElementById('out'), terms=document.getElementById('terms'),
    q=document.getElementById('q'), go=document.getElementById('go'),
    sug=document.getElementById('sug'), sel=-1, items=[], t=null;
function esc(s){return (s||'').replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function hide(){sug.className='';sel=-1;items=[];q.setAttribute('aria-expanded','false');}
function draw(list){
  items=list;sel=-1;
  if(!list.length){hide();return;}
  sug.innerHTML='<div class="h">questions these letters answer</div><ul>'+
    list.map(function(s,i){return '<li role="option" data-i="'+i+'">'+esc(s.q)+
      '<small>'+esc(s.subject.slice(0,86))+'</small></li>';}).join('')+'</ul>';
  sug.className='on';q.setAttribute('aria-expanded','true');
  Array.prototype.forEach.call(sug.querySelectorAll('li'),function(li){
    li.addEventListener('mousedown',function(e){e.preventDefault();run(items[+li.dataset.i].q);});});
}
function fetchSug(){
  var v=q.value.trim();
  if(v.length<2){hide();return;}
  fetch('/api/suggest?q='+encodeURIComponent(v)).then(function(r){return r.json();})
   .then(function(d){ if(q.value.trim()===v) draw(d.suggestions||[]); }).catch(hide);
}
function move(d){
  if(!items.length)return;
  sel=(sel+d+items.length+1)%(items.length+1);
  Array.prototype.forEach.call(sug.querySelectorAll('li'),function(li,i){
    li.className=(i===sel)?'sel':'';});
  if(sel>=0&&sel<items.length) q.value=items[sel].q;
}
q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(fetchSug,110);});
q.addEventListener('keydown',function(e){
  if(e.key==='ArrowDown'){e.preventDefault();move(1);}
  else if(e.key==='ArrowUp'){e.preventDefault();move(-1);}
  else if(e.key==='Escape'){hide();}
  else if(e.key==='Enter'&&sel>=0&&sel<items.length){e.preventDefault();run(items[sel].q);}});
q.addEventListener('blur',function(){setTimeout(hide,120);});
function run(text){
  if(!text.trim())return;
  q.value=text; hide(); go.disabled=true;
  out.innerHTML='<p class="none">searching…</p>';
  history.replaceState(null,'','?q='+encodeURIComponent(text));
  fetch('/api/search?q='+encodeURIComponent(text)).then(function(r){return r.json();})
   .then(function(d){
    go.disabled=false;
    terms.innerHTML='searched as: '+d.terms.map(function(x){return '<b>'+esc(x)+'</b>';}).join(' ');
    if(!d.results.length){out.innerHTML='<p class="none">Nothing in the archive matches that.</p>';return;}
    out.innerHTML=d.results.map(function(r,i){
      var tag=r.kind&&r.kind!=='teaching'?' <span class="tag">'+esc(r.kind)+'</span>':'';
      var au=r.author&&r.author.toLowerCase().indexOf('gary')<0?' · '+esc(r.author):'';
      return '<div class="r"><h2><span class="rank">'+(i+1)+'.</span> '+
        '<a href="/site/'+encodeURI(r.path)+'">'+esc(r.title)+'</a>'+tag+'</h2>'+
        '<div class="meta">'+r.words+' words'+(r.date?' · '+esc(r.date):'')+au+'</div>'+
        (r.subject?'<p class="subj">'+esc(r.subject)+'</p>':'')+
        (r.ask?'<p class="ask"><span>answers:</span> '+esc(r.ask)+'</p>':'')+'</div>';
    }).join('');
   }).catch(function(){go.disabled=false;out.innerHTML='<p class="none">search failed</p>';});
}
document.getElementById('f').addEventListener('submit',function(e){e.preventDefault();run(q.value);});
document.querySelectorAll('.ex a').forEach(function(a){
  a.addEventListener('click',function(e){e.preventDefault();run(a.dataset.q);});});
var pre=new URLSearchParams(location.search).get('q'); if(pre) run(pre);
</script></body></html>"""


def best_ask(question, brief):
    """Which of this letter's asks is closest to what was typed.

    Shown under each result so the list explains itself: the reason a letter is here is
    usually a question it answers, not a word it contains.
    """
    asks = (brief or {}).get("asks") or []
    qt = set(bm25.tokenize(question))
    if not asks or not qt:
        return ""
    best, score = "", 0.0
    for a in asks:
        at = set(bm25.tokenize(a))
        if not at:
            continue
        # Overlap normalised by the square root of the union: rewards shared terms
        # without letting a long ask win purely by covering more ground.
        s = len(qt & at) / float(len(qt | at)) ** 0.5
        if s > score:
            best, score = a, s
    return best if score > 0 else ""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        SimpleHTTPRequestHandler.__init__(self, *a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        first = args[0] if args else ""
        if "/api/search" in first:
            sys.stderr.write("  %s\n" % (first,))

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        question = (qs.get("q") or [""])[0].strip()

        if parsed.path == "/api/suggest":
            return self._json({"suggestions": S.suggest(question, top=8) if question else []})

        if parsed.path == "/api/search":
            if not question:
                return self._json({"terms": [], "results": []})
            terms = thesaurus.expand(question)
            results = []
            for doc, score in R.search(question, terms=terms):
                b = R.briefs.get(doc["path"]) or {}
                results.append({
                    "path": doc["path"], "title": doc["title"] or doc["path"],
                    "words": doc["words"], "date": doc.get("date"),
                    "score": round(score, 3), "subject": b.get("subject", ""),
                    "kind": b.get("kind", ""), "author": b.get("author", ""),
                    "ask": best_ask(question, b),
                })
            return self._json({"terms": terms, "results": results})

        if parsed.path in ("/", "/search", "/search/"):
            body = (PAGE.replace("__N__", str(len(R.docs)))
                        .replace("__A__", "{:,}".format(len(S.items)))).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        return SimpleHTTPRequestHandler.do_GET(self)


def main():
    global R, S
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8848
    sys.stderr.write("building index… ")
    sys.stderr.flush()
    docs, _ = corpus.load()
    R = retrieve.Retriever(docs)
    S = suggest.Suggester(R.briefs)
    sys.stderr.write("%d letters, %d questions ready\n" % (len(docs), len(S.items)))

    ThreadingTCPServer.allow_reuse_address = True
    httpd = ThreadingTCPServer(("127.0.0.1", port), Handler)
    sys.stderr.write("http://localhost:%d\n" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        httpd.server_close()


if __name__ == "__main__":
    main()
