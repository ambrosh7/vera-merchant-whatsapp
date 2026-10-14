"""Post-LLM validation + light repair for composed messages."""

from __future__ import annotations

import re
from typing import Any, Optional

ALLOWED_CTAS = frozenset(
    {
        "open_ended",
        "binary_yes_no",
        "binary_confirm_cancel",
        "multi_choice_slot",
        "none",
        "binary_yes_stop",
    }
)

CTA_ALIASES = {
    "yes_no": "binary_yes_no",
    "binary": "binary_yes_no",
    "confirm": "binary_confirm_cancel",
    "slots": "multi_choice_slot",
    "slot": "multi_choice_slot",
    "open": "open_ended",
}

URL_RE = re.compile(r"https?://|www\.", re.I)


def normalize_cta(cta: Optional[str]) -> str:
    if not cta:
        return "open_ended"
    key = str(cta).strip().lower().replace(" ", "_")
    key = CTA_ALIASES.get(key, key)
    if key in ALLOWED_CTAS:
        return key
    return "open_ended"


def _taboos(category: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    voice = category.get("voice") or {}
    raw = voice.get("vocab_taboo") or voice.get("taboos") or []
    from_facts = (facts.get("category") or {}).get("vocab_taboo") or []
    out = []
    for t in list(raw) + list(from_facts):
        # taboos may include parenthetical notes — take phrase before (
        phrase = str(t).split("(")[0].strip().strip('"').lower()
        if phrase:
            out.append(phrase)
    return out


def scrub_taboos(body: str, taboos: list[str]) -> tuple[str, list[str]]:
    hits = []
    cleaned = body
    for t in taboos:
        if t and t in cleaned.lower():
            hits.append(t)
            # case-insensitive remove
            cleaned = re.sub(re.escape(t), "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned, hits


def validate_composition(
    result: dict[str, Any],
    category: dict[str, Any],
    facts: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    """
    Returns (ok, repaired_result, errors).
    ok=False means skip/re-prompt.
    """
    errors: list[str] = []
    body = (result.get("body") or "").strip()
    rationale = (result.get("rationale") or "").strip()
    cta = normalize_cta(result.get("cta"))

    if not body:
        errors.append("empty_body")
    if not rationale:
        errors.append("empty_rationale")
        rationale = "Composed from allowlisted fact pack."

    if URL_RE.search(body or ""):
        errors.append("url_present")
        body = URL_RE.sub("", body)
        body = re.sub(r"\s{2,}", " ", body).strip()

    taboos = _taboos(category, facts)
    body, hits = scrub_taboos(body, taboos)
    if hits:
        errors.append(f"taboo:{','.join(hits)}")

    # hi-en preference → require Latin mix (not Devanagari-only walls of text)
    lang_pref = ""
    cust = facts.get("customer") or {}
    if isinstance(cust, dict):
        lang_pref = str(cust.get("language_pref") or "").lower()
    mlangs = (facts.get("merchant") or {}).get("languages") or []
    wants_hi_en = "hi-en" in lang_pref or any(
        str(x).lower() in ("hi-en", "hi-en mix") for x in mlangs
    )
    if wants_hi_en and body:
        dev = len(re.findall(r"[\u0900-\u097F]", body))
        lat = len(re.findall(r"[A-Za-z]", body))
        if dev > 40 and lat < max(12, dev // 4):
            errors.append("hi_en_needs_latin_mix")
            ok_lang = False
        else:
            ok_lang = True
    else:
        ok_lang = True

    params = result.get("template_params")
    if not isinstance(params, list) or not params:
        m = facts.get("merchant") or {}
        params = [
            m.get("owner_first_name") or m.get("name") or "merchant",
            (facts.get("trigger") or {}).get("kind") or "nudge",
            "follow_up",
        ]
    params = [str(p) for p in params][:5]

    send_as = result.get("send_as") or facts.get("send_as") or "vera"
    if send_as not in ("vera", "merchant_on_behalf"):
        send_as = facts.get("send_as") or "vera"

    repaired = {
        "body": body,
        "cta": cta,
        "rationale": rationale,
        "send_as": send_as,
        "suppression_key": result.get("suppression_key")
        or (facts.get("trigger") or {}).get("suppression_key")
        or "",
        "template_name": result.get("template_name")
        or f"vera_{(facts.get('trigger') or {}).get('kind', 'generic')}_v1",
        "template_params": params,
    }

    # Fatal if still empty after scrub
    ok = bool(repaired["body"]) and "empty_body" not in errors and ok_lang
    # URL after scrub attempt — if still present, fail
    if URL_RE.search(repaired["body"]):
        ok = False
        errors.append("url_unremovable")

    return ok, repaired, errors
