"""
Example showing ScrapeGraphAI crawler usage for recipe extraction.

This demonstrates how to use ScrapeGraphAI's crawler for direct URL-to-model extraction.
"""

import os
from typing import Optional

from .models import RecipeExtraction, Ingredient


def extract_recipe_example():
    """Example of ScrapeGraphAI crawler usage for recipe extraction."""
    
    # Example URL (this would be a real recipe URL)
    example_url = "https://example.com/chocolate-chip-cookies"
    
    # Get API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    try:
        # Try to import ScrapeGraphAI
        from scrapegraphai.graphs import SmartScraperGraph
        
        # Create ScrapeGraphAI configuration
        graph_config = {
            "llm": {
                "model": "gpt-4o-mini",
                "api_key": api_key,
            },
        }
        
        # Create prompt for recipe extraction
        prompt = """Extract comprehensive recipe information from this web page. 
        Return the data structured according to the RecipeExtraction schema with title, ingredients, instructions, etc."""
        
        # Use ScrapeGraphAI's SmartScraperGraph to crawl and extract directly from URL
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=example_url,  # Direct URL crawling
            schema=RecipeExtraction,
            config=graph_config
        )
        
        # Execute the crawling and extraction
        result = smart_scraper_graph.run()
        
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
            source_url=example_url,
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
