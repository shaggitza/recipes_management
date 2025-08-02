"""
Simple integration test to verify mongomock setup works correctly.
"""
import pytest
from app.models.recipe import Recipe, RecipeCreate, Ingredient, Source


class TestMongomockIntegration:
    """Test that mongomock integration works correctly."""
    
    @pytest.mark.asyncio
    async def test_recipe_crud_with_mongomock(self, clean_db):
        """Test basic CRUD operations with mongomock."""
        # Create a recipe
        recipe_data = RecipeCreate(
            title="Mongomock Test Recipe",
            description="Testing mongomock integration",
            ingredients=[
                Ingredient(name="Test Ingredient", amount="1", unit="cup")
            ],
            instructions=["Test instruction"],
            difficulty="easy",
            tags=["test"]
        )
        
        # Convert to Recipe document and save
        recipe = Recipe(**recipe_data.model_dump())
        saved_recipe = await recipe.insert()
        
        assert saved_recipe.id is not None
        assert saved_recipe.title == "Mongomock Test Recipe"
        
        # Retrieve the recipe
        found_recipe = await Recipe.get(saved_recipe.id)
        assert found_recipe is not None
        assert found_recipe.title == "Mongomock Test Recipe"
        assert len(found_recipe.ingredients) == 1
        
        # Update the recipe
        found_recipe.title = "Updated Test Recipe"
        await found_recipe.save()
        
        # Verify update
        updated_recipe = await Recipe.get(saved_recipe.id)
        assert updated_recipe.title == "Updated Test Recipe"
        
        # Count recipes
        count = await Recipe.count()
        assert count == 1
        
        # Delete the recipe
        await updated_recipe.delete()
        
        # Verify deletion
        deleted_recipe = await Recipe.get(saved_recipe.id)
        assert deleted_recipe is None
        
        # Count should be 0
        count = await Recipe.count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_recipe_find_operations(self, clean_db):
        """Test find operations with mongomock."""
        # Create multiple recipes
        recipes_data = [
            RecipeCreate(title="Easy Recipe", difficulty="easy", tags=["quick"]),
            RecipeCreate(title="Hard Recipe", difficulty="hard", tags=["complex"]),
            RecipeCreate(title="Medium Recipe", difficulty="medium", tags=["quick"])
        ]
        
        saved_recipes = []
        for recipe_data in recipes_data:
            recipe = Recipe(**recipe_data.model_dump())
            saved_recipe = await recipe.insert()
            saved_recipes.append(saved_recipe)
        
        # Test find all
        all_recipes = await Recipe.find_all().to_list()
        assert len(all_recipes) == 3
        
        # Test find with filter
        easy_recipes = await Recipe.find(Recipe.difficulty == "easy").to_list()
        assert len(easy_recipes) == 1
        assert easy_recipes[0].title == "Easy Recipe"
        
        # Test find with in filter
        quick_recipes = await Recipe.find({"tags": {"$in": ["quick"]}}).to_list()
        assert len(quick_recipes) == 2
        
        # Clean up
        await Recipe.delete_all()