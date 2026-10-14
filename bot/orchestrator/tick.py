"""Tick handler — rank, consent, compose with soft deadline (Phase E)."""

from __future__ import annotations

import logging
import time

from bot import config
from bot.composer.composer import compose
from bot.composer.helpers.consent import consent_allows
from bot.models import TickAction
from bot.orchestrator.suppression import (
    merchant_is_blocked,
    parse_expired,
    rank_score,
)
from bot.store.context_store import ContextStore
from bot.store.conversation_store import ConversationStore

logger = logging.getLogger(__name__)

# Leave headroom so the HTTP response still clears the judge's 30s budget.
_DEADLINE_HEADROOM_SECONDS = 1.5


def handle_tick(
    now: str,
    available_triggers: list[str],
    contexts: ContextStore,
    conversations: ConversationStore,
) -> list[TickAction]:
    started = time.monotonic()
    deadline = started + float(config.TICK_DEADLINE_SECONDS)

    candidates: list[tuple[int, str]] = []

    for trg_id in available_triggers:
        trigger = contexts.get_trigger(trg_id)
        if not trigger:
            continue
        if parse_expired(trigger.get("expires_at"), now):
            continue

        suppression_key = trigger.get("suppression_key") or ""
        if conversations.is_suppression_used(suppression_key):
            continue

        merchant_id = trigger.get("merchant_id")
        if not merchant_id:
            continue
        if merchant_is_blocked(merchant_id, conversations, now=now):
            continue

        merchant = contexts.get_merchant(merchant_id)
        if not merchant:
            continue

        category_slug = merchant.get("category_slug")
        if not category_slug:
            continue
        category = contexts.get_category(category_slug)
        if not category:
            continue

        customer = None
        customer_id = trigger.get("customer_id")
        if trigger.get("scope") == "customer":
            if not customer_id:
                continue
            customer = contexts.get_customer(customer_id)
            if not customer:
                continue
            if not consent_allows(trigger, customer):
                continue

        score = rank_score(trigger, merchant)
        candidates.append((score, trg_id))

    # Highest score first; stable tie-break by trigger id
    candidates.sort(key=lambda x: (-x[0], x[1]))

    actions: list[TickAction] = []
    seen_merchants: set[str] = set()

    for score, trg_id in candidates:
        if len(actions) >= config.MAX_TICK_ACTIONS:
            break
        # Soft deadline: return partial list rather than risk judge timeout
        if time.monotonic() >= deadline - _DEADLINE_HEADROOM_SECONDS:
            logger.warning(
                "tick soft-deadline hit after %d action(s); returning partial",
                len(actions),
            )
            break

        # Always re-read latest store versions immediately before compose (E.1)
        trigger = contexts.get_trigger(trg_id)
        if not trigger:
            continue
        merchant_id = trigger.get("merchant_id")
        if not merchant_id or merchant_id in seen_merchants:
            continue
        merchant = contexts.get_merchant(merchant_id)
        if not merchant:
            continue
        category_slug = merchant.get("category_slug")
        if not category_slug:
            continue
        category = contexts.get_category(category_slug)
        if not category:
            continue

        customer = None
        customer_id = trigger.get("customer_id")
        if trigger.get("scope") == "customer":
            if not customer_id:
                continue
            customer = contexts.get_customer(customer_id)
            if not customer:
                continue
            if not consent_allows(trigger, customer):
                continue

        try:
            composed = compose(category, merchant, trigger, customer)
        except Exception as exc:
            logger.warning("compose failed for %s: %s — skipping", trg_id, exc)
            continue

        kind = (trigger.get("kind") or "nudge").replace(" ", "_")
        conversation_id = f"conv_{merchant_id}_{kind}"
        if conversations.get(conversation_id) is not None:
            conversation_id = f"{conversation_id}_{trg_id}"

        suppression_key = trigger.get("suppression_key") or ""
        action = TickAction(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            send_as=composed["send_as"],
            trigger_id=trg_id,
            template_name=composed.get("template_name") or f"vera_{kind}_v1",
            template_params=list(composed.get("template_params") or []),
            body=composed["body"],
            cta=composed["cta"],
            suppression_key=composed["suppression_key"] or suppression_key,
            rationale=composed["rationale"] + f" [rank={score}]",
        )
        actions.append(action)
        seen_merchants.add(merchant_id)

        conversations.create(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            trigger_id=trg_id,
            send_as=composed["send_as"],
            suppression_key=action.suppression_key,
            first_body=action.body,
        )

    return actions
