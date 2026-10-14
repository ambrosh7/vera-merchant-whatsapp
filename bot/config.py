"""Runtime configuration — env-driven (Phase A+)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def _split_members(raw: str) -> list[str]:
    return [m.strip() for m in raw.split(",") if m.strip()]


TEAM_NAME = os.getenv("TEAM_NAME", "Team Alpha")
TEAM_MEMBERS = _split_members(os.getenv("TEAM_MEMBERS", "Ambrosh"))
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "team@example.com")
BOT_VERSION = os.getenv("BOT_VERSION", "1.0.0")
APPROACH = os.getenv(
    "APPROACH",
    "Groq-backed 4-context fact-pack composer; kind-family prompts; "
    "urgency ranking + consent; multi-turn FSM "
    "(auto-reply / intent / hostile); soft tick deadline; "
    "client rate limits (30rpm/8k tpm) with deterministic fallback",
)
SUBMITTED_AT = os.getenv(
    "SUBMITTED_AT",
    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# Groq openai/gpt-oss-120b default caps (override via env if tier changes)
LLM_RPM = int(os.getenv("LLM_RPM", "30"))          # requests / minute
LLM_RPD = int(os.getenv("LLM_RPD", "1000"))        # requests / day
LLM_TPM = int(os.getenv("LLM_TPM", "8000"))        # tokens / minute
LLM_TPD = int(os.getenv("LLM_TPD", "200000"))      # tokens / day
LLM_LIMIT_HEADROOM = float(os.getenv("LLM_LIMIT_HEADROOM", "0.85"))
# gpt-oss needs headroom for JSON; too-low caps cause empty failed_generation
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "900"))
# Skip LLM repair re-prompt when remaining minute budget is tight
LLM_REPAIR_MIN_TPM_REMAINING = int(os.getenv("LLM_REPAIR_MIN_TPM_REMAINING", "2000"))
# Force deterministic compose (offline freeze / CI); skips Groq entirely
COMPOSER_FORCE_DETERMINISTIC = os.getenv(
    "COMPOSER_FORCE_DETERMINISTIC", ""
).strip().lower() in ("1", "true", "yes", "on")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
MAX_TICK_ACTIONS = int(os.getenv("MAX_TICK_ACTIONS", "3"))
TICK_DEADLINE_SECONDS = int(os.getenv("TICK_DEADLINE_SECONDS", "25"))
# Frozen for offline submission determinism (Phase E). Bump only with regen.
COMPOSER_PROMPT_VERSION = os.getenv("COMPOSER_PROMPT_VERSION", "composer_v1")
COMPOSER_PROMPT_FROZEN = True

VALID_SCOPES = frozenset({"category", "merchant", "customer", "trigger"})
