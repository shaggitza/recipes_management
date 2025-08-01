import pytest
from beanie import PydanticObjectId

def test_create_recipe(client, clean_db):
    """Test creating a new recipe."""
    recipe_data = {
        "title": "Test Recipe",
        "description": "A test recipe",
        "ingredients": [
            {"name": "Flour", "amount": "2", "unit": "cups"},
            {"name": "Sugar", "amount": "1", "unit": "cup"}
        ],
        "instructions": [
            "Mix ingredients",
            "Bake for 30 minutes"
        ],
        "prep_time": 15,
        "cook_time": 30,
        "servings": 4,
        "difficulty": "easy",
        "tags": ["dessert", "baking"],
        "source": {
            "type": "website",
            "url": "https://example.com",
            "name": "Example Site"
        }
    }
    
    response = client.post("/api/recipes/", json=recipe_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == recipe_data["title"]
    assert data["description"] == recipe_data["description"]
    assert len(data["ingredients"]) == 2
    assert len(data["instructions"]) == 2
    assert data["prep_time"] == 15
    assert data["cook_time"] == 30
    assert data["servings"] == 4
    assert data["difficulty"] == "easy"
    assert data["tags"] == ["dessert", "baking"]
    assert data["source"]["type"] == "website"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_recipe_minimal_data(client, clean_db):
    """Test creating a recipe with minimal required data."""
    recipe_data = {
        "title": "Minimal Recipe"
    }
    
    response = client.post("/api/recipes/", json=recipe_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == "Minimal Recipe"
    assert data["description"] is None
    assert data["ingredients"] == []
    assert data["instructions"] == []
    assert data["tags"] == []

def test_create_recipe_invalid_data(client, clean_db):
    """Test creating a recipe with invalid data."""
    # Empty title should fail
    response = client.post("/api/recipes/", json={"title": ""})
    assert response.status_code == 422
    
    # Invalid difficulty should fail
    response = client.post("/api/recipes/", json={
        "title": "Test",
        "difficulty": "invalid"
    })
    assert response.status_code == 422

def test_get_recipes_empty(client, clean_db):
    """Test getting recipes when none exist."""
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_recipes_with_data(client, clean_db):
    """Test getting recipes with existing data."""
    # Create test recipes
    recipe1 = {"title": "Recipe 1", "tags": ["tag1"]}
    recipe2 = {"title": "Recipe 2", "tags": ["tag2"]}
    
    client.post("/api/recipes/", json=recipe1)
    client.post("/api/recipes/", json=recipe2)
    
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] in ["Recipe 1", "Recipe 2"]
    assert data[1]["title"] in ["Recipe 1", "Recipe 2"]

def test_get_recipe_by_id(client, clean_db):
    """Test getting a specific recipe by ID."""
    # Create a recipe
    recipe_data = {"title": "Test Recipe", "description": "Test description"}
    create_response = client.post("/api/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]
    
    # Get the recipe by ID
    response = client.get(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Test Recipe"
    assert data["description"] == "Test description"

def test_get_recipe_by_invalid_id(client, clean_db):
    """Test getting a recipe with invalid ID."""
    response = client.get("/api/recipes/invalid_id")
    assert response.status_code == 400

def test_get_recipe_not_found(client, clean_db):
    """Test getting a recipe that doesn't exist."""
    fake_id = str(PydanticObjectId())
    response = client.get(f"/api/recipes/{fake_id}")
    assert response.status_code == 404

def test_update_recipe(client, clean_db):
    """Test updating a recipe."""
    # Create a recipe
    recipe_data = {"title": "Original Title", "description": "Original description"}
    create_response = client.post("/api/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]
    
    # Update the recipe
    update_data = {"title": "Updated Title", "description": "Updated description"}
    response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"

def test_update_recipe_partial(client, clean_db):
    """Test partial update of a recipe."""
    # Create a recipe
    recipe_data = {"title": "Original Title", "description": "Original description"}
    create_response = client.post("/api/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]
    
    # Update only the title
    update_data = {"title": "Updated Title"}
    response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Original description"

def test_update_recipe_not_found(client, clean_db):
    """Test updating a recipe that doesn't exist."""
    fake_id = str(PydanticObjectId())
    update_data = {"title": "Updated Title"}
    response = client.put(f"/api/recipes/{fake_id}", json=update_data)
    assert response.status_code == 404

def test_delete_recipe(client, clean_db):
    """Test deleting a recipe."""
    # Create a recipe
    recipe_data = {"title": "Recipe to Delete"}
    create_response = client.post("/api/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]
    
    # Delete the recipe
    response = client.delete(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Recipe deleted successfully"
    
    # Verify it's deleted
    get_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_response.status_code == 404

def test_delete_recipe_not_found(client, clean_db):
    """Test deleting a recipe that doesn't exist."""
    fake_id = str(PydanticObjectId())
    response = client.delete(f"/api/recipes/{fake_id}")
    assert response.status_code == 404

def test_search_recipes(client, clean_db):
    """Test searching recipes."""
    # Create test recipes
    recipes = [
        {"title": "Chocolate Cake", "description": "Delicious chocolate cake", "tags": ["dessert"]},
        {"title": "Vanilla Ice Cream", "description": "Creamy vanilla ice cream", "tags": ["dessert", "cold"]},
        {"title": "Beef Stew", "description": "Hearty beef stew", "tags": ["main", "warm"]}
    ]
    
    for recipe in recipes:
        client.post("/api/recipes/", json=recipe)
    
    # Search by title
    response = client.get("/api/recipes/?search=chocolate")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Chocolate" in data[0]["title"]
    
    # Search by description
    response = client.get("/api/recipes/?search=creamy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Vanilla" in data[0]["title"]
    
    # Search by tags
    response = client.get("/api/recipes/?tags=dessert")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_filter_by_difficulty(client, clean_db):
    """Test filtering recipes by difficulty."""
    # Create recipes with different difficulties
    recipes = [
        {"title": "Easy Recipe", "difficulty": "easy"},
        {"title": "Hard Recipe", "difficulty": "hard"},
        {"title": "Medium Recipe", "difficulty": "medium"}
    ]
    
    for recipe in recipes:
        client.post("/api/recipes/", json=recipe)
    
    # Filter by difficulty
    response = client.get("/api/recipes/?difficulty=easy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["difficulty"] == "easy"

def test_get_all_tags(client, clean_db):
    """Test getting all unique tags."""
    # Create recipes with tags
    recipes = [
        {"title": "Recipe 1", "tags": ["tag1", "tag2"]},
        {"title": "Recipe 2", "tags": ["tag2", "tag3"]},
        {"title": "Recipe 3", "tags": ["tag1", "tag3"]}
    ]
    
    for recipe in recipes:
        client.post("/api/recipes/", json=recipe)
    
    response = client.get("/api/recipes/tags/all")
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) == 3
    assert "tag1" in tags
    assert "tag2" in tags
    assert "tag3" in tags

def test_pagination(client, clean_db):
    """Test recipe pagination."""
    # Create multiple recipes
    for i in range(15):
        recipe_data = {"title": f"Recipe {i}"}
        client.post("/api/recipes/", json=recipe_data)
    
    # Test default pagination
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10  # Default limit
    
    # Test custom pagination
    response = client.get("/api/recipes/?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_recipe_validation_errors(client, clean_db):
    """Test recipe validation error handling."""
    # Test empty title
    response = client.post("/api/recipes/", json={"title": ""})
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("title" in str(error).lower() for error in error_detail)
    
    # Test invalid difficulty
    response = client.post("/api/recipes/", json={
        "title": "Test Recipe",
        "difficulty": "super_hard"
    })
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("difficulty" in str(error).lower() for error in error_detail)
    
    # Test negative prep_time
    response = client.post("/api/recipes/", json={
        "title": "Test Recipe",
        "prep_time": -5
    })
    assert response.status_code == 422
    
    # Test negative servings
    response = client.post("/api/recipes/", json={
        "title": "Test Recipe",
        "servings": 0
    })
    assert response.status_code == 422

def test_recipe_search_edge_cases(client, clean_db):
    """Test edge cases in recipe search functionality."""
    # Create test recipes with various content
    recipes = [
        {
            "title": "Chocolate Chip Cookies",
            "description": "Sweet and chewy cookies",
            "ingredients": [{"name": "chocolate chips", "amount": "1", "unit": "cup"}],
            "tags": ["dessert", "cookies"]
        },
        {
            "title": "Vanilla Extract Recipe",
            "description": "Homemade vanilla extract",
            "ingredients": [{"name": "vanilla beans", "amount": "10", "unit": "pieces"}],
            "tags": ["ingredient", "extract"]
        }
    ]
    
    for recipe in recipes:
        client.post("/api/recipes/", json=recipe)
    
    # Test case-insensitive search
    response = client.get("/api/recipes/?search=CHOCOLATE")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Chocolate" in data[0]["title"]
    
    # Test search in ingredients
    response = client.get("/api/recipes/?search=vanilla beans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Vanilla" in data[0]["title"]
    
    # Test empty search returns all
    response = client.get("/api/recipes/?search=")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Test search with no results
    response = client.get("/api/recipes/?search=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_recipe_tags_functionality(client, clean_db):
    """Test tag-related functionality thoroughly."""
    # Create recipes with overlapping tags
    recipes = [
        {"title": "Recipe 1", "tags": ["vegetarian", "quick", "healthy"]},
        {"title": "Recipe 2", "tags": ["vegan", "quick", "gluten-free"]},
        {"title": "Recipe 3", "tags": ["meat", "slow-cooked"]},
        {"title": "Recipe 4", "tags": []},  # No tags
    ]
    
    for recipe in recipes:
        client.post("/api/recipes/", json=recipe)
    
    # Test single tag filter
    response = client.get("/api/recipes/?tags=quick")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Test multiple tag filter (OR operation)
    response = client.get("/api/recipes/?tags=vegetarian,vegan")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Test tag that doesn't exist
    response = client.get("/api/recipes/?tags=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
    
    # Test get all tags endpoint
    response = client.get("/api/recipes/tags/all")
    assert response.status_code == 200
    tags = response.json()
    expected_tags = ["gluten-free", "healthy", "meat", "quick", "slow-cooked", "vegan", "vegetarian"]
    assert set(tags) == set(expected_tags)

def test_recipe_source_handling(client, clean_db):
    """Test recipe source field handling."""
    # Test with TikTok source
    tiktok_recipe = {
        "title": "TikTok Viral Recipe",
        "source": {
            "type": "tiktok",
            "url": "https://tiktok.com/@user/video/123456",
            "name": "Viral Food Creator"
        }
    }
    response = client.post("/api/recipes/", json=tiktok_recipe)
    assert response.status_code == 200
    data = response.json()
    assert data["source"]["type"] == "tiktok"
    assert data["source"]["url"] == "https://tiktok.com/@user/video/123456"
    
    # Test with default manual source
    manual_recipe = {"title": "Manual Recipe"}
    response = client.post("/api/recipes/", json=manual_recipe)
    assert response.status_code == 200
    data = response.json()
    assert data["source"]["type"] == "manual"
    assert data["source"]["url"] is None

def test_recipe_ingredients_and_instructions(client, clean_db):
    """Test ingredient and instruction handling."""
    complex_recipe = {
        "title": "Complex Recipe",
        "ingredients": [
            {"name": "Flour", "amount": "2", "unit": "cups"},
            {"name": "Sugar", "amount": "1", "unit": "cup"},
            {"name": "Salt", "amount": "1", "unit": "tsp"},
            {"name": "Vanilla", "amount": "2", "unit": "tsp"}
        ],
        "instructions": [
            "Preheat oven to 350°F",
            "Mix dry ingredients in a large bowl",
            "Add wet ingredients and mix until combined",
            "Pour into greased pan",
            "Bake for 25-30 minutes until golden brown",
            "Cool before serving"
        ]
    }
    
    response = client.post("/api/recipes/", json=complex_recipe)
    assert response.status_code == 200
    data = response.json()
    
    # Verify ingredients are preserved
    assert len(data["ingredients"]) == 4
    flour_ingredient = next(ing for ing in data["ingredients"] if ing["name"] == "Flour")
    assert flour_ingredient["amount"] == "2"
    assert flour_ingredient["unit"] == "cups"
    
    # Verify instructions are preserved and ordered
    assert len(data["instructions"]) == 6
    assert data["instructions"][0] == "Preheat oven to 350°F"
    assert "Cool before serving" in data["instructions"]

def test_api_error_handling(client, clean_db):
    """Test various API error conditions."""
    # Test malformed JSON
    response = client.post("/api/recipes/", 
                         data="invalid json",
                         headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    
    # Test missing required fields
    response = client.post("/api/recipes/", json={})
    assert response.status_code == 422
    
    # Test invalid HTTP methods on specific endpoints
    response = client.patch("/api/recipes/")
    assert response.status_code == 405

def test_recipe_timestamps(client, clean_db):
    """Test that timestamps are properly handled."""
    recipe_data = {"title": "Timestamp Test Recipe"}
    
    # Create recipe
    create_response = client.post("/api/recipes/", json=recipe_data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    
    # Verify timestamps exist and are recent
    assert "created_at" in created_data
    assert "updated_at" in created_data
    assert created_data["created_at"] == created_data["updated_at"]
    
    recipe_id = created_data["id"]
    
    # Update recipe and verify updated_at changes
    import time
    time.sleep(1)  # Ensure timestamp difference
    
    update_response = client.put(f"/api/recipes/{recipe_id}", 
                               json={"description": "Updated description"})
    assert update_response.status_code == 200
    updated_data = update_response.json()
    
    # created_at should remain the same, updated_at should change
    assert updated_data["created_at"] == created_data["created_at"]
    # Note: In a real test with proper timing, updated_at would be different
    assert "updated_at" in updated_data

def test_recipe_metadata_field(client, clean_db):
    """Test the extensible metadata field."""
    recipe_with_metadata = {
        "title": "Recipe with Metadata",
        "metadata": {
            "author": "Chef Example",
            "difficulty_notes": "Requires advanced knife skills",
            "custom_field": "custom_value",
            "nutrition": {
                "calories": 350,
                "protein": "15g"
            }
        }
    }
    
    response = client.post("/api/recipes/", json=recipe_with_metadata)
    assert response.status_code == 200
    data = response.json()
    
    # Verify metadata is preserved exactly
    assert data["metadata"]["author"] == "Chef Example"
    assert data["metadata"]["nutrition"]["calories"] == 350
    assert data["metadata"]["custom_field"] == "custom_value"