"""Road-level real-time traffic state. Per-road traffic stored in MongoDB."""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StrictFloat, StrictInt

from .database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

TRAFFIC_STATE_COLL = "traffic_state"


def _traffic_state_collection():
    return get_database()[TRAFFIC_STATE_COLL]


class RoadTrafficUpdate(BaseModel):
    """Payload for updating road-level traffic state."""
    road_id: str = Field(..., min_length=1)
    timestamp: str = Field(..., description="ISO format timestamp string")
    vehicle_count: StrictInt = Field(..., ge=0)
    avg_speed: StrictFloat = Field(..., ge=0)
    queue_length: StrictInt = Field(..., ge=0)


def _validate_timestamp(ts: str) -> None:
    """Validate timestamp is valid ISO format. Raises HTTPException if invalid."""
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid timestamp: must be ISO 8601 format")


@router.post("/road/update")
async def update_road_traffic(update: RoadTrafficUpdate):
    """Update real-time traffic state for a road."""
    _validate_timestamp(update.timestamp)

    coll = _traffic_state_collection()
    doc = {
        "road_id": update.road_id,
        "timestamp": update.timestamp,
        "vehicle_count": update.vehicle_count,
        "avg_speed": update.avg_speed,
        "queue_length": update.queue_length,
    }

    await coll.update_one(
        {"road_id": update.road_id},
        {"$set": doc},
        upsert=True,
    )

    logger.info(
        "Road traffic update: road_id=%s, timestamp=%s, vehicle_count=%s, avg_speed=%s, queue_length=%s",
        update.road_id,
        update.timestamp,
        update.vehicle_count,
        update.avg_speed,
        update.queue_length,
    )

    return {"status": "received", "road_id": update.road_id}


@router.get("/road/{road_id}")
async def get_road_traffic(road_id: str):
    """Get current traffic state for a road. Returns 404 if not found."""
    doc = await _traffic_state_collection().find_one(
        {"road_id": road_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Road traffic state not found")
    return doc
