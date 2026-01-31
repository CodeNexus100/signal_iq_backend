import motor.motor_asyncio
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "signal_iq")

class Database:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_database():
    if db_instance.client is None:
        db_instance.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
        db_instance.db = db_instance.client[DATABASE_NAME]
    return db_instance.db

async def close_database_connection():
    if db_instance.client:
        db_instance.client.close()
        db_instance.client = None
        db_instance.db = None
        logger.info("MongoDB connection closed")
