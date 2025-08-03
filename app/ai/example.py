"""
Example showing the simplified langfun usage similar to your example.

This demonstrates how to use langfun for recipe extraction in a much simpler way.
"""

import langfun as lf
import pyglove as pg
import os
from typing import Optional

# Simple models similar to your example
class Ingredient(pg.Object):
    name: str
    amount: str
    unit: Optional[str] = None

class Recipe(pg.Object):
    title: str
    description: Optional[str] = None
    ingredients: list[Ingredient] = []
    instructions: list[str] = []
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: list[str] = []

def extract_recipe_example():
    """Example of simple langfun usage for recipe extraction."""
    
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
    
    # Simple langfun query - just like your example!
    recipe = lf.query(
        f'Extract recipe information from this content: {content}',
        Recipe,
        lm=lf.llms.Gpt4o(api_key=api_key),
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
