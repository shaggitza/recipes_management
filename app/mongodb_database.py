"""
Real MongoDB database implementation.
To use this instead of mock database, update app/main.py imports.
"""
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None
    ObjectId = None
    print("MongoDB dependencies not available. Using mock database.")

from app.config import settings

class Database:
    client = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    if not MONGODB_AVAILABLE:
        raise ImportError("MongoDB dependencies not installed. Run: pip install motor pymongo")
    
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Test connection
    try:
        await db.client.admin.command('ismaster')
        print(f"✅ Connected to MongoDB at {settings.mongodb_url}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("📴 MongoDB connection closed")

def get_database():
    """Get database instance"""
    if not db.database:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db.database

# Update Recipe model to work with real ObjectId
def dict_to_recipe(recipe_dict):
    """Convert MongoDB document to Recipe-compatible dict"""
    if "_id" in recipe_dict:
        recipe_dict["id"] = str(recipe_dict["_id"])
    return recipe_dict

def recipe_to_dict(recipe):
    """Convert Recipe to MongoDB document"""
    recipe_dict = recipe.dict(by_alias=True)
    if "id" in recipe_dict:
        if isinstance(recipe_dict["id"], str) and ObjectId:
            recipe_dict["_id"] = ObjectId(recipe_dict["id"]) if ObjectId.is_valid(recipe_dict["id"]) else ObjectId()
        del recipe_dict["id"]
    return recipe_dict