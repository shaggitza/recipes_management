import pytest
import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.main import app
from app.database import db
from app.config import settings
from app.models.recipe import Recipe

# Test database configuration
TEST_DATABASE_URL = "mongodb://localhost:27017"
TEST_DATABASE_NAME = "test_recipes_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Set up test database with Beanie."""
    # Connect to test database
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    database = client[TEST_DATABASE_NAME]
    
    # Set test database
    db.client = client
    db.database = database
    
    # Initialize Beanie for testing
    await init_beanie(database=database, document_models=[Recipe])
    
    yield database
    
    # Clean up
    await client.drop_database(TEST_DATABASE_NAME)
    client.close()

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
async def clean_db(test_db):
    """Clean test database before each test."""
    await Recipe.delete_all()
    yield test_db