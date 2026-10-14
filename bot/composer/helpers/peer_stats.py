"""Peer benchmark framing from real numbers only."""

from __future__ import annotations

from typing import Any, Optional


def peer_ctr_framing(
    merchant: dict[str, Any],
    category: dict[str, Any],
) -> Optional[str]:
    perf = merchant.get("performance") or {}
    peer = category.get("peer_stats") or {}
    ctr = perf.get("ctr")
    peer_ctr = peer.get("avg_ctr")
    if ctr is None or peer_ctr is None:
        return None
    try:
        ctr_f = float(ctr)
        peer_f = float(peer_ctr)
    except (TypeError, ValueError):
        return None
    if ctr_f < peer_f:
        return f"your CTR {ctr_f:.1%} is below peer ~{peer_f:.1%}"
    if ctr_f > peer_f:
        return f"your CTR {ctr_f:.1%} is ahead of peer ~{peer_f:.1%}"
    return f"your CTR {ctr_f:.1%} is in line with peers"
