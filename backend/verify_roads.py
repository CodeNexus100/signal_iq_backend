
import asyncio
import logging
from app.database import get_database, close_database_connection
from app.topology_routes import ROADS_COLL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: This script must be run from the backend directory to resolve 'app' imports correctly.


async def verify_bidirectional_roads():
    db = get_database()
    roads_coll = db[ROADS_COLL]

    roads: list = await roads_coll.find({}, {"_id": 0}).to_list(length=None)
    logger.info(f"Loaded {len(roads)} roads.")
    
    road_map = {r["road_id"]: r for r in roads}
    
    missing_reverse = []
    
    for r in roads:
        fr = r["from"]
        to = r["to"]
        
        # Construct expected reverse ID
        # Note: The current seed script uses logic that might produce "A->B"
        # We need to check if a road exists with from=to and to=fr
        
        reverse_found = False
        for potential_reverse in roads:
            if potential_reverse["from"] == to and potential_reverse["to"] == fr:
                reverse_found = True
                break
        
        if not reverse_found:
            missing_reverse.append(f"{fr}->{to}")

    if missing_reverse:
        logger.error(f"FAIL: Found {len(missing_reverse)} roads without reverse connection:")
        for m in missing_reverse:
            logger.error(f"  - {m}")
        return False
    else:
        logger.info("PASS: All roads are bidirectional.")
        return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        success = loop.run_until_complete(verify_bidirectional_roads())
        if not success:
            exit(1)
    finally:
        loop.run_until_complete(close_database_connection())
