"""Section 10: Multi-Intersection Signal Coordination.

Backend-only green-wave coordination. Upstream intersections adapt
active_axis based on downstream congestion and phase state.
"""
import logging
from typing import List, Optional, Tuple

from .database import get_database

logger = logging.getLogger(__name__)

ROADS_COLL = "roads"


async def get_downstream_intersection_ids(intersection_id: str) -> List[str]:
    """Get intersection IDs that are one hop downstream (outgoing roads' targets)."""
    roads = get_database()[ROADS_COLL]
    cursor = roads.find({"from": intersection_id}, {"to": 1})
    docs = await cursor.to_list(length=None)
    return [d["to"] for d in docs]


def compute_coordinated_axis(
    local_active_axis: str,
    downstream_states: List[dict],
) -> Tuple[str, str, Optional[str]]:
    """
    Apply coordination rules. First match wins.
    Returns (active_axis, reason, inherited_from).
    """
    # Rule 1 — Downstream Block Dominance
    for d in downstream_states:
        if d.get("downstream_blocked"):
            axis = d.get("active_axis", "X")
            if axis in ("X", "Z"):
                return (axis, "DOWNSTREAM_BLOCKED", d.get("intersection_id"))

    # Rule 2 — Green-Wave Alignment
    for d in downstream_states:
        axis = d.get("active_axis")
        if axis in ("X", "Z"):
            return (axis, "GREEN_WAVE_ALIGNMENT", d.get("intersection_id"))

    # Rule 3 — Local Default
    return (local_active_axis, "LOCAL_DEFAULT", None)
