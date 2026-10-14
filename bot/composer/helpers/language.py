"""Language preference → prompt / compose instruction."""

from __future__ import annotations

from typing import Any, Optional


def language_instruction(
    merchant: dict[str, Any],
    customer: Optional[dict[str, Any]] = None,
) -> str:
    if customer:
        pref = ((customer.get("identity") or {}).get("language_pref") or "").lower()
        if "hi-en" in pref or pref == "hi-en mix":
            return "Use natural Hindi-English code-mix."
        if pref in ("hi", "hindi"):
            return "Prefer Hindi with light English terms where natural."
        if "te-en" in pref or "te" in pref:
            return "Light Telugu-English mix OK; English base fine."
        if "kn-en" in pref or "kn" in pref:
            return "Light Kannada-English mix OK; English base fine."
        if "english" in pref or pref == "en":
            return "Write in clear English."
        if pref:
            return f"Honor language_pref={pref}."
    langs = (merchant.get("identity") or {}).get("languages") or []
    if "hi" in langs:
        return "Hindi-English code-mix is welcome."
    return "Default to clear English; match merchant languages when obvious."


def prefers_hi_mix(customer: Optional[dict[str, Any]]) -> bool:
    if not customer:
        return False
    pref = ((customer.get("identity") or {}).get("language_pref") or "").lower()
    return "hi" in pref or "mix" in pref
