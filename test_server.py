#!/usr/bin/env python3
"""
Simple test server using mongomock
"""

import sys
import os
import uvicorn
import asyncio
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment to use mock database
os.environ["USE_MOCK_DB"] = "true"

async def setup_sample_data():
    """Add sample data for testing"""
    try:
        from app.services.recipe_service import recipe_service
        from app.models.recipe import RecipeCreate
        
        # Sample recipes
        sample_recipes = [
            RecipeCreate(
                title="Classic Pasta Carbonara",
                description="A traditional Italian pasta dish with eggs, cheese, and pancetta",
                prep_time=15,
                cook_time=20,
                servings=4,
                difficulty="medium",
                tags=["pasta", "dinner", "italian", "quick"],
                meal_times=["lunch", "dinner"],
                ingredients=[
                    {"name": "Spaghetti", "amount": "400", "unit": "g"},
                    {"name": "Pancetta", "amount": "150", "unit": "g"},
                    {"name": "Eggs", "amount": "3", "unit": "pieces"},
                    {"name": "Parmesan Cheese", "amount": "100", "unit": "g"},
                    {"name": "Black Pepper", "amount": "1", "unit": "tsp"}
                ],
                instructions=[
                    "Cook spaghetti in salted boiling water according to package instructions",
                    "Meanwhile, cut pancetta into small cubes and cook in a large pan until crispy",
                    "In a bowl, whisk together eggs, grated parmesan, and black pepper",
                    "Drain pasta and immediately add to the pan with pancetta",
                    "Remove from heat and quickly stir in the egg mixture to create a creamy sauce",
                    "Serve immediately with extra parmesan and black pepper"
                ],
                source={"type": "manual", "url": None, "name": None},
                images=[]
            ),
            RecipeCreate(
                title="Chocolate Chip Cookies",
                description="Soft and chewy chocolate chip cookies that are perfect for any occasion",
                prep_time=20,
                cook_time=12,
                servings=24,
                difficulty="easy",
                tags=["dessert", "cookies", "chocolate", "baking"],
                meal_times=["snack", "dessert"],
                ingredients=[
                    {"name": "All-purpose flour", "amount": "2.25", "unit": "cups"},
                    {"name": "Butter", "amount": "1", "unit": "cup"},
                    {"name": "Brown sugar", "amount": "0.75", "unit": "cup"},
                    {"name": "White sugar", "amount": "0.75", "unit": "cup"},
                    {"name": "Eggs", "amount": "2", "unit": "pieces"},
                    {"name": "Vanilla extract", "amount": "2", "unit": "tsp"},
                    {"name": "Chocolate chips", "amount": "2", "unit": "cups"}
                ],
                instructions=[
                    "Preheat oven to 375°F (190°C)",
                    "In a large bowl, cream together butter and both sugars until light and fluffy",
                    "Beat in eggs one at a time, then add vanilla extract",
                    "Gradually mix in flour until just combined",
                    "Fold in chocolate chips",
                    "Drop rounded tablespoons of dough onto ungreased baking sheets",
                    "Bake for 9-12 minutes until edges are golden brown",
                    "Cool on baking sheet for 5 minutes before transferring to wire rack"
                ],
                source={"type": "manual", "url": None, "name": None},
                images=[]
            ),
            RecipeCreate(
                title="Grilled Chicken Salad",
                description="A healthy and protein-packed salad with grilled chicken and fresh vegetables",
                prep_time=25,
                cook_time=15,
                servings=2,
                difficulty="easy",
                tags=["salad", "healthy", "protein", "lunch"],
                meal_times=["lunch", "dinner"],
                ingredients=[
                    {"name": "Chicken breast", "amount": "2", "unit": "pieces"},
                    {"name": "Mixed greens", "amount": "4", "unit": "cups"},
                    {"name": "Cherry tomatoes", "amount": "1", "unit": "cup"},
                    {"name": "Cucumber", "amount": "1", "unit": "piece"},
                    {"name": "Red onion", "amount": "0.25", "unit": "piece"},
                    {"name": "Olive oil", "amount": "3", "unit": "tbsp"},
                    {"name": "Balsamic vinegar", "amount": "2", "unit": "tbsp"}
                ],
                instructions=[
                    "Season chicken breasts with salt, pepper, and olive oil",
                    "Heat grill or grill pan to medium-high heat",
                    "Grill chicken for 6-7 minutes per side until cooked through",
                    "Let chicken rest for 5 minutes, then slice into strips",
                    "In a large bowl, combine mixed greens, halved cherry tomatoes, diced cucumber, and thinly sliced red onion",
                    "Whisk together olive oil and balsamic vinegar for dressing",
                    "Top salad with sliced chicken and drizzle with dressing"
                ],
                source={"type": "manual", "url": None, "name": None},
                images=[]
            )
        ]
        
        print("Adding sample recipes...")
        for recipe_data in sample_recipes:
            try:
                await recipe_service.create_recipe(recipe_data)
                print(f"✅ Added recipe: {recipe_data.title}")
            except Exception as e:
                print(f"❌ Failed to add recipe {recipe_data.title}: {e}")
        
        print("Sample data setup complete!")
        
    except Exception as e:
        print(f"Error setting up sample data: {e}")

if __name__ == "__main__":
    from app.main import app
    
    # Setup sample data
    print("Setting up sample data...")
    try:
        asyncio.run(setup_sample_data())
    except Exception as e:
        print(f"Warning: Could not setup sample data: {e}")
    
    print("Starting Recipe Management App...")
    print("Visit: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)