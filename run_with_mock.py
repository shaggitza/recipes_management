#!/usr/bin/env python3
"""
Run the Recipe Management app with mock database for development
"""

import sys
import os
import uvicorn

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch the database import to use mock database
def patch_database():
    from app import mock_database
    import app.database
    # Replace the functions in the main database module
    app.database.connect_to_mongo = mock_database.connect_to_mongo
    app.database.close_mongo_connection = mock_database.close_mongo_connection
    app.database.get_database = mock_database.get_database
    app.database.db = mock_database.db

def create_app():
    patch_database()
    from app.main import app
    return app

if __name__ == "__main__":
    app = create_app()
    
    # Add some sample data
    import asyncio
    from datetime import datetime
    
    async def add_sample_data():
        from app import mock_database
        await mock_database.connect_to_mongo()
        db = mock_database.get_database()
        
        # Add sample recipes for testing
        sample_recipes = [
            {
                "title": "Classic Pasta",
                "description": "A simple and delicious pasta dish",
                "prep_time": 15,
                "cook_time": 20,
                "servings": 4,
                "difficulty": "easy",
                "tags": ["pasta", "dinner", "quick"],
                "meal_times": ["lunch", "dinner"],
                "ingredients": [
                    {"name": "Pasta", "amount": "400g", "unit": "g"},
                    {"name": "Olive Oil", "amount": "2", "unit": "tbsp"},
                    {"name": "Garlic", "amount": "3", "unit": "cloves"}
                ],
                "instructions": [
                    "Boil water in a large pot",
                    "Add pasta and cook according to package instructions",
                    "Heat olive oil in a pan and sauté garlic",
                    "Drain pasta and mix with the garlic oil"
                ],
                "source": {"type": "manual", "url": None, "name": None},
                "images": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "title": "Chocolate Cake",
                "description": "Rich and moist chocolate cake",
                "prep_time": 30,
                "cook_time": 45,
                "servings": 8,
                "difficulty": "medium",
                "tags": ["dessert", "chocolate", "cake"],
                "meal_times": ["dessert"],
                "ingredients": [
                    {"name": "Flour", "amount": "2", "unit": "cups"},
                    {"name": "Cocoa Powder", "amount": "0.5", "unit": "cup"},
                    {"name": "Sugar", "amount": "1.5", "unit": "cups"},
                    {"name": "Eggs", "amount": "2", "unit": "pieces"}
                ],
                "instructions": [
                    "Preheat oven to 350°F",
                    "Mix dry ingredients in a bowl",
                    "Beat eggs and add to dry ingredients",
                    "Bake for 45 minutes"
                ],
                "source": {"type": "manual", "url": None, "name": None},
                "images": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        for recipe in sample_recipes:
            await db.recipes.insert_one(recipe)
        
        print("Added sample recipes to mock database")
    
    # Run sample data setup
    asyncio.run(add_sample_data())
    
    print("Starting Recipe Management App with Mock Database...")
    print("Visit: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)