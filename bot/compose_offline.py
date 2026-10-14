#!/usr/bin/env python3
"""Generate draft submission.jsonl from test_pairs.json (Phase B)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bot.composer.composer import compose


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="dataset/expanded",
        help="Expanded dataset directory",
    )
    parser.add_argument(
        "--pairs",
        default=None,
        help="test_pairs.json path (default: <dataset>/test_pairs.json)",
    )
    parser.add_argument(
        "--out",
        default="submission.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max pairs (0 = all)",
    )
    args = parser.parse_args()

    root = Path(args.dataset)
    pairs_path = Path(args.pairs) if args.pairs else root / "test_pairs.json"
    pairs = load_json(pairs_path)["pairs"]
    if args.limit:
        pairs = pairs[: args.limit]

    categories = {
        p.stem: load_json(p) for p in (root / "categories").glob("*.json")
    }
    merchants = {
        load_json(p)["merchant_id"]: load_json(p)
        for p in (root / "merchants").glob("*.json")
    }
    customers = {
        load_json(p)["customer_id"]: load_json(p)
        for p in (root / "customers").glob("*.json")
    }
    triggers = {
        load_json(p)["id"]: load_json(p)
        for p in (root / "triggers").glob("*.json")
    }

    out_path = Path(args.out)
    n = 0
    with out_path.open("w", encoding="utf-8") as fp:
        for pair in pairs:
            trg = triggers[pair["trigger_id"]]
            mer = merchants[pair["merchant_id"]]
            cat = categories[mer["category_slug"]]
            cust = None
            cid = pair.get("customer_id")
            if cid:
                cust = customers.get(cid)
            result = compose(cat, mer, trg, cust)
            line = {
                "test_id": pair["test_id"],
                "body": result["body"],
                "cta": result["cta"],
                "send_as": result["send_as"],
                "suppression_key": result["suppression_key"],
                "rationale": result["rationale"],
            }
            fp.write(json.dumps(line, ensure_ascii=False) + "\n")
            n += 1

    print(f"Wrote {n} lines → {out_path.resolve()}")


if __name__ == "__main__":
    main()
