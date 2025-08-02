import pytest
import pytest_asyncio
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import mongomock_motor
from beanie import init_beanie

# Set test environment variables early
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017/test_recipes_db")
os.environ.setdefault("DATABASE_NAME", "test_recipes_db")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("USE_STRUCTURED_LOGGING", "false")  # Use simple logging in tests
os.environ.setdefault("ENVIRONMENT", "test")

from app.main import app
from app.database import db
from app.config import settings
from app.models.recipe import Recipe


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "ai: mark test as AI functionality test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "database: mark test as requiring database")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names and locations."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark AI tests
        if "ai" in item.nodeid.lower() or "test_ai" in item.name:
            item.add_marker(pytest.mark.ai)
        
        # Mark database tests
        if "database" in item.nodeid.lower() or "db" in item.name:
            item.add_marker(pytest.mark.database)
        
        # Mark slow tests
        if "slow" in item.name or "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Set up test database with mongomock."""
    try:
        # Use mongomock for testing
        client = mongomock_motor.AsyncMongoMockClient()
        database = client[settings.database_name]
        
        # Set test database
        db.client = client
        db.database = database
        
        # Initialize Beanie for testing with mongomock
        await init_beanie(database=database, document_models=[Recipe])
        
        yield database
        
        # Clean up - mongomock doesn't need explicit cleanup
        client.close()
        
    except Exception as e:
        pytest.skip(f"Failed to setup mongomock: {e}")


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def clean_db(test_db):
    """Clean test database before each test."""
    if test_db is None:
        pytest.skip("Database not available")
    # Clear all recipes before each test
    await Recipe.delete_all()
    yield test_db
    # Clear all recipes after each test as well
    await Recipe.delete_all()


@pytest.fixture
def sample_recipe_data():
    """Provide sample recipe data for testing."""
    return {
        "title": "Test Recipe",
        "description": "A recipe for testing purposes",
        "ingredients": [
            {"name": "Flour", "amount": "2", "unit": "cups"},
            {"name": "Sugar", "amount": "1", "unit": "cup"},
            {"name": "Eggs", "amount": "2", "unit": "pieces"}
        ],
        "instructions": [
            "Mix dry ingredients",
            "Add eggs and mix",
            "Bake for 30 minutes"
        ],
        "prep_time": 15,
        "cook_time": 30,
        "servings": 6,
        "difficulty": "easy",
        "tags": ["dessert", "baking"],
        "cuisine": "American"
    }


@pytest.fixture
def mock_recipe_repository():
    """Create a mock recipe repository for testing."""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.search = AsyncMock(return_value=[])
    repo.get_by_source_url = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_recipe_scraper():
    """Create a mock recipe scraper for testing."""
    from app.ai.models import ScrapedData, ExtractedImage
    
    scraper = Mock()
    scraper.scrape_url = Mock(return_value=ScrapedData(
        url="https://example.com/recipe",
        html_content="<h1>Test Recipe</h1>",
        title="Test Recipe",
        status_code=200,
        images=[
            ExtractedImage(
                src="https://example.com/image.jpg",
                alt="Recipe image",
                width=400,
                height=300
            )
        ],
        structured_data=[]
    ))
    return scraper


@pytest.fixture
def mock_recipe_extractor():
    """Create a mock recipe extractor for testing."""
    from app.ai.models import ExtractedRecipe
    
    extractor = Mock()
    extractor.extract_recipe = Mock(return_value=ExtractedRecipe(
        title="Mock Extracted Recipe",
        extraction_method="mock"
    ))
    extractor.use_ai = True
    extractor.api_key = "mock-key"
    return extractor


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup test logging configuration."""
    import logging
    
    # Set simple logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)