"""Per-turn language detection for reply matching (Phase D)."""

from __future__ import annotations

import re
from typing import Literal, Optional

Lang = Literal["en", "hi", "hi-en"]

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_HI_LATIN = (
    "haan",
    "han",
    "nahi",
    "nahin",
    "bhej",
    "kar do",
    "theek",
    "thik",
    "accha",
    "acha",
    "ji ",
    "yaar",
    "mat ",
    "kyun",
    "kya ",
)


def detect_language(message: str) -> Lang:
    text = message or ""
    has_deva = bool(_DEVANAGARI_RE.search(text))
    lowered = text.lower()
    has_hi_latin = any(t in lowered for t in _HI_LATIN)
    has_ascii_words = bool(re.search(r"[a-zA-Z]{3,}", text))

    if has_deva and has_ascii_words:
        return "hi-en"
    if has_deva:
        return "hi"
    if has_hi_latin and has_ascii_words:
        return "hi-en"
    if has_hi_latin:
        return "hi"
    return "en"


def match_reply_language(
    merchant_message: str,
    prior: Optional[str] = None,
) -> Lang:
    """Prefer latest merchant turn; fall back to prior observed language."""
    if (merchant_message or "").strip():
        return detect_language(merchant_message)
    if prior in ("en", "hi", "hi-en"):
        return prior  # type: ignore[return-value]
    return "en"
