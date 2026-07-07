#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting Library-Yui dev services..."
echo "API:    http://127.0.0.1:8787/health"
echo "Web:    http://127.0.0.1:5174"
echo "Status: http://127.0.0.1:5175"

(cd "$ROOT/apps/api" && python -m uvicorn main:app --reload --port 8787) &
(cd "$ROOT/apps/web" && npm run dev -- --host 127.0.0.1 --port 5174) &
(cd "$ROOT/apps/status" && npm run dev -- --host 127.0.0.1 --port 5175) &

wait
