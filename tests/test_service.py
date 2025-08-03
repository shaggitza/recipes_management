"""
Unit tests for the Recipe Service layer.
Tests business logic, validation, and error handling.
"""
import pytest
from typing import List
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone

from fastapi import HTTPException
from beanie import PydanticObjectId

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, Ingredient, Source
from app.services.recipe_service import RecipeService
from app.repositories.recipe_repository import BaseRepository


class MockRepository(BaseRepository):
    """Mock repository for testing service layer."""
    
    def __init__(self):
        self.recipes = {}
        self.next_id = 1
    
    async def create(self, data: RecipeCreate) -> Recipe:
        # Create a mock recipe instead of a real Recipe document
        recipe_data = data.model_dump()
        recipe_data['id'] = PydanticObjectId()
        recipe_data['created_at'] = datetime.now(timezone.utc)
        recipe_data['updated_at'] = datetime.now(timezone.utc)
        
        # Convert MealTime enums to strings for compatibility
        if 'meal_times' in recipe_data:
            recipe_data['meal_times'] = [mt.value if hasattr(mt, 'value') else mt for mt in recipe_data['meal_times']]
        
        # Use Mock instead of Recipe to avoid database initialization issues
        recipe = Mock(spec=Recipe)
        for key, value in recipe_data.items():
            setattr(recipe, key, value)
        
        self.recipes[str(recipe.id)] = recipe
        return recipe
    
    async def get_by_id(self, recipe_id: PydanticObjectId) -> Recipe:
        return self.recipes.get(str(recipe_id))
    
    async def get_all(self, skip: int = 0, limit: int = 10, filters=None) -> List[Recipe]:
        recipes_list = list(self.recipes.values())
        return recipes_list[skip:skip + limit]
    
    async def update(self, recipe_id: PydanticObjectId, data: RecipeUpdate) -> Recipe:
        recipe = self.recipes.get(str(recipe_id))
        if not recipe:
            return None
        
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            setattr(recipe, field, value)
        
        return recipe
    
    async def delete(self, recipe_id: PydanticObjectId) -> bool:
        recipe_key = str(recipe_id)
        if recipe_key in self.recipes:
            del self.recipes[recipe_key]
            return True
        return False
    
    async def search(self, query: str, skip: int = 0, limit: int = 10) -> List[Recipe]:
        matching_recipes = [
            recipe for recipe in self.recipes.values()
            if query.lower() in recipe.title.lower()
        ]
        return matching_recipes[skip:skip + limit]
    
    async def get_all_tags(self) -> List[str]:
        all_tags = set()
        for recipe in self.recipes.values():
            all_tags.update(recipe.tags)
        return sorted(list(all_tags))
    
    async def count(self, filters=None) -> int:
        return len(self.recipes)
    
    async def get_recipes_by_difficulty(self, difficulty: str) -> List[Recipe]:
        return [
            recipe for recipe in self.recipes.values()
            if recipe.difficulty == difficulty
        ]
    
    async def get_recent_recipes(self, limit: int = 10) -> List[Recipe]:
        recipes_list = sorted(
            self.recipes.values(),
            key=lambda r: r.created_at,
            reverse=True
        )
        return recipes_list[:limit]
    
    async def get_all_meal_times(self) -> List[str]:
        """Get all unique meal times from recipes"""
        meal_times = set()
        for recipe in self.recipes.values():
            meal_times.update(recipe.meal_times)
        return sorted(list(meal_times))
    
    async def get_recipes_by_meal_times(self, meal_times: List[str]) -> List[Recipe]:
        """Get recipes that contain any of the specified meal times"""
        return [
            recipe for recipe in self.recipes.values()
            if any(mt in recipe.meal_times for mt in meal_times)
        ]


class TestRecipeService:
    """Test the RecipeService with proper business logic validation."""
    
    @pytest.fixture
    def mock_repository(self) -> MockRepository:
        """Create a mock repository for testing."""
        return MockRepository()
    
    @pytest.fixture
    def service(self, mock_repository: MockRepository) -> RecipeService:
        """Create a service instance with mock repository."""
        return RecipeService(repository=mock_repository)
    
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
            source=Source(type="manual")
        )
    
    @pytest.mark.asyncio
    async def test_create_recipe_success(
        self, 
        service: RecipeService, 
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test creating a recipe successfully."""
        result = await service.create_recipe(sample_recipe_create)
        
        assert result.title == "Test Recipe"
        assert result.description == "A test recipe"
        assert len(result.ingredients) == 2
        assert len(result.instructions) == 2
        assert result.difficulty == "easy"
    
    @pytest.mark.asyncio
    async def test_create_recipe_empty_title(self, service: RecipeService) -> None:
        """Test creating a recipe with empty title fails."""
        recipe_data = RecipeCreate(
            title="   ",  # Only whitespace
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=["Mix"]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_recipe(recipe_data)
        
        assert exc_info.value.status_code == 400
        assert "title cannot be empty" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_create_recipe_no_ingredients(self, service: RecipeService) -> None:
        """Test creating a recipe without ingredients fails."""
        recipe_data = RecipeCreate(
            title="Test Recipe",
            ingredients=[],  # No ingredients
            instructions=["Mix"]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_recipe(recipe_data)
        
        assert exc_info.value.status_code == 400
        assert "at least one ingredient" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_create_recipe_no_instructions(self, service: RecipeService) -> None:
        """Test creating a recipe without instructions fails."""
        recipe_data = RecipeCreate(
            title="Test Recipe",
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=[]  # No instructions
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_recipe(recipe_data)
        
        assert exc_info.value.status_code == 400
        assert "at least one instruction" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recipe_by_id_success(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test getting a recipe by ID successfully."""
        # First create a recipe
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        # Then retrieve it
        result = await service.get_recipe_by_id(str(created_recipe.id))
        
        assert result.id == created_recipe.id
        assert result.title == "Test Recipe"
    
    @pytest.mark.asyncio
    async def test_get_recipe_by_id_invalid_format(self, service: RecipeService) -> None:
        """Test getting a recipe with invalid ID format."""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipe_by_id("invalid-id")
        
        assert exc_info.value.status_code == 400
        assert "Invalid recipe ID format" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recipe_by_id_not_found(self, service: RecipeService) -> None:
        """Test getting a non-existent recipe."""
        fake_id = str(PydanticObjectId())
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipe_by_id(fake_id)
        
        assert exc_info.value.status_code == 404
        assert "Recipe not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recipes_with_pagination(self, service: RecipeService) -> None:
        """Test getting recipes with pagination parameters."""
        # Create multiple recipes
        for i in range(5):
            recipe_data = RecipeCreate(
                title=f"Recipe {i}",
                ingredients=[Ingredient(name="Flour", amount="1")],
                instructions=["Mix"]
            )
            await service.create_recipe(recipe_data)
        
        # Test pagination
        result = await service.get_recipes(skip=1, limit=2)
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_recipes_invalid_pagination(self, service: RecipeService) -> None:
        """Test getting recipes with invalid pagination parameters."""
        # Negative skip
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipes(skip=-1)
        
        assert exc_info.value.status_code == 400
        assert "non-negative" in exc_info.value.detail
        
        # Invalid limit
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipes(limit=0)
        
        assert exc_info.value.status_code == 400
        assert "between 1 and 100" in exc_info.value.detail
        
        # Limit too large
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipes(limit=101)
        
        assert exc_info.value.status_code == 400
        assert "between 1 and 100" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recipes_invalid_difficulty(self, service: RecipeService) -> None:
        """Test getting recipes with invalid difficulty filter."""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipes(difficulty="invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid difficulty level" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_recipe_success(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test updating a recipe successfully."""
        # Create a recipe first
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        # Update it
        update_data = RecipeUpdate(
            title="Updated Recipe",
            difficulty="hard"
        )
        
        result = await service.update_recipe(str(created_recipe.id), update_data)
        
        assert result.title == "Updated Recipe"
        assert result.difficulty == "hard"
        assert result.description == "A test recipe"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_recipe_empty_title(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test updating a recipe with empty title fails."""
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        update_data = RecipeUpdate(title="   ")  # Only whitespace
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_recipe(str(created_recipe.id), update_data)
        
        assert exc_info.value.status_code == 400
        assert "title cannot be empty" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_recipe_empty_ingredients(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test updating a recipe with empty ingredients fails."""
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        update_data = RecipeUpdate(ingredients=[])  # Empty list
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_recipe(str(created_recipe.id), update_data)
        
        assert exc_info.value.status_code == 400
        assert "at least one ingredient" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_recipe_empty_instructions(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test updating a recipe with empty instructions fails."""
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        update_data = RecipeUpdate(instructions=[])  # Empty list
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_recipe(str(created_recipe.id), update_data)
        
        assert exc_info.value.status_code == 400
        assert "at least one instruction" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_update_recipe_not_found(self, service: RecipeService) -> None:
        """Test updating a non-existent recipe."""
        fake_id = str(PydanticObjectId())
        update_data = RecipeUpdate(title="Updated")
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_recipe(fake_id, update_data)
        
        assert exc_info.value.status_code == 404
        assert "Recipe not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_delete_recipe_success(
        self, 
        service: RecipeService,
        sample_recipe_create: RecipeCreate
    ) -> None:
        """Test deleting a recipe successfully."""
        created_recipe = await service.create_recipe(sample_recipe_create)
        
        result = await service.delete_recipe(str(created_recipe.id))
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_recipe_not_found(self, service: RecipeService) -> None:
        """Test deleting a non-existent recipe."""
        fake_id = str(PydanticObjectId())
        
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_recipe(fake_id)
        
        assert exc_info.value.status_code == 404
        assert "Recipe not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_search_recipes_success(self, service: RecipeService) -> None:
        """Test searching recipes successfully."""
        # Create test recipes
        recipe_data1 = RecipeCreate(
            title="Chocolate Cake",
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=["Mix"]
        )
        recipe_data2 = RecipeCreate(
            title="Vanilla Ice Cream",
            ingredients=[Ingredient(name="Cream", amount="1")],
            instructions=["Freeze"]
        )
        
        await service.create_recipe(recipe_data1)
        await service.create_recipe(recipe_data2)
        
        # Search for chocolate
        result = await service.search_recipes("Chocolate")
        
        assert len(result) == 1
        assert "Chocolate" in result[0].title
    
    @pytest.mark.asyncio
    async def test_search_recipes_empty_query(self, service: RecipeService) -> None:
        """Test searching with empty query fails."""
        with pytest.raises(HTTPException) as exc_info:
            await service.search_recipes("   ")  # Only whitespace
        
        assert exc_info.value.status_code == 400
        assert "Search query cannot be empty" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_search_recipes_invalid_pagination(self, service: RecipeService) -> None:
        """Test searching with invalid pagination parameters."""
        with pytest.raises(HTTPException) as exc_info:
            await service.search_recipes("test", skip=-1)
        
        assert exc_info.value.status_code == 400
        assert "non-negative" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_all_tags(self, service: RecipeService) -> None:
        """Test getting all unique tags."""
        # Create recipes with different tags
        recipe1 = RecipeCreate(
            title="Recipe 1",
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=["Mix"],
            tags=["vegetarian", "quick"]
        )
        recipe2 = RecipeCreate(
            title="Recipe 2",
            ingredients=[Ingredient(name="Meat", amount="1")],
            instructions=["Cook"],
            tags=["quick", "protein"]
        )
        
        await service.create_recipe(recipe1)
        await service.create_recipe(recipe2)
        
        result = await service.get_all_tags()
        
        assert "vegetarian" in result
        assert "quick" in result
        assert "protein" in result
        assert len(set(result)) == len(result)  # No duplicates
    
    @pytest.mark.asyncio
    async def test_get_recipe_count(self, service: RecipeService) -> None:
        """Test getting recipe count."""
        # Create some recipes
        for i in range(3):
            recipe_data = RecipeCreate(
                title=f"Recipe {i}",
                ingredients=[Ingredient(name="Flour", amount="1")],
                instructions=["Mix"]
            )
            await service.create_recipe(recipe_data)
        
        result = await service.get_recipe_count()
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_get_recipe_count_invalid_difficulty(self, service: RecipeService) -> None:
        """Test getting recipe count with invalid difficulty."""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipe_count(difficulty="invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid difficulty level" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recipes_by_difficulty(self, service: RecipeService) -> None:
        """Test getting recipes by difficulty level."""
        easy_recipe = RecipeCreate(
            title="Easy Recipe",
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=["Mix"],
            difficulty="easy"
        )
        hard_recipe = RecipeCreate(
            title="Hard Recipe",
            ingredients=[Ingredient(name="Flour", amount="1")],
            instructions=["Mix"],
            difficulty="hard"
        )
        
        await service.create_recipe(easy_recipe)
        await service.create_recipe(hard_recipe)
        
        result = await service.get_recipes_by_difficulty("easy")
        
        assert len(result) == 1
        assert result[0].difficulty == "easy"
    
    @pytest.mark.asyncio
    async def test_get_recipes_by_difficulty_invalid(self, service: RecipeService) -> None:
        """Test getting recipes by invalid difficulty."""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recipes_by_difficulty("invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid difficulty level" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_recent_recipes(self, service: RecipeService) -> None:
        """Test getting recent recipes."""
        # Create some recipes
        for i in range(5):
            recipe_data = RecipeCreate(
                title=f"Recipe {i}",
                ingredients=[Ingredient(name="Flour", amount="1")],
                instructions=["Mix"]
            )
            await service.create_recipe(recipe_data)
        
        result = await service.get_recent_recipes(3)
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_get_recent_recipes_invalid_limit(self, service: RecipeService) -> None:
        """Test getting recent recipes with invalid limit."""
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recent_recipes(0)
        
        assert exc_info.value.status_code == 400
        assert "between 1 and 100" in exc_info.value.detail
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_recent_recipes(101)
        
        assert exc_info.value.status_code == 400
        assert "between 1 and 100" in exc_info.value.detail