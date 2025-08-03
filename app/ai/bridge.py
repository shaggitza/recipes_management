"""Compatibility layer to bridge old and new langfun extraction APIs."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .simple_extractor import SimpleRecipeExtractor
from .models import RecipeExtraction

logger = logging.getLogger("app.ai.bridge")


def _clean_pyglove_dict(data) -> Any:
    """Clean PyGlove dictionary by removing _type fields and converting nested objects."""
    if isinstance(data, dict):
        # Remove _type field and recursively clean nested objects
        cleaned = {}
        for key, value in data.items():
            if key != '_type':  # Skip PyGlove type information
                cleaned[key] = _clean_pyglove_dict(value)
        return cleaned
    elif isinstance(data, list):
        # Recursively clean list items
        return [_clean_pyglove_dict(item) for item in data]
    else:
        # Return primitive values as-is
        return data


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
    """Convert RecipeExtraction to dictionary format using PyGlove's to_json() method."""
    # Use PyGlove's built-in to_json() method and clean up the result
    recipe_dict = _clean_pyglove_dict(recipe.to_json())
    
    # Add source_url which isn't part of the PyGlove model
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
            error_msg = f"Recipe extraction failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
