"""
Optional offline tiebreaker for multi-turn reply (Phase D).

Keeps `respond(state, merchant_message)` in sync with `/v1/reply` behavior.
"""

from __future__ import annotations

from typing import Any, Union

from bot.models import ReplyEndResponse, ReplySendResponse, ReplyWaitResponse
from bot.orchestrator.reply import handle_reply
from bot.store.conversation_store import ConversationState, ConversationStore

ReplyResponse = Union[ReplySendResponse, ReplyWaitResponse, ReplyEndResponse]


def respond(
    state: ConversationState,
    merchant_message: str,
    *,
    received_at: str = "2026-04-26T12:00:00Z",
    turn_number: int | None = None,
    conversations: ConversationStore | None = None,
    contexts: Any = None,
) -> dict[str, Any]:
    """
    Continue a conversation given an in-memory ConversationState + inbound text.

    Returns a plain dict matching the `/v1/reply` JSON shape.
    """
    store = conversations or ConversationStore()
    # Ensure the provided state is the one the store mutates
    store._data[state.conversation_id] = state  # noqa: SLF001

    next_turn = turn_number if turn_number is not None else len(state.turns) + 1
    result = handle_reply(
        conversation_id=state.conversation_id,
        merchant_id=state.merchant_id or None,
        customer_id=state.customer_id,
        from_role="merchant",
        message=merchant_message,
        received_at=received_at,
        turn_number=next_turn,
        conversations=store,
        contexts=contexts,
    )
    if isinstance(result, ReplySendResponse):
        return {
            "action": "send",
            "body": result.body,
            "cta": result.cta,
            "rationale": result.rationale,
        }
    if isinstance(result, ReplyWaitResponse):
        return {
            "action": "wait",
            "wait_seconds": result.wait_seconds,
            "rationale": result.rationale,
        }
    return {"action": "end", "rationale": result.rationale}
