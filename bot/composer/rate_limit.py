"""
Sliding-window limiter for Groq / LLM quotas.

Defaults match openai/gpt-oss-120b free-tier style caps:
  30 RPM · 1K RPD · 8K TPM · 200K TPD

Uses headroom so we fail soft (deterministic fallback) before hard 429s.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, Optional, Tuple

from bot import config

logger = logging.getLogger(__name__)


class RateLimitExceeded(RuntimeError):
    """Raised when a call would breach configured LLM budgets."""


@dataclass
class _Event:
    ts: float
    tokens: int


class LLMRateLimiter:
    def __init__(
        self,
        *,
        rpm: Optional[int] = None,
        rpd: Optional[int] = None,
        tpm: Optional[int] = None,
        tpd: Optional[int] = None,
        headroom: Optional[float] = None,
    ) -> None:
        self.rpm = int(rpm if rpm is not None else config.LLM_RPM)
        self.rpd = int(rpd if rpd is not None else config.LLM_RPD)
        self.tpm = int(tpm if tpm is not None else config.LLM_TPM)
        self.tpd = int(tpd if tpd is not None else config.LLM_TPD)
        self.headroom = float(
            headroom if headroom is not None else config.LLM_LIMIT_HEADROOM
        )
        self._minute: Deque[_Event] = deque()
        self._day_key: str = ""
        self._day_requests: int = 0
        self._day_tokens: int = 0
        self._lock = threading.Lock()

    def _effective(self, limit: int) -> int:
        return max(1, int(limit * self.headroom))

    def _prune_minute(self, now: float) -> None:
        cutoff = now - 60.0
        while self._minute and self._minute[0].ts < cutoff:
            self._minute.popleft()

    def _roll_day(self, now: float) -> None:
        key = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")
        if key != self._day_key:
            self._day_key = key
            self._day_requests = 0
            self._day_tokens = 0

    def snapshot(self) -> dict:
        with self._lock:
            now = time.time()
            self._prune_minute(now)
            self._roll_day(now)
            min_tokens = sum(e.tokens for e in self._minute)
            return {
                "rpm_used": len(self._minute),
                "rpm_limit": self._effective(self.rpm),
                "tpm_used": min_tokens,
                "tpm_limit": self._effective(self.tpm),
                "rpd_used": self._day_requests,
                "rpd_limit": self._effective(self.rpd),
                "tpd_used": self._day_tokens,
                "tpd_limit": self._effective(self.tpd),
                "headroom": self.headroom,
            }

    def estimate_tokens(self, system: str, user: str, max_output: int) -> int:
        # Rough chars/4 + small overhead; prefer over-estimate to stay under TPM/TPD.
        inp = (len(system or "") + len(user or "")) // 4 + 24
        return inp + int(max_output)

    def can_call(self, estimated_tokens: int) -> Tuple[bool, str]:
        with self._lock:
            return self._can_call_unlocked(estimated_tokens)

    def _can_call_unlocked(self, estimated_tokens: int) -> Tuple[bool, str]:
        now = time.time()
        self._prune_minute(now)
        self._roll_day(now)
        est = max(1, int(estimated_tokens))

        if len(self._minute) + 1 > self._effective(self.rpm):
            return False, f"rpm {len(self._minute)+1}/{self._effective(self.rpm)}"
        min_tokens = sum(e.tokens for e in self._minute)
        if min_tokens + est > self._effective(self.tpm):
            return False, f"tpm {min_tokens+est}/{self._effective(self.tpm)}"
        if self._day_requests + 1 > self._effective(self.rpd):
            return False, f"rpd {self._day_requests+1}/{self._effective(self.rpd)}"
        if self._day_tokens + est > self._effective(self.tpd):
            return False, f"tpd {self._day_tokens+est}/{self._effective(self.tpd)}"
        return True, "ok"

    def reserve(self, estimated_tokens: int) -> None:
        """Reserve budget before the HTTP call (pessimistic)."""
        with self._lock:
            ok, reason = self._can_call_unlocked(estimated_tokens)
            if not ok:
                raise RateLimitExceeded(f"LLM budget exceeded ({reason})")
            now = time.time()
            est = max(1, int(estimated_tokens))
            self._minute.append(_Event(ts=now, tokens=est))
            self._day_requests += 1
            self._day_tokens += est

    def reconcile(self, estimated_tokens: int, actual_tokens: Optional[int]) -> None:
        """Adjust last reservation to actual usage when provider reports it."""
        if actual_tokens is None:
            return
        with self._lock:
            if not self._minute:
                return
            last = self._minute[-1]
            delta = int(actual_tokens) - int(estimated_tokens)
            if delta == 0:
                return
            last.tokens = max(1, int(actual_tokens))
            self._day_tokens = max(0, self._day_tokens + delta)


_GLOBAL: Optional[LLMRateLimiter] = None
_GLOBAL_LOCK = threading.Lock()


def get_rate_limiter() -> LLMRateLimiter:
    global _GLOBAL
    with _GLOBAL_LOCK:
        if _GLOBAL is None:
            _GLOBAL = LLMRateLimiter()
            logger.info(
                "LLM rate limiter: rpm=%s rpd=%s tpm=%s tpd=%s headroom=%.2f",
                _GLOBAL.rpm,
                _GLOBAL.rpd,
                _GLOBAL.tpm,
                _GLOBAL.tpd,
                _GLOBAL.headroom,
            )
        return _GLOBAL


def reset_rate_limiter_for_tests() -> None:
    global _GLOBAL
    with _GLOBAL_LOCK:
        _GLOBAL = LLMRateLimiter()
