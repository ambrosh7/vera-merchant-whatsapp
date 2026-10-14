"""Phase A stub composer — placeholder bodies; replaced by LLM in Phase B."""

from __future__ import annotations

from typing import Any, Optional


def stub_compose(
    category: dict[str, Any],
    merchant: dict[str, Any],
    trigger: dict[str, Any],
    customer: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Return a minimal valid compose dict.

    Uses only identity/trigger fields so warmup + tick contract tests pass
    without an LLM. Not scored for quality.
    """
    identity = merchant.get("identity") or {}
    name = identity.get("owner_first_name") or identity.get("name") or "there"
    biz = identity.get("name") or "your business"
    kind = trigger.get("kind", "nudge")
    scope = trigger.get("scope", "merchant")
    send_as = "merchant_on_behalf" if scope == "customer" else "vera"

    if send_as == "merchant_on_behalf" and customer:
        cust_name = (customer.get("identity") or {}).get("name", "there")
        body = (
            f"Hi {cust_name}, {biz} here. "
            f"[Phase-A stub for {kind}] — real composer lands in Phase B."
        )
        cta = "open_ended"
    else:
        body = (
            f"Hi {name} — quick note from Vera about {kind.replace('_', ' ')} "
            f"for {biz}. [Phase-A stub — real composer lands in Phase B.]"
        )
        cta = "open_ended"

    return {
        "body": body,
        "cta": cta,
        "send_as": send_as,
        "suppression_key": trigger.get("suppression_key") or "",
        "rationale": (
            f"Phase-A stub: joined category={category.get('slug')}, "
            f"merchant={merchant.get('merchant_id')}, trigger={trigger.get('id') or trigger.get('kind')}"
        ),
        "template_name": f"vera_{kind}_stub_v1",
        "template_params": [str(name), kind, biz],
    }
