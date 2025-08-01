"""
Unit tests for the Recipe Management models and validation.
Tests the Pydantic models and validation logic in isolation.
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime
from pydantic import ValidationError

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeResponse, Ingredient, Source

class TestIngredientModel:
    """Test the Ingredient model."""
    
    def test_ingredient_creation_valid(self) -> None:
        """Test creating a valid ingredient."""
        ingredient = Ingredient(name="Flour", amount="2", unit="cups")
        assert ingredient.name == "Flour"
        assert ingredient.amount == "2"
        assert ingredient.unit == "cups"
    
    def test_ingredient_creation_without_unit(self) -> None:
        """Test creating an ingredient without unit."""
        ingredient = Ingredient(name="Salt", amount="1")
        assert ingredient.name == "Salt"
        assert ingredient.amount == "1"
        assert ingredient.unit is None
    
    def test_ingredient_creation_with_none_unit(self) -> None:
        """Test creating an ingredient with explicit None unit."""
        ingredient = Ingredient(name="Pepper", amount="1", unit=None)
        assert ingredient.name == "Pepper"
        assert ingredient.amount == "1"
        assert ingredient.unit is None

class TestSourceModel:
    """Test the Source model."""
    
    def test_source_default_manual(self) -> None:
        """Test default source creation."""
        source = Source()
        assert source.type == "manual"
        assert source.url is None
        assert source.name is None
    
    def test_source_tiktok(self) -> None:
        """Test TikTok source creation."""
        source = Source(
            type="tiktok",
            url="https://tiktok.com/@user/video/123",
            name="Viral Recipe Creator"
        )
        assert source.type == "tiktok"
        assert source.url == "https://tiktok.com/@user/video/123"
        assert source.name == "Viral Recipe Creator"
    
    def test_source_website(self) -> None:
        """Test website source creation."""
        source = Source(
            type="website",
            url="https://example.com/recipe",
            name="Example Recipe Site"
        )
        assert source.type == "website"
        assert source.url == "https://example.com/recipe"
        assert source.name == "Example Recipe Site"

class TestRecipeCreateModel:
    """Test the RecipeCreate model."""
    
    def test_recipe_create_minimal(self) -> None:
        """Test creating a recipe with minimal data."""
        recipe = RecipeCreate(title="Test Recipe")
        assert recipe.title == "Test Recipe"
        assert recipe.description is None
        assert recipe.ingredients == []
        assert recipe.instructions == []
        assert recipe.prep_time is None
        assert recipe.cook_time is None
        assert recipe.servings is None
        assert recipe.difficulty is None
        assert recipe.tags == []
        assert recipe.source.type == "manual"
        assert recipe.images == []
        assert recipe.metadata == {}
    
    def test_recipe_create_full(self) -> None:
        """Test creating a recipe with all fields."""
        recipe_data = {
            "title": "Full Test Recipe",
            "description": "A complete test recipe",
            "ingredients": [
                {"name": "Flour", "amount": "2", "unit": "cups"},
                {"name": "Sugar", "amount": "1", "unit": "cup"}
            ],
            "instructions": ["Mix ingredients", "Bake"],
            "prep_time": 15,
            "cook_time": 30,
            "servings": 4,
            "difficulty": "medium",
            "tags": ["dessert", "baking"],
            "source": {
                "type": "website",
                "url": "https://example.com",
                "name": "Example Site"
            },
            "images": ["https://example.com/image.jpg"],
            "metadata": {"author": "Test Chef"}
        }
        
        recipe = RecipeCreate(**recipe_data)
        assert recipe.title == "Full Test Recipe"
        assert recipe.description == "A complete test recipe"
        assert len(recipe.ingredients) == 2
        assert recipe.ingredients[0].name == "Flour"
        assert len(recipe.instructions) == 2
        assert recipe.prep_time == 15
        assert recipe.cook_time == 30
        assert recipe.servings == 4
        assert recipe.difficulty == "medium"
        assert recipe.tags == ["dessert", "baking"]
        assert recipe.source.type == "website"
        assert recipe.images == ["https://example.com/image.jpg"]
        assert recipe.metadata == {"author": "Test Chef"}
    
    def test_recipe_create_validation_errors(self) -> None:
        """Test validation errors in RecipeCreate."""
        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="")
        assert "title" in str(exc_info.value)
        
        # Invalid difficulty should fail
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", difficulty="invalid")
        assert "difficulty" in str(exc_info.value)
        
        # Negative prep_time should fail
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", prep_time=-5)
        assert "prep_time" in str(exc_info.value)
        
        # Zero servings should fail
        with pytest.raises(ValidationError) as exc_info:
            RecipeCreate(title="Test", servings=0)
        assert "servings" in str(exc_info.value)
    
    def test_recipe_create_difficulty_validation(self) -> None:
        """Test difficulty field validation."""
        # Valid difficulties
        for difficulty in ["easy", "medium", "hard"]:
            recipe = RecipeCreate(title="Test", difficulty=difficulty)
            assert recipe.difficulty == difficulty
        
        # Invalid difficulty
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", difficulty="super_hard")

class TestRecipeUpdateModel:
    """Test the RecipeUpdate model."""
    
    def test_recipe_update_partial(self) -> None:
        """Test partial recipe update."""
        update = RecipeUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None
        assert update.ingredients is None
        assert update.prep_time is None
    
    def test_recipe_update_multiple_fields(self) -> None:
        """Test updating multiple fields."""
        update = RecipeUpdate(
            title="Updated Recipe",
            description="Updated description",
            difficulty="hard"
        )
        assert update.title == "Updated Recipe"
        assert update.description == "Updated description"
        assert update.difficulty == "hard"
        assert update.prep_time is None  # Not updated
    
    def test_recipe_update_validation(self) -> None:
        """Test validation in RecipeUpdate."""
        # Invalid difficulty should fail
        with pytest.raises(ValidationError):
            RecipeUpdate(difficulty="invalid")
        
        # Empty title should fail
        with pytest.raises(ValidationError):
            RecipeUpdate(title="")

class TestRecipeResponseModel:
    """Test the RecipeResponse model."""
    
    def test_recipe_response_creation(self) -> None:
        """Test creating a RecipeResponse."""
        from bson import ObjectId
        
        object_id = str(ObjectId())
        response_data = {
            "id": object_id,
            "title": "Response Test Recipe",
            "description": "Test recipe response",
            "ingredients": [],
            "instructions": [],
            "prep_time": None,
            "cook_time": None,
            "servings": None,
            "difficulty": None,
            "tags": [],
            "source": {"type": "manual"},
            "images": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
        
        response = RecipeResponse(**response_data)
        assert response.id == object_id
        assert response.title == "Response Test Recipe"
        assert response.description == "Test recipe response"

class TestRecipeModelValidation:
    """Test comprehensive recipe model validation."""
    
    def test_title_length_validation(self) -> None:
        """Test title length constraints."""
        # Valid title
        recipe = RecipeCreate(title="A" * 200)  # Exactly 200 chars
        assert len(recipe.title) == 200
        
        # Title too long should fail
        with pytest.raises(ValidationError):
            RecipeCreate(title="A" * 201)  # 201 chars
    
    def test_description_length_validation(self) -> None:
        """Test description length constraints."""
        # Valid description
        recipe = RecipeCreate(title="Test", description="A" * 1000)  # Exactly 1000 chars
        assert len(recipe.description) == 1000
        
        # Description too long should fail
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", description="A" * 1001)  # 1001 chars
    
    def test_numeric_field_validation(self) -> None:
        """Test numeric field constraints."""
        # Valid numeric values
        recipe = RecipeCreate(
            title="Test",
            prep_time=0,  # Minimum valid value
            cook_time=0,  # Minimum valid value
            servings=1    # Minimum valid value
        )
        assert recipe.prep_time == 0
        assert recipe.cook_time == 0
        assert recipe.servings == 1
        
        # Large valid values
        recipe = RecipeCreate(
            title="Test",
            prep_time=9999,
            cook_time=9999,
            servings=9999
        )
        assert recipe.prep_time == 9999
    
    def test_complex_ingredient_validation(self) -> None:
        """Test complex ingredient scenarios."""
        ingredients = [
            {"name": "Flour", "amount": "2", "unit": "cups"},
            {"name": "Eggs", "amount": "3", "unit": None},
            {"name": "Salt", "amount": "1", "unit": "pinch"},
            {"name": "Water", "amount": "as needed"}  # No unit specified
        ]
        
        recipe = RecipeCreate(title="Test", ingredients=ingredients)
        assert len(recipe.ingredients) == 4
        assert recipe.ingredients[0].unit == "cups"
        assert recipe.ingredients[1].unit is None
        assert recipe.ingredients[2].unit == "pinch"
        assert recipe.ingredients[3].unit is None
    
    def test_metadata_flexibility(self) -> None:
        """Test metadata field flexibility."""
        complex_metadata = {
            "author": "Test Chef",
            "created_by_bot": True,
            "nutrition": {
                "calories": 350,
                "protein": "15g",
                "carbs": "45g"
            },
            "tags_source": ["automated", "verified"],
            "difficulty_score": 7.5,
            "custom_field": None,
            "nested": {
                "deeply": {
                    "nested": {
                        "value": "test"
                    }
                }
            }
        }
        
        recipe = RecipeCreate(title="Test", metadata=complex_metadata)
        assert recipe.metadata["author"] == "Test Chef"
        assert recipe.metadata["created_by_bot"] is True
        assert recipe.metadata["nutrition"]["calories"] == 350
        assert recipe.metadata["custom_field"] is None
        assert recipe.metadata["nested"]["deeply"]["nested"]["value"] == "test"

class TestModelInteraction:
    """Test interaction between different models."""
    
    def test_create_to_response_conversion(self) -> None:
        """Test converting RecipeCreate to RecipeResponse format."""
        from bson import ObjectId
        
        create_data = {
            "title": "Conversion Test",
            "description": "Testing model conversion",
            "ingredients": [{"name": "Test", "amount": "1"}],
            "instructions": ["Do something"],
            "difficulty": "easy",
            "tags": ["test"],
            "metadata": {"test": True}
        }
        
        recipe_create = RecipeCreate(**create_data)
        
        # Simulate what would happen in the API
        recipe_dict = recipe_create.model_dump()
        recipe_dict["id"] = str(ObjectId())
        recipe_dict["created_at"] = datetime.utcnow()
        recipe_dict["updated_at"] = datetime.utcnow()
        
        response = RecipeResponse(**recipe_dict)
        
        assert response.title == create_data["title"]
        assert response.description == create_data["description"]
        assert len(response.ingredients) == 1
        assert response.difficulty == "easy"
        assert response.metadata["test"] is True
    
    def test_update_model_exclusion(self) -> None:
        """Test that RecipeUpdate properly excludes unset fields."""
        update = RecipeUpdate(title="Updated")
        
        # Only title should be in the dict when excluding unset
        update_dict = update.model_dump(exclude_unset=True)
        assert "title" in update_dict
        assert "description" not in update_dict
        assert "prep_time" not in update_dict
        
        # All fields should be present when not excluding unset
        full_dict = update.model_dump(exclude_unset=False)
        assert "title" in full_dict
        assert "description" in full_dict
        assert "prep_time" in full_dict