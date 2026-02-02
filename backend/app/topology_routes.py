"""Topology router: intersections and roads as a directed graph."""
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from .database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

INTERSECTIONS_COLL = "intersections"
ROADS_COLL = "roads"


def _intersections_collection():
    return get_database()[INTERSECTIONS_COLL]


def _roads_collection():
    return get_database()[ROADS_COLL]


def _road_id(from_id: str, to_id: str) -> str:
    return f"{from_id}->{to_id}"


@router.post("/seed")
async def seed_topology():
    """Seed a small dummy city graph (3x3 grid of intersections)."""
    db = get_database()
    intersections = db[INTERSECTIONS_COLL]
    roads = db[ROADS_COLL]

    # 3x3 grid intersection IDs
    ids = [
        ["I00", "I01", "I02"],
        ["I10", "I11", "I12"],
        ["I20", "I21", "I22"],
    ]

    # Clear existing seed data (idempotent seed)
    await intersections.delete_many({})
    await roads.delete_many({})

    # Insert intersections
    for r, row in enumerate(ids):
        for c, iid in enumerate(row):
            await intersections.insert_one({
                "intersection_id": iid,
                "name": f"Intersection {iid}",
                "position": {"lat": float(r), "lng": float(c)},
            })

    # Insert directed roads (two-way streets = two directed edges)
    def add_road(fr: str, to: str, length: float = 100.0):
        return {"road_id": _road_id(fr, to), "from": fr, "to": to, "length_m": length}

    road_docs = []
    # Horizontal edges
    for row in ids:
        for j in range(len(row) - 1):
            road_docs.append(add_road(row[j], row[j + 1]))
            road_docs.append(add_road(row[j + 1], row[j]))
    # Vertical edges
    for c in range(3):
        for r in range(2):
            road_docs.append(add_road(ids[r][c], ids[r + 1][c]))
            road_docs.append(add_road(ids[r + 1][c], ids[r][c]))

    await roads.insert_many(road_docs)

    logger.info("Topology seeded: 9 intersections, %d roads", len(road_docs))
    return {"status": "seeded", "intersections": 9, "roads": len(road_docs)}


@router.get("/intersections")
async def list_intersections() -> List[dict]:
    """List all intersections."""
    cursor = _intersections_collection().find({}, {"_id": 0})
    results = await cursor.to_list(length=None)
    return results


@router.get("/intersections/{intersection_id}")
async def get_intersection(intersection_id: str) -> dict:
    """Get a single intersection by ID."""
    doc = await _intersections_collection().find_one(
        {"intersection_id": intersection_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Intersection not found")
    return doc


@router.get("/roads")
async def list_roads() -> List[dict]:
    """List all roads (directed edges)."""
    cursor = _roads_collection().find({}, {"_id": 0})
    results = await cursor.to_list(length=None)
    return results


@router.get("/intersections/{intersection_id}/incoming")
async def get_incoming_roads(intersection_id: str) -> List[dict]:
    """Get roads that end at this intersection (incoming edges)."""
    await _ensure_intersection_exists(intersection_id)
    cursor = _roads_collection().find({"to": intersection_id}, {"_id": 0})
    return await cursor.to_list(length=None)


@router.get("/intersections/{intersection_id}/outgoing")
async def get_outgoing_roads(intersection_id: str) -> List[dict]:
    """Get roads that start from this intersection (outgoing edges)."""
    await _ensure_intersection_exists(intersection_id)
    cursor = _roads_collection().find({"from": intersection_id}, {"_id": 0})
    return await cursor.to_list(length=None)


async def _ensure_intersection_exists(intersection_id: str) -> None:
    doc = await _intersections_collection().find_one({"intersection_id": intersection_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Intersection not found")
