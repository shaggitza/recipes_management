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
        Extract recipe data from web content using langfun.
        
        Args:
            content: Scraped web content
            source_url: Original URL  
            images: Optional list of images from the page
            
        Returns:
            RecipeExtraction object with extracted data
        """
        try:
            logger.info(f"Extracting recipe from content (length: {len(content)})")
            
            # Create prompt for recipe extraction
            prompt = self._create_extraction_prompt(content, images)
            
            # Use langfun to extract recipe data
            recipe = lf.query(
                prompt,
                RecipeExtraction,
                lm=lf.llms.Gpt4o(api_key=self.api_key),
            )
            
            logger.info(f"Successfully extracted recipe: {recipe.title}")
            return recipe
            
        except Exception as e:
            logger.error(f"Recipe extraction failed: {e}")
            # Return a basic recipe object with error info
            return RecipeExtraction(
                title=f"Failed to extract recipe from {source_url}",
                description=f"Extraction error: {str(e)}",
                ingredients=[],
                instructions=[],
                tags=["extraction_error"]
            )

    def _create_extraction_prompt(self, content: str, images: Optional[List[dict]] = None) -> str:
        """Create a prompt for recipe extraction."""
        
        images_section = ""
        if images:
            images_section = f"""

Available images from the page:
{self._format_images_for_prompt(images[:5])}  # Limit to 5 images

Please select the most relevant recipe images and include them in the images field.
"""

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
- For images, set relevance_score (0.0-1.0) and is_primary (true for main image)

Appliance Settings:
- IMPORTANT: Generate appropriate appliance settings based on the cooking methods mentioned in the recipe
- Choose from: gas_burner, airfryer, electric_grill, electric_stove, induction_stove, oven, charcoal_grill, stove
- Include realistic temperature/heat levels, durations, and required utensils
- Examples: If recipe mentions "bake at 350°F", add oven settings. If it says "fry in pan", add gas_burner or stove settings
- For each appliance, specify appropriate utensils if mentioned (pans, trays, etc.)

Web Content:
{content}  # Limit content for token efficiency
{images_section}"""

    def _format_images_for_prompt(self, images: List[dict]) -> str:
        """Format images for inclusion in the prompt."""
        formatted = []
        for i, img in enumerate(images):
            img_info = f"Image {i+1}: {img['url']}"
            if img.get('alt_text'):
                img_info += f" (alt: {img['alt_text']})"
            if img.get('title'):
                img_info += f" (title: {img['title']})"
            formatted.append(img_info)
        return "\n".join(formatted)
