"""
Real MongoDB database implementation using Beanie ODM.
"""
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from beanie import init_beanie
    from app.models.recipe import Recipe
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None
    print("MongoDB dependencies not available. Using mock database.")

from typing import Optional
from app.config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo() -> None:
    """Create database connection and initialize Beanie"""
    if not MONGODB_AVAILABLE:
        raise ImportError("MongoDB dependencies not installed. Run: pip install motor pymongo beanie")
    
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Test connection
    try:
        await db.client.admin.command('ismaster')
        print(f"✅ Connected to MongoDB at {settings.mongodb_url}")
        
        # Initialize Beanie with the Recipe model
        await init_beanie(database=db.database, document_models=[Recipe])
        print("✅ Beanie ODM initialized")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB or initialize Beanie: {e}")
        raise

async def close_mongo_connection() -> None:
    """Close database connection"""
    if db.client:
        db.client.close()
        print("📴 MongoDB connection closed")

def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance"""
    if not db.database:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db.database