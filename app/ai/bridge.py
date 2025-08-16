"""Compatibility layer for recipe extraction APIs."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .simple_extractor import SimpleRecipeExtractor
from .models import RecipeExtraction

logger = logging.getLogger("app.ai.bridge")


class RecipeExtractionResult:
    """Result wrapper to maintain compatibility with existing code."""
    
    def __init__(self, success: bool, recipe: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None, source_url: str = "", 
                 extraction_metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.recipe = recipe
        self.error = error
        self.source_url = source_url
        self.extraction_metadata = extraction_metadata or {}


def recipe_extraction_to_dict(recipe: RecipeExtraction, source_url: str) -> Dict[str, Any]:
    """Convert RecipeExtraction to dictionary format using Pydantic's model_dump method."""
    # Use Pydantic's model_dump() method to convert to dictionary
    recipe_dict = recipe.model_dump()
    
    # Ensure source_url is set
    recipe_dict["source_url"] = source_url
    
    return recipe_dict


class RecipeExtractor:
    """Compatibility wrapper for the old RecipeExtractor interface."""
    
    def __init__(self, use_ai: bool = True, api_key: Optional[str] = None):
        """Initialize with compatibility for old interface."""
        if not use_ai:
            raise ValueError("Only AI extraction is supported in the new implementation")
            
        self.use_ai = use_ai
        self.api_key = api_key
        self._extractor = SimpleRecipeExtractor(api_key=api_key)
        
        logger.info("RecipeExtractor initialized with ScrapeGraphAI backend")

    async def extract_recipe(
        self, content: str, source_url: str, images: Optional[List[dict]] = None
    ) -> RecipeExtractionResult:
        """
        Extract recipe with compatibility wrapper.
        
        Maintains the same interface as the old extractor but uses the new ScrapeGraphAI backend.
        Images parameter is ignored in the simplified version.
        """
        try:
            logger.info(f"Extracting recipe from {source_url} using ScrapeGraphAI")
            
            # Use the new ScrapeGraphAI extractor (ignore images parameter)
            recipe_extraction = await self._extractor.extract_recipe(content, source_url)
            
            # Convert to expected dictionary format
            recipe_dict = recipe_extraction_to_dict(recipe_extraction, source_url)
            
            return RecipeExtractionResult(
                success=True,
                recipe=recipe_dict,
                error=None,
                source_url=source_url,
                extraction_metadata={
                    "method": "scrapegraphai",
                    "content_length": len(content),
                    "model": "gpt-4o-mini",
                    "images_analyzed": 0,  # Always 0 in simplified version
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            error_msg = f"Recipe extraction failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
