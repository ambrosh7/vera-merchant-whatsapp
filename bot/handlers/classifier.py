"""Rule-first reply classifier (Phase D). LLM optional later — not required."""

from __future__ import annotations

from typing import Literal, Optional

from bot.handlers.auto_reply import (
    is_identical_to_previous,
    looks_like_auto_reply,
    normalize_message,
)
from bot.handlers.intent import is_intent_commit

Label = Literal[
    "empty",
    "auto_reply",
    "opt_out",
    "hostile",
    "intent_commit",
    "off_topic",
    "question",
    "engaged",
]

_OPT_OUT_PHRASES = (
    "stop messaging",
    "stop sending",
    "not interested",
    "unsubscribe",
    "don't message",
    "do not message",
    "dont message",
    "leave me alone",
    "remove me",
    "opt out",
    "opt-out",
    "stop these",
    "stop this",
    "mat bhejo",
    "mat message",
)

# Standalone "stop" / "band karo" handled separately to avoid false positives.
_OPT_OUT_EXACT = frozenset(
    {
        "stop",
        "stop.",
        "stop!",
        "band karo",
        "band karo.",
        "no more",
        "enough",
    }
)

_HOSTILE_PHRASES = (
    "why are you bothering",
    "this is useless",
    "useless",
    "spam",
    "annoying",
    "irritating",
    "shut up",
    "get lost",
    "don't bother",
    "do not bother",
    "waste of time",
    "bakwas",
    "bewakoof",
    "idiot",
    "stupid bot",
    "harassment",
)

_OFF_TOPIC_PHRASES = (
    "gst",
    "tax filing",
    "income tax",
    "itr ",
    "tds ",
    "accounting software",
    "file my taxes",
    "ca for gst",
    "payroll",
    "pf filing",
    "esi filing",
)


def classify(
    message: str,
    *,
    previous_inbound: Optional[str] = None,
) -> Label:
    raw = message or ""
    lowered = normalize_message(raw)
    if not lowered:
        return "empty"

    if looks_like_auto_reply(raw) or is_identical_to_previous(raw, previous_inbound):
        return "auto_reply"

    if lowered in _OPT_OUT_EXACT or any(p in lowered for p in _OPT_OUT_PHRASES):
        return "opt_out"

    if any(p in lowered for p in _HOSTILE_PHRASES):
        return "hostile"

    # Intent before generic engaged so "ok let's do it" flips mode.
    if is_intent_commit(raw):
        return "intent_commit"

    if any(p in lowered for p in _OFF_TOPIC_PHRASES):
        return "off_topic"

    if "?" in raw or lowered.startswith(
        ("what ", "how ", "when ", "where ", "why ", "can you", "could you")
    ):
        return "question"

    return "engaged"
