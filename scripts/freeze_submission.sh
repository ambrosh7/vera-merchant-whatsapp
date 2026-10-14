#!/usr/bin/env bash
# Regenerate and freeze submission.jsonl (Phase E).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export COMPOSER_FORCE_DETERMINISTIC=1
python3 -m bot.compose_offline --dataset dataset/expanded --out submission.jsonl
python3 -m bot.compose_offline --dataset dataset/expanded --out /tmp/submission_check.jsonl
if ! cmp -s submission.jsonl /tmp/submission_check.jsonl; then
  echo "ERROR: non-deterministic compose output" >&2
  exit 1
fi
echo "Frozen submission.jsonl (30 lines) @ COMPOSER_PROMPT_VERSION=${COMPOSER_PROMPT_VERSION:-composer_v1}"
