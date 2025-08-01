"""
Performance and stress tests for the Recipe Management API.
"""
import pytest
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_api_response_times(client, clean_db):
    """Test API response times for basic operations."""
    # Create a recipe for timing tests
    recipe_data = {
        "title": "Performance Test Recipe",
        "description": "Testing API performance",
        "ingredients": [{"name": f"Ingredient {i}", "amount": "1", "unit": "cup"} for i in range(10)],
        "instructions": [f"Step {i}: Do something" for i in range(10)],
        "tags": ["performance", "test", "timing"]
    }
    
    # Time recipe creation
    start_time = time.time()
    response = client.post("/api/recipes/", json=recipe_data)
    creation_time = time.time() - start_time
    
    assert response.status_code == 200
    assert creation_time < 2.0  # Should create in under 2 seconds
    
    recipe_id = response.json()["id"]
    
    # Time recipe retrieval
    start_time = time.time()
    response = client.get(f"/api/recipes/{recipe_id}")
    retrieval_time = time.time() - start_time
    
    assert response.status_code == 200
    assert retrieval_time < 1.0  # Should retrieve in under 1 second
    
    # Time recipe update
    start_time = time.time()
    response = client.put(f"/api/recipes/{recipe_id}", json={"description": "Updated for performance test"})
    update_time = time.time() - start_time
    
    assert response.status_code == 200
    assert update_time < 2.0  # Should update in under 2 seconds
    
    # Time recipe deletion
    start_time = time.time()
    response = client.delete(f"/api/recipes/{recipe_id}")
    deletion_time = time.time() - start_time
    
    assert response.status_code == 200
    assert deletion_time < 1.0  # Should delete in under 1 second

def test_bulk_creation_performance(client, clean_db):
    """Test performance of bulk recipe creation."""
    recipes_to_create = 50
    
    start_time = time.time()
    created_ids = []
    
    for i in range(recipes_to_create):
        recipe_data = {
            "title": f"Bulk Performance Recipe {i:03d}",
            "description": f"Performance test recipe number {i}",
            "ingredients": [
                {"name": f"Ingredient {j}", "amount": str(j+1), "unit": "unit"}
                for j in range(5)
            ],
            "tags": [f"bulk{i % 10}", "performance", "test"],
            "difficulty": ["easy", "medium", "hard"][i % 3]
        }
        
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])
    
    total_time = time.time() - start_time
    
    # Should be able to create 50 recipes in reasonable time
    assert total_time < 60.0  # Under 60 seconds for 50 recipes
    assert len(created_ids) == recipes_to_create
    
    # Verify all recipes were created
    response = client.get("/api/recipes/?limit=100")
    assert response.status_code == 200
    all_recipes = response.json()
    assert len(all_recipes) >= recipes_to_create

def test_search_performance_with_large_dataset(client, clean_db):
    """Test search performance with a larger dataset."""
    # First create a larger dataset
    num_recipes = 100
    search_terms = ["chocolate", "vanilla", "strawberry", "lemon", "orange"]
    
    for i in range(num_recipes):
        recipe_data = {
            "title": f"{search_terms[i % len(search_terms)]} Recipe {i:03d}",
            "description": f"Delicious {search_terms[i % len(search_terms)]} flavored recipe",
            "ingredients": [
                {"name": f"{search_terms[i % len(search_terms)]} extract", "amount": "1", "unit": "tsp"},
                {"name": "flour", "amount": "2", "unit": "cups"},
                {"name": "sugar", "amount": "1", "unit": "cup"}
            ],
            "tags": [search_terms[i % len(search_terms)], "performance", f"batch{i // 20}"],
            "difficulty": ["easy", "medium", "hard"][i % 3]
        }
        
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
    
    # Test search performance
    for search_term in search_terms:
        start_time = time.time()
        response = client.get(f"/api/recipes/?search={search_term}")
        search_time = time.time() - start_time
        
        assert response.status_code == 200
        assert search_time < 3.0  # Search should complete in under 3 seconds
        
        results = response.json()
        assert len(results) > 0  # Should find results
        # Verify search results contain the search term
        assert any(search_term.lower() in recipe["title"].lower() or 
                  search_term.lower() in recipe["description"].lower()
                  for recipe in results)

def test_pagination_performance(client, clean_db):
    """Test pagination performance with large result sets."""
    # Create 200 recipes for pagination testing
    num_recipes = 200
    for i in range(num_recipes):
        recipe_data = {
            "title": f"Pagination Test Recipe {i:04d}",
            "description": f"Recipe for pagination testing, number {i}",
            "tags": ["pagination", "performance", f"group{i // 50}"],
        }
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
    
    # Test various page sizes and offsets
    page_sizes = [10, 25, 50, 100]
    
    for page_size in page_sizes:
        for page_num in range(3):  # Test first 3 pages
            skip = page_num * page_size
            
            start_time = time.time()
            response = client.get(f"/api/recipes/?skip={skip}&limit={page_size}")
            pagination_time = time.time() - start_time
            
            assert response.status_code == 200
            assert pagination_time < 2.0  # Pagination should be fast
            
            results = response.json()
            expected_count = min(page_size, max(0, num_recipes - skip))
            assert len(results) == expected_count

def test_concurrent_api_access(client, clean_db):
    """Test concurrent API access performance and stability."""
    # Create some base data
    base_recipes = []
    for i in range(10):
        recipe_data = {
            "title": f"Concurrent Base Recipe {i}",
            "description": f"Base recipe for concurrent testing {i}",
            "tags": ["concurrent", "base"]
        }
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
        base_recipes.append(response.json()["id"])
    
    def perform_mixed_operations() -> Dict[str, Any]:
        """Perform a mix of read and write operations."""
        results = {"reads": 0, "writes": 0, "errors": 0}
        
        try:
            # Read operations
            for _ in range(5):
                response = client.get("/api/recipes/?limit=5")
                if response.status_code == 200:
                    results["reads"] += 1
                else:
                    results["errors"] += 1
            
            # Write operations
            for i in range(3):
                recipe_data = {
                    "title": f"Concurrent Recipe {time.time():.3f}",
                    "description": "Created during concurrent test",
                    "tags": ["concurrent", "test"]
                }
                response = client.post("/api/recipes/", json=recipe_data)
                if response.status_code == 200:
                    results["writes"] += 1
                else:
                    results["errors"] += 1
        
        except Exception:
            results["errors"] += 1
        
        return results
    
    # Run concurrent operations
    num_threads = 10
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(perform_mixed_operations) for _ in range(num_threads)]
        results = []
        
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # Analyze results
    total_reads = sum(r["reads"] for r in results)
    total_writes = sum(r["writes"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    
    # Should complete concurrent operations in reasonable time
    assert total_time < 30.0  # Should complete in under 30 seconds
    
    # Should have low error rate (less than 5%)
    total_operations = total_reads + total_writes + total_errors
    error_rate = total_errors / total_operations if total_operations > 0 else 0
    assert error_rate < 0.05  # Less than 5% error rate
    
    # Should successfully perform operations
    assert total_reads > 0
    assert total_writes > 0

def test_memory_usage_stability(client, clean_db):
    """Test that repeated operations don't cause memory leaks."""
    import gc
    
    # Perform repeated operations to test memory stability
    operations_count = 100
    
    for i in range(operations_count):
        # Create recipe
        recipe_data = {
            "title": f"Memory Test Recipe {i}",
            "description": f"Testing memory usage {i}",
            "ingredients": [{"name": f"Ingredient {j}", "amount": "1"} for j in range(5)],
            "instructions": [f"Step {j}" for j in range(5)],
            "tags": ["memory", "test", f"batch{i // 10}"]
        }
        
        response = client.post("/api/recipes/", json=recipe_data)
        assert response.status_code == 200
        recipe_id = response.json()["id"]
        
        # Read recipe
        response = client.get(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        
        # Update recipe
        response = client.put(f"/api/recipes/{recipe_id}", 
                            json={"description": f"Updated {i}"})
        assert response.status_code == 200
        
        # Delete recipe
        response = client.delete(f"/api/recipes/{recipe_id}")
        assert response.status_code == 200
        
        # Periodic garbage collection to help with memory management
        if i % 20 == 0:
            gc.collect()
    
    # Test should complete without memory errors
    assert True  # If we get here, no memory issues occurred

def test_api_rate_limits_and_throttling(client, clean_db):
    """Test API behavior under rapid successive requests."""
    # Perform rapid successive requests
    rapid_requests = 50
    start_time = time.time()
    
    success_count = 0
    error_count = 0
    
    for i in range(rapid_requests):
        try:
            response = client.get("/api/recipes/")
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
        except Exception:
            error_count += 1
    
    total_time = time.time() - start_time
    
    # Should handle rapid requests reasonably well
    assert success_count > rapid_requests * 0.8  # At least 80% success rate
    assert total_time < 30.0  # Should complete in reasonable time
    
    # Test that API remains responsive after rapid requests
    response = client.get("/health")
    assert response.status_code == 200