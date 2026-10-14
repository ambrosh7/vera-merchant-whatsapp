"""Interactive demo catalog + compose for the Vera product UI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "dataset"


@lru_cache(maxsize=1)
def _load_seeds() -> dict[str, Any]:
    categories = {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in (SEED / "categories").glob("*.json")
    }
    merchants = json.loads((SEED / "merchants_seed.json").read_text(encoding="utf-8"))[
        "merchants"
    ]
    customers = json.loads((SEED / "customers_seed.json").read_text(encoding="utf-8"))[
        "customers"
    ]
    triggers = json.loads((SEED / "triggers_seed.json").read_text(encoding="utf-8"))[
        "triggers"
    ]
    return {
        "categories": categories,
        "merchants": merchants,
        "customers": customers,
        "triggers": triggers,
    }


def _merchant_label(m: dict[str, Any]) -> str:
    ident = m.get("identity") or {}
    return f"{ident.get('name', m.get('merchant_id'))} · {ident.get('locality', '')}"


def _trigger_label(t: dict[str, Any]) -> str:
    return f"{t.get('kind')} · urgency {t.get('urgency')} · {t.get('id')}"


def catalog() -> dict[str, Any]:
    data = _load_seeds()
    scenarios = [
        {
            "id": "case_research_digest",
            "title": "Share a clinical update",
            "blurb": "New fluoride research your patients may ask about",
            "category_slug": "dentists",
            "merchant_id": "m_001_drmeera_dentist_delhi",
            "trigger_id": "trg_001_research_digest_dentists",
            "customer_id": None,
        },
        {
            "id": "case_recall_priya",
            "title": "Book a recall visit",
            "blurb": "Priya is due for her 6-month cleaning",
            "category_slug": "dentists",
            "merchant_id": "m_001_drmeera_dentist_delhi",
            "trigger_id": "trg_003_recall_due_priya",
            "customer_id": "c_001_priya_for_m001",
        },
        {
            "id": "case_regulation",
            "title": "Prep for compliance",
            "blurb": "Radiograph rules update before the Dec deadline",
            "category_slug": "dentists",
            "merchant_id": "m_001_drmeera_dentist_delhi",
            "trigger_id": "trg_002_compliance_dci_radiograph",
            "customer_id": None,
        },
        {
            "id": "case_salon_wedding",
            "title": "Wedding package follow-up",
            "blurb": "Stay close to a bridal client at Studio11",
            "category_slug": "salons",
            "merchant_id": "m_003_studio11_salon_hyderabad",
            "trigger_id": next(
                (
                    t["id"]
                    for t in data["triggers"]
                    if t.get("kind") == "wedding_package_followup"
                ),
                data["triggers"][0]["id"],
            ),
            "customer_id": next(
                (
                    c["customer_id"]
                    for c in data["customers"]
                    if "kavya" in c["customer_id"].lower()
                    or (c.get("identity") or {}).get("name", "").lower().startswith(
                        "kavya"
                    )
                ),
                None,
            ),
        },
        {
            "id": "case_curious_ask",
            "title": "Ask what's working",
            "blurb": "A light check-in to spark a reply from the cafe",
            "category_slug": "restaurants",
            "merchant_id": "m_006_southindiancafe_restaurant_bangalore",
            "trigger_id": next(
                (t["id"] for t in data["triggers"] if t.get("kind") == "curious_ask_due"),
                data["triggers"][0]["id"],
            ),
            "customer_id": None,
        },
    ]

    return {
        "scenarios": scenarios,
        "categories": [
            {"slug": slug, "tone": (cat.get("voice") or {}).get("tone")}
            for slug, cat in data["categories"].items()
        ],
        "merchants": [
            {
                "merchant_id": m["merchant_id"],
                "category_slug": m.get("category_slug"),
                "label": _merchant_label(m),
                "owner": (m.get("identity") or {}).get("owner_first_name"),
                "city": (m.get("identity") or {}).get("city"),
            }
            for m in data["merchants"]
        ],
        "triggers": [
            {
                "id": t["id"],
                "kind": t.get("kind"),
                "scope": t.get("scope"),
                "urgency": t.get("urgency"),
                "label": _trigger_label(t),
                "merchant_id": t.get("merchant_id")
                or (t.get("payload") or {}).get("merchant_id"),
            }
            for t in data["triggers"]
        ],
        "customers": [
            {
                "customer_id": c["customer_id"],
                "label": (c.get("identity") or {}).get("name") or c["customer_id"],
                "language_pref": (c.get("identity") or {}).get("language_pref"),
                "merchant_hint": c["customer_id"].split("_for_")[-1]
                if "_for_" in c["customer_id"]
                else None,
            }
            for c in data["customers"]
        ],
    }


def resolve_bundle(
    *,
    category_slug: str,
    merchant_id: str,
    trigger_id: str,
    customer_id: Optional[str] = None,
) -> dict[str, Any]:
    data = _load_seeds()
    category = data["categories"].get(category_slug)
    merchant = next(
        (m for m in data["merchants"] if m["merchant_id"] == merchant_id), None
    )
    trigger = next((t for t in data["triggers"] if t["id"] == trigger_id), None)
    customer = None
    if customer_id:
        customer = next(
            (c for c in data["customers"] if c["customer_id"] == customer_id), None
        )
    if not category or not merchant or not trigger:
        raise KeyError("Unknown category, merchant, or trigger id")
    return {
        "category": category,
        "merchant": merchant,
        "trigger": trigger,
        "customer": customer,
    }
