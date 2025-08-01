from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from app.config import settings
from app.models.recipe import Recipe


class Database:
    """Database connection manager with proper async patterns"""
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def create_connection(cls) -> None:
        """Create database connection and initialize Beanie with proper error handling"""
        if cls.client is not None:
            return  # Already connected
        
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.database = cls.client[settings.database_name]
            
            # Initialize Beanie with the Recipe model
            await init_beanie(database=cls.database, document_models=[Recipe])
            
            # Test the connection
            await cls.database.command("ping")
            
        except Exception as e:
            if cls.client:
                cls.client.close()
                cls.client = None
                cls.database = None
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    @classmethod
    async def close_connection(cls) -> None:
        """Close database connection properly"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None

    @classmethod
    def get_database(cls) -> Optional[AsyncIOMotorDatabase]:
        """Get database instance"""
        return cls.database

    @classmethod
    def is_connected(cls) -> bool:
        """Check if database is connected"""
        return cls.client is not None and cls.database is not None


# Global database instance
db = Database()


async def connect_to_mongo() -> None:
    """Connect to MongoDB - convenience function for backward compatibility"""
    await db.create_connection()


async def close_mongo_connection() -> None:
    """Close MongoDB connection - convenience function for backward compatibility"""
    await db.close_connection()


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance - convenience function for backward compatibility"""
    return db.get_database()