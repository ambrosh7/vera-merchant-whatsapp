"""
EngagementComposer — Phase B/C.

compose(category, merchant, trigger, customer?) → dict
Uses LLM when LLM_API_KEY is set; otherwise deterministic fact-pack composer.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from bot import config
from bot.composer.deterministic import deterministic_compose
from bot.composer.fact_pack import assemble_fact_pack
from bot.composer.helpers.language import language_instruction
from bot.composer.llm import LLMClient
from bot.composer.rate_limit import RateLimitExceeded, get_rate_limiter
from bot.composer.router import load_prompt_text
from bot.composer.validators import validate_composition

logger = logging.getLogger(__name__)

_llm = LLMClient()


def _can_afford_repair() -> bool:
    """Avoid a second Groq call when minute token budget is already tight."""
    snap = get_rate_limiter().snapshot()
    remaining = snap["tpm_limit"] - snap["tpm_used"]
    return remaining >= int(config.LLM_REPAIR_MIN_TPM_REMAINING)


def compose(
    category: dict,
    merchant: dict,
    trigger: dict,
    customer: dict | None = None,
    *,
    force_english: bool = False,
) -> dict:
    """
    Public compose API (also used offline via root bot.py).

    Returns keys: body, cta, send_as, suppression_key, rationale,
                  template_name, template_params

    force_english: product UI / demos — clear English only (no hi-en mix).
    """
    facts = assemble_fact_pack(category, merchant, trigger, customer)
    facts["prompt_version"] = config.COMPOSER_PROMPT_VERSION
    if force_english:
        facts["language_instruction"] = (
            "Write in clear English only. No Hindi, Devanagari, or code-mix."
        )
        if facts.get("customer"):
            facts["customer"]["language_pref"] = "en"
    else:
        facts["language_instruction"] = language_instruction(merchant, customer)
    kind = (trigger.get("kind") or "").strip()

    result: Optional[dict[str, Any]] = None
    source = "deterministic"

    # Golden-path kinds: case-study templates beat LLM drift under rate limits.
    prefer_deterministic = kind in {
        "regulation_change",
        "supply_alert",
        "research_digest",
        "recall_due",
        "appointment_tomorrow",
    }

    if (
        _llm.available
        and not config.COMPOSER_FORCE_DETERMINISTIC
        and not prefer_deterministic
    ):
        try:
            result = _compose_via_llm(facts, kind, repair=False)
            source = "llm"
            ok, repaired, errors = validate_composition(result, category, facts)
            if not ok:
                if _can_afford_repair():
                    logger.warning("compose validate fail %s — repairing", errors)
                    result = _compose_via_llm(
                        facts,
                        kind,
                        repair=True,
                        prior=result,
                        errors=errors,
                    )
                    ok, repaired, errors = validate_composition(result, category, facts)
                    if not ok:
                        logger.warning(
                            "repair failed %s — falling back deterministic", errors
                        )
                        result = None
                    else:
                        result = repaired
                else:
                    logger.warning(
                        "compose validate fail %s — skip repair (LLM TPM tight)",
                        errors,
                    )
                    result = None
            else:
                result = repaired
        except RateLimitExceeded as exc:
            logger.warning("LLM rate-limited: %s — deterministic fallback", exc)
            result = None
        except Exception as exc:
            logger.warning("LLM compose failed: %s — deterministic fallback", exc)
            result = None

    if result is None:
        result = deterministic_compose(facts)
        source = "deterministic"
        ok, repaired, errors = validate_composition(result, category, facts)
        result = repaired if ok else result

    result["send_as"] = result.get("send_as") or facts["send_as"]
    result["suppression_key"] = (
        result.get("suppression_key")
        or trigger.get("suppression_key")
        or ""
    )
    # Keep rationale honest about path
    if source == "deterministic" and "deterministic" not in (result.get("rationale") or ""):
        result["rationale"] = (result.get("rationale") or "") + f" [{config.COMPOSER_PROMPT_VERSION}/{source}]"
    else:
        result["rationale"] = (result.get("rationale") or "") + f" [{config.COMPOSER_PROMPT_VERSION}/{source}]"

    return {
        "body": result["body"],
        "cta": result["cta"],
        "send_as": result["send_as"],
        "suppression_key": result["suppression_key"],
        "rationale": result["rationale"].strip(),
        "template_name": result.get("template_name")
        or f"vera_{kind or 'generic'}_v1",
        "template_params": list(result.get("template_params") or []),
    }


def _compact_facts_for_llm(facts: dict[str, Any]) -> dict[str, Any]:
    """Drop bulky / null fields so a single call fits ~8K TPM budgets."""
    skip = {"prompt_version"}
    out: dict[str, Any] = {}
    for k, v in facts.items():
        if k in skip or v is None or v == "" or v == [] or v == {}:
            continue
        out[k] = v
    # Cap long free-text fields
    for key in ("language_instruction",):
        if isinstance(out.get(key), str) and len(out[key]) > 240:
            out[key] = out[key][:240]
    # Compliance nudges: hide cohort stats so the model can't misuse them
    kind = ((facts.get("trigger") or {}).get("kind") or "").strip()
    if kind == "regulation_change" and isinstance(out.get("merchant"), dict):
        mer = dict(out["merchant"])
        mer.pop("customer_aggregate", None)
        mer.pop("signals", None)
        mer.pop("review_themes", None)
        out["merchant"] = mer
    return out


def _compose_via_llm(
    facts: dict[str, Any],
    kind: str,
    *,
    repair: bool = False,
    prior: Optional[dict[str, Any]] = None,
    errors: Optional[list[str]] = None,
) -> dict[str, Any]:
    system = load_prompt_text(kind)
    # Keep system short for TPM — base rules + kind notes only
    if len(system) > 3500:
        system = system[:3500]
    user_obj = {
        "instruction": (
            "Compose one WhatsApp message from this fact pack only. "
            "JSON keys: body, cta, rationale, template_params. "
            "Never invent numbers not present in fact_pack."
        ),
        "fact_pack": _compact_facts_for_llm(facts),
    }
    if repair:
        # Keep repair payload small — body/cta/errors only
        prior_slim = None
        if isinstance(prior, dict):
            prior_slim = {
                "body": prior.get("body"),
                "cta": prior.get("cta"),
                "rationale": prior.get("rationale"),
            }
        user_obj["repair"] = {
            "prior": prior_slim,
            "errors": errors,
            "instruction": "Fix the prior output to resolve errors. Still JSON only.",
        }
    user = json.dumps(user_obj, ensure_ascii=False)
    timeout = max(5.0, float(config.TICK_DEADLINE_SECONDS) - 5.0)
    return _llm.complete_json(system, user, timeout=timeout)
