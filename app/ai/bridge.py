"""Compatibility layer to bridge old and new langfun extraction APIs."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .simple_extractor import SimpleRecipeExtractor
from .models import RecipeExtraction

logger = logging.getLogger("app.ai.bridge")


def _convert_appliance_setting_to_dict(setting) -> Dict[str, Any]:
    """Convert a PyGlove appliance setting to dictionary format."""
    if hasattr(setting, 'model_dump'):
        # If it has model_dump, it's a Pydantic-like object
        return setting.model_dump()
    elif hasattr(setting, '_sym_attributes'):
        # PyGlove object - use _sym_attributes to get the actual data
        setting_dict = {}
        sym_attrs = setting._sym_attributes
        
        for key, value in sym_attrs.items():
            if key == 'utensils' and value:
                # Convert utensils list
                setting_dict[key] = [
                    _convert_utensil_to_dict(utensil) for utensil in value
                ]
            else:
                setting_dict[key] = value
        
        return setting_dict
    elif hasattr(setting, '__dict__'):
        # Convert regular object to dict, filtering out internal attributes
        setting_dict = {}
        for key, value in setting.__dict__.items():
            if not key.startswith('_'):
                if key == 'utensils' and value:
                    # Convert utensils list
                    setting_dict[key] = [
                        _convert_utensil_to_dict(utensil) for utensil in value
                    ]
                else:
                    setting_dict[key] = value
        return setting_dict
    else:
        # Fallback: try to access attributes directly
        try:
            setting_dict = {}
            # Get all the attributes from the class definition
            setting_dict['appliance_type'] = getattr(setting, 'appliance_type', None)
            
            # Common attributes that might exist
            for attr in ['flame_level', 'heat_level', 'power_level', 'temperature_fahrenheit', 
                        'duration_minutes', 'preheat_required', 'shake_interval_minutes',
                        'rack_position', 'convection', 'heat_zone', 'lid_position', 'notes']:
                if hasattr(setting, attr):
                    setting_dict[attr] = getattr(setting, attr)
            
            # Handle utensils
            if hasattr(setting, 'utensils'):
                utensils = getattr(setting, 'utensils', [])
                if utensils:
                    setting_dict['utensils'] = [
                        _convert_utensil_to_dict(utensil) for utensil in utensils
                    ]
                else:
                    setting_dict['utensils'] = []
            
            return setting_dict
        except:
            # Final fallback
            return {"appliance_type": "unknown", "error": "conversion_failed"}


def _convert_utensil_to_dict(utensil) -> Dict[str, Any]:
    """Convert a PyGlove utensil to dictionary format."""
    if hasattr(utensil, 'model_dump'):
        return utensil.model_dump()
    elif hasattr(utensil, '_sym_attributes'):
        # PyGlove object - use _sym_attributes
        return dict(utensil._sym_attributes)
    elif hasattr(utensil, '__dict__'):
        return {k: v for k, v in utensil.__dict__.items() if not k.startswith('_')}
    else:
        # For PyGlove objects, try to access attributes directly
        try:
            utensil_dict = {}
            for attr in ['type', 'size', 'material', 'notes']:
                if hasattr(utensil, attr):
                    utensil_dict[attr] = getattr(utensil, attr)
            return utensil_dict
        except:
            return {"type": "unknown", "error": "conversion_failed"}


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
            {"name": ing.name, "amount": ing.amount, "unit": ing.unit}
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
                "is_primary": img.is_primary,
            }
            for img in recipe.images
        ],
        "appliance_settings": [
            _convert_appliance_setting_to_dict(setting)
            for setting in recipe.appliance_settings
        ],
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
            error_msg = f"Recipe extraction failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
