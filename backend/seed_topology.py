
import asyncio
import logging
from app.database import get_database, close_database_connection
from app.topology_routes import _road_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERSECTIONS_COLL = "intersections"
ROADS_COLL = "roads"

async def seed_topology():
    """Seed a 3x3 grid of intersections matching frontend scale (20 units spacing)."""
    db = get_database()
    intersections_coll = db[INTERSECTIONS_COLL]
    roads_coll = db[ROADS_COLL]

    # 3x3 grid intersection IDs
    # Row 0: Z=0, Row 1: Z=20, Row 2: Z=40
    # Col 0: X=0, Col 1: X=20, Col 2: X=40
    
    rows = 3
    cols = 3
    spacing = 20.0
    
    ids = []
    
    # Clear existing data
    await intersections_coll.delete_many({})
    await roads_coll.delete_many({})
    logger.info("Cleared existing topology data.")

    # Create Intersections
    for r in range(rows):
        row_ids = []
        for c in range(cols):
            iid = f"I{r}{c}"
            row_ids.append(iid)
            
            # Map grid (row, col) to (z, x)
            # Frontend often treats Y as up, so X and Z are the ground plane.
            # Let's map lat -> Z (North/South), lng -> X (East/West)
            # Position (0,0) is top-left in many grids, but let's just stick to positive coords.
            
            z = r * spacing
            x = c * spacing
            
            doc = {
                "intersection_id": iid,
                "name": f"Intersection {iid}",
                "position": {"lat": z, "lng": x}, # Using lat for Z, lng for X to match requester's "lat/lng to represent X/Z"
            }
            await intersections_coll.insert_one(doc)
            logger.info(f"Inserted intersection {iid} at (lat={z}, lng={x})")
        ids.append(row_ids)

    # Create Roads
    def add_road(fr: str, to: str):
        # Calculate length roughly (manhattan distance is fine for grid)
        # Actually in this grid it's always 'spacing' (20.0)
        return {
            "road_id": _road_id(fr, to),
            "from": fr,
            "to": to,
            "length_m": spacing
        }

    road_docs = []
    
    # Horizontal edges (West <-> East)
    for r in range(rows):
        for c in range(cols - 1):
            # Eastbound
            road_docs.append(add_road(ids[r][c], ids[r][c+1]))
            # Westbound
            road_docs.append(add_road(ids[r][c+1], ids[r][c]))

    # Vertical edges (North <-> South)
    for c in range(cols):
        for r in range(rows - 1):
            # Southbound (increasing Z)
            road_docs.append(add_road(ids[r][c], ids[r+1][c]))
            # Northbound (decreasing Z)
            road_docs.append(add_road(ids[r+1][c], ids[r][c]))

    if road_docs:
        await roads_coll.insert_many(road_docs)
        logger.info(f"Inserted {len(road_docs)} roads.")
    
    logger.info("Seeding complete.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(seed_topology())
    finally:
        loop.run_until_complete(close_database_connection())
