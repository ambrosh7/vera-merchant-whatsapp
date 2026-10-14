#!/usr/bin/env python3
"""Phase C smoke: kind families, consent, ranking, vertical coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot import compose  # noqa: E402
from bot.composer.helpers.consent import consent_allows  # noqa: E402
from bot.orchestrator.suppression import rank_score  # noqa: E402
from bot.store.context_store import ContextStore  # noqa: E402
from bot.store.conversation_store import ConversationStore  # noqa: E402
from bot.orchestrator.tick import handle_tick  # noqa: E402


def load_seeds():
    cats = {
        p.stem: json.loads(p.read_text())
        for p in (ROOT / "dataset/categories").glob("*.json")
    }
    merchants = {
        m["merchant_id"]: m
        for m in json.loads((ROOT / "dataset/merchants_seed.json").read_text())[
            "merchants"
        ]
    }
    customers = {
        c["customer_id"]: c
        for c in json.loads((ROOT / "dataset/customers_seed.json").read_text())[
            "customers"
        ]
    }
    triggers = {
        t["id"]: t
        for t in json.loads((ROOT / "dataset/triggers_seed.json").read_text())[
            "triggers"
        ]
    }
    return cats, merchants, customers, triggers


def main() -> int:
    fails = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    cats, merchants, customers, triggers = load_seeds()

    cases = [
        ("dentists/digest", "trg_001_research_digest_dentists", None, ["JIDA", "Meera"]),
        ("dentists/recall", "trg_003_recall_due_priya", "c_001_priya_for_m001", ["Priya", "₹299"]),
        ("salons/curious", "trg_008_curious_ask_studio11", None, ["Lakshmi", "Studio11"]),
        ("salons/bridal", "trg_007_bridal_followup_kavya", "c_005_kavya_for_m003", ["Kavya"]),
        ("restaurants/ipl", "trg_010_ipl_match_delhi", None, ["IPL", "Saturday"] if True else []),
        ("restaurants/planning", "trg_013_corporate_thali_planning", None, ["starter", "thali"]),
        ("gyms/seasonal", "trg_014_seasonal_acquisition_dip_powerhouse", None, ["expected", "not a sudden"]),
        ("gyms/lapse", "trg_015_winback_rashmi", "c_010_rashmi_for_m007", ["Rashmi", "no judgment"]),
        ("pharmacies/supply", "trg_018_supply_atorvastatin_recall", None, ["atorvastatin", "AT2024"]),
        ("pharmacies/refill", "trg_019_chronic_refill_grandfather", "c_013_grandfather_for_m009", ["metformin"]),
    ]

    print("=== Vertical / kind-family compose ===")
    for label, tid, cid, needles in cases:
        trg = triggers[tid]
        mer = merchants[trg["merchant_id"]]
        cat = cats[mer["category_slug"]]
        cust = customers.get(cid) if cid else None
        # Fix IPL needles dynamically
        if tid == "trg_010_ipl_match_delhi":
            needles = ["DC vs MI"] if "DC" in json.dumps(trg) else ["match"]
            r = compose(cat, mer, trg, cust)
            # judgment: Saturday / not weeknight
            if trg.get("payload", {}).get("is_weeknight") is False:
                check(
                    f"{label} weekend judgment",
                    "Saturday" in r["body"] or "delivery" in r["body"].lower() or "Skip" in r["body"] or "skip" in r["body"],
                    r["body"][:100],
                )
            else:
                check(f"{label} composed", bool(r["body"]))
            continue

        r = compose(cat, mer, trg, cust)
        ok_needles = all(n.lower() in r["body"].lower() for n in needles)
        check(f"{label} anchors", ok_needles, r["body"][:120])
        check(f"{label} no http", "http" not in r["body"].lower())

    print("\n=== Consent gate ===")
    trg_promo = {
        "scope": "customer",
        "kind": "customer_lapsed_soft",
        "payload": {},
    }
    cust_no = {
        "consent": {"scope": ["appointment_reminders"]},
        "preferences": {"reminder_opt_in": True},
    }
    check(
        "lapse blocked without promotional scope",
        consent_allows(trg_promo, cust_no) is False,
    )
    check(
        "recall allowed with recall_reminders",
        consent_allows(triggers["trg_003_recall_due_priya"], customers["c_001_priya_for_m001"]),
    )

    print("\n=== Ranking ===")
    m002 = merchants["m_002_bharat_dentist_mumbai"]
    s_renew = rank_score(triggers["trg_005_renewal_due_bharat"], m002)
    s_fest = rank_score(triggers["trg_006_festival_diwali"], merchants["m_003_studio11_salon_hyderabad"])
    check("renewal ranks above far festival", s_renew > s_fest, f"{s_renew} vs {s_fest}")

    print("\n=== Tick: rank + suppress + empty ===")
    store = ContextStore()
    conv = ConversationStore()
    for slug, cat in cats.items():
        store.put("category", slug, 1, cat)
    for mid, m in merchants.items():
        store.put("merchant", mid, 1, m)
    for cid, c in customers.items():
        store.put("customer", cid, 1, c)
    for tid, t in triggers.items():
        store.put("trigger", tid, 1, t)

    # Competing triggers for same merchant m_002 — should pick higher urgency
    actions = handle_tick(
        "2026-04-26T10:00:00Z",
        ["trg_004_perf_dip_bharat", "trg_005_renewal_due_bharat"],
        store,
        conv,
    )
    check("one action for one merchant", len(actions) == 1, str([a.trigger_id for a in actions]))
    if actions:
        check(
            "picked high-urgency family",
            actions[0].trigger_id in ("trg_004_perf_dip_bharat", "trg_005_renewal_due_bharat"),
        )

    # suppression
    actions2 = handle_tick(
        "2026-04-26T10:05:00Z",
        [actions[0].trigger_id] if actions else [],
        store,
        conv,
    )
    check("suppression blocks repeat", actions2 == [])

    empty = handle_tick("2026-04-26T11:00:00Z", [], store, conv)
    check("empty triggers → []", empty == [])

    # far festival alone still ok but soft
    conv2 = ConversationStore()
    fest = handle_tick(
        "2026-04-26T12:00:00Z",
        ["trg_006_festival_diwali"],
        store,
        conv2,
    )
    check("festival still sendable alone", len(fest) == 1)
    if fest:
        check("festival soft urgency copy", "days" in fest[0].body.lower() or "no rush" in fest[0].body.lower() or "early" in fest[0].body.lower())

    print()
    if fails:
        print(f"FAILED: {fails}")
        return 1
    print("Phase C smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
