#!/usr/bin/env python3
"""
Challenge offline entrypoint.

Prefer: `from bot import compose` (package export).
This file mirrors the brief's `bot.py` surface for `python bot.py` demos.
"""

from __future__ import annotations

# Re-export from package (directory `bot/`).
from bot.composer.composer import compose as compose  # noqa: F401

__all__ = ["compose"]


if __name__ == "__main__":
    import json
    from pathlib import Path

    root = Path(__file__).parent
    cat = json.loads((root / "dataset/categories/dentists.json").read_text())
    merchants = json.loads((root / "dataset/merchants_seed.json").read_text())[
        "merchants"
    ]
    triggers = json.loads((root / "dataset/triggers_seed.json").read_text())[
        "triggers"
    ]
    customers = json.loads((root / "dataset/customers_seed.json").read_text())[
        "customers"
    ]
    m = next(x for x in merchants if x["merchant_id"].startswith("m_001"))
    t = next(x for x in triggers if x["id"] == "trg_001_research_digest_dentists")
    print("=== research_digest ===")
    print(json.dumps(compose(cat, m, t, None), indent=2, ensure_ascii=False))
    t2 = next(x for x in triggers if x["id"] == "trg_003_recall_due_priya")
    c = next(x for x in customers if x["customer_id"] == "c_001_priya_for_m001")
    print("=== recall_due ===")
    print(json.dumps(compose(cat, m, t2, c), indent=2, ensure_ascii=False))
