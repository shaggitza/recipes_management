from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from app.config import settings
from app.models.recipe import Recipe

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo() -> None:
    """Create database connection and initialize Beanie"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Initialize Beanie with the Recipe model
    await init_beanie(database=db.database, document_models=[Recipe])

async def close_mongo_connection() -> None:
    """Close database connection"""
    if db.client:
        db.client.close()

def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance"""
    return db.database