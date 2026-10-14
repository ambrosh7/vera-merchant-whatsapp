#!/usr/bin/env bash
# Regenerate submission.jsonl using live LLM (Groq), with pacing for TPM/RPM.
# Falls back to deterministic per-pair if rate-limited. Writes frozen snapshot.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate 2>/dev/null || true

export COMPOSER_FORCE_DETERMINISTIC=0
export PYTHONUNBUFFERED=1

python3 - <<'PY'
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from bot.composer.composer import compose
from bot.composer.rate_limit import get_rate_limiter

root = Path("dataset/expanded")
pairs = json.loads((root / "test_pairs.json").read_text())["pairs"]
categories = {p.stem: json.loads(p.read_text()) for p in (root / "categories").glob("*.json")}
merchants = {
    json.loads(p.read_text())["merchant_id"]: json.loads(p.read_text())
    for p in (root / "merchants").glob("*.json")
}
customers = {
    json.loads(p.read_text())["customer_id"]: json.loads(p.read_text())
    for p in (root / "customers").glob("*.json")
}
triggers = {
    json.loads(p.read_text())["id"]: json.loads(p.read_text())
    for p in (root / "triggers").glob("*.json")
}

out = Path("submission.jsonl")
llm_n = det_n = 0
lines = []

for i, pair in enumerate(pairs, 1):
    # Pace for ~8k TPM / 30 RPM with headroom
    snap = get_rate_limiter().snapshot()
    tpm_left = snap["tpm_limit"] - snap["tpm_used"]
    if tpm_left < 2500 or snap["rpm_used"] >= snap["rpm_limit"] - 1:
        wait = 25
        print(f"[{i:02d}] cooling {wait}s (tpm_left={tpm_left}, rpm={snap['rpm_used']})", flush=True)
        time.sleep(wait)

    trg = triggers[pair["trigger_id"]]
    mer = merchants[pair["merchant_id"]]
    cat = categories[mer["category_slug"]]
    cust = customers.get(pair["customer_id"]) if pair.get("customer_id") else None
    result = compose(cat, mer, trg, cust)
    src = "llm" if "/llm]" in (result.get("rationale") or "") or result.get("rationale", "").endswith("/llm]") else (
        "llm" if "[composer_v1/llm]" in (result.get("rationale") or "") else "deterministic"
    )
    if "llm]" in (result.get("rationale") or ""):
        llm_n += 1
        src = "llm"
    else:
        det_n += 1
        src = "deterministic"

    line = {
        "test_id": pair["test_id"],
        "body": result["body"],
        "cta": result["cta"],
        "send_as": result["send_as"],
        "suppression_key": result["suppression_key"],
        "rationale": result["rationale"],
    }
    lines.append(line)
    print(f"[{i:02d}/{len(pairs)}] {pair['test_id']} via {src} | {result['body'][:72]}...", flush=True)
    time.sleep(2.5)

out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n", encoding="utf-8")
print(f"Wrote {len(lines)} lines → {out.resolve()}")
print(f"LLM={llm_n} deterministic_fallback={det_n}")
PY
