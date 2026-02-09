
import asyncio
import logging
import random
from datetime import datetime
from app.database import get_database, close_database_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_traffic():
    db = get_database()
    roads_coll = db["roads"]
    traffic_coll = db["traffic_state"]
    
    # Get all roads
    roads = await roads_coll.find({}, {"_id": 0, "road_id": 1}).to_list(length=None)
    logger.info(f"Found {len(roads)} roads. Seeding traffic...")
    
    traffic_docs = []
    timestamp = datetime.now().isoformat()
    
    for r in roads:
        road_id = r["road_id"]
        
        # Generate random congested traffic data
        # High vehicle count (20-50), Low speed (5-15 km/h)
        vehicle_count = random.randint(20, 50)
        avg_speed = round(random.uniform(5.0, 15.0), 2)
        queue_length = random.randint(5, 15)
        
        doc = {
            "road_id": road_id,
            "timestamp": timestamp,
            "vehicle_count": vehicle_count,
            "avg_speed": avg_speed,
            "queue_length": queue_length,
        }
        
        # Upsert: Update if exists, Insert if not
        # We must await inside the loop or use update_many/bulk_write, but update_one is fine for 24 items
        await traffic_coll.update_one(
            {"road_id": road_id},
            {"$set": doc},
            upsert=True
        )
        traffic_docs.append(doc)
        
    logger.info(f"Successfully seeded traffic for {len(traffic_docs)} roads.")
    print(f"Seeded {len(traffic_docs)} roads with traffic data.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(seed_traffic())
    finally:
        loop.run_until_complete(close_database_connection())
