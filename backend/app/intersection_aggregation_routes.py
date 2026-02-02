"""Intersection state aggregation. Reads from topology and traffic_state, no writes."""
import logging

from fastapi import APIRouter, HTTPException

from .database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

INTERSECTIONS_COLL = "intersections"
ROADS_COLL = "roads"
TRAFFIC_STATE_COLL = "traffic_state"


def _db():
    return get_database()


@router.get("/intersection/{intersection_id}/snapshot")
async def get_intersection_snapshot(intersection_id: str):
    """
    Aggregate incoming road traffic per intersection.
    Returns total_queue, total_vehicles, avg_speed, load_score.
    """
    db = _db()
    intersections = db[INTERSECTIONS_COLL]
    roads = db[ROADS_COLL]
    traffic_state = db[TRAFFIC_STATE_COLL]

    # Ensure intersection exists
    inter = await intersections.find_one({"intersection_id": intersection_id})
    if not inter:
        raise HTTPException(status_code=404, detail="Intersection not found")

    # Get incoming roads (edges where to = intersection_id)
    incoming = await roads.find({"to": intersection_id}, {"_id": 0}).to_list(length=None)
    if not incoming:
        snapshot = {
            "intersection_id": intersection_id,
            "total_queue": 0,
            "total_vehicles": 0,
            "avg_speed": 0.0,
            "load_score": 0,
            "incoming_road_ids": [],
            "roads_with_data": 0,
        }
        logger.info("Intersection snapshot: %s, no incoming roads", intersection_id)
        return snapshot

    road_ids = [r["road_id"] for r in incoming]

    # Fetch traffic state for each incoming road
    total_queue = 0
    total_vehicles = 0
    speed_sum = 0.0
    roads_with_data = 0

    for road_id in road_ids:
        ts = await traffic_state.find_one({"road_id": road_id}, {"_id": 0})
        if not ts:
            continue
        total_queue += ts.get("queue_length", 0)
        total_vehicles += ts.get("vehicle_count", 0)
        speed_sum += ts.get("avg_speed", 0.0)
        roads_with_data += 1

    avg_speed = speed_sum / roads_with_data if roads_with_data else 0.0
    load_score = total_queue + total_vehicles

    snapshot = {
        "intersection_id": intersection_id,
        "total_queue": total_queue,
        "total_vehicles": total_vehicles,
        "avg_speed": round(avg_speed, 2),
        "load_score": load_score,
        "incoming_road_ids": road_ids,
        "roads_with_data": roads_with_data,
    }

    logger.info(
        "Intersection snapshot: %s, total_queue=%s, total_vehicles=%s, avg_speed=%s, load_score=%s",
        intersection_id,
        total_queue,
        total_vehicles,
        avg_speed,
        load_score,
    )
    return snapshot
