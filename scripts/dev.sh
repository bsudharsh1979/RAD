#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/services/api"
export COURSE_MATERIALS_DIR="$ROOT/course-materials"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$ROOT/data/academy.db}"
mkdir -p "$ROOT/data"
cd "$ROOT/services/api"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd "$ROOT/apps/web"
npm run dev -- --hostname 0.0.0.0 --port 3000 &
WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null || true' EXIT
echo "API http://localhost:8000  Web http://localhost:3000"
wait
