#!/usr/bin/env bash
# Serve the archive locally. Search runs in the browser (index.html + search.js over
# search-index.json), so a plain static server is all it needs -- the same as GitHub Pages.
#
#   ./serve.sh          http://localhost:8848
#   ./serve.sh 9000     pick a port
cd "$(dirname "$0")" && exec python3 -m http.server --bind 127.0.0.1 "${1:-8848}"
