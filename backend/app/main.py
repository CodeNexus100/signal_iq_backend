import logging
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StrictFloat, StrictInt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SignalIQ", version="0.1.0")

# In-memory storage for raw traffic updates
traffic_data: List[dict] = []

# In-memory per-intersection state
traffic_state: Dict[str, dict] = {}

# In-memory per-intersection congestion status
congestion_state: Dict[str, bool] = {}

# Rule-based congestion thresholds
MAX_VEHICLES = 20
MIN_SPEED = 10.0  # km/h
MAX_QUEUE = 10


class TrafficUpdate(BaseModel):
    """Traffic update payload model."""

    intersection_id: str
    timestamp: str = Field(..., description="ISO format timestamp string")
    vehicle_count: StrictInt
    avg_speed: StrictFloat
    queue_length: StrictInt


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("SignalIQ application starting up")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/traffic/update")
async def update_traffic(update: TrafficUpdate):
    """Receive and store traffic update data and update intersection state."""
    # Store the raw update in memory
    traffic_data.append(update.dict())

    # Build latest state for this intersection
    state = {
        "intersection_id": update.intersection_id,
        "vehicle_count": update.vehicle_count,
        "avg_speed": update.avg_speed,
        "queue_length": update.queue_length,
        "last_updated": update.timestamp,
    }

    # Determine if this is a create or update of state
    intersection_id = update.intersection_id
    is_new = intersection_id not in traffic_state
    traffic_state[intersection_id] = state

    if is_new:
        logger.info("Traffic state created for intersection_id=%s: %s", intersection_id, state)
    else:
        logger.info("Traffic state updated for intersection_id=%s: %s", intersection_id, state)

    # Compute congestion status based on latest state
    was_congested = congestion_state.get(intersection_id, False)
    is_congested = (
        state["vehicle_count"] > MAX_VEHICLES
        or state["avg_speed"] < MIN_SPEED
        or state["queue_length"] > MAX_QUEUE
    )
    congestion_state[intersection_id] = is_congested

    # Log congestion transitions
    if not was_congested and is_congested:
        logger.info("Congestion started at intersection_id=%s", intersection_id)
    elif was_congested and not is_congested:
        logger.info("Congestion cleared at intersection_id=%s", intersection_id)

    # Log the received update as well
    logger.info(
        "Traffic update received: intersection_id=%s, timestamp=%s, "
        "vehicle_count=%s, avg_speed=%s, queue_length=%s",
        update.intersection_id,
        update.timestamp,
        update.vehicle_count,
        update.avg_speed,
        update.queue_length,
    )

    return {"status": "received", "intersection_id": update.intersection_id}


@app.get("/traffic/state/{intersection_id}")
async def get_traffic_state(intersection_id: str):
    """Return the current traffic state for an intersection or 404 if not found."""
    state = traffic_state.get(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Intersection state not found")
    return state


@app.get("/traffic/congestion/{intersection_id}")
async def get_congestion(intersection_id: str):
    """Return the congestion status for an intersection or 404 if state not found."""
    if intersection_id not in traffic_state:
        raise HTTPException(status_code=404, detail="Intersection state not found")

    congested = congestion_state.get(intersection_id, False)
    return {
        "intersection_id": intersection_id,
        "congested": congested,
    }
