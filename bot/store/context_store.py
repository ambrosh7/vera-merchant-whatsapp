"""Versioned in-memory context store for judge `/v1/context` pushes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


@dataclass
class StoredContext:
    version: int
    payload: dict[str, Any]
    stored_at: str


class ContextStore:
    """key = (scope, context_id) → StoredContext. Higher version replaces atomically."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], StoredContext] = {}

    def clear(self) -> int:
        n = len(self._data)
        self._data.clear()
        return n

    def counts(self) -> dict[str, int]:
        out = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
        for scope, _ in self._data:
            if scope in out:
                out[scope] += 1
        return out

    def get(self, scope: str, context_id: str) -> Optional[StoredContext]:
        return self._data.get((scope, context_id))

    def get_payload(self, scope: str, context_id: str) -> Optional[dict[str, Any]]:
        item = self.get(scope, context_id)
        return deepcopy(item.payload) if item else None

    def put(
        self,
        scope: str,
        context_id: str,
        version: int,
        payload: dict[str, Any],
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """
        Store payload if version is newer.

        Returns:
            (accepted, current_version_if_rejected, stored_at_if_accepted)
        """
        key = (scope, context_id)
        cur = self._data.get(key)
        if cur is not None and cur.version >= version:
            return False, cur.version, None

        stored_at = _utc_now_iso()
        self._data[key] = StoredContext(
            version=version,
            payload=deepcopy(payload),
            stored_at=stored_at,
        )
        return True, None, stored_at

    # --- convenience indexes for Phase A tick joins ---

    def get_category(self, slug: str) -> Optional[dict[str, Any]]:
        return self.get_payload("category", slug)

    def get_merchant(self, merchant_id: str) -> Optional[dict[str, Any]]:
        return self.get_payload("merchant", merchant_id)

    def get_customer(self, customer_id: str) -> Optional[dict[str, Any]]:
        return self.get_payload("customer", customer_id)

    def get_trigger(self, trigger_id: str) -> Optional[dict[str, Any]]:
        return self.get_payload("trigger", trigger_id)
