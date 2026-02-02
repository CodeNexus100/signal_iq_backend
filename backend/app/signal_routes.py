"""Graph-safe signal timing engine.

Uses Section 7 aggregation (via congestion logic) and Section 8
congestion detection to compute safe signal timings.
"""
import logging
from typing import Dict

from fastapi import APIRouter

from .congestion_models import CongestionLevel
from .congestion_routes import get_congestion
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


@router.get("/signal/{intersection_id}", response_model=SignalTimingResponse)
async def get_signal_timing(intersection_id: str) -> SignalTimingResponse:
    """Graph-safe signal timing based on congestion and downstream blocking.

    - Base green is adjusted by congestion level.
    - If downstream is blocked, force MIN_GREEN to avoid spillback.
    - Green time is clamped within [MIN_GREEN_TIME, MAX_GREEN_TIME].
    - Red time is derived from a fixed cycle time.
    """
    # Use Section 8 graph-aware congestion detection
    congestion = await get_congestion(intersection_id)
    level = congestion.level
    downstream_blocked = congestion.downstream_blocked

    # Start from base green and extend based on congestion level
    extension = LEVEL_EXTENSION.get(level, 0)
    green_time = BASE_GREEN_TIME + extension

    # If downstream is blocked, be conservative: force minimum green
    if downstream_blocked:
        green_time = MIN_GREEN_TIME

    # Enforce safety bounds
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))

    # Derive red time from cycle; never negative
    red_time = max(CYCLE_TIME - green_time, 0)

    # Get or initialize active_axis (deterministic: first request sets to "X")
    if intersection_id not in signal_phase_state:
        signal_phase_state[intersection_id] = "X"
        logger.info("Initialized signal phase for intersection_id=%s: active_axis=X", intersection_id)

    active_axis = signal_phase_state[intersection_id]

    logger.info(
        "Signal timing decision: intersection_id=%s, active_axis=%s, level=%s, "
        "downstream_blocked=%s, green_time=%s, red_time=%s",
        intersection_id,
        active_axis,
        level.value,
        downstream_blocked,
        green_time,
        red_time,
    )

    return SignalTimingResponse(
        intersection_id=intersection_id,
        active_axis=active_axis,
        green_time=green_time,
        red_time=red_time,
        level=level,
        downstream_blocked=downstream_blocked,
    )

