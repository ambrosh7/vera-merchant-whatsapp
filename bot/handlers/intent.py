"""Intent-commit detection — EN + common HI (Phase D)."""

from __future__ import annotations

import re

from bot.handlers.auto_reply import normalize_message

# Explicit commit / execute-now language (not soft interest alone).
_COMMIT_PHRASES = (
    "let's do it",
    "lets do it",
    "ok go ahead",
    "okay go ahead",
    "go ahead",
    "yes send it",
    "yes, send",
    "send it",
    "send the",
    "what's next",
    "whats next",
    "what next",
    "do it",
    "please proceed",
    "please send",
    "haan kar do",
    "han kar do",
    "kar do",
    "bhej do",
    "bhej dena",
    "haan bhej",
    "han bhej",
    "kar dena",
    "ok kar do",
    "confirm",
    "confirmed",
    "yes please send",
    "yes draft",
    "schedule it",
    "go for it",
    "ship it",
    "execute",
    "join magicpin",
    "sign me up",
)

_COMMIT_RE = re.compile(
    r"\b("
    r"let'?s do it|go ahead|what'?s next|send it|"
    r"bhej do|haan kar do|han kar do|kar do|"
    r"confirm(ed)?|proceed|schedule it"
    r")\b",
    re.IGNORECASE,
)


def is_intent_commit(message: str) -> bool:
    lowered = normalize_message(message)
    if not lowered:
        return False
    if any(p in lowered for p in _COMMIT_PHRASES):
        return True
    return bool(_COMMIT_RE.search(lowered))
