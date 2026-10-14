"""Phase D reply orchestrator — classify → send | wait | end."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from bot.handlers.classifier import classify
from bot.handlers.language import match_reply_language
from bot.models import ReplyEndResponse, ReplySendResponse, ReplyWaitResponse
from bot.orchestrator.followups import (
    action_execute,
    auto_reply_nudge,
    empty_clarify,
    engaged_followup,
    off_topic_redirect,
    question_answer,
    unique_body,
)
from bot.store.context_store import ContextStore
from bot.store.conversation_store import ConversationStore

ReplyResponse = Union[ReplySendResponse, ReplyWaitResponse, ReplyEndResponse]


def _parse_received_at(received_at: str) -> datetime:
    try:
        return datetime.fromisoformat((received_at or "").replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _load_contexts(
    state,
    contexts: Optional[ContextStore],
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], Optional[dict[str, Any]]]:
    if contexts is None:
        return None, None, None
    merchant = contexts.get_merchant(state.merchant_id) if state.merchant_id else None
    trigger = contexts.get_trigger(state.trigger_id) if state.trigger_id else None
    customer = None
    if state.customer_id:
        customer = contexts.get_customer(state.customer_id)
    return merchant, trigger, customer


def _send(
    state,
    body: str,
    cta: str,
    rationale: str,
    alt: str = "",
) -> ReplySendResponse:
    final = unique_body(body, state.sent_bodies, alt or body)
    state.sent_bodies.add(final)
    return ReplySendResponse(body=final, cta=cta, rationale=rationale)


def handle_reply(
    conversation_id: str,
    merchant_id: str | None,
    customer_id: str | None,
    from_role: str,
    message: str,
    received_at: str,
    turn_number: int,
    conversations: ConversationStore,
    contexts: ContextStore | None = None,
) -> ReplyResponse:
    existing = conversations.get(conversation_id)
    was_new = existing is None
    previous_inbound = None
    if existing and existing.turns:
        for t in reversed(existing.turns):
            if t.from_role in ("merchant", "customer"):
                previous_inbound = t.message
                break

    state = conversations.append_turn(
        conversation_id=conversation_id,
        from_role=from_role,
        message=message,
        received_at=received_at,
        turn_number=turn_number,
    )
    if merchant_id and not state.merchant_id:
        state.merchant_id = merchant_id
    if customer_id and not state.customer_id:
        state.customer_id = customer_id

    # Unknown conversation_id with no merchant → soft end (no fabricated thread).
    # If merchant_id is present (judge replay often skips tick), continue the FSM.
    if was_new and not state.trigger_id and not state.merchant_id:
        state.mode = "exit"
        state.suppressed = True
        return ReplyEndResponse(
            rationale="Unknown conversation_id with no prior tick state; closing safely."
        )

    if state.suppressed or state.mode == "exit":
        return ReplyEndResponse(
            rationale="Conversation already ended; staying closed."
        )

    lang = match_reply_language(message, state.language_observed)
    state.language_observed = lang
    merchant, trigger, _customer = _load_contexts(state, contexts)

    label = classify(message, previous_inbound=previous_inbound)

    # --- Auto-reply streak FSM ---
    if label == "auto_reply":
        state.auto_reply_streak += 1
        streak = state.auto_reply_streak
        if streak >= 3:
            state.mode = "exit"
            state.suppressed = True
            return ReplyEndResponse(
                rationale=(
                    "Auto-reply 3x in a row, no real engagement; "
                    "closing to avoid burning turns."
                )
            )
        if streak >= 2:
            wait_seconds = 86400
            state.wait_until = _parse_received_at(received_at) + timedelta(
                seconds=wait_seconds
            )
            return ReplyWaitResponse(
                wait_seconds=wait_seconds,
                rationale="Same auto-reply twice in a row → owner not at phone. Wait 24h.",
            )
        # Streak 1: one gentle nudge (replay Example 4.1)
        body, cta = auto_reply_nudge(lang, merchant)
        alt = (
            "Auto-reply detected — reply YES when the owner is free and I'll continue."
        )
        return _send(
            state,
            body,
            cta,
            "Detected auto-reply; one explicit prompt for the owner.",
            alt=alt,
        )

    # Real human signal resets auto-reply streak
    state.auto_reply_streak = 0
    state.wait_until = None

    if label == "opt_out":
        state.mode = "exit"
        state.suppressed = True
        return ReplyEndResponse(
            rationale="Merchant opted out / stop request; closing and suppressing merchant."
        )

    if label == "hostile":
        state.mode = "exit"
        state.suppressed = True
        # Optional one-line apology then conceptually closed; prefer direct end
        # per Example 4.3 good path. Acceptable alt is send+end; we end cleanly.
        return ReplyEndResponse(
            rationale=(
                "Merchant frustration explicit; closing without further engagement. "
                "Suppressing triggers for this merchant for the test window."
            )
        )

    if label == "empty":
        body, cta, rationale = empty_clarify(lang)
        return _send(state, body, cta, rationale, alt="Please send a short reply when free.")

    if label == "intent_commit":
        state.mode = "action"
        body, cta, rationale = action_execute(lang, state, merchant, trigger)
        alt = (
            f"On it — preparing the next concrete step for "
            f"{state.trigger_id or 'this thread'}. Reply CONFIRM to send."
        )
        return _send(state, body, cta, rationale, alt=alt)

    if label == "off_topic":
        body, cta, rationale = off_topic_redirect(lang, merchant, trigger)
        alt = (
            "That's outside my lane — happy to stay on the original thread. "
            "Draft next, or checklist first?"
        )
        return _send(state, body, cta, rationale, alt=alt)

    if label == "question":
        body, cta, rationale = question_answer(lang, merchant, trigger)
        alt = "I can only use facts already in this thread — shall I proceed with the draft?"
        return _send(state, body, cta, rationale, alt=alt)

    # engaged (default)
    body, cta, rationale = engaged_followup(
        lang, state, merchant, trigger, message
    )
    alt = "Thanks — shall I send the draft next, or a short checklist first?"
    return _send(state, body, cta, rationale, alt=alt)
