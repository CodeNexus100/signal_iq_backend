import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StrictFloat, StrictInt

router = APIRouter()
logger = logging.getLogger(__name__)

# Rule-based congestion thresholds
MAX_VEHICLES = 20
MIN_SPEED = 10.0  # km/h
MAX_QUEUE = 10

# Signal timing constants
BASE_GREEN_TIME = 30
MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
CONGESTION_GREEN_EXTENSION = 15
CYCLE_TIME = 90

# In-memory storage (Consider moving to DB later)
traffic_state: Dict[str, dict] = {}
congestion_state: Dict[str, bool] = {}
signal_timing_state: Dict[str, dict] = {}

class TrafficUpdate(BaseModel):
    intersection_id: str
    timestamp: str = Field(..., description="ISO format timestamp string")
    vehicle_count: StrictInt
    avg_speed: StrictFloat
    queue_length: StrictInt

@router.post("/traffic/update")
async def update_traffic(update: TrafficUpdate):
    intersection_id = update.intersection_id
    state = update.dict()
    traffic_state[intersection_id] = state

    # Compute congestion
    is_congested = (
        state["vehicle_count"] > MAX_VEHICLES
        or state["avg_speed"] < MIN_SPEED
        or state["queue_length"] > MAX_QUEUE
    )
    congestion_state[intersection_id] = is_congested

    # Update signal timing
    _update_signal_timing(intersection_id, is_congested)
    
    logger.info(f"Traffic update for {intersection_id}: congested={is_congested}")
    return {"status": "received", "intersection_id": intersection_id}

@router.get("/traffic/state/{intersection_id}")
async def get_traffic_state(intersection_id: str):
    state = traffic_state.get(intersection_id)
    if not state:
        raise HTTPException(status_code=404, detail="Intersection state not found")
    return state

@router.get("/traffic/congestion/{intersection_id}")
async def get_congestion(intersection_id: str):
    if intersection_id not in traffic_state:
        raise HTTPException(status_code=404, detail="Intersection state not found")
    return {"intersection_id": intersection_id, "congested": congestion_state.get(intersection_id, False)}

@router.get("/traffic/signal/{intersection_id}")
async def get_signal_timing(intersection_id: str):
    if intersection_id not in traffic_state:
        raise HTTPException(status_code=404, detail="Intersection state not found")
    timing = signal_timing_state.get(intersection_id)
    if not timing:
        raise HTTPException(status_code=404, detail="Signal timing not found")
    return {"intersection_id": intersection_id, **timing}

def _update_signal_timing(intersection_id: str, is_congested: bool):
    green_time = BASE_GREEN_TIME + (CONGESTION_GREEN_EXTENSION if is_congested else 0)
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
    red_time = CYCLE_TIME - green_time
    signal_timing_state[intersection_id] = {"green_time": green_time, "red_time": red_time}
