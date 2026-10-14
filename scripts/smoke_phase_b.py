#!/usr/bin/env python3
"""Phase B smoke: offline compose for Case Study 1–2 shapes (no LLM required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot import compose  # noqa: E402


def main() -> int:
    cat = json.loads((ROOT / "dataset/categories/dentists.json").read_text())
    merchants = json.loads((ROOT / "dataset/merchants_seed.json").read_text())[
        "merchants"
    ]
    triggers = json.loads((ROOT / "dataset/triggers_seed.json").read_text())[
        "triggers"
    ]
    customers = json.loads((ROOT / "dataset/customers_seed.json").read_text())[
        "customers"
    ]

    m = next(x for x in merchants if "m_001" in x["merchant_id"])
    t1 = next(x for x in triggers if x["id"] == "trg_001_research_digest_dentists")
    t2 = next(x for x in triggers if x["id"] == "trg_003_recall_due_priya")
    c1 = next(x for x in customers if x["customer_id"] == "c_001_priya_for_m001")

    r1 = compose(cat, m, t1, None)
    r2 = compose(cat, m, t2, c1)

    fails = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    print("G1 research_digest\n", r1["body"], "\n")
    check("G1 send_as vera", r1["send_as"] == "vera")
    check("G1 cites JIDA or source", "JIDA" in r1["body"] or "p.14" in r1["body"])
    check("G1 has number", any(x in r1["body"] for x in ("2100", "2,100", "38")))
    check("G1 merchant anchor", "high-risk" in r1["body"].lower() or "Meera" in r1["body"])
    check("G1 no URL", "http" not in r1["body"].lower())
    check("G1 rationale", bool(r1.get("rationale")))

    print("G2 recall_due\n", r2["body"], "\n")
    check("G2 send_as merchant_on_behalf", r2["send_as"] == "merchant_on_behalf")
    check("G2 has Priya", "Priya" in r2["body"])
    check("G2 has slot or ₹299", "Nov" in r2["body"] or "₹299" in r2["body"] or "299" in r2["body"])
    check("G2 hi-en cue", "Apke" in r2["body"] or "ya " in r2["body"] or "hain" in r2["body"])
    check("G2 no guaranteed", "guaranteed" not in r2["body"].lower())

    print()
    if fails:
        print(f"FAILED: {fails}")
        return 1
    print("Phase B golden-path smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
