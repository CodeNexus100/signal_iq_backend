"""Graph-safe signal timing engine.

Uses Section 7 aggregation (via congestion logic), Section 8
congestion detection, and Section 10 coordination.
"""
import logging
from typing import Dict, Optional, Set

from fastapi import APIRouter

from .congestion_models import CongestionLevel
from .congestion_routes import get_congestion
from .signal_coordination import (
    compute_coordinated_axis,
    get_downstream_intersection_ids,
)
from .signal_models import SignalTimingResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Base timing constants (seconds)
BASE_GREEN_TIME = 30
MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
CYCLE_TIME = 90

# Extra green by congestion level (before safety clamping)
LEVEL_EXTENSION = {
    CongestionLevel.LOW: 0,
    CongestionLevel.MEDIUM: 10,
    CongestionLevel.HIGH: 20,
}

# In-memory signal phase state: intersection_id -> active_axis ("X" or "Z")
# Backend owns phase state; initialized deterministically on first request.
signal_phase_state: Dict[str, str] = {}

# Last returned active_axis per intersection. Only log coordination when it changes.
_last_active_axis_cache: Dict[str, str] = {}


async def _get_signal_timing_internal(
    intersection_id: str,
    _computing: Optional[Set[str]] = None,
) -> SignalTimingResponse:
    """Internal implementation with cycle detection for coordination recursion."""
    if _computing is None:
        _computing = set()
    if intersection_id in _computing:
        return await _get_local_signal_timing(intersection_id)
    _computing.add(intersection_id)
    try:
        return await _get_signal_timing_impl(intersection_id, _computing)
    finally:
        _computing.discard(intersection_id)


async def _get_local_signal_timing(intersection_id: str) -> SignalTimingResponse:
    """Return local timing and phase only (no coordination). Used for cycle break."""
    congestion = await get_congestion(intersection_id)
    level = congestion.level
    downstream_blocked = congestion.downstream_blocked

    extension = LEVEL_EXTENSION.get(level, 0)
    green_time = BASE_GREEN_TIME + extension
    if downstream_blocked:
        green_time = MIN_GREEN_TIME
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
    red_time = max(CYCLE_TIME - green_time, 0)

    if intersection_id not in signal_phase_state:
        signal_phase_state[intersection_id] = "X"
    active_axis = signal_phase_state[intersection_id]

    return SignalTimingResponse(
        intersection_id=intersection_id,
        active_axis=active_axis,
        green_time=green_time,
        red_time=red_time,
        level=level,
        downstream_blocked=downstream_blocked,
    )


async def _get_signal_timing_impl(
    intersection_id: str,
    _computing: Set[str],
) -> SignalTimingResponse:
    """Compute timing, apply coordination, return response."""
    congestion = await get_congestion(intersection_id)
    level = congestion.level
    downstream_blocked = congestion.downstream_blocked

    extension = LEVEL_EXTENSION.get(level, 0)
    green_time = BASE_GREEN_TIME + extension
    if downstream_blocked:
        green_time = MIN_GREEN_TIME
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
    red_time = max(CYCLE_TIME - green_time, 0)

    if intersection_id not in signal_phase_state:
        signal_phase_state[intersection_id] = "X"
    local_active_axis = signal_phase_state[intersection_id]

    # Section 10: Apply coordination
    # Reuse downstream signal response (includes downstream_blocked); avoid redundant get_congestion.
    downstream_ids = await get_downstream_intersection_ids(intersection_id)
    downstream_states = []
    for d_id in downstream_ids:
        try:
            sig_d = await _get_signal_timing_internal(d_id, _computing)
            downstream_states.append({
                "intersection_id": d_id,
                "downstream_blocked": sig_d.downstream_blocked,
                "active_axis": sig_d.active_axis,
            })
        except Exception:
            continue

    active_axis, reason, inherited_from = compute_coordinated_axis(
        local_active_axis, downstream_states
    )

    # Only log when active_axis actually changes
    prev_axis = _last_active_axis_cache.get(intersection_id)
    if prev_axis is None or prev_axis != active_axis:
        _last_active_axis_cache[intersection_id] = active_axis
        logger.info(
            "[SignalCoordination] intersection=%s reason=%s inherited_from=%s active_axis=%s",
            intersection_id,
            reason,
            inherited_from or "-",
            active_axis,
        )

    return SignalTimingResponse(
        intersection_id=intersection_id,
        active_axis=active_axis,
        green_time=green_time,
        red_time=red_time,
        level=level,
        downstream_blocked=downstream_blocked,
    )


@router.get("/signal/{intersection_id}", response_model=SignalTimingResponse)
async def get_signal_timing(intersection_id: str) -> SignalTimingResponse:
    """Graph-safe signal timing based on congestion, downstream blocking, and coordination.

    - Base green is adjusted by congestion level.
    - If downstream is blocked, force MIN_GREEN to avoid spillback.
    - Green time is clamped within [MIN_GREEN_TIME, MAX_GREEN_TIME].
    - Section 10: active_axis coordinated with downstream (green-wave).
    """
    return await _get_signal_timing_internal(intersection_id)

