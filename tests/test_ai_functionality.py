"""
Comprehensive tests for AI-powered recipe import functionality.
Tests both the individual components and the complete integration flow.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.ai.scraper import RecipeScraper
from app.ai.extractor import RecipeExtractor
from app.ai.transformer import RecipeTransformer
from app.ai.importer import RecipeImporter
from app.ai.models import RecipeExtraction, ExtractedImage


class TestRecipeScraper:
    """Test the recipe scraping functionality."""
    
    @pytest.fixture
    def scraper(self):
        return RecipeScraper()
    
    def test_scraper_initialization(self, scraper):
        """Test that scraper initializes correctly."""
        assert scraper is not None
        assert hasattr(scraper, 'session')
    
    @patch('requests.get')
    def test_scrape_basic_html(self, mock_get, scraper):
        """Test basic HTML scraping functionality."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Recipe</title></head>
            <body>
                <h1>Chocolate Cake</h1>
                <div class="recipe-content">
                    <p>A delicious chocolate cake recipe</p>
                    <ul class="ingredients">
                        <li>2 cups flour</li>
                        <li>1 cup sugar</li>
                    </ul>
                    <ol class="instructions">
                        <li>Mix ingredients</li>
                        <li>Bake for 30 minutes</li>
                    </ol>
                </div>
                <img src="/recipe-image.jpg" alt="Chocolate cake">
            </body>
        </html>
        """
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        result = scraper.scrape_url("https://example.com/recipe")
        
        assert result is not None
        assert result.url == "https://example.com/recipe"
        assert result.status_code == 200
        assert "Chocolate Cake" in result.html_content
        assert len(result.images) > 0
        assert result.images[0].src == "/recipe-image.jpg"
    
    @patch('requests.get')
    def test_scrape_with_structured_data(self, mock_get, scraper):
        """Test scraping with JSON-LD structured data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "http://schema.org",
                    "@type": "Recipe",
                    "name": "Chocolate Cake",
                    "description": "A delicious chocolate cake",
                    "recipeIngredient": ["2 cups flour", "1 cup sugar"],
                    "recipeInstructions": [
                        {"@type": "HowToStep", "text": "Mix ingredients"},
                        {"@type": "HowToStep", "text": "Bake for 30 minutes"}
                    ],
                    "prepTime": "PT15M",
                    "cookTime": "PT30M",
                    "recipeYield": "8 servings"
                }
                </script>
            </head>
            <body><h1>Chocolate Cake</h1></body>
        </html>
        """
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        result = scraper.scrape_url("https://example.com/recipe")
        
        assert result is not None
        assert len(result.structured_data) > 0
        recipe_data = result.structured_data[0]
        assert recipe_data["name"] == "Chocolate Cake"
        assert len(recipe_data["recipeIngredient"]) == 2
    
    @patch('requests.get')
    def test_scrape_error_handling(self, mock_get, scraper):
        """Test error handling in scraping."""
        # Test network error
        mock_get.side_effect = ConnectionError("Network error")
        
        result = scraper.scrape_url("https://example.com/recipe")
        assert result is None
        
        # Test HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        
        result = scraper.scrape_url("https://example.com/recipe")
        assert result is None


class TestRecipeExtractor:
    """Test the AI recipe extraction functionality."""
    
    @pytest.fixture
    def extractor(self):
        return RecipeExtractor(api_key="test-key")
    
    @pytest.fixture
    def sample_scraped_data(self):
        from app.ai.models import ScrapedData, ExtractedImage
        return ScrapedData(
            url="https://example.com/recipe",
            html_content="<h1>Chocolate Cake</h1><p>Delicious cake recipe</p>",
            title="Chocolate Cake Recipe",
            status_code=200,
            images=[
                ExtractedImage(
                    src="https://example.com/cake.jpg",
                    alt="Chocolate cake",
                    width=400,
                    height=300
                )
            ],
            structured_data=[]
        )
    
    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes correctly."""
        assert extractor is not None
        assert extractor.api_key == "test-key"
    
    def test_fallback_extraction(self, extractor, sample_scraped_data):
        """Test fallback rule-based extraction."""
        # Force fallback mode
        extractor.use_ai = False
        
        result = extractor.extract_recipe(sample_scraped_data)
        
        assert result is not None
        assert isinstance(result, RecipeExtraction)
        assert result.title == "Chocolate Cake Recipe"
        assert result.extraction_method == "rule_based"
    
    @patch('app.ai.extractor.LANGFUN_AVAILABLE', True)
    @patch('langfun.query')
    def test_ai_extraction(self, mock_query, extractor, sample_scraped_data):
        """Test AI-powered extraction with langfun."""
        # Mock langfun response
        mock_recipe = Mock()
        mock_recipe.title = "Chocolate Cake"
        mock_recipe.description = "Delicious chocolate cake"
        mock_recipe.ingredients = ["2 cups flour", "1 cup sugar"]
        mock_recipe.instructions = ["Mix ingredients", "Bake for 30 minutes"]
        mock_recipe.prep_time = 15
        mock_recipe.cook_time = 30
        mock_recipe.servings = 8
        mock_recipe.difficulty = "easy"
        mock_recipe.cuisine = "American"
        mock_recipe.tags = ["dessert", "cake"]
        
        mock_query.return_value = mock_recipe
        
        # Enable AI mode
        extractor.use_ai = True
        
        result = extractor.extract_recipe(sample_scraped_data)
        
        assert result is not None
        assert result.title == "Chocolate Cake"
        assert result.extraction_method == "langfun_ai"
        assert len(result.ingredients) == 2
        assert len(result.instructions) == 2
        
        # Verify langfun was called
        mock_query.assert_called_once()
    
    def test_image_analysis(self, extractor, sample_scraped_data):
        """Test image analysis and selection."""
        result = extractor.extract_recipe(sample_scraped_data)
        
        assert result is not None
        assert len(result.images) > 0
        # Images should have relevance scores
        assert all(0.0 <= img.relevance_score <= 1.0 for img in result.images)


class TestRecipeTransformer:
    """Test the recipe transformation functionality."""
    
    @pytest.fixture
    def transformer(self):
        return RecipeTransformer()
    
    @pytest.fixture
    def sample_extracted_recipe(self):
        return RecipeExtraction(
            title="Chocolate Cake",
            description="Delicious chocolate cake",
            ingredients=["2 cups flour", "1 cup sugar", "1/2 cup cocoa powder"],
            instructions=["Mix dry ingredients", "Add wet ingredients", "Bake for 30 minutes"],
            prep_time=15,
            cook_time=30,
            servings=8,
            difficulty="easy",
            cuisine="American",
            tags=["dessert", "cake"],
            source_url="https://example.com/recipe",
            extraction_method="test"
        )
    
    def test_transformer_initialization(self, transformer):
        """Test that transformer initializes correctly."""
        assert transformer is not None
    
    def test_transform_to_recipe_model(self, transformer, sample_extracted_recipe):
        """Test transformation to Recipe model."""
        recipe = transformer.transform_to_recipe(sample_extracted_recipe)
        
        assert recipe is not None
        assert recipe.title == "Chocolate Cake"
        assert recipe.description == "Delicious chocolate cake"
        assert len(recipe.ingredients) == 3
        assert len(recipe.instructions) == 3
        assert recipe.prep_time == 15
        assert recipe.cook_time == 30
        assert recipe.servings == 8
        assert recipe.difficulty == "easy"
        assert "dessert" in recipe.tags
        assert "cake" in recipe.tags
        assert recipe.source.url == "https://example.com/recipe"
        assert recipe.source.type == "website"
    
    def test_ingredient_parsing(self, transformer):
        """Test ingredient parsing functionality."""
        ingredients = [
            "2 cups all-purpose flour",
            "1 cup granulated sugar",
            "1/2 teaspoon salt",
            "3 large eggs"
        ]
        
        recipe = RecipeExtraction(
            title="Test Recipe",
            ingredients=ingredients,
            extraction_method="test"
        )
        
        transformed = transformer.transform_to_recipe(recipe)
        
        assert len(transformed.ingredients) == 4
        # Check that ingredients are properly structured
        flour_ingredient = next(ing for ing in transformed.ingredients if "flour" in ing.name.lower())
        assert flour_ingredient.amount == "2"
        assert flour_ingredient.unit == "cups"
    
    def test_metadata_handling(self, transformer, sample_extracted_recipe):
        """Test metadata preservation."""
        metadata = {"custom_field": "custom_value", "source_author": "Test Chef"}
        
        recipe = transformer.transform_to_recipe(sample_extracted_recipe, metadata)
        
        assert recipe.metadata is not None
        assert recipe.metadata["custom_field"] == "custom_value"
        assert recipe.metadata["source_author"] == "Test Chef"


class TestRecipeImporter:
    """Test the complete recipe import functionality."""
    
    @pytest.fixture
    async def mock_repository(self):
        """Create a mock repository."""
        repo = Mock()
        repo.create = AsyncMock()
        repo.get_by_source_url = AsyncMock(return_value=None)
        return repo
    
    @pytest.fixture
    def importer(self, mock_repository):
        """Create a recipe importer with mock repository."""
        return RecipeImporter(mock_repository, api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_import_from_url_success(self, importer):
        """Test successful recipe import from URL."""
        with patch.object(importer.scraper, 'scrape_url') as mock_scrape, \
             patch.object(importer.extractor, 'extract_recipe') as mock_extract, \
             patch.object(importer.transformer, 'transform_to_recipe') as mock_transform:
            
            # Mock scraper
            mock_scrape.return_value = Mock(url="https://example.com/recipe")
            
            # Mock extractor
            mock_extracted = RecipeExtraction(
                title="Test Recipe",
                extraction_method="test"
            )
            mock_extract.return_value = mock_extracted
            
            # Mock transformer
            from app.models.recipe import Recipe
            mock_recipe = Recipe(title="Test Recipe")
            mock_recipe.id = "test-id"
            mock_transform.return_value = mock_recipe
            
            # Mock repository create
            importer.repository.create.return_value = mock_recipe
            
            result = await importer.import_recipe_from_url("https://example.com/recipe")
            
            assert result.success is True
            assert result.recipe_id == "test-id"
            assert result.url == "https://example.com/recipe"
            assert result.attempts == 1
    
    @pytest.mark.asyncio
    async def test_import_with_retry_logic(self, importer):
        """Test import retry logic on failures."""
        with patch.object(importer.scraper, 'scrape_url') as mock_scrape:
            # First call fails, second succeeds
            mock_scrape.side_effect = [None, Mock(url="https://example.com/recipe")]
            
            with patch.object(importer.extractor, 'extract_recipe') as mock_extract, \
                 patch.object(importer.transformer, 'transform_to_recipe') as mock_transform:
                
                mock_extracted = RecipeExtraction(title="Test Recipe", extraction_method="test")
                mock_extract.return_value = mock_extracted
                
                from app.models.recipe import Recipe
                mock_recipe = Recipe(title="Test Recipe")
                mock_recipe.id = "test-id"
                mock_transform.return_value = mock_recipe
                importer.repository.create.return_value = mock_recipe
                
                result = await importer.import_recipe_from_url("https://example.com/recipe")
                
                assert result.success is True
                assert result.attempts == 2  # Should have retried once
    
    @pytest.mark.asyncio
    async def test_import_failure_after_max_retries(self, importer):
        """Test import failure after maximum retries."""
        with patch.object(importer.scraper, 'scrape_url', return_value=None):
            result = await importer.import_recipe_from_url("https://example.com/recipe")
            
            assert result.success is False
            assert result.attempts == 3  # Should have tried 3 times
            assert "scraping failed" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_batch_import(self, importer):
        """Test batch import functionality."""
        urls = [
            "https://example.com/recipe1",
            "https://example.com/recipe2",
            "https://example.com/recipe3"
        ]
        
        with patch.object(importer, 'import_recipe_from_url') as mock_import:
            # Mock successful imports
            mock_import.return_value = Mock(
                success=True,
                recipe_id="test-id",
                url="https://example.com/recipe",
                attempts=1,
                error=None
            )
            
            results = await importer.batch_import(urls, max_concurrent=2)
            
            assert len(results) == 3
            assert all(result.success for result in results.values())
            # Should have been called once for each URL
            assert mock_import.call_count == 3


class TestAIImportAPI:
    """Test the AI import API endpoints."""
    
    def test_import_endpoint_exists(self):
        """Test that the import endpoint is accessible."""
        client = TestClient(app)
        
        # Test with invalid URL to get validation error (not 404)
        response = client.post("/ai/import", json={"url": "invalid-url"})
        assert response.status_code == 422  # Validation error, not 404
    
    def test_test_extraction_endpoint(self):
        """Test the test extraction endpoint."""
        client = TestClient(app)
        response = client.get("/ai/import/test")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "ai_backend" in data
    
    def test_supported_sources_endpoint(self):
        """Test the supported sources endpoint."""
        client = TestClient(app)
        response = client.get("/ai/import/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_sources" in data
        assert "general_support" in data
        assert "limitations" in data


class TestErrorHandling:
    """Test error handling across AI components."""
    
    def test_scraper_timeout_handling(self):
        """Test scraper timeout handling."""
        scraper = RecipeScraper()
        
        with patch('requests.get', side_effect=TimeoutError("Request timeout")):
            result = scraper.scrape_url("https://example.com/recipe")
            assert result is None
    
    def test_extractor_api_error_handling(self):
        """Test extractor API error handling."""
        extractor = RecipeExtractor(api_key="invalid-key")
        
        # Test with mock data
        from app.ai.models import ScrapedData
        sample_data = ScrapedData(
            url="https://example.com/recipe",
            html_content="<h1>Test</h1>",
            title="Test",
            status_code=200
        )
        
        # Should fall back to rule-based extraction
        result = extractor.extract_recipe(sample_data)
        assert result is not None
        assert result.extraction_method == "rule_based"
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        scraper = RecipeScraper()
        
        # Test completely invalid URL
        result = scraper.scrape_url("not-a-url")
        assert result is None
        
        # Test URL with invalid scheme
        result = scraper.scrape_url("ftp://example.com/recipe")
        assert result is None


class TestLoggingIntegration:
    """Test logging integration in AI components."""
    
    def test_import_logging(self):
        """Test that import operations are properly logged."""
        with patch('app.routers.ai_import.logger') as mock_logger:
            client = TestClient(app)
            
            # Make request that will fail validation
            response = client.post("/ai/import", json={"url": "invalid"})
            
            # Should log the request attempt
            assert mock_logger.info.called or mock_logger.error.called
    
    def test_extraction_logging(self):
        """Test that extraction operations are logged."""
        extractor = RecipeExtractor()
        
        with patch('app.ai.extractor.logger') as mock_logger:
            from app.ai.models import ScrapedData
            sample_data = ScrapedData(
                url="https://example.com/recipe",
                html_content="<h1>Test</h1>",
                title="Test",
                status_code=200
            )
            
            extractor.extract_recipe(sample_data)
            
            # Should have logged the extraction attempt
            assert mock_logger.info.called or mock_logger.debug.called


@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for the complete AI pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_import_flow(self):
        """Test the complete end-to-end import flow."""
        # This test requires actual components but mocks external calls
        from app.repositories.recipe_repository import RecipeRepository
        
        repository = Mock()
        repository.create = AsyncMock()
        repository.get_by_source_url = AsyncMock(return_value=None)
        
        importer = RecipeImporter(repository, api_key="test-key")
        
        # Mock the scraping to return structured data
        sample_html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "http://schema.org",
                    "@type": "Recipe",
                    "name": "Integration Test Recipe",
                    "description": "A test recipe for integration testing",
                    "recipeIngredient": ["1 cup flour", "2 eggs"],
                    "recipeInstructions": [
                        {"@type": "HowToStep", "text": "Mix ingredients"}
                    ]
                }
                </script>
            </head>
            <body><h1>Integration Test Recipe</h1></body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = sample_html
            mock_response.headers = {'content-type': 'text/html'}
            mock_get.return_value = mock_response
            
            # Mock repository create
            from app.models.recipe import Recipe
            mock_recipe = Recipe(title="Integration Test Recipe")
            mock_recipe.id = "integration-test-id"
            repository.create.return_value = mock_recipe
            
            # Perform import
            result = await importer.import_recipe_from_url("https://example.com/recipe")
            
            assert result.success is True
            assert result.recipe_id == "integration-test-id"
            
            # Verify repository was called
            repository.create.assert_called_once()
            
            # Verify the created recipe has expected data
            created_recipe = repository.create.call_args[0][0]
            assert created_recipe.title == "Integration Test Recipe"
            assert len(created_recipe.ingredients) == 2
            assert len(created_recipe.instructions) == 1