/* Browser port of halbert/retrieve.py over search-index.json (see build_search.py).
 *
 * Every step mirrors the Python line for line -- thesaurus.expand, bm25.tokenize,
 * BM25.search, Retriever.search -- including iteration order, so ties break the same
 * way. test_static_search.py holds it to the Python ranking; change both together.
 */
(function (root) {
  "use strict";

  function Searcher(ix) {
    this.ix = ix;
    this.stop = new Set(ix.stop);
    this.noise = new Set(ix.thes.noise);
    // sorted(PHRASES, key=-len) -- JS sort is stable, like Python's
    this.phrases = ix.thes.phrases.slice().sort(function (a, b) {
      return b[0].length - a[0].length;
    });
    this.arms = [[prep(ix.aug), ix.fuse.w_aug], [prep(ix.brief), ix.fuse.w_brief]];
  }

  function prep(a) {
    var n = a.len.length, idf = new Map();
    Object.keys(a.post).forEach(function (t) {
      var df = a.post[t].length / 2;
      idf.set(t, Math.log(1.0 + (n - df + 0.5) / (df + 0.5)));
    });
    a.idf = idf;
    return a;
  }

  // thesaurus.expand
  Searcher.prototype.expand = function (question) {
    var text = question.toLowerCase().replace(/[^a-z0-9 ]/g, " ");
    var out = [], consumed = text, self = this;
    this.phrases.forEach(function (p) {
      if (consumed.indexOf(p[0]) >= 0) {
        out.push.apply(out, words(p[1]));
        consumed = consumed.split(p[0]).join(" ");
      }
    });
    words(consumed).forEach(function (w) {
      if (self.noise.has(w) || w.length < 3) return;
      if (Object.prototype.hasOwnProperty.call(self.ix.thes.words, w))
        out.push.apply(out, words(self.ix.thes.words[w]));
      else out.push(w);
    });
    var seen = new Set();
    return out.filter(function (t) { if (seen.has(t)) return false; seen.add(t); return true; });
  };

  function words(s) { return s.split(/\s+/).filter(Boolean); }

  // bm25.tokenize
  Searcher.prototype.tokenize = function (text) {
    var stop = this.stop;
    return (text.toLowerCase().match(/[a-z0-9']+/g) || []).filter(function (w) {
      return !stop.has(w) && w.length > 1;
    });
  };

  // BM25.search -> [[docIndexInArm, score], ...]
  function bm25(a, q, top) {
    var scores = new Map();
    q.forEach(function (t) {
      var idf = a.idf.get(t);
      if (idf === undefined) return;
      var p = a.post[t];
      for (var j = 0; j < p.length; j += 2) {
        var i = p[j], f = p[j + 1];
        var denom = f + a.k1 * (1 - a.b + a.b * a.len[i] / a.avgdl);
        scores.set(i, (scores.get(i) || 0.0) + idf * (f * (a.k1 + 1)) / denom);
      }
    });
    return Array.from(scores).sort(function (x, y) { return y[1] - x[1]; }).slice(0, top);
  }

  // Retriever.search
  Searcher.prototype.search = function (question) {
    var ix = this.ix, terms = this.expand(question), self = this;
    var queries = [terms.join(" "), question], combined = new Map();
    queries.forEach(function (query) {
      var q = self.tokenize(query);
      self.arms.forEach(function (pair) {
        var a = pair[0], weight = pair[1];
        if (!weight) return;
        var hits = bm25(a, q, ix.fuse.pool);
        if (!hits.length) return;
        var hi = hits[0][1], lo = hits[hits.length - 1][1], span = (hi - lo) || 1.0;
        hits.forEach(function (h) {
          var d = a.doc[h[0]];
          combined.set(d, (combined.get(d) || 0.0) + weight * ((h[1] - lo) / span));
        });
      });
    });
    var ranked = Array.from(combined).map(function (kv) {
      var k = ix.docs[kv[0]].k || "teaching";
      var f = Object.prototype.hasOwnProperty.call(ix.fuse.demote, k) ? ix.fuse.demote[k] : 1.0;
      return [kv[0], kv[1] * f];
    }).sort(function (x, y) { return y[1] - x[1]; }).slice(0, ix.fuse.top);
    return {
      terms: terms,
      results: ranked.map(function (r) { return { doc: ix.docs[r[0]], score: r[1] }; })
    };
  };

  if (typeof module === "object" && module.exports) module.exports = Searcher;
  else root.HalbertSearch = Searcher;
})(this);
