"""
Example showing ScrapeGraphAI usage for recipe extraction.

This demonstrates how to use ScrapeGraphAI for recipe extraction with better Pydantic integration.
"""

import os
from typing import Optional

from .models import RecipeExtraction, Ingredient


def extract_recipe_example():
    """Example of ScrapeGraphAI usage for recipe extraction."""
    
    # Sample web content (this would come from scraping)
    content = """
    Title: Classic Chocolate Chip Cookies
    
    A delicious recipe for soft and chewy chocolate chip cookies that everyone will love!
    
    Ingredients:
    - 2 1/4 cups all-purpose flour
    - 1 tsp baking soda
    - 1 tsp salt
    - 1 cup butter, softened
    - 3/4 cup granulated sugar
    - 3/4 cup brown sugar
    - 2 large eggs
    - 2 tsp vanilla extract
    - 2 cups chocolate chips
    
    Instructions:
    1. Preheat oven to 375°F
    2. Mix flour, baking soda, and salt in a bowl
    3. Cream butter and sugars until light and fluffy
    4. Beat in eggs and vanilla
    5. Gradually mix in flour mixture
    6. Stir in chocolate chips
    7. Drop spoonfuls on baking sheet
    8. Bake for 9-11 minutes
    
    Prep time: 15 minutes
    Cook time: 10 minutes
    Serves: 24 cookies
    Difficulty: Easy
    """
    
    # Get API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    try:
        # Try to import ScrapeGraphAI
        from scrapegraphai.graphs import JSONScraperGraph
        
        # Create ScrapeGraphAI configuration
        graph_config = {
            "llm": {
                "model": "gpt-4o-mini",
                "api_key": api_key,
            },
        }
        
        # Create prompt for recipe extraction
        prompt = """Extract comprehensive recipe information from this content. 
        Return the data structured according to the RecipeExtraction schema with title, ingredients, instructions, etc."""
        
        # Use ScrapeGraphAI with our Pydantic schema
        json_scraper_graph = JSONScraperGraph(
            prompt=prompt,
            source=content,
            schema=RecipeExtraction,
            config=graph_config
        )
        
        # Execute the extraction
        result = json_scraper_graph.run()
        
        if isinstance(result, dict):
            recipe = RecipeExtraction(**result)
        else:
            recipe = result
        
    except ImportError:
        print("ScrapeGraphAI not available, using mock data")
        # Fallback mock recipe for demonstration
        recipe = RecipeExtraction(
            title="Classic Chocolate Chip Cookies",
            description="A delicious recipe for soft and chewy chocolate chip cookies that everyone will love!",
            ingredients=[
                Ingredient(name="all-purpose flour", amount="2 1/4", unit="cups"),
                Ingredient(name="baking soda", amount="1", unit="tsp"),
                Ingredient(name="salt", amount="1", unit="tsp"),
                Ingredient(name="butter, softened", amount="1", unit="cup"),
                Ingredient(name="granulated sugar", amount="3/4", unit="cup"),
                Ingredient(name="brown sugar", amount="3/4", unit="cup"),
                Ingredient(name="large eggs", amount="2"),
                Ingredient(name="vanilla extract", amount="2", unit="tsp"),
                Ingredient(name="chocolate chips", amount="2", unit="cups"),
            ],
            instructions=[
                "Preheat oven to 375°F",
                "Mix flour, baking soda, and salt in a bowl",
                "Cream butter and sugars until light and fluffy",
                "Beat in eggs and vanilla",
                "Gradually mix in flour mixture",
                "Stir in chocolate chips",
                "Drop spoonfuls on baking sheet",
                "Bake for 9-11 minutes",
            ],
            prep_time=15,
            cook_time=10,
            servings=24,
            difficulty="easy",
            tags=["dessert", "cookies", "american"],
            meal_times=["dessert"],
        )
    
    print("Extracted Recipe:")
    print(f"Title: {recipe.title}")
    print(f"Description: {recipe.description}")
    print(f"Ingredients ({len(recipe.ingredients)}):")
    for ing in recipe.ingredients:
        unit_str = f" {ing.unit}" if ing.unit else ""
        print(f"  - {ing.amount}{unit_str} {ing.name}")
    print(f"Instructions ({len(recipe.instructions)}):")
    for i, instruction in enumerate(recipe.instructions, 1):
        print(f"  {i}. {instruction}")
    print(f"Prep time: {recipe.prep_time} minutes")
    print(f"Cook time: {recipe.cook_time} minutes")
    print(f"Servings: {recipe.servings}")
    print(f"Difficulty: {recipe.difficulty}")
    print(f"Tags: {recipe.tags}")
    
    return recipe


if __name__ == "__main__":
    extract_recipe_example()
