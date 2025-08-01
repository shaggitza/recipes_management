from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.database