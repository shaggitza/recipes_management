"""
Integration tests for the Recipe Management API.
Tests the full workflow and integration between components.
"""
import pytest
from typing import Dict, Any

def test_complete_recipe_lifecycle(client, clean_db):
    """Test the complete lifecycle of a recipe from creation to deletion."""
    # Step 1: Create a recipe
    recipe_data = {
        "title": "Integration Test Recipe",
        "description": "A recipe for testing the complete API workflow",
        "ingredients": [
            {"name": "Test Ingredient 1", "amount": "1", "unit": "cup"},
            {"name": "Test Ingredient 2", "amount": "2", "unit": "tbsp"}
        ],
        "instructions": [
            "Step 1: Prepare ingredients",
            "Step 2: Mix everything together",
            "Step 3: Cook until done"
        ],
        "prep_time": 10,
        "cook_time": 25,
        "servings": 4,
        "difficulty": "medium",
        "tags": ["test", "integration", "api"],
        "source": {
            "type": "website",
            "url": "https://example.com/recipe",
            "name": "Test Recipe Site"
        },
        "metadata": {
            "test_run": True,
            "created_by": "integration_test"
        }
    }
    
    # Create the recipe
    create_response = client.post("/api/recipes/", json=recipe_data)
    assert create_response.status_code == 200
    created_recipe = create_response.json()
    recipe_id = created_recipe["id"]
    
    # Verify all fields were saved correctly
    assert created_recipe["title"] == recipe_data["title"]
    assert created_recipe["description"] == recipe_data["description"]
    assert len(created_recipe["ingredients"]) == 2
    assert len(created_recipe["instructions"]) == 3
    assert created_recipe["prep_time"] == 10
    assert created_recipe["cook_time"] == 25
    assert created_recipe["servings"] == 4
    assert created_recipe["difficulty"] == "medium"
    assert set(created_recipe["tags"]) == set(recipe_data["tags"])
    
    # Step 2: Retrieve the recipe by ID
    get_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_response.status_code == 200
    retrieved_recipe = get_response.json()
    assert retrieved_recipe["id"] == recipe_id
    assert retrieved_recipe["title"] == recipe_data["title"]
    
    # Step 3: Update the recipe
    update_data = {
        "title": "Updated Integration Test Recipe",
        "description": "Updated description for testing",
        "prep_time": 15,
        "tags": ["test", "integration", "api", "updated"]
    }
    
    update_response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
    assert update_response.status_code == 200
    updated_recipe = update_response.json()
    
    # Verify updates were applied
    assert updated_recipe["title"] == update_data["title"]
    assert updated_recipe["description"] == update_data["description"]
    assert updated_recipe["prep_time"] == 15
    assert "updated" in updated_recipe["tags"]
    
    # Verify unchanged fields remain the same
    assert updated_recipe["cook_time"] == 25  # Unchanged
    assert updated_recipe["servings"] == 4    # Unchanged
    
    # Step 4: Search for the recipe
    search_response = client.get(f"/api/recipes/?search=Updated Integration")
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) == 1
    assert search_results[0]["id"] == recipe_id
    
    # Step 5: Filter by tags
    tag_response = client.get("/api/recipes/?tags=updated")
    assert tag_response.status_code == 200
    tag_results = tag_response.json()
    assert len(tag_results) == 1
    assert tag_results[0]["id"] == recipe_id
    
    # Step 6: Test tags endpoint
    tags_response = client.get("/api/recipes/tags/all")
    assert tags_response.status_code == 200
    all_tags = tags_response.json()
    assert "updated" in all_tags
    assert "integration" in all_tags
    
    # Step 7: Delete the recipe
    delete_response = client.delete(f"/api/recipes/{recipe_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Recipe deleted successfully"
    
    # Step 8: Verify deletion
    get_deleted_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_deleted_response.status_code == 404

def test_bulk_operations_and_pagination(client, clean_db):
    """Test bulk operations and pagination functionality."""
    # Create multiple recipes for testing
    recipes_data = []
    for i in range(25):
        recipe = {
            "title": f"Bulk Test Recipe {i:02d}",
            "description": f"Description for recipe {i}",
            "difficulty": ["easy", "medium", "hard"][i % 3],
            "tags": [f"tag{i % 5}", "bulk", "test"],
            "prep_time": 10 + (i % 20),
            "metadata": {"batch": "bulk_test", "index": i}
        }
        recipes_data.append(recipe)
    
    # Create all recipes
    created_ids = []
    for recipe_data in recipes_data:
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])
    
    # Test pagination - first page
    page1_response = client.get("/api/recipes/?limit=10")
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    assert len(page1_data) == 10
    
    # Test pagination - second page
    page2_response = client.get("/api/recipes/?skip=10&limit=10")
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    assert len(page2_data) == 10
    
    # Verify no duplicates between pages
    page1_ids = {recipe["id"] for recipe in page1_data}
    page2_ids = {recipe["id"] for recipe in page2_data}
    assert len(page1_ids.intersection(page2_ids)) == 0
    
    # Test filtering by difficulty
    easy_response = client.get("/api/recipes/?difficulty=easy")
    assert easy_response.status_code == 200
    easy_recipes = easy_response.json()
    assert all(recipe["difficulty"] == "easy" for recipe in easy_recipes)
    assert len(easy_recipes) > 0
    
    # Test tag filtering
    tag_response = client.get("/api/recipes/?tags=bulk")
    assert tag_response.status_code == 200
    bulk_recipes = tag_response.json()
    assert len(bulk_recipes) == 25  # All should have 'bulk' tag
    
    # Test search functionality
    search_response = client.get("/api/recipes/?search=Recipe 0")
    assert search_response.status_code == 200
    search_results = search_response.json()
    # Should find recipes with "Recipe 0" in the title (00, 01, 02, etc.)
    assert len(search_results) >= 10

def test_error_scenarios_and_edge_cases(client, clean_db):
    """Test various error scenarios and edge cases."""
    # Test creating recipe with minimal data
    minimal_recipe = {"title": "Minimal Recipe"}
    response = client.post("/api/recipes/", json=minimal_recipe)
    assert response.status_code == 200
    minimal_data = response.json()
    assert minimal_data["ingredients"] == []
    assert minimal_data["instructions"] == []
    assert minimal_data["tags"] == []
    
    # Test updating non-existent recipe
    from beanie import PydanticObjectId
    fake_id = str(PydanticObjectId())
    response = client.put(f"/api/recipes/{fake_id}", json={"title": "Updated"})
    assert response.status_code == 404
    
    # Test deleting non-existent recipe
    response = client.delete(f"/api/recipes/{fake_id}")
    assert response.status_code == 404
    
    # Test invalid ID format
    response = client.get("/api/recipes/invalid-id-format")
    assert response.status_code == 400
    
    # Test empty search and filters
    response = client.get("/api/recipes/?search=&tags=&difficulty=")
    assert response.status_code == 200
    
    # Test pagination edge cases
    response = client.get("/api/recipes/?skip=1000&limit=10")
    assert response.status_code == 200
    assert response.json() == []  # Should return empty list for out-of-range skip
    
    # Test invalid pagination parameters
    response = client.get("/api/recipes/?skip=-1")
    assert response.status_code == 422  # Validation error
    
    response = client.get("/api/recipes/?limit=0")
    assert response.status_code == 422  # Validation error

def test_concurrent_operations(client, clean_db):
    """Test concurrent operations to ensure data consistency."""
    import threading
    import time
    
    # Create a base recipe
    base_recipe = {
        "title": "Concurrent Test Recipe",
        "description": "Testing concurrent operations",
        "tags": ["concurrent", "test"]
    }
    
    response = client.post("/api/recipes/", json=base_recipe)
    assert response.status_code == 200
    recipe_id = response.json()["id"]
    
    # Simulate concurrent updates
    results = []
    
    def update_recipe(update_data: Dict[str, Any], result_list: list):
        try:
            response = client.put(f"/api/recipes/{recipe_id}", json=update_data)
            result_list.append(response.status_code)
        except Exception as e:
            result_list.append(f"Error: {str(e)}")
    
    # Create multiple threads to update the recipe concurrently
    threads = []
    for i in range(5):
        update_data = {"description": f"Updated by thread {i}"}
        thread = threading.Thread(target=update_recipe, args=(update_data, results))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all operations completed successfully
    assert len(results) == 5
    assert all(status == 200 for status in results)
    
    # Verify the recipe still exists and is valid
    final_response = client.get(f"/api/recipes/{recipe_id}")
    assert final_response.status_code == 200

def test_data_validation_comprehensive(client, clean_db):
    """Test comprehensive data validation scenarios."""
    # Test title length limits
    long_title = "x" * 201  # Exceeds 200 char limit
    response = client.post("/api/recipes/", json={"title": long_title})
    assert response.status_code == 422
    
    # Test description length limits
    long_description = "x" * 1001  # Exceeds 1000 char limit
    response = client.post("/api/recipes/", json={
        "title": "Test",
        "description": long_description
    })
    assert response.status_code == 422
    
    # Test valid difficulty values
    for difficulty in ["easy", "medium", "hard"]:
        response = client.post("/api/recipes/", json={
            "title": f"Test {difficulty}",
            "difficulty": difficulty
        })
        assert response.status_code == 200
    
    # Test ingredient validation
    complex_ingredients = [
        {"name": "Ingredient with unit", "amount": "1.5", "unit": "cups"},
        {"name": "Ingredient without unit", "amount": "3", "unit": None},
        {"name": "Ingredient no unit specified", "amount": "2"}  # unit should default to None
    ]
    
    response = client.post("/api/recipes/", json={
        "title": "Complex Ingredients Test",
        "ingredients": complex_ingredients
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["ingredients"]) == 3
    
    # Test metadata flexibility
    complex_metadata = {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "number": 42,
        "boolean": True,
        "null_value": None
    }
    
    response = client.post("/api/recipes/", json={
        "title": "Metadata Test",
        "metadata": complex_metadata
    })
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["nested"]["key"] == "value"
    assert data["metadata"]["list"] == [1, 2, 3]
    assert data["metadata"]["boolean"] is True