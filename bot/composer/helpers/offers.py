"""Active offer helpers — never invent prices."""

from __future__ import annotations

from typing import Any, Optional


def active_offers(merchant: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for o in merchant.get("offers") or []:
        if o.get("status") == "active" and o.get("title"):
            out.append(o)
    return out


def active_offer_titles(merchant: dict[str, Any]) -> list[str]:
    return [o["title"] for o in active_offers(merchant)]


def primary_offer_title(merchant: dict[str, Any]) -> Optional[str]:
    titles = active_offer_titles(merchant)
    return titles[0] if titles else None
