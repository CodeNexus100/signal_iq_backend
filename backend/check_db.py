
import asyncio
from app.database import get_database, close_database_connection

async def check_data():
    db = get_database()
    intersections = db["intersections"]
    roads = db["roads"]
    
    i_count = await intersections.count_documents({})
    r_count = await roads.count_documents({})
    
    print(f"Total Intersections: {i_count}")
    print(f"Total Roads: {r_count}")

    # Print coords
    cursor = intersections.find({})
    async for i in cursor:
        pos = i.get('position', {})
        print(f"Node {i.get('intersection_id')}: {pos}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(check_data())
    finally:
        loop.run_until_complete(close_database_connection())
