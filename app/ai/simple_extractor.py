"""AI-powered recipe extraction using ScrapeGraphAI's crawler."""

import logging
import os
from typing import Optional

from .models import RecipeExtraction

logger = logging.getLogger("app.ai.extractor")


class SimpleRecipeExtractor:
    """Recipe extractor using ScrapeGraphAI's crawler for direct URL-to-model extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the extractor with OpenAI API key."""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    async def extract_recipe_from_url(self, url: str) -> RecipeExtraction:
        """
        Extract recipe data directly from URL using ScrapeGraphAI's crawler.
        
        Args:
            url: URL of the recipe page to extract from
            
        Returns:
            RecipeExtraction object with extracted data
        """
        try:
            logger.info(f"Extracting recipe directly from URL: {url}")
            
            # Import ScrapeGraphAI here to handle import errors gracefully
            try:
                from scrapegraphai.graphs import SmartScraperGraph
            except ImportError:
                logger.warning("ScrapeGraphAI not available, falling back to mock implementation")
                return self._mock_extraction(url)
            
            # Create ScrapeGraphAI configuration
            graph_config = {
                "llm": {
                    "model": "gpt-4o-mini",
                    "api_key": self.api_key,
                },
            }
            
            # Create the prompt for recipe extraction
            prompt = self._create_extraction_prompt()
            
            # Use ScrapeGraphAI's SmartScraperGraph to crawl and extract directly from URL
            smart_scraper_graph = SmartScraperGraph(
                prompt=prompt,
                source=url,  # Direct URL crawling
                schema=RecipeExtraction,
                config=graph_config
            )
            
            # Execute the crawling and extraction asynchronously
            result = await smart_scraper_graph.run_safe_async()
            
            # Ensure source_url is set
            if isinstance(result, dict):
                result['source_url'] = url
                recipe = RecipeExtraction(**result)
            else:
                recipe = result
                recipe.source_url = url
            
            logger.info(f"Successfully extracted recipe: {recipe.title}")
            return recipe
            
        except Exception as e:
            error_msg = f"Recipe extraction failed for {url}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    # Backward compatibility method - delegates to new URL-based method
    async def extract_recipe(self, content: str, source_url: str, images: Optional[list] = None) -> RecipeExtraction:
        """
        Backward compatibility method that delegates to URL-based extraction.
        
        Note: content and images parameters are ignored since we now extract directly from URL.
        """
        logger.warning("extract_recipe() is deprecated, use extract_recipe_from_url() instead")
        return await self.extract_recipe_from_url(source_url)

    def _create_extraction_prompt(self) -> str:
        """Create a prompt for recipe extraction optimized for ScrapeGraphAI."""
        
        return """Extract comprehensive recipe information from this web content.

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

Return the data structured according to the RecipeExtraction schema."""

    def _mock_extraction(self, url: str) -> RecipeExtraction:
        """
        Fallback mock extraction when ScrapeGraphAI is not available.
        This is useful for testing and development.
        """
        logger.info("Using mock extraction fallback")
        
        # Simple mock recipe extraction
        return RecipeExtraction(
            title="Mock Recipe",
            description="This is a mock recipe extracted when ScrapeGraphAI is not available",
            ingredients=[],
            instructions=[],
            prep_time=15,
            cook_time=30,
            servings=4,
            difficulty="easy",
            tags=["mock"],
            meal_times=[],
            images=[],
            source_url=url,
            appliance_settings=[]
        )


