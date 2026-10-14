"""Consent gate for customer-scoped sends."""

from __future__ import annotations

from typing import Any, Optional

# trigger.kind → consent scopes that authorize the send
KIND_CONSENT_SCOPES: dict[str, set[str]] = {
    "recall_due": {"recall_reminders", "appointment_reminders"},
    "appointment_tomorrow": {"appointment_reminders", "recall_reminders"},
    "customer_lapsed_soft": {"promotional_offers", "recall_reminders"},
    "customer_lapsed_hard": {"promotional_offers", "recall_reminders"},
    "chronic_refill_due": {
        "appointment_reminders",
        "promotional_offers",
        "recall_reminders",
        "treatment_followup",
    },
    "wedding_package_followup": {
        "bridal_package_followup",
        "appointment_reminders",
        "promotional_offers",
    },
    "trial_followup": {"appointment_reminders", "promotional_offers", "trial_followup"},
}


def consent_allows(
    trigger: dict[str, Any],
    customer: Optional[dict[str, Any]],
) -> bool:
    """
    Merchant-scoped triggers always allowed.
    Customer-scoped: require overlap between consent.scope and kind requirements.
    If kind has no mapping, allow only when consent.scope is non-empty (opted in somehow).
    """
    if trigger.get("scope") != "customer":
        return True
    if not customer:
        return False
    consent = customer.get("consent") or {}
    scopes = set(consent.get("scope") or [])
    prefs = customer.get("preferences") or {}
    if prefs.get("reminder_opt_in") is False:
        # hard opt-out of reminders
        kind = trigger.get("kind") or ""
        if kind in ("recall_due", "appointment_tomorrow", "chronic_refill_due"):
            return False

    kind = trigger.get("kind") or ""
    required = KIND_CONSENT_SCOPES.get(kind)
    if required is None:
        return bool(scopes)  # must have opted into something
    return bool(scopes & required)
