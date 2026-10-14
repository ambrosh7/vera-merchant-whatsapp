#!/usr/bin/env bash
# Local deploy preflight: smokes + optional judge scenarios.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || true

BOT_URL="${BOT_URL:-http://127.0.0.1:8080}"
export BOT_URL

echo "== Phase smokes =="
python3 scripts/smoke_phase_b.py
python3 scripts/smoke_phase_c.py
python3 scripts/smoke_phase_d.py
python3 scripts/smoke_phase_e.py
python3 scripts/smoke_rate_limit.py

echo "== HTTP health =="
curl -fsS "$BOT_URL/v1/healthz" | python3 -m json.tool
curl -fsS "$BOT_URL/v1/metadata" | python3 -m json.tool

if [[ "${RUN_JUDGE:-1}" == "1" ]]; then
  echo "== Judge: all (warmup + replay) =="
  TEST_SCENARIO=all python3 judge_simulator.py
  echo "== Judge: phase2_short (scored compose) =="
  TEST_SCENARIO=phase2_short python3 judge_simulator.py
fi

echo "PREFLIGHT OK — ready to deploy (docker compose up --build / fly deploy)"
