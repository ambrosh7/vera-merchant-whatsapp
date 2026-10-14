"""Deterministic multi-turn follow-up bodies (Phase D) — no LLM required."""

from __future__ import annotations

from typing import Any, Optional

from bot.handlers.language import Lang
from bot.store.conversation_store import ConversationState


def _owner(merchant: Optional[dict[str, Any]]) -> str:
    if not merchant:
        return "there"
    ident = merchant.get("identity") or {}
    return ident.get("owner_first_name") or ident.get("name") or "there"


def _biz(merchant: Optional[dict[str, Any]]) -> str:
    if not merchant:
        return "your business"
    return (merchant.get("identity") or {}).get("name") or "your business"


def _trigger_hook(trigger: Optional[dict[str, Any]]) -> str:
    if not trigger:
        return "the earlier note"
    kind = (trigger.get("kind") or "nudge").replace("_", " ")
    payload = trigger.get("payload") or {}
    if kind == "research digest":
        return "the research digest thread"
    if "ipl" in kind:
        match = payload.get("match") or "tonight's match"
        return f"the {match} plan"
    if "planning" in kind:
        return "the planning draft"
    if "recall" in kind or "appointment" in kind:
        return "the booking follow-up"
    if "perf" in kind or "seasonal" in kind:
        return "the performance note"
    return f"the {kind} thread"


def unique_body(candidate: str, sent: set[str], alt: str) -> str:
    if candidate not in sent:
        return candidate
    if alt not in sent:
        return alt
    # Last resort: append a short differentiator without inventing facts
    n = 2
    while True:
        tagged = f"{alt} ({n})"
        if tagged not in sent:
            return tagged
        n += 1


def auto_reply_nudge(lang: Lang, merchant: Optional[dict[str, Any]]) -> tuple[str, str]:
    name = _owner(merchant)
    if lang in ("hi", "hi-en"):
        body = (
            f"Lagta hai ye auto-reply hai, {name}. "
            "Jab aap personally dekho to bas 'Yes' reply kar dena — main wait karungi."
        )
    else:
        body = (
            f"Looks like an auto-reply, {name}. "
            "When the owner sees this, just reply Yes and I'll continue."
        )
    return body, "binary_yes_no"


def action_execute(
    lang: Lang,
    state: ConversationState,
    merchant: Optional[dict[str, Any]],
    trigger: Optional[dict[str, Any]],
) -> tuple[str, str, str]:
    """Concrete next step — never another qualifying question."""
    name = _owner(merchant)
    hook = _trigger_hook(trigger)
    kind = (trigger.get("kind") if trigger else "") or ""
    payload = (trigger.get("payload") if trigger else {}) or {}

    if "research" in kind or "digest" in kind:
        if lang in ("hi", "hi-en"):
            body = (
                f"Done, {name}. Abstract draft ready in ~90s. "
                "Patient WhatsApp + GBP post draft bhi bana rahi hoon — "
                "CONFIRM reply karo to patient list pe schedule karungi."
            )
        else:
            body = (
                f"Great, {name}. Drafting the abstract now (~90s). "
                "I'll also pre-fill the patient WhatsApp + GBP post. "
                "Reply CONFIRM to send the WhatsApp draft to your high-risk patient list."
            )
        return body, "binary_confirm_cancel", "Merchant committed; executing digest follow-through."

    if "planning" in kind:
        topic = payload.get("topic") or payload.get("intent") or "package"
        body = (
            f"Locked in, {name}. Drafting the {topic} outline now — "
            "scope, pricing band from your active offers, and a sample WhatsApp. "
            "Reply CONFIRM and I'll deliver the full draft next."
        )
        return body, "binary_confirm_cancel", "Planning intent committed; delivering artifact path."

    if lang in ("hi", "hi-en"):
        body = (
            f"Theek hai {name} — ab action mode. "
            f"{hook} ke liye next step execute kar rahi hoon. "
            "CONFIRM bolo to draft bhej deti hoon."
        )
    else:
        body = (
            f"Perfect, {name}. Switching to action on {hook}. "
            "I'll prepare the concrete draft now — reply CONFIRM to send it."
        )
    return body, "binary_confirm_cancel", "Explicit commit; action mode, no more qualification."


def engaged_followup(
    lang: Lang,
    state: ConversationState,
    merchant: Optional[dict[str, Any]],
    trigger: Optional[dict[str, Any]],
    inbound: str,
) -> tuple[str, str, str]:
    name = _owner(merchant)
    hook = _trigger_hook(trigger)
    if state.mode == "action":
        return action_execute(lang, state, merchant, trigger)

    # Soft engagement — one clear binary path, no Vera re-intro
    if lang in ("hi", "hi-en"):
        body = (
            f"Samajh gayi, {name}. {hook} pe aage badhte hain — "
            "abstract/draft bhejoon, ya pehle short checklist?"
        )
    else:
        body = (
            f"Got it, {name}. On {hook}: should I send the draft next, "
            "or a 3-bullet checklist first?"
        )
    rationale = "Merchant engaged; advancing with a binary next step (still qualify, not action)."
    return body, "binary_yes_no", rationale


def off_topic_redirect(
    lang: Lang,
    merchant: Optional[dict[str, Any]],
    trigger: Optional[dict[str, Any]],
) -> tuple[str, str, str]:
    hook = _trigger_hook(trigger)
    if lang in ("hi", "hi-en"):
        body = (
            "GST/filing meri lane nahi — woh aapke CA ke saath best rahega. "
            f"Wapas {hook} pe: draft pehle bhejoon, ya abstract?"
        )
    else:
        body = (
            "I'll leave GST filing to your CA — outside what I can help with directly. "
            f"Coming back to {hook}: want the draft first, or the abstract?"
        )
    return body, "open_ended", "Off-topic declined; redirected to original trigger thread."


def question_answer(
    lang: Lang,
    merchant: Optional[dict[str, Any]],
    trigger: Optional[dict[str, Any]],
) -> tuple[str, str, str]:
    """Honest brief answer without fabricating numbers not in context."""
    hook = _trigger_hook(trigger)
    biz = _biz(merchant)
    body = (
        f"Fair question on {biz}. I only use the facts already in this thread for {hook} — "
        "I don't have extra numbers beyond what was shared. "
        "Want me to proceed with the draft from those facts?"
    )
    return body, "binary_yes_no", "On-topic question; answered without inventing data."


def hostile_apology(lang: Lang) -> tuple[str, str]:
    if lang in ("hi", "hi-en"):
        body = "Maaf kijiye — ab message nahi bhejungi. Agar baad mein chahiye ho to 'Hi' likh dena."
    else:
        body = (
            "Apologies — I won't message again. "
            "If anything changes, you can always restart with 'Hi'."
        )
    return body, "none"


def empty_clarify(lang: Lang) -> tuple[str, str, str]:
    if lang in ("hi", "hi-en"):
        body = "Message blank lag raha hai — ek short reply de dena jab free ho."
    else:
        body = "Looks like an empty message — reply briefly whenever you're free."
    return body, "open_ended", "Empty inbound; one gentle clarify."
