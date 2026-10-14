#!/usr/bin/env python3
"""Phase E smoke: adaptive versions, soft deadline, submission freeze, healthz."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot import compose  # noqa: E402
from bot.config import COMPOSER_PROMPT_FROZEN, COMPOSER_PROMPT_VERSION, MAX_TICK_ACTIONS  # noqa: E402
from bot.orchestrator.tick import handle_tick  # noqa: E402
from bot.store.context_store import ContextStore  # noqa: E402
from bot.store.conversation_store import ConversationStore  # noqa: E402


def main() -> int:
    fails = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

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

    print("=== E.1 Adaptive context ===")
    store = ContextStore()
    conv = ConversationStore()
    dentists = deepcopy(cats["dentists"])
    store.put("category", "dentists", 1, dentists)
    m001 = deepcopy(merchants["m_001_drmeera_dentist_delhi"])
    store.put("merchant", m001["merchant_id"], 1, m001)
    store.put("trigger", "trg_001_research_digest_dentists", 1, triggers["trg_001_research_digest_dentists"])

    a1 = handle_tick(
        "2026-04-26T10:00:00Z",
        ["trg_001_research_digest_dentists"],
        store,
        ConversationStore(),
    )
    check("v1 digest send", len(a1) == 1 and "JIDA" in a1[0].body)

    # Bump category with a new digest item + retarget trigger
    new_item = {
        "id": "d_2026W18_new_protocol",
        "kind": "research",
        "title": "Weekly chlorhexidine rinse protocol cuts peri-implant mucositis",
        "source": "IDJ May 2026, p.8",
        "trial_n": 640,
        "patient_segment": "implant_patients",
        "summary": "640-patient trial: weekly rinse protocol reduced mucositis markers 29%.",
        "actionable": "Flag implant patients for rinse counseling.",
    }
    dentists_v2 = deepcopy(dentists)
    dentists_v2["digest"] = [new_item] + list(dentists_v2.get("digest") or [])
    store.put("category", "dentists", 2, dentists_v2)

    trg_v2 = deepcopy(triggers["trg_001_research_digest_dentists"])
    trg_v2["payload"] = {
        "category": "dentists",
        "top_item_id": "d_2026W18_new_protocol",
    }
    trg_v2["suppression_key"] = "research:dentists:2026-W18"
    store.put("trigger", "trg_001_research_digest_dentists", 2, trg_v2)

    a2 = handle_tick(
        "2026-04-26T10:10:00Z",
        ["trg_001_research_digest_dentists"],
        store,
        ConversationStore(),
    )
    body2 = a2[0].body if a2 else ""
    check(
        "v2 digest uses new item",
        len(a2) == 1
        and ("IDJ" in body2 or "chlorhexidine" in body2.lower() or "mucositis" in body2.lower()),
        body2[:120],
    )

    # Performance bump
    m002 = deepcopy(merchants["m_002_bharat_dentist_mumbai"])
    store.put("merchant", m002["merchant_id"], 1, m002)
    store.put("trigger", "trg_004_perf_dip_bharat", 1, triggers["trg_004_perf_dip_bharat"])
    store.put("category", m002["category_slug"], 1, cats[m002["category_slug"]])

    before = compose(
        cats[m002["category_slug"]],
        m002,
        triggers["trg_004_perf_dip_bharat"],
        None,
    )
    m002_v2 = deepcopy(m002)
    perf = m002_v2.setdefault("performance", {})
    # Force a distinctive number into performance for the bump
    if "calls" in perf:
        perf["calls"] = 42
    elif "views" in perf:
        perf["views"] = 42
    else:
        perf["ctr"] = 0.042
    # Also stamp a signal the deterministic path often surfaces
    m002_v2["performance"] = perf
    # Put distinctive metric in a field compose cites for perf_dip
    payload_metrics = json.dumps(m002_v2.get("performance") or {})
    check("perf payload mutable", "42" in payload_metrics or "0.042" in payload_metrics)

    store.put("merchant", m002["merchant_id"], 2, m002_v2)
    latest = store.get_merchant(m002["merchant_id"])
    after = compose(
        store.get_category(m002["category_slug"]) or cats[m002["category_slug"]],
        latest or m002_v2,
        triggers["trg_004_perf_dip_bharat"],
        None,
    )
    # At minimum latest store read must differ from v1 snapshot when numbers change
    check(
        "latest merchant version served",
        (latest or {}).get("performance") == m002_v2.get("performance"),
    )
    check("perf compose still non-empty", bool(after.get("body")) and bool(before.get("body")))

    # Mid-test customer + recall
    recall_id = "trg_003_recall_due_priya"
    store.put("trigger", recall_id, 1, triggers[recall_id])
    store.put("merchant", m001["merchant_id"], 1, m001)
    # Ensure category present
    store.put("category", "dentists", 2, dentists_v2)
    # No customer yet
    miss = handle_tick(
        "2026-04-26T11:00:00Z",
        [recall_id],
        store,
        ConversationStore(),
    )
    check("recall skipped without customer", miss == [])

    cust = customers["c_001_priya_for_m001"]
    store.put("customer", cust["customer_id"], 1, cust)
    hit = handle_tick(
        "2026-04-26T11:01:00Z",
        [recall_id],
        store,
        ConversationStore(),
    )
    check(
        "recall after customer push",
        len(hit) == 1 and "Priya" in hit[0].body,
        hit[0].body[:100] if hit else "",
    )

    print("=== E.2 Latency / reliability ===")
    check("prompt frozen flag", COMPOSER_PROMPT_FROZEN is True)
    check("prompt version set", COMPOSER_PROMPT_VERSION == "composer_v1", COMPOSER_PROMPT_VERSION)
    check("tick action cap ≤5", MAX_TICK_ACTIONS <= 5, str(MAX_TICK_ACTIONS))

    # Soft deadline: zero budget → immediate soft stop (partial/empty list)
    import bot.config as cfg

    old_deadline = cfg.TICK_DEADLINE_SECONDS
    try:
        cfg.TICK_DEADLINE_SECONDS = 0
        t0 = time.monotonic()
        partial = handle_tick(
            "2026-04-26T12:00:00Z",
            ["trg_001_research_digest_dentists", "trg_004_perf_dip_bharat"],
            store,
            ConversationStore(),
        )
        elapsed = time.monotonic() - t0
        check(
            "soft deadline returns quickly / empty",
            elapsed < 2.0 and isinstance(partial, list) and len(partial) == 0,
            f"elapsed={elapsed:.3f}s n={len(partial)}",
        )
    finally:
        cfg.TICK_DEADLINE_SECONDS = old_deadline

    from bot.app import healthz
    import asyncio

    hz = asyncio.run(healthz())
    check("healthz ok", hz.status == "ok" and "category" in hz.contexts_loaded)

    print("=== E.3 Submission freeze ===")
    sub_path = ROOT / "submission.jsonl"
    check("submission.jsonl exists", sub_path.is_file())
    lines = [ln for ln in sub_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    check("30 lines", len(lines) == 30, str(len(lines)))
    required = {"test_id", "body", "cta", "send_as", "suppression_key", "rationale"}
    schema_ok = True
    ids = []
    for ln in lines:
        obj = json.loads(ln)
        ids.append(obj.get("test_id"))
        if not required.issubset(obj.keys()) or not obj.get("body"):
            schema_ok = False
            break
    check("schema complete", schema_ok)
    check("test_ids T01..T30-ish", len(set(ids)) == 30 and ids[0] == "T01", str(ids[:3]))

    # Determinism: regenerate twice to temp files
    with tempfile.TemporaryDirectory() as td:
        out1 = Path(td) / "a.jsonl"
        out2 = Path(td) / "b.jsonl"
        env = dict(**__import__("os").environ)
        env["COMPOSER_FORCE_DETERMINISTIC"] = "1"
        env.pop("LLM_API_KEY", None)  # belt-and-suspenders for freeze determinism
        cmd = [
            sys.executable,
            "-m",
            "bot.compose_offline",
            "--dataset",
            str(ROOT / "dataset/expanded"),
            "--out",
        ]
        r1 = subprocess.run(
            cmd + [str(out1)], cwd=str(ROOT), capture_output=True, text=True, env=env
        )
        r2 = subprocess.run(
            cmd + [str(out2)], cwd=str(ROOT), capture_output=True, text=True, env=env
        )
        check("regen run1 ok", r1.returncode == 0, r1.stderr[-200:])
        check("regen run2 ok", r2.returncode == 0, r2.stderr[-200:])
        if r1.returncode == 0 and r2.returncode == 0:
            check("determinism identical", out1.read_text() == out2.read_text())

    print("=== E.4 Metadata / docs ===")
    check("root README exists", (ROOT / "README.md").is_file())
    check("Dockerfile exists", (ROOT / "Dockerfile").is_file())
    from bot import config as bot_config

    check("metadata approach non-empty", bool(bot_config.APPROACH))
    check("metadata version", bool(bot_config.BOT_VERSION))

    print()
    if fails:
        print(f"Phase E smoke FAILED ({fails} checks)")
        return 1
    print("Phase E smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
