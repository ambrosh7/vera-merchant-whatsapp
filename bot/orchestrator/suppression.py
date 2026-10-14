"""Suppression + trigger ranking for /v1/tick (Phase C)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from bot.store.conversation_store import ConversationStore

# Soft priority boosts by kind family (added to urgency*10)
KIND_BONUS: dict[str, int] = {
    "supply_alert": 8,
    "regulation_change": 5,
    "renewal_due": 5,
    "perf_dip": 5,
    "recall_due": 4,
    "appointment_tomorrow": 4,
    "chronic_refill_due": 4,
    "active_planning_intent": 4,
    "ipl_match_today": 3,
    "review_theme_emerged": 3,
    # Prefer digest for warmup/scoring demos when urgency ties are close
    "research_digest": 6,
    "customer_lapsed_hard": 3,
    "customer_lapsed_soft": 2,
    "curious_ask_due": 1,
    "festival_upcoming": 0,
    "dormant_with_vera": 1,
    "seasonal_perf_dip": 1,
    "perf_spike": 1,
}


def parse_expired(expires_at: Optional[str], now: str) -> bool:
    if not expires_at:
        return False
    try:
        exp = expires_at.replace("Z", "+00:00")
        n = now.replace("Z", "+00:00")
        exp_dt = datetime.fromisoformat(exp)
        now_dt = datetime.fromisoformat(n)
        if exp_dt.tzinfo is None and now_dt.tzinfo is not None:
            now_dt = now_dt.replace(tzinfo=None)
        elif now_dt.tzinfo is None and exp_dt.tzinfo is not None:
            exp_dt = exp_dt.replace(tzinfo=None)
        return now_dt >= exp_dt
    except (ValueError, TypeError):
        return False


def rank_score(trigger: dict[str, Any], merchant: dict[str, Any]) -> int:
    urgency = int(trigger.get("urgency") or 1)
    kind = trigger.get("kind") or ""
    score = urgency * 10 + KIND_BONUS.get(kind, 0)
    signals = merchant.get("signals") or []
    if "engaged_in_last_48h" in signals:
        score += 4
    if any(str(s).startswith("dormant_with_vera") for s in signals):
        if kind in ("curious_ask_due", "festival_upcoming"):
            score -= 5
    # Far-away festivals: down-rank
    payload = trigger.get("payload") or {}
    days_until = payload.get("days_until")
    if kind == "festival_upcoming" and isinstance(days_until, (int, float)) and days_until > 60:
        score -= 8
    return score


def merchant_is_blocked(
    merchant_id: str,
    conversations: ConversationStore,
    now: Optional[str] = None,
) -> bool:
    """Skip proactive sends if merchant has exit/suppressed or active wait."""
    for state in conversations._data.values():  # noqa: SLF001 — intentional store scan
        if state.merchant_id != merchant_id:
            continue
        if state.suppressed or state.mode == "exit":
            return True
        if state.wait_until is not None:
            if now:
                try:
                    n = datetime.fromisoformat(now.replace("Z", "+00:00"))
                    wu = state.wait_until
                    if wu.tzinfo is None and n.tzinfo is not None:
                        n = n.replace(tzinfo=None)
                    if n < wu:
                        return True
                except (ValueError, TypeError):
                    return True
            else:
                return True
    return False
