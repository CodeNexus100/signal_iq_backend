"""Graph-aware congestion detection. Reads from topology and traffic_state, no writes."""
import logging
from typing import Dict, List, Tuple

from fastapi import APIRouter, HTTPException

from .congestion_models import CongestionLevel, CongestionResponse
from .database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

INTERSECTIONS_COLL = "intersections"
ROADS_COLL = "roads"
TRAFFIC_STATE_COLL = "traffic_state"

# Load-score thresholds for base classification
LOAD_LOW_MAX = 10
LOAD_MEDIUM_MAX = 30
# load_score >= LOAD_MEDIUM_MAX -> HIGH

# In-memory cache: intersection_id -> (level, downstream_blocked)
# Only log when level OR downstream_blocked changes.
_congestion_state_cache: Dict[str, Tuple[CongestionLevel, bool]] = {}


def _db():
    return get_database()


async def _get_snapshot(db, intersection_id: str) -> dict:
    """Replicate Section 7 aggregation: aggregate incoming road traffic per intersection."""
    intersections = db[INTERSECTIONS_COLL]
    roads = db[ROADS_COLL]
    traffic_state = db[TRAFFIC_STATE_COLL]

    inter = await intersections.find_one({"intersection_id": intersection_id})
    if not inter:
        return None

    incoming = await roads.find({"to": intersection_id}, {"_id": 0}).to_list(length=None)
    if not incoming:
        return {"load_score": 0, "total_queue": 0, "total_vehicles": 0, "avg_speed": 0.0}

    road_ids = [r["road_id"] for r in incoming]
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
    return {"load_score": load_score, "total_queue": total_queue, "total_vehicles": total_vehicles, "avg_speed": avg_speed}


def _classify_base(load_score: int) -> CongestionLevel:
    """Classify load_score into LOW, MEDIUM, or HIGH."""
    if load_score < LOAD_LOW_MAX:
        return CongestionLevel.LOW
    if load_score < LOAD_MEDIUM_MAX:
        return CongestionLevel.MEDIUM
    return CongestionLevel.HIGH


def _escalate(level: CongestionLevel) -> CongestionLevel:
    """Escalate one step: LOW->MEDIUM, MEDIUM->HIGH, HIGH->HIGH."""
    if level == CongestionLevel.LOW:
        return CongestionLevel.MEDIUM
    if level == CongestionLevel.MEDIUM:
        return CongestionLevel.HIGH
    return CongestionLevel.HIGH


async def _get_downstream_intersection_ids(db, intersection_id: str) -> List[str]:
    """Get intersection IDs that are one hop downstream (outgoing roads' targets)."""
    roads = db[ROADS_COLL]
    outgoing = await roads.find({"from": intersection_id}, {"to": 1}).to_list(length=None)
    return [r["to"] for r in outgoing]


@router.get("/congestion/{intersection_id}", response_model=CongestionResponse)
async def get_congestion(intersection_id: str) -> CongestionResponse:
    """
    Graph-aware congestion for an intersection.
    Classifies as LOW/MEDIUM/HIGH. Escalates if downstream is blocked (HIGH).
    """
    db = _db()
    intersections = db[INTERSECTIONS_COLL]

    inter = await intersections.find_one({"intersection_id": intersection_id})
    if not inter:
        raise HTTPException(status_code=404, detail="Intersection not found")

    # Section 7 aggregation
    snapshot = await _get_snapshot(db, intersection_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Intersection not found")

    load_score = snapshot["load_score"]
    base_level = _classify_base(load_score)

    # One-hop downstream lookup
    downstream_ids = await _get_downstream_intersection_ids(db, intersection_id)
    downstream_blocked = False

    for down_id in downstream_ids:
        down_snapshot = await _get_snapshot(db, down_id)
        if down_snapshot and _classify_base(down_snapshot["load_score"]) == CongestionLevel.HIGH:
            downstream_blocked = True
            break

    # Escalate if downstream blocked
    level = _escalate(base_level) if downstream_blocked else base_level
    escalated = level != base_level

    # Only log when level OR downstream_blocked changes
    prev = _congestion_state_cache.get(intersection_id)
    if prev is None or prev[0] != level or prev[1] != downstream_blocked:
        _congestion_state_cache[intersection_id] = (level, downstream_blocked)
        logger.info(
            "Congestion: intersection_id=%s, base_level=%s, level=%s, escalated=%s, downstream_blocked=%s, load_score=%s",
            intersection_id,
            base_level.value,
            level.value,
            escalated,
            downstream_blocked,
            load_score,
        )

    return CongestionResponse(
        intersection_id=intersection_id,
        level=level,
        base_level=base_level,
        escalated=escalated,
        downstream_blocked=downstream_blocked,
        load_score=load_score,
        downstream_intersection_ids=downstream_ids,
    )
