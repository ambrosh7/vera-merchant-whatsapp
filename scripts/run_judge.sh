#!/usr/bin/env bash
# Run judge_simulator against BOT_URL using .env Groq credentials.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || true

export BOT_URL="${BOT_URL:-http://127.0.0.1:8080}"
export TEST_SCENARIO="${1:-all}"
export LLM_PROVIDER="${LLM_PROVIDER:-groq}"
export LLM_MODEL="${LLM_MODEL:-openai/gpt-oss-120b}"

echo "Judge scenario=$TEST_SCENARIO bot=$BOT_URL provider=$LLM_PROVIDER model=$LLM_MODEL"
exec python3 judge_simulator.py
