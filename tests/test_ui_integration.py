"""
UI Integration tests for the Recipe Management application.
Tests the basic frontend functionality by simulating browser interactions.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUIBasicFunctionality:
    """Test basic UI functionality and API integration."""
    
    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
    def test_static_files_served(self):
        """Test that static files are properly served."""
        # Test CSS file
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        
        # Test JavaScript file
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        
    def test_api_endpoints_for_ui(self):
        """Test API endpoints that the UI depends on."""
        # Test getting all recipes (should work even if empty)
        response = client.get("/api/recipes/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test getting tags (used by frontend)
        response = client.get("/api/recipes/tags/all")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test recipe count endpoint
        response = client.get("/api/recipes/count")
        assert response.status_code == 200
        assert "count" in response.json()
        assert isinstance(response.json()["count"], int)

class TestRecipeCreationWorkflow:
    """Test the recipe creation workflow that the UI uses."""
    
    def test_create_recipe_via_api(self):
        """Test creating a recipe through the API that the UI would use."""
        recipe_data = {
            "title": "Test UI Recipe",
            "description": "A recipe for testing UI integration",
            "ingredients": [
                {"name": "flour", "amount": "2", "unit": "cups"},
                {"name": "sugar", "amount": "1", "unit": "cup"}
            ],
            "instructions": [
                "Mix flour and sugar",
                "Bake for 30 minutes"
            ],
            "prep_time": 15,
            "cook_time": 30,
            "servings": 8,
            "difficulty": "easy",
            "tags": ["dessert", "baking"],
            "source": {
                "type": "manual"
            }
        }
        
        # Create recipe
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 201
        
        created_recipe = response.json()
        assert created_recipe["title"] == recipe_data["title"]
        assert created_recipe["description"] == recipe_data["description"]
        assert len(created_recipe["ingredients"]) == 2
        assert len(created_recipe["instructions"]) == 2
        assert created_recipe["difficulty"] == "easy"
        assert "id" in created_recipe
        assert isinstance(created_recipe["id"], str)
        
        recipe_id = created_recipe["id"]
        
        # Test getting the specific recipe
        response = client.get(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        retrieved_recipe = response.json()
        assert retrieved_recipe["id"] == recipe_id
        assert retrieved_recipe["title"] == recipe_data["title"]
        
        # Test updating the recipe
        update_data = {
            "title": "Updated UI Recipe",
            "servings": 10
        }
        response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
        assert response.status_code == 200
        updated_recipe = response.json()
        assert updated_recipe["title"] == "Updated UI Recipe"
        assert updated_recipe["servings"] == 10
        assert updated_recipe["description"] == recipe_data["description"]  # Should remain unchanged
        
        # Test deleting the recipe
        response = client.delete(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        
        # Verify recipe is deleted
        response = client.get(f"/api/recipes/{recipe_id}")
        assert response.status_code == 404

class TestUIFilteringAndSearch:
    """Test filtering and search functionality used by the UI."""
    
    @pytest.fixture(autouse=True)
    def setup_test_recipes(self):
        """Create test recipes for filtering tests."""
        self.test_recipes = []
        
        recipes_data = [
            {
                "title": "Easy Pasta",
                "description": "Simple pasta recipe",
                "difficulty": "easy",
                "tags": ["pasta", "italian", "quick"],
                "ingredients": [{"name": "pasta", "amount": "1", "unit": "lb"}],
                "instructions": ["Boil water", "Cook pasta"]
            },
            {
                "title": "Complex Cake",
                "description": "Difficult cake recipe",
                "difficulty": "hard",
                "tags": ["dessert", "cake", "baking"],
                "ingredients": [{"name": "flour", "amount": "2", "unit": "cups"}],
                "instructions": ["Mix ingredients", "Bake carefully"]
            },
            {
                "title": "Medium Soup",
                "description": "Moderate difficulty soup",
                "difficulty": "medium",
                "tags": ["soup", "healthy"],
                "ingredients": [{"name": "vegetables", "amount": "1", "unit": "cup"}],
                "instructions": ["Chop vegetables", "Simmer"]
            }
        ]
        
        for recipe_data in recipes_data:
            response = client.post("/api/recipes/", json=recipe_data)
            if response.status_code == 201:
                self.test_recipes.append(response.json())
        
        yield
        
        # Cleanup
        for recipe in self.test_recipes:
            client.delete(f"/api/recipes/{recipe['id']}")
    
    def test_filter_by_difficulty(self):
        """Test filtering recipes by difficulty level."""
        response = client.get("/api/recipes/?difficulty=easy")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) >= 1
        for recipe in recipes:
            assert recipe["difficulty"] == "easy"
    
    def test_search_recipes(self):
        """Test recipe search functionality."""
        response = client.get("/api/recipes/search?q=pasta")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) >= 1
        # Should find the pasta recipe
        pasta_found = any("pasta" in recipe["title"].lower() for recipe in recipes)
        assert pasta_found
    
    def test_get_recipes_by_difficulty_endpoint(self):
        """Test the specific difficulty endpoint."""
        response = client.get("/api/recipes/difficulty/hard")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) >= 1
        for recipe in recipes:
            assert recipe["difficulty"] == "hard"
    
    def test_pagination(self):
        """Test recipe pagination."""
        # Test with limit
        response = client.get("/api/recipes/?limit=2")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) <= 2
        
        # Test with skip
        response = client.get("/api/recipes/?skip=1&limit=2")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) <= 2

class TestUIErrorHandling:
    """Test error handling scenarios that the UI needs to handle."""
    
    def test_invalid_recipe_creation(self):
        """Test creating invalid recipes."""
        # Empty title should fail
        invalid_data = {
            "title": "",
            "ingredients": [],
            "instructions": []
        }
        response = client.post("/api/recipes/", json=invalid_data)
        assert response.status_code == 422
        
        # Invalid difficulty should fail
        invalid_data = {
            "title": "Test Recipe",
            "difficulty": "invalid_difficulty",
            "ingredients": [],
            "instructions": []
        }
        response = client.post("/api/recipes/", json=invalid_data)
        assert response.status_code == 422
    
    def test_nonexistent_recipe_access(self):
        """Test accessing non-existent recipes."""
        fake_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        
        response = client.get(f"/api/recipes/{fake_id}")
        assert response.status_code == 404
        
        response = client.put(f"/api/recipes/{fake_id}", json={"title": "Updated"})
        assert response.status_code == 404
        
        response = client.delete(f"/api/recipes/{fake_id}")
        assert response.status_code == 404
    
    def test_invalid_recipe_id_format(self):
        """Test invalid recipe ID formats."""
        invalid_id = "invalid_id_format"
        
        response = client.get(f"/api/recipes/{invalid_id}")
        assert response.status_code == 400
        assert "Invalid recipe ID format" in response.json()["detail"]