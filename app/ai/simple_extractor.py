"""Simplified AI-powered recipe extraction using langfun."""

import logging
import os
from typing import Optional, List

import langfun as lf

from .models import RecipeExtraction

logger = logging.getLogger("app.ai.extractor")


class SimpleRecipeExtractor:
    """Simplified recipe extractor using langfun like the example you provided."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the extractor with OpenAI API key."""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    async def extract_recipe(self, content: str, source_url: str, images: Optional[List[dict]] = None) -> RecipeExtraction:
        """
        Extract recipe data from web content using langfun - simplified without image processing.
        
        Args:
            content: Scraped web content
            source_url: Original URL  
            images: Optional list of images from the page (ignored)
            
        Returns:
            RecipeExtraction object with extracted data
        """
        try:
            logger.info(f"Extracting recipe from content (length: {len(content)})")
            
            # Create simplified prompt without image processing
            prompt = self._create_extraction_prompt(content)
            
            # Use langfun to extract recipe data
            recipe = lf.query(
                prompt,
                RecipeExtraction,
                lm=lf.llms.Gpt4o(api_key=self.api_key),
            )
            
            logger.info(f"Successfully extracted recipe: {recipe.title}")
            return recipe
            
        except Exception as e:
            error_msg = f"Recipe extraction failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _create_extraction_prompt(self, content: str) -> str:
        """Create a simplified prompt for recipe extraction without image processing."""
        
        return f"""Extract comprehensive recipe information from this web content.

Rules:
- Translate any non-Romanian text to Romanian
- never send None where a value it's required (amount, name, title, etc.)
- never write something that is not expected by the model
- Estimate prep_time and cook_time if not explicitly stated (in minutes)
- Set difficulty as "easy", "medium", or "hard"
- Extract meaningful tags (cuisine, meal type, dietary restrictions, etc.)
- tags should only contain one or two words, it should not repeat something that is allready in other fields, use country, origin, type of food, and other categorizations
- For meal_times, use only these values: "breakfast", "lunch", "dinner", "snack", "brunch", "dessert"
- Include clear step-by-step instructions and split one to many if needed
- title should be a clasic name of the recipe, not a description, nor adjectives should be used
- Images field should always be empty (image extraction is simplified)

Appliance Settings:
- IMPORTANT: Generate appropriate appliance settings based on the cooking methods mentioned in the recipe
- Choose from: gas_burner, airfryer, electric_grill, electric_stove, induction_stove, oven, charcoal_grill, stove
- Include realistic temperature/heat levels, durations, and required utensils
- Examples: If recipe mentions "bake at 350°F", add oven settings. If it says "fry in pan", add gas_burner or stove settings
- For each appliance, specify appropriate utensils if mentioned (pans, trays, etc.)

Web Content:
{content}"""


