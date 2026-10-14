"""Auto-reply / canned WhatsApp Business reply detection (Phase D)."""

from __future__ import annotations

import re

_AUTO_REPLY_PHRASES = (
    "thank you for contacting",
    "thanks for contacting",
    "our team will respond",
    "we will get back to you",
    "we'll get back to you",
    "we will respond shortly",
    "automated assistant",
    "this is an automated",
    "i am an automated",
    "this is an auto reply",
    "this is an auto-reply",
    "currently unavailable",
    "outside business hours",
    "office hours",
    "team tak pahuncha",
    "team tak pahucha",
    "jaldi reply karenge",
    "hum jald hi",
)

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_message(message: str) -> str:
    return _WHITESPACE_RE.sub(" ", (message or "").strip().lower())


def looks_like_auto_reply(message: str) -> bool:
    lowered = normalize_message(message)
    if not lowered:
        return False
    return any(p in lowered for p in _AUTO_REPLY_PHRASES)


def is_identical_to_previous(message: str, previous: str | None) -> bool:
    if not previous:
        return False
    return normalize_message(message) == normalize_message(previous) and bool(
        normalize_message(message)
    )
