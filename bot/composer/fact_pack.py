"""
Assemble allowlisted facts for composition.

HARD RULE: the LLM/prompt may only use fields present in the returned fact pack.
If a field is missing, omit it from the message — never invent.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional


def resolve_digest_item(
    category: dict[str, Any],
    item_id: Optional[str],
) -> Optional[dict[str, Any]]:
    if not item_id:
        return None
    for item in category.get("digest") or []:
        if item.get("id") == item_id:
            return deepcopy(item)
    return None


def _active_offers(merchant: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for o in merchant.get("offers") or []:
        if o.get("status") == "active":
            out.append(
                {
                    "id": o.get("id"),
                    "title": o.get("title"),
                    "status": o.get("status"),
                }
            )
    return out


def assemble_fact_pack(
    category: dict[str, Any],
    merchant: dict[str, Any],
    trigger: dict[str, Any],
    customer: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a minimal, verifiable fact pack for compose()."""
    identity = merchant.get("identity") or {}
    performance = merchant.get("performance") or {}
    peer = category.get("peer_stats") or {}
    voice = category.get("voice") or {}
    payload = trigger.get("payload") or {}

    top_item_id = payload.get("top_item_id") or payload.get("digest_item_id")
    digest_item = resolve_digest_item(category, top_item_id)

    # Sometimes top facts are embedded directly in payload
    if digest_item is None and isinstance(payload.get("top_item"), dict):
        digest_item = deepcopy(payload["top_item"])

    send_as = (
        "merchant_on_behalf" if trigger.get("scope") == "customer" else "vera"
    )

    facts: dict[str, Any] = {
        "prompt_version": None,  # filled by composer
        "send_as": send_as,
        "trigger": {
            "id": trigger.get("id"),
            "kind": trigger.get("kind"),
            "scope": trigger.get("scope"),
            "source": trigger.get("source"),
            "urgency": trigger.get("urgency"),
            "suppression_key": trigger.get("suppression_key") or "",
            "expires_at": trigger.get("expires_at"),
            "payload": deepcopy(payload),
        },
        "category": {
            "slug": category.get("slug"),
            "tone": voice.get("tone"),
            "register": voice.get("register"),
            "code_mix": voice.get("code_mix"),
            "vocab_allowed": list(voice.get("vocab_allowed") or [])[:12],
            "vocab_taboo": list(
                voice.get("vocab_taboo") or voice.get("taboos") or []
            ),
            "peer_stats": {
                "avg_ctr": peer.get("avg_ctr"),
                "avg_rating": peer.get("avg_rating"),
                "avg_review_count": peer.get("avg_review_count"),
                "scope": peer.get("scope"),
            },
        },
        "merchant": {
            "merchant_id": merchant.get("merchant_id"),
            "name": identity.get("name"),
            "owner_first_name": identity.get("owner_first_name"),
            "city": identity.get("city"),
            "locality": identity.get("locality"),
            "languages": list(identity.get("languages") or []),
            "verified": identity.get("verified"),
            "subscription": deepcopy(merchant.get("subscription") or {}),
            "performance": {
                "views": performance.get("views"),
                "calls": performance.get("calls"),
                "directions": performance.get("directions"),
                "ctr": performance.get("ctr"),
                "delta_7d": deepcopy(performance.get("delta_7d") or {}),
            },
            "active_offers": _active_offers(merchant),
            "signals": list(merchant.get("signals") or []),
            "customer_aggregate": deepcopy(
                merchant.get("customer_aggregate") or {}
            ),
            "review_themes": deepcopy(merchant.get("review_themes") or [])[:3],
        },
        "digest_item": digest_item,
        "customer": None,
    }

    if customer:
        c_identity = customer.get("identity") or {}
        facts["customer"] = {
            "customer_id": customer.get("customer_id"),
            "name": c_identity.get("name"),
            "language_pref": c_identity.get("language_pref"),
            "age_band": c_identity.get("age_band"),
            "state": customer.get("state"),
            "relationship": deepcopy(customer.get("relationship") or {}),
            "preferences": deepcopy(customer.get("preferences") or {}),
            "consent": deepcopy(customer.get("consent") or {}),
        }

    return facts
