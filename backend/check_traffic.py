
import asyncio
from app.database import get_database, close_database_connection

async def check_traffic():
    db = get_database()
    traffic_coll = db["traffic_state"]
    
    count = await traffic_coll.count_documents({})
    print(f"Total Traffic Records: {count}")
    
    if count == 0:
        print("No traffic data found in DB.")
    else:
        cursor = traffic_coll.find({})
        async for doc in cursor:
            # Filter for meaningful traffic? e.g. vehicle_count > 0
            if doc.get("vehicle_count", 0) > 0:
                print(f"Road {doc.get('road_id')}: {doc.get('vehicle_count')} vehicles, Speed {doc.get('avg_speed')}")
            else:
                 print(f"Road {doc.get('road_id')}: No active vehicles (Record exists)")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(check_traffic())
    finally:
        loop.run_until_complete(close_database_connection())
