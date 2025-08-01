#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        from app.main import app
        from app.models.recipe import Recipe, RecipeCreate
        from app.routers.recipes import router
        from app.mock_database import Database
        from app.config import settings
        
        print("✅ All imports successful!")
        print(f"✅ App title: {settings.app_title}")
        print(f"✅ App version: {settings.app_version}")
        print("✅ FastAPI app created successfully")
        print("✅ Recipe models imported successfully")
        print("✅ API routes imported successfully")
        
        # Test creating a recipe model
        recipe_data = {
            "title": "Test Recipe",
            "description": "A test recipe for validation",
            "ingredients": [
                {"name": "Test Ingredient", "amount": "1", "unit": "cup"}
            ],
            "instructions": ["Test instruction"],
            "tags": ["test"]
        }
        
        recipe = RecipeCreate(**recipe_data)
        print(f"✅ Recipe model validation successful: {recipe.title}")
        
        # Test Recipe creation with generated ID
        full_recipe = Recipe(**recipe_data)
        print(f"✅ Recipe with ID generated successfully: {full_recipe.id[:8]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Import or validation error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Recipe Management Application...")
    print("=" * 50)
    
    success = await test_imports()
    
    if success:
        print("=" * 50)
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("1. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Open http://localhost:8000 in your browser")
        print("\nNote: Currently using in-memory storage for demonstration.")
        print("For production, replace mock_database with real MongoDB connection.")
    else:
        print("=" * 50)
        print("❌ Tests failed! Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())