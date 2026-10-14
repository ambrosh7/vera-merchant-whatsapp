"""Map trigger.kind → prompt variant filename."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

KIND_TO_PROMPT = {
    "research_digest": "research_digest.md",
    "regulation_change": "research_digest.md",
    "cde_opportunity": "research_digest.md",
    "recall_due": "recall_due.md",
    "appointment_tomorrow": "recall_due.md",
    "perf_dip": "performance.md",
    "perf_spike": "performance.md",
    "seasonal_perf_dip": "performance.md",
    "festival_upcoming": "events.md",
    "ipl_match_today": "events.md",
    "curious_ask_due": "engagement.md",
    "review_theme_emerged": "engagement.md",
    "renewal_due": "commercial.md",
    "winback_eligible": "commercial.md",
    "customer_lapsed_soft": "customer_lifecycle.md",
    "customer_lapsed_hard": "customer_lifecycle.md",
    "chronic_refill_due": "customer_lifecycle.md",
    "wedding_package_followup": "customer_lifecycle.md",
    "trial_followup": "customer_lifecycle.md",
    "active_planning_intent": "planning.md",
    "supply_alert": "supply_alert.md",
    "competitor_opened": "supply_alert.md",
    "gbp_unverified": "supply_alert.md",
    "dormant_with_vera": "supply_alert.md",
    "category_seasonal": "supply_alert.md",
    "milestone_reached": "supply_alert.md",
}


def prompt_files_for_kind(kind: str) -> list[Path]:
    files = [PROMPTS_DIR / "base.md"]
    name = KIND_TO_PROMPT.get(kind or "", "default.md")
    variant = PROMPTS_DIR / name
    if not variant.exists():
        variant = PROMPTS_DIR / "default.md"
    files.append(variant)
    return [p for p in files if p.exists()]


def load_prompt_text(kind: str) -> str:
    parts = [path.read_text(encoding="utf-8") for path in prompt_files_for_kind(kind)]
    return "\n\n".join(parts).strip()
