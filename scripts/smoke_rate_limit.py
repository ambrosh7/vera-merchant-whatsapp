#!/usr/bin/env python3
"""Unit smoke for LLM rate limiter (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.composer.rate_limit import (  # noqa: E402
    LLMRateLimiter,
    RateLimitExceeded,
    reset_rate_limiter_for_tests,
)


def main() -> int:
    fails = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    # Tiny budgets for the test
    lim = LLMRateLimiter(rpm=10, rpd=50, tpm=700, tpd=5000, headroom=1.0)

    lim.reserve(300)
    lim.reserve(300)
    ok, reason = lim.can_call(300)
    check("tpm blocks third large call", ok is False and "tpm" in reason, reason)

    lim2 = LLMRateLimiter(rpm=2, rpd=100, tpm=50_000, tpd=200_000, headroom=1.0)
    lim2.reserve(10)
    lim2.reserve(10)
    ok2, reason2 = lim2.can_call(10)
    check("rpm blocks third request", ok2 is False and "rpm" in reason2, reason2)

    raised = False
    try:
        lim2.reserve(10)
    except RateLimitExceeded:
        raised = True
    check("reserve raises", raised)

    lim3 = LLMRateLimiter(rpm=10, rpd=2, tpm=50_000, tpd=200_000, headroom=1.0)
    lim3.reserve(10)
    lim3.reserve(10)
    ok3, reason3 = lim3.can_call(10)
    check("rpd blocks", ok3 is False and "rpd" in reason3, reason3)

    lim4 = LLMRateLimiter(rpm=30, rpd=1000, tpm=8000, tpd=500, headroom=1.0)
    lim4.reserve(400)
    ok4, reason4 = lim4.can_call(200)
    check("tpd blocks", ok4 is False and "tpd" in reason4, reason4)

    # Headroom: effective rpm = floor(30*0.85)=25
    lim5 = LLMRateLimiter(rpm=30, rpd=1000, tpm=8000, tpd=200000, headroom=0.85)
    for _ in range(25):
        lim5.reserve(1)
    ok5, reason5 = lim5.can_call(1)
    check("headroom stops before hard rpm", ok5 is False, reason5)

    reset_rate_limiter_for_tests()
    print()
    if fails:
        print(f"Rate-limit smoke FAILED ({fails})")
        return 1
    print("Rate-limit smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
