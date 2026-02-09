"""Graph-safe signal timing engine.

Uses Section 7 aggregation (via congestion logic), Section 8
congestion detection, and Section 10 coordination.
"""
import logging
import random
from typing import Dict, Optional, Set

from fastapi import APIRouter

from .congestion_models import CongestionLevel
from .signal_models import SignalTimingResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Base timing constants (seconds)
BASE_GREEN_TIME = 30
MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
CYCLE_TIME = 90

# In-memory signal phase state: intersection_id -> active_axis ("X" or "Z")
# Backend owns phase state; initialized deterministically on first request.
signal_phase_state: Dict[str, str] = {}


@router.get("/signal/{intersection_id}", response_model=SignalTimingResponse)
async def get_signal_timing(intersection_id: str) -> SignalTimingResponse:
    """Graph-safe signal timing based on congestion, downstream blocking, and coordination.
    
    DEMO VERSION: Returns dummy data with random toggling for visualization.
    """
    
    try:
        # Dummy logic for demo purposes as requested
        # Randomly toggle active axis sometimes or keep it stable
        if intersection_id not in signal_phase_state:
            signal_phase_state[intersection_id] = "X"
        
        # 10% chance to switch axis on every poll for demo dynamism
        if random.random() < 0.1:
             signal_phase_state[intersection_id] = "Z" if signal_phase_state[intersection_id] == "X" else "X"

        active_axis = signal_phase_state[intersection_id]
        
        # Random congestion level
        levels = [CongestionLevel.LOW, CongestionLevel.MEDIUM, CongestionLevel.HIGH]
        level = random.choice(levels)
        
        downstream_blocked = False
        if level == CongestionLevel.HIGH and random.random() < 0.3:
            downstream_blocked = True

        green_time = 15
        red_time = 75

        return SignalTimingResponse(
            intersection_id=intersection_id,
            active_axis=active_axis,
            green_time=green_time,
            red_time=red_time,
            level=level,
            downstream_blocked=downstream_blocked,
        )
    except Exception as e:
        logger.error(f"Error getting signal timing for {intersection_id}: {e}")
        # Fallback default object
        return SignalTimingResponse(
            intersection_id=intersection_id,
            active_axis="X",
            green_time=30,
            red_time=30,
            level=CongestionLevel.LOW,
            downstream_blocked=False,
        )

