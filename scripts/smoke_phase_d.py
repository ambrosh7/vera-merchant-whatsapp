#!/usr/bin/env python3
"""Phase D smoke: auto-reply hell, intent transition, hostile, anti-repetition."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.orchestrator.reply import handle_reply  # noqa: E402
from bot.orchestrator.suppression import merchant_is_blocked  # noqa: E402
from bot.store.context_store import ContextStore  # noqa: E402
from bot.store.conversation_store import ConversationStore  # noqa: E402
from conversation_handlers import respond  # noqa: E402


def _seed_contexts() -> ContextStore:
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
    triggers = {
        t["id"]: t
        for t in json.loads((ROOT / "dataset/triggers_seed.json").read_text())[
            "triggers"
        ]
    }
    ctx = ContextStore()
    for slug, payload in cats.items():
        ctx.put("category", slug, 1, payload)
    for mid, payload in merchants.items():
        ctx.put("merchant", mid, 1, payload)
    for tid, payload in triggers.items():
        ctx.put("trigger", tid, 1, payload)
    return ctx


def _open_conv(
    conversations: ConversationStore,
    *,
    cid: str,
    merchant_id: str,
    trigger_id: str,
    body: str = "Initial outreach about this week's opportunity.",
) -> None:
    conversations.create(
        conversation_id=cid,
        merchant_id=merchant_id,
        customer_id=None,
        trigger_id=trigger_id,
        send_as="vera",
        suppression_key=f"smoke:{cid}",
        first_body=body,
    )


def main() -> int:
    fails = 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            fails += 1

    contexts = _seed_contexts()
    mid = "m_001_drmeera_dentist_delhi"
    tid = "trg_001_research_digest_dentists"
    canned = (
        "Thank you for contacting Dr. Meera's Dental Clinic! "
        "Our team will respond shortly."
    )

    print("=== S1 Auto-reply hell ===")
    convs = ConversationStore()
    cid = "conv_smoke_autoreply"
    _open_conv(convs, cid=cid, merchant_id=mid, trigger_id=tid)

    r1 = handle_reply(cid, mid, None, "merchant", canned, "2026-04-26T10:00:00Z", 2, convs, contexts)
    check("streak1 send or wait", r1.action in ("send", "wait"), getattr(r1, "action", ""))
    if r1.action == "send":
        check("streak1 mentions auto-reply", "auto-reply" in r1.body.lower() or "yes" in r1.body.lower())

    r2 = handle_reply(cid, mid, None, "merchant", canned, "2026-04-26T10:01:00Z", 3, convs, contexts)
    check("streak2 wait", r2.action == "wait", getattr(r2, "rationale", "")[:80])

    r3 = handle_reply(cid, mid, None, "merchant", canned, "2026-04-26T10:02:00Z", 4, convs, contexts)
    check("streak3 end", r3.action == "end", getattr(r3, "rationale", "")[:80])

    r4 = handle_reply(cid, mid, None, "merchant", "hello again", "2026-04-26T10:03:00Z", 5, convs, contexts)
    check("after end stays ended", r4.action == "end")

    print("=== S2 Intent transition ===")
    convs2 = ConversationStore()
    cid2 = "conv_smoke_intent"
    _open_conv(convs2, cid=cid2, merchant_id=mid, trigger_id=tid)
    eng = handle_reply(
        cid2, mid, None, "merchant",
        "Interesting — tell me more?",
        "2026-04-26T11:00:00Z", 2, convs2, contexts,
    )
    check("engaged is send", eng.action == "send")
    commit = handle_reply(
        cid2, mid, None, "merchant",
        "Ok, let's do it. What's next?",
        "2026-04-26T11:01:00Z", 3, convs2, contexts,
    )
    check("intent → send", commit.action == "send")
    body_l = commit.body.lower() if commit.action == "send" else ""
    check(
        "action mode (no extra qualify)",
        commit.action == "send"
        and ("confirm" in body_l or "draft" in body_l or "preparing" in body_l or "execut" in body_l)
        and "would you say" not in body_l
        and "most of your" not in body_l,
        body_l[:100],
    )
    st = convs2.get(cid2)
    check("mode flipped to action", st is not None and st.mode == "action", st.mode if st else "")

    hi = handle_reply(
        cid2, mid, None, "merchant",
        "haan bhej do",
        "2026-04-26T11:02:00Z", 4, convs2, contexts,
    )
    check("Hindi commit still action send", hi.action == "send")

    print("=== S3 Hostile / opt-out ===")
    convs3 = ConversationStore()
    cid3 = "conv_smoke_hostile"
    _open_conv(convs3, cid=cid3, merchant_id=mid, trigger_id=tid)
    h = handle_reply(
        cid3, mid, None, "merchant",
        "Why are you bothering me. This is useless. Stop sending these.",
        "2026-04-26T12:00:00Z", 2, convs3, contexts,
    )
    check("hostile → end", h.action == "end")
    check("merchant blocked after hostile", merchant_is_blocked(mid, convs3))

    convs4 = ConversationStore()
    cid4 = "conv_smoke_optout"
    _open_conv(convs4, cid=cid4, merchant_id=mid, trigger_id=tid)
    o = handle_reply(
        cid4, mid, None, "merchant",
        "Not interested. Stop messaging me.",
        "2026-04-26T12:10:00Z", 2, convs4, contexts,
    )
    check("opt-out → end", o.action == "end")

    print("=== Off-topic + anti-repetition + unknown ===")
    convs5 = ConversationStore()
    cid5 = "conv_smoke_offtopic"
    _open_conv(convs5, cid=cid5, merchant_id=mid, trigger_id=tid)
    ot = handle_reply(
        cid5, mid, None, "merchant",
        "Btw can you also help me with my GST filing this month?",
        "2026-04-26T13:00:00Z", 2, convs5, contexts,
    )
    check("off-topic send", ot.action == "send")
    if ot.action == "send":
        check("redirects / declines GST", "gst" in ot.body.lower() or "ca" in ot.body.lower())

    # Same engaged template path twice with different inbound → bodies must differ
    convs6 = ConversationStore()
    cid6 = "conv_smoke_antirepeat"
    _open_conv(convs6, cid=cid6, merchant_id=mid, trigger_id=tid, body="PLACEHOLDER")
    a = handle_reply(
        cid6, mid, None, "merchant", "Sounds good, interested.",
        "2026-04-26T14:00:00Z", 2, convs6, contexts,
    )
    assert a.action == "send"
    first_body = a.body
    b = handle_reply(
        cid6, mid, None, "merchant", "Yes I want to hear more about this.",
        "2026-04-26T14:01:00Z", 3, convs6, contexts,
    )
    check(
        "anti-repetition",
        b.action == "send" and b.body != first_body,
        f"{first_body[:40]!r} vs {getattr(b, 'body', '')[:40]!r}",
    )

    unknown = handle_reply(
        "conv_never_opened", None, None, "merchant", "hi",
        "2026-04-26T15:00:00Z", 1, ConversationStore(), contexts,
    )
    check("unknown conversation soft end", unknown.action == "end")

    # Judge-style: merchant_id present, no prior tick → continue FSM (not soft-end)
    judge_style = handle_reply(
        "conv_judge_style", mid, None, "merchant",
        "Ok, let's do it. What's next?",
        "2026-04-26T15:05:00Z", 2, ConversationStore(), contexts,
    )
    check("judge-style reply without tick", judge_style.action == "send")

    print("=== conversation_handlers.respond ===")
    convs7 = ConversationStore()
    cid7 = "conv_smoke_respond"
    _open_conv(convs7, cid=cid7, merchant_id=mid, trigger_id=tid)
    st7 = convs7.get(cid7)
    assert st7
    out = respond(st7, canned, conversations=convs7, contexts=contexts)
    check("respond wrapper action", out.get("action") in ("send", "wait"), str(out.get("action")))

    print()
    if fails:
        print(f"Phase D smoke FAILED ({fails} checks)")
        return 1
    print("Phase D smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
