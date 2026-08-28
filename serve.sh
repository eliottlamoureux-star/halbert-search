#!/usr/bin/env bash
# Serve the archive with search. Wraps serve.py, which reuses halbert/retrieve.py
# so the web results match the CLI and the /halbert skill exactly.
#
#   ./serve.sh          http://localhost:8848
#   ./serve.sh 9000     pick a port
exec "$(dirname "$0")/serve.py" "${1:-8848}"
