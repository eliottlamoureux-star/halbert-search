#!/usr/bin/env bash
# Serve the local Halbert archive. Usage: ./serve.sh [port]
set -euo pipefail
PORT="${1:-8848}"
cd "$(dirname "$0")"
echo "The Gary Halbert Letter — local archive"
echo "  http://localhost:${PORT}/"
echo "  (ctrl-c to stop)"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
