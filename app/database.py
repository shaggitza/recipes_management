import logging
import time
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from app.config import settings
from app.models.recipe import Recipe
from app.logging_config import DatabaseLogger

logger = logging.getLogger("app.database")


class Database:
    """Database connection manager with proper async patterns and comprehensive logging"""
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def create_connection(cls) -> None:
        """Create database connection and initialize Beanie with proper error handling"""
        if cls.client is not None:
            logger.debug("Database connection already exists")
            return  # Already connected
        
        start_time = time.time()
        
        logger.info("Creating database connection", extra={
            "extra_data": {
                "mongodb_url": settings.mongodb_url.replace("://", "://***:***@") if "@" in settings.mongodb_url else settings.mongodb_url,
                "database_name": settings.database_name
            }
        })
        
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.database = cls.client[settings.database_name]
            
            logger.debug("Initializing Beanie ODM with Recipe model")
            
            # Initialize Beanie with the Recipe model
            await init_beanie(database=cls.database, document_models=[Recipe])
            
            # Test the connection
            logger.debug("Testing database connection")
            await cls.database.command("ping")
            
            connection_time = (time.time() - start_time) * 1000
            
            DatabaseLogger.log_operation(
                logger, 
                operation="connect", 
                duration=connection_time,
                database=settings.database_name,
                models_initialized=["Recipe"]
            )
            
        except Exception as e:
            connection_time = (time.time() - start_time) * 1000
            
            # Clean up on failure
            if cls.client:
                cls.client.close()
                cls.client = None
                cls.database = None
            
            DatabaseLogger.log_error(
                logger, 
                operation="connect", 
                error=e,
                duration=connection_time,
                database=settings.database_name
            )
            
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    @classmethod
    async def close_connection(cls) -> None:
        """Close database connection properly"""
        if cls.client is None:
            logger.debug("No database connection to close")
            return
            
        logger.info("Closing database connection")
        
        try:
            cls.client.close()
            cls.client = None
            cls.database = None
            
            DatabaseLogger.log_operation(
                logger, 
                operation="disconnect",
                database=settings.database_name
            )
            
        except Exception as e:
            DatabaseLogger.log_error(
                logger, 
                operation="disconnect", 
                error=e,
                database=settings.database_name
            )

    @classmethod
    def get_database(cls) -> Optional[AsyncIOMotorDatabase]:
        """Get database instance"""
        if cls.database is None:
            logger.warning("Database instance requested but not connected")
        return cls.database

    @classmethod
    def is_connected(cls) -> bool:
        """Check if database is connected"""
        connected = cls.client is not None and cls.database is not None
        logger.debug("Database connection status check", extra={
            "extra_data": {"connected": connected}
        })
        return connected


# Global database instance
db = Database()


async def connect_to_mongo() -> None:
    """Connect to MongoDB - convenience function for backward compatibility"""
    logger.debug("connect_to_mongo() called")
    await db.create_connection()


async def close_mongo_connection() -> None:
    """Close MongoDB connection - convenience function for backward compatibility"""
    logger.debug("close_mongo_connection() called")
    await db.close_connection()


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance - convenience function for backward compatibility"""
    return db.get_database()