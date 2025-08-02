"""Compatibility layer to bridge old and new langfun extraction APIs."""

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
    """Convert RecipeExtraction to dictionary format expected by existing code."""
    return {
        "title": recipe.title,
        "description": recipe.description,
        "ingredients": [
            {
                "name": ing.name,
                "amount": ing.amount,
                "unit": ing.unit
            }
            for ing in recipe.ingredients
        ],
        "instructions": list(recipe.instructions),
        "prep_time": recipe.prep_time,
        "cook_time": recipe.cook_time,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "tags": list(recipe.tags),
        "meal_times": list(recipe.meal_times),
        "source_url": source_url,
        "images": [
            {
                "url": img.url,
                "alt_text": img.alt_text,
                "title": img.title,
                "relevance_score": img.relevance_score,
                "is_primary": img.is_primary
            }
            for img in recipe.images
        ]
    }


class RecipeExtractor:
    """Compatibility wrapper for the old RecipeExtractor interface."""
    
    def __init__(self, use_ai: bool = True, api_key: Optional[str] = None):
        """Initialize with compatibility for old interface."""
        if not use_ai:
            raise ValueError("Only AI extraction is supported in the new implementation")
            
        self.use_ai = use_ai
        self.api_key = api_key
        self._extractor = SimpleRecipeExtractor(api_key=api_key)
        
        logger.info("RecipeExtractor initialized with simplified langfun backend")

    async def extract_recipe(
        self, content: str, source_url: str, images: Optional[List[dict]] = None
    ) -> RecipeExtractionResult:
        """
        Extract recipe with compatibility wrapper.
        
        Maintains the same interface as the old extractor but uses the new simplified backend.
        """
        try:
            logger.info(f"Extracting recipe from {source_url} using simplified langfun")
            
            # Use the new simplified extractor
            recipe_extraction = await self._extractor.extract_recipe(content, source_url, images)
            
            # Convert to expected dictionary format
            recipe_dict = recipe_extraction_to_dict(recipe_extraction, source_url)
            
            return RecipeExtractionResult(
                success=True,
                recipe=recipe_dict,
                error=None,
                source_url=source_url,
                extraction_metadata={
                    "method": "simplified_langfun",
                    "content_length": len(content),
                    "model": "gpt-4o",
                    "images_analyzed": len(images or []),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Recipe extraction failed: {e}")
            return RecipeExtractionResult(
                success=False,
                recipe=None,
                error=str(e),
                source_url=source_url,
                extraction_metadata={
                    "method": "simplified_langfun",
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
