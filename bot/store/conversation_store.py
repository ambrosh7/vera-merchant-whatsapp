"""In-memory conversation state for multi-turn `/v1/reply` (Phase D)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional


@dataclass
class Turn:
    from_role: str
    message: str
    received_at: str
    turn_number: int


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    trigger_id: str
    send_as: Literal["vera", "merchant_on_behalf"]
    turns: list[Turn] = field(default_factory=list)
    sent_bodies: set[str] = field(default_factory=set)
    auto_reply_streak: int = 0
    mode: Literal["qualify", "action", "exit"] = "qualify"
    suppressed: bool = False
    wait_until: Optional[datetime] = None
    language_observed: Optional[str] = None
    suppression_key: str = ""


class ConversationStore:
    def __init__(self) -> None:
        self._data: dict[str, ConversationState] = {}
        self._used_suppression_keys: dict[str, str] = {}  # key → conversation_id

    def clear(self) -> int:
        n = len(self._data)
        self._data.clear()
        self._used_suppression_keys.clear()
        return n

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        return self._data.get(conversation_id)

    def create(
        self,
        conversation_id: str,
        merchant_id: str,
        customer_id: Optional[str],
        trigger_id: str,
        send_as: Literal["vera", "merchant_on_behalf"],
        suppression_key: str = "",
        first_body: str = "",
    ) -> ConversationState:
        state = ConversationState(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            trigger_id=trigger_id,
            send_as=send_as,
            suppression_key=suppression_key,
        )
        if first_body:
            state.sent_bodies.add(first_body)
        self._data[conversation_id] = state
        if suppression_key:
            self._used_suppression_keys[suppression_key] = conversation_id
        return state

    def append_turn(
        self,
        conversation_id: str,
        from_role: str,
        message: str,
        received_at: str,
        turn_number: int,
    ) -> ConversationState:
        state = self._data.get(conversation_id)
        if state is None:
            state = ConversationState(
                conversation_id=conversation_id,
                merchant_id="",
                customer_id=None,
                trigger_id="",
                send_as="vera",
            )
            self._data[conversation_id] = state
        state.turns.append(
            Turn(
                from_role=from_role,
                message=message,
                received_at=received_at,
                turn_number=turn_number,
            )
        )
        return state

    def is_suppression_used(self, suppression_key: str) -> bool:
        if not suppression_key:
            return False
        return suppression_key in self._used_suppression_keys

    def mark_suppression(self, suppression_key: str, conversation_id: str) -> None:
        if suppression_key:
            self._used_suppression_keys[suppression_key] = conversation_id

    def snapshot(self, conversation_id: str) -> Optional[dict[str, Any]]:
        state = self.get(conversation_id)
        if not state:
            return None
        return {
            "conversation_id": state.conversation_id,
            "merchant_id": state.merchant_id,
            "customer_id": state.customer_id,
            "trigger_id": state.trigger_id,
            "send_as": state.send_as,
            "mode": state.mode,
            "suppressed": state.suppressed,
            "auto_reply_streak": state.auto_reply_streak,
            "turn_count": len(state.turns),
        }
