#!/usr/bin/env python3
"""
Phase A contract smoke test (no LLM).

Usage:
    # terminal 1: uvicorn bot.app:app --host 0.0.0.0 --port 8080
    # terminal 2:
    python scripts/smoke_phase_a.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
DATASET = ROOT / "dataset"


def req(method: str, path: str, body: dict | None = None, timeout: int = 10):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{BOT_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return e.code, payload


def main() -> int:
    failures = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal failures
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures += 1

    print(f"Smoke Phase A against {BOT_URL}\n")

    # teardown for clean slate
    req("POST", "/v1/teardown", {})

    code, health = req("GET", "/v1/healthz")
    check("healthz 200", code == 200 and health.get("status") == "ok")
    check(
        "healthz zeros",
        health.get("contexts_loaded")
        == {"category": 0, "merchant": 0, "customer": 0, "trigger": 0},
        str(health.get("contexts_loaded")),
    )

    code, meta = req("GET", "/v1/metadata")
    check("metadata 200", code == 200 and "team_name" in meta)

    # push 5 categories
    for path in sorted((DATASET / "categories").glob("*.json")):
        payload = json.loads(path.read_text())
        slug = payload["slug"]
        code, resp = req(
            "POST",
            "/v1/context",
            {
                "scope": "category",
                "context_id": slug,
                "version": 1,
                "delivered_at": "2026-04-26T09:45:00Z",
                "payload": payload,
            },
        )
        check(f"push category/{slug}", code == 200 and resp.get("accepted") is True)

    # idempotent / stale version
    dentists = json.loads((DATASET / "categories" / "dentists.json").read_text())
    code, resp = req(
        "POST",
        "/v1/context",
        {
            "scope": "category",
            "context_id": "dentists",
            "version": 1,
            "delivered_at": "2026-04-26T09:45:00Z",
            "payload": dentists,
        },
    )
    check("stale same version → 409", code == 409 and resp.get("reason") == "stale_version")

    # merchants + customers from seeds
    merchants = json.loads((DATASET / "merchants_seed.json").read_text())["merchants"]
    for m in merchants:
        code, resp = req(
            "POST",
            "/v1/context",
            {
                "scope": "merchant",
                "context_id": m["merchant_id"],
                "version": 1,
                "delivered_at": "2026-04-26T09:45:30Z",
                "payload": m,
            },
        )
        check(f"push merchant/{m['merchant_id'][:20]}", code == 200 and resp.get("accepted"))

    customers = json.loads((DATASET / "customers_seed.json").read_text())["customers"]
    for c in customers:
        code, resp = req(
            "POST",
            "/v1/context",
            {
                "scope": "customer",
                "context_id": c["customer_id"],
                "version": 1,
                "delivered_at": "2026-04-26T09:46:00Z",
                "payload": c,
            },
        )
        check(f"push customer/{c['customer_id'][:20]}", code == 200 and resp.get("accepted"))

    code, health = req("GET", "/v1/healthz")
    loaded = health.get("contexts_loaded", {})
    check(
        "healthz counts after seeds",
        loaded.get("category") == 5
        and loaded.get("merchant") == len(merchants)
        and loaded.get("customer") == len(customers)
        and loaded.get("trigger") == 0,
        str(loaded),
    )

    # trigger + tick
    triggers = json.loads((DATASET / "triggers_seed.json").read_text())["triggers"]
    trg = next(t for t in triggers if t["id"] == "trg_001_research_digest_dentists")
    code, resp = req(
        "POST",
        "/v1/context",
        {
            "scope": "trigger",
            "context_id": trg["id"],
            "version": 1,
            "delivered_at": "2026-04-26T10:32:00Z",
            "payload": trg,
        },
    )
    check("push trigger trg_001", code == 200 and resp.get("accepted"))

    code, tick = req(
        "POST",
        "/v1/tick",
        {
            "now": "2026-04-26T10:35:00Z",
            "available_triggers": ["trg_001_research_digest_dentists"],
        },
    )
    actions = tick.get("actions", []) if isinstance(tick, dict) else []
    check("tick returns action", code == 200 and len(actions) == 1, f"n={len(actions)}")
    if actions:
        a = actions[0]
        check("action has required keys", all(
            k in a
            for k in (
                "conversation_id",
                "merchant_id",
                "send_as",
                "trigger_id",
                "body",
                "cta",
                "suppression_key",
                "rationale",
            )
        ))
        check("send_as vera", a.get("send_as") == "vera")
        conv_id = a["conversation_id"]

        # suppression: second tick should not re-send
        code, tick2 = req(
            "POST",
            "/v1/tick",
            {
                "now": "2026-04-26T10:40:00Z",
                "available_triggers": ["trg_001_research_digest_dentists"],
            },
        )
        check(
            "suppression blocks second tick",
            code == 200 and tick2.get("actions") == [],
            str(tick2.get("actions")),
        )

        # reply opt-out
        code, reply = req(
            "POST",
            "/v1/reply",
            {
                "conversation_id": conv_id,
                "merchant_id": a["merchant_id"],
                "customer_id": None,
                "from_role": "merchant",
                "message": "Not interested. Stop messaging me.",
                "received_at": "2026-04-26T10:42:00Z",
                "turn_number": 2,
            },
        )
        check("opt-out → end", code == 200 and reply.get("action") == "end", str(reply))

    # empty tick
    code, empty = req(
        "POST",
        "/v1/tick",
        {"now": "2026-04-26T11:00:00Z", "available_triggers": []},
    )
    check("empty triggers → []", code == 200 and empty.get("actions") == [])

    print()
    if failures:
        print(f"FAILED: {failures} check(s)")
        return 1
    print("ALL CHECKS PASSED — Phase A contract smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
