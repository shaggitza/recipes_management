"""
Unit tests for the Recipe Management models and validation.
Tests the Pydantic models with proper validation logic.
"""
import pytest
from typing import Dict, Any, List
from datetime import datetime, timezone
from pydantic import ValidationError

from app.models.recipe import RecipeCreate, RecipeUpdate, RecipeResponse, Ingredient, Source


class TestIngredientModel:
    """Test the Ingredient model with proper validation."""
    
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
    
    def test_ingredient_validation_errors(self) -> None:
        """Test ingredient validation errors."""
        # Empty name
        with pytest.raises(ValidationError):
            Ingredient(name="", amount="1")
        
        # Empty amount
        with pytest.raises(ValidationError):
            Ingredient(name="Salt", amount="")
        
        # Name too long
        with pytest.raises(ValidationError):
            Ingredient(name="a" * 101, amount="1")
        
        # Amount too long
        with pytest.raises(ValidationError):
            Ingredient(name="Salt", amount="a" * 51)


class TestSourceModel:
    """Test the Source model with Literal types."""
    
    def test_source_creation_default(self) -> None:
        """Test creating a default source."""
        source = Source()
        assert source.type == "manual"
        assert source.url is None
        assert source.name is None
    
    def test_source_creation_tiktok(self) -> None:
        """Test creating a TikTok source."""
        source = Source(
            type="tiktok",
            url="https://tiktok.com/@user/video/123",
            name="TikTok Recipe"
        )
        assert source.type == "tiktok"
        assert source.url == "https://tiktok.com/@user/video/123"
        assert source.name == "TikTok Recipe"
    
    def test_source_validation_errors(self) -> None:
        """Test source validation errors."""
        # Invalid type
        with pytest.raises(ValidationError):
            Source(type="invalid_type")
        
        # URL too long
        with pytest.raises(ValidationError):
            Source(type="website", url="a" * 501)
        
        # Name too long
        with pytest.raises(ValidationError):
            Source(type="book", name="a" * 201)


class TestRecipeCreateModel:
    """Test the RecipeCreate model."""
    
    def test_recipe_create_minimal(self) -> None:
        """Test creating RecipeCreate with minimal fields."""
        recipe_data = RecipeCreate(title="Test Recipe")
        assert recipe_data.title == "Test Recipe"
        assert recipe_data.description is None
        assert recipe_data.ingredients == []
        assert recipe_data.instructions == []
    
    def test_recipe_create_full(self) -> None:
        """Test creating RecipeCreate with all fields."""
        ingredients = [Ingredient(name="Flour", amount="2", unit="cups")]
        source = Source(type="website", url="https://example.com")
        
        recipe_data = RecipeCreate(
            title="Full Recipe",
            description="A complete recipe",
            ingredients=ingredients,
            instructions=["Mix ingredients"],
            prep_time=15,
            cook_time=30,
            servings=4,
            difficulty="easy",
            tags=["quick", "easy"],
            source=source,
            images=["image.jpg"],
            metadata={"notes": "test"}
        )
        
        assert recipe_data.title == "Full Recipe"
        assert len(recipe_data.ingredients) == 1
        assert recipe_data.difficulty == "easy"
        assert recipe_data.tags == ["quick", "easy"]
    
    def test_recipe_create_tag_normalization(self) -> None:
        """Test tag normalization in RecipeCreate."""
        recipe_data = RecipeCreate(
            title="Test",
            tags=["VEGETARIAN", "  quick  ", "vegetarian"]
        )
        assert set(recipe_data.tags) == {"vegetarian", "quick"}
    
    def test_recipe_create_validation_errors(self) -> None:
        """Test RecipeCreate validation errors."""
        # Empty title
        with pytest.raises(ValidationError):
            RecipeCreate(title="")
        
        # Title too long
        with pytest.raises(ValidationError):
            RecipeCreate(title="a" * 201)
        
        # Description too long
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", description="a" * 1001)
        
        # Invalid prep time
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", prep_time=-1)
        
        # Prep time too large
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", prep_time=1441)
        
        # Invalid servings
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", servings=0)
        
        # Too many servings
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", servings=101)
        
        # Invalid difficulty
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", difficulty="invalid")
        
        # Too many tags
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", tags=["tag"] * 21)
        
        # Too many images
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", images=["image.jpg"] * 11)
    
    def test_recipe_create_difficulty_validation(self) -> None:
        """Test difficulty validation in RecipeCreate."""
        # Valid difficulties
        for difficulty in ["easy", "medium", "hard"]:
            recipe = RecipeCreate(title="Test", difficulty=difficulty)
            assert recipe.difficulty == difficulty
        
        # Invalid difficulty
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", difficulty="invalid")


class TestRecipeUpdateModel:
    """Test the RecipeUpdate model."""
    
    def test_recipe_update_empty(self) -> None:
        """Test creating empty RecipeUpdate."""
        recipe_update = RecipeUpdate()
        assert recipe_update.title is None
        assert recipe_update.description is None
        assert recipe_update.ingredients is None
    
    def test_recipe_update_partial(self) -> None:
        """Test creating partial RecipeUpdate."""
        recipe_update = RecipeUpdate(
            title="Updated Title",
            difficulty="hard",
            tags=["updated"]
        )
        assert recipe_update.title == "Updated Title"
        assert recipe_update.difficulty == "hard"
        assert recipe_update.tags == ["updated"]
        assert recipe_update.description is None
    
    def test_recipe_update_multiple_fields(self) -> None:
        """Test updating multiple fields."""
        ingredients = [Ingredient(name="Updated Flour", amount="3", unit="cups")]
        recipe_update = RecipeUpdate(
            title="Updated Recipe",
            ingredients=ingredients,
            prep_time=20,
            cook_time=40,
            servings=6,
            difficulty="medium"
        )
        
        assert recipe_update.title == "Updated Recipe"
        assert len(recipe_update.ingredients) == 1
        assert recipe_update.prep_time == 20
        assert recipe_update.cook_time == 40
        assert recipe_update.servings == 6
        assert recipe_update.difficulty == "medium"
    
    def test_recipe_update_tag_normalization(self) -> None:
        """Test tag normalization in RecipeUpdate."""
        recipe_update = RecipeUpdate(tags=["UPDATED", "  tag  "])
        assert set(recipe_update.tags) == {"updated", "tag"}
    
    def test_recipe_update_validation(self) -> None:
        """Test RecipeUpdate validation."""
        # Valid update
        update = RecipeUpdate(title="Valid Title", prep_time=30)
        assert update.title == "Valid Title"
        
        # Invalid title length
        with pytest.raises(ValidationError):
            RecipeUpdate(title="a" * 201)
        
        # Invalid prep time
        with pytest.raises(ValidationError):
            RecipeUpdate(prep_time=-1)


class TestRecipeResponseModel:
    """Test the RecipeResponse model with proper ID handling."""
    
    def test_recipe_response_creation(self) -> None:
        """Test creating RecipeResponse with proper field mapping."""
        response_data = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "Test Recipe",
            "description": "Test description",
            "ingredients": [{"name": "Flour", "amount": "1", "unit": "cup"}],
            "instructions": ["Mix"],
            "prep_time": 15,
            "cook_time": 30,
            "servings": 4,
            "difficulty": "easy",
            "tags": ["test"],
            "source": {"type": "manual"},
            "images": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "metadata": {}
        }
        
        response = RecipeResponse(**response_data)
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.title == "Test Recipe"
        assert response.difficulty == "easy"
        assert response.total_time == 45


class TestRecipeModelValidation:
    """Test Recipe model validation with edge cases."""
    
    def test_title_length_validation(self) -> None:
        """Test title length constraints."""
        # Valid title
        recipe = RecipeCreate(title="Valid Recipe Title")
        assert recipe.title == "Valid Recipe Title"
        
        # Maximum length title
        max_title = "a" * 200
        recipe = RecipeCreate(title=max_title)
        assert recipe.title == max_title
        
        # Title too long
        with pytest.raises(ValidationError):
            RecipeCreate(title="a" * 201)
    
    def test_description_length_validation(self) -> None:
        """Test description length constraints."""
        # Valid description
        recipe = RecipeCreate(title="Test", description="Valid description")
        assert recipe.description == "Valid description"
        
        # Maximum length description
        max_desc = "a" * 1000
        recipe = RecipeCreate(title="Test", description=max_desc)
        assert recipe.description == max_desc
        
        # Description too long
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", description="a" * 1001)
    
    def test_numeric_field_validation(self) -> None:
        """Test numeric field constraints."""
        # Valid numeric fields
        recipe = RecipeCreate(
            title="Test",
            prep_time=30,
            cook_time=60,
            servings=4
        )
        assert recipe.prep_time == 30
        assert recipe.cook_time == 60
        assert recipe.servings == 4
        
        # Test maximum values (should now fail with our constraints)
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", prep_time=1441)  # > 1440 (24 hours)
        
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", cook_time=1441)  # > 1440 (24 hours)
        
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", servings=101)  # > 100
    
    def test_complex_ingredient_validation(self) -> None:
        """Test complex ingredient scenarios."""
        # Valid complex ingredients
        ingredients = [
            Ingredient(name="All-purpose flour", amount="2.5", unit="cups"),
            Ingredient(name="Extra virgin olive oil", amount="1/4", unit="cup"),
            Ingredient(name="Sea salt", amount="1", unit="pinch")
        ]
        
        recipe = RecipeCreate(title="Test", ingredients=ingredients)
        assert len(recipe.ingredients) == 3
        assert recipe.ingredients[0].name == "All-purpose flour"
        assert recipe.ingredients[1].amount == "1/4"
        assert recipe.ingredients[2].unit == "pinch"
    
    def test_metadata_flexibility(self) -> None:
        """Test metadata field flexibility."""
        metadata = {
            "nutrition": {"calories": 250, "protein": "12g"},
            "source_notes": "Modified from original",
            "rating": 4.5,
            "custom_tags": ["family-favorite", "quick-prep"]
        }
        
        recipe = RecipeCreate(title="Test", metadata=metadata)
        assert recipe.metadata["nutrition"]["calories"] == 250
        assert recipe.metadata["rating"] == 4.5
        assert "family-favorite" in recipe.metadata["custom_tags"]


class TestModelInteraction:
    """Test interactions between different model types."""
    
    def test_create_to_response_conversion(self) -> None:
        """Test converting RecipeCreate to RecipeResponse-like structure."""
        create_data = RecipeCreate(
            title="Conversion Test",
            description="Testing model conversion",
            ingredients=[Ingredient(name="Test", amount="1")],
            instructions=["Test instruction"],
            difficulty="easy",
            tags=["test"]
        )
        
        # Simulate what happens in the API
        recipe_dict = create_data.model_dump()
        recipe_dict["_id"] = "507f1f77bcf86cd799439011"
        recipe_dict["created_at"] = datetime.now()
        recipe_dict["updated_at"] = datetime.now()
        
        response = RecipeResponse(**recipe_dict)
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.title == "Conversion Test"
        assert response.difficulty == "easy"
    
    def test_update_model_exclusion(self) -> None:
        """Test RecipeUpdate proper field exclusion."""
        update_data = RecipeUpdate(title="Updated", description=None)
        
        # Test exclude_unset behavior
        dumped = update_data.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "description" not in dumped  # None values excluded when exclude_unset=True
        
        # Test exclude_none behavior
        dumped_none = update_data.model_dump(exclude_none=True)
        assert "title" in dumped_none
        assert "description" not in dumped_none
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
    
    def test_recipe_response_from_recipe(self) -> None:
        """Test RecipeResponse.from_recipe method with proper ObjectId conversion."""
        from bson import ObjectId
        
        # Create a mock Recipe document with ObjectId
        class MockRecipe:
            def __init__(self):
                self.id = ObjectId()
                self.title = "Test Recipe"
                self.description = "Test description"
                self.ingredients = []
                self.instructions = []
                self.prep_time = 30
                self.cook_time = 45
                self.servings = 4
                self.difficulty = "medium"
                self.tags = ["test", "quick"]
                self.source = {"type": "manual"}
                self.images = []
                self.created_at = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                self.metadata = {}
            
            def model_dump(self):
                return {
                    "title": self.title,
                    "description": self.description,
                    "ingredients": self.ingredients,
                    "instructions": self.instructions,
                    "prep_time": self.prep_time,
                    "cook_time": self.cook_time,
                    "servings": self.servings,
                    "difficulty": self.difficulty,
                    "tags": self.tags,
                    "source": self.source,
                    "images": self.images,
                    "created_at": self.created_at,
                    "updated_at": self.updated_at,
                    "metadata": self.metadata
                }
        
        mock_recipe = MockRecipe()
        
        # Convert using the from_recipe method
        response = RecipeResponse.from_recipe(mock_recipe)
        
        # Verify the ID is properly converted to string
        assert response.id == str(mock_recipe.id)
        assert isinstance(response.id, str)
        assert response.title == mock_recipe.title
        assert response.description == mock_recipe.description
        assert response.prep_time == mock_recipe.prep_time
        assert response.cook_time == mock_recipe.cook_time
        assert response.difficulty == mock_recipe.difficulty
        assert response.tags == mock_recipe.tags

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
        # Valid numeric fields
        recipe = RecipeCreate(
            title="Test",
            prep_time=30,
            cook_time=60,
            servings=4
        )
        assert recipe.prep_time == 30
        assert recipe.cook_time == 60
        assert recipe.servings == 4
        
        # Test maximum valid values
        recipe_max = RecipeCreate(
            title="Test",
            prep_time=1440,  # 24 hours max
            cook_time=1440,  # 24 hours max
            servings=100     # 100 servings max
        )
        assert recipe_max.prep_time == 1440
        assert recipe_max.cook_time == 1440
        assert recipe_max.servings == 100
        
        # Test values exceeding limits (should fail)
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", prep_time=1441)  # > 1440 (24 hours)
        
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", cook_time=1441)  # > 1440 (24 hours)
        
        with pytest.raises(ValidationError):
            RecipeCreate(title="Test", servings=101)  # > 100
    
    def test_complex_ingredient_validation(self) -> None:
        """Test complex ingredient scenarios."""
        # Valid complex ingredients
        ingredients = [
            Ingredient(name="All-purpose flour", amount="2.5", unit="cups"),
            Ingredient(name="Extra virgin olive oil", amount="1/4", unit="cup"),
            Ingredient(name="Sea salt", amount="1", unit="pinch")
        ]
        
        recipe = RecipeCreate(title="Test", ingredients=ingredients)
        assert len(recipe.ingredients) == 3
        assert recipe.ingredients[0].name == "All-purpose flour"
        assert recipe.ingredients[1].amount == "1/4"
        assert recipe.ingredients[2].unit == "pinch"
    
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