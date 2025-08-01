import pytest
from bson import ObjectId

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
    assert response.status_code == 200
    
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
    assert response.status_code == 200
    
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
    fake_id = str(ObjectId())
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
    fake_id = str(ObjectId())
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
    fake_id = str(ObjectId())
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