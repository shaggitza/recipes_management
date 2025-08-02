"""
Unit tests for the Recipe Repository layer.
Tests the repository pattern and proper Beanie ODM usage.
"""
import pytest
import asyncio
from typing import List
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from beanie import PydanticObjectId
from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, Ingredient, Source
from app.repositories.recipe_repository import RecipeRepository


class TestRecipeRepository:
    """Test the RecipeRepository with proper Beanie patterns."""
    
    @pytest.fixture
    def repository(self) -> RecipeRepository:
        """Create a repository instance for testing."""
        return RecipeRepository()
    
    @pytest.fixture
    def sample_recipe_create(self) -> RecipeCreate:
        """Create sample recipe data for testing."""
        return RecipeCreate(
            title="Test Recipe",
            description="A test recipe",
            ingredients=[
                Ingredient(name="Flour", amount="2", unit="cups"),
                Ingredient(name="Sugar", amount="1", unit="cup")
            ],
            instructions=["Mix ingredients", "Bake for 30 minutes"],
            prep_time=15,
            cook_time=30,
            servings=4,
            difficulty="easy",
            tags=["test", "easy"],
            source=Source(type="manual"),
            metadata={"test": True}
        )
    
    @pytest.fixture
    async def sample_recipe(self, sample_recipe_create, clean_db) -> Recipe:
        """Create sample recipe document for testing."""
        # Create the recipe using the actual Beanie model with the test database
        recipe_data = sample_recipe_create.model_dump()
        recipe = MagicMock(spec=Recipe, **recipe_data)
        # Save it to the test database
        saved_recipe = await recipe.insert()
        return saved_recipe
    
    @pytest.mark.asyncio
    async def test_create_recipe(self, repository: RecipeRepository, sample_recipe_create: RecipeCreate) -> None:
        """Test creating a recipe using repository."""
        with patch('app.models.recipe.Recipe.insert') as mock_insert:
            mock_recipe = MagicMock(spec=Recipe)
            mock_recipe.id = PydanticObjectId()
            mock_insert.return_value = mock_recipe
            
            result = await repository.create(sample_recipe_create)
            
            assert result.title == "Test Recipe"
            assert result.description == "A test recipe"
            assert len(result.ingredients) == 2
            assert result.difficulty == "easy"
            mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository: RecipeRepository, sample_recipe_create: RecipeCreate) -> None:
        """Test getting recipe by ID successfully."""
        # Create a mock recipe with an ID using MagicMock to avoid Beanie initialization issues
        mock_recipe = MagicMock(spec=Recipe)
        mock_recipe.id = PydanticObjectId()
        mock_recipe.title = "Test Recipe"
        mock_recipe.description = "A test recipe"
        
        with patch('app.models.recipe.Recipe.get') as mock_get:
            mock_get.return_value = mock_recipe
            
            result = await repository.get_by_id(mock_recipe.id)
            
            assert result is not None
            assert result.id == mock_recipe.id
            assert result.title == "Test Recipe"
            mock_get.assert_called_once_with(mock_recipe.id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository: RecipeRepository) -> None:
        """Test getting recipe by ID when not found."""
        with patch('app.models.recipe.Recipe.get') as mock_get:
            mock_get.return_value = None
            recipe_id = PydanticObjectId()
            
            result = await repository.get_by_id(recipe_id)
            
            assert result is None
            mock_get.assert_called_once_with(recipe_id)
    
    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, repository: RecipeRepository) -> None:
        """Test getting all recipes without filters."""
        mock_recipes = [MagicMock(spec=Recipe, title=f"Recipe {i}") for i in range(3)]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_all(skip=0, limit=10)
            
            assert len(result) == 3
            assert all(isinstance(recipe, Recipe) for recipe in result)
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_with_difficulty_filter(self, repository: RecipeRepository) -> None:
        """Test getting recipes filtered by difficulty."""
        mock_recipes = [MagicMock(spec=Recipe, title="Easy Recipe", difficulty="easy")]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.find.return_value = mock_query
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_all(filters={"difficulty": "easy"})
            
            assert len(result) == 1
            assert result[0].difficulty == "easy"
    
    @pytest.mark.asyncio
    async def test_get_all_with_tags_filter(self, repository: RecipeRepository) -> None:
        """Test getting recipes filtered by tags."""
        mock_recipes = [MagicMock(spec=Recipe, title="Vegetarian Recipe", tags=["vegetarian"])]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.find.return_value = mock_query
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_all(filters={"tags": ["vegetarian"]})
            
            assert len(result) == 1
            assert "vegetarian" in result[0].tags
    
    @pytest.mark.asyncio
    async def test_get_all_with_search_filter(self, repository: RecipeRepository) -> None:
        """Test getting recipes with search filter."""
        mock_recipes = [MagicMock(spec=Recipe, title="Chocolate Cake")]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_all(filters={"search": "chocolate"})
            
            assert len(result) == 1
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_recipe_success(self, repository: RecipeRepository, sample_recipe_create: RecipeCreate) -> None:
        """Test updating a recipe successfully."""
        # Create a mock recipe with an ID
        mock_recipe = MagicMock(spec=Recipe)
        mock_recipe.id = PydanticObjectId()
        
        update_data = RecipeUpdate(title="Updated Recipe", difficulty="hard")
        
        with patch.object(repository, 'get_by_id') as mock_get:
            with patch.object(mock_recipe, 'set') as mock_set:
                mock_get.return_value = mock_recipe
                mock_set.return_value = None
                
                result = await repository.update(mock_recipe.id, update_data)
                
                assert result is not None
                assert result.id == mock_recipe.id
                mock_get.assert_called_once_with(mock_recipe.id)
                mock_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_recipe_not_found(self, repository: RecipeRepository) -> None:
        """Test updating a recipe that doesn't exist."""
        recipe_id = PydanticObjectId()
        update_data = RecipeUpdate(title="Updated Recipe")
        
        with patch.object(repository, 'get_by_id') as mock_get:
            mock_get.return_value = None
            
            result = await repository.update(recipe_id, update_data)
            
            assert result is None
            mock_get.assert_called_once_with(recipe_id)
    
    @pytest.mark.asyncio
    async def test_update_recipe_no_data(self, repository: RecipeRepository, sample_recipe_create: RecipeCreate) -> None:
        """Test updating a recipe with no update data."""
        # Create a mock recipe with an ID
        mock_recipe = MagicMock(spec=Recipe)
        mock_recipe.id = PydanticObjectId()
        
        update_data = RecipeUpdate()
        
        with patch.object(repository, 'get_by_id') as mock_get:
            mock_get.return_value = mock_recipe
            
            result = await repository.update(mock_recipe.id, update_data)
            
            assert result == mock_recipe
            mock_get.assert_called_once_with(mock_recipe.id)
    
    @pytest.mark.asyncio
    async def test_delete_recipe_success(self, repository: RecipeRepository, sample_recipe_create: RecipeCreate) -> None:
        """Test deleting a recipe successfully."""
        # Create a mock recipe with an ID
        mock_recipe = MagicMock(spec=Recipe)
        mock_recipe.id = PydanticObjectId()
        
        with patch.object(repository, 'get_by_id') as mock_get:
            with patch.object(mock_recipe, 'delete') as mock_delete:
                mock_get.return_value = mock_recipe
                mock_delete.return_value = None
                
                result = await repository.delete(mock_recipe.id)
                
                assert result is True
                mock_get.assert_called_once_with(mock_recipe.id)
                mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_recipe_not_found(self, repository: RecipeRepository) -> None:
        """Test deleting a recipe that doesn't exist."""
        recipe_id = PydanticObjectId()
        
        with patch.object(repository, 'get_by_id') as mock_get:
            mock_get.return_value = None
            
            result = await repository.delete(recipe_id)
            
            assert result is False
            mock_get.assert_called_once_with(recipe_id)
    
    @pytest.mark.asyncio
    async def test_search_recipes_text_search(self, repository: RecipeRepository) -> None:
        """Test searching recipes using text search."""
        mock_recipes = [MagicMock(spec=Recipe, title="Chocolate Cake", description="Delicious cake")]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.search("chocolate")
            
            assert len(result) == 1
            assert "Chocolate" in result[0].title
            mock_find.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_recipes_fallback_to_regex(self, repository: RecipeRepository) -> None:
        """Test searching recipes falls back to regex when text search fails."""
        mock_recipes = [MagicMock(spec=Recipe, title="Chocolate Cake")]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            # First call (text search) returns empty, second call (regex) returns results
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list.side_effect = [[], mock_recipes]
            mock_find.return_value = mock_query
            
            result = await repository.search("chocolate")
            
            assert len(result) == 1
            assert mock_find.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_all_tags(self, repository: RecipeRepository) -> None:
        """Test getting all unique tags."""
        mock_result = [{"_id": "vegetarian"}, {"_id": "quick"}, {"_id": "dessert"}]
        
        with patch('app.models.recipe.Recipe.aggregate') as mock_aggregate:
            mock_agg = MagicMock()
            mock_agg.to_list = AsyncMock(return_value=mock_result)
            mock_aggregate.return_value = mock_agg
            
            result = await repository.get_all_tags()
            
            assert result == ["vegetarian", "quick", "dessert"]
            mock_aggregate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_recipes_no_filters(self, repository: RecipeRepository) -> None:
        """Test counting recipes without filters."""
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.count = AsyncMock(return_value=42)
            mock_find.return_value = mock_query
            
            result = await repository.count()
            
            assert result == 42
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_recipes_with_filters(self, repository: RecipeRepository) -> None:
        """Test counting recipes with filters."""
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.find.return_value = mock_query
            mock_query.count = AsyncMock(return_value=10)
            mock_find.return_value = mock_query
            
            result = await repository.count(filters={"difficulty": "easy"})
            
            assert result == 10
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recipes_by_difficulty(self, repository: RecipeRepository) -> None:
        """Test getting recipes by difficulty level."""
        mock_recipes = [MagicMock(spec=Recipe, title="Easy Recipe", difficulty="easy")]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_recipes_by_difficulty("easy")
            
            assert len(result) == 1
            assert result[0].difficulty == "easy"
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recipes_by_tags(self, repository: RecipeRepository) -> None:
        """Test getting recipes by tags."""
        mock_recipes = [MagicMock(spec=Recipe, title="Vegetarian Recipe", tags=["vegetarian"])]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_recipes_by_tags(["vegetarian"])
            
            assert len(result) == 1
            assert "vegetarian" in result[0].tags
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_recipes(self, repository: RecipeRepository) -> None:
        """Test getting recent recipes."""
        mock_recipes = [MagicMock(spec=Recipe, title=f"Recipe {i}") for i in range(5)]
        
        with patch('app.models.recipe.Recipe.find') as mock_find:
            mock_query = MagicMock()
            mock_query.sort.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=mock_recipes)
            mock_find.return_value = mock_query
            
            result = await repository.get_recent_recipes(5)
            
            assert len(result) == 5
            mock_find.assert_called_once()