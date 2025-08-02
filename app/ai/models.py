"""Simplified langfun models for structured recipe data extraction."""

from typing import List, Optional
import pyglove as pg

# Import MealTime from the main models for consistency
from app.models.recipe import MealTime


class Ingredient(pg.Object):
    """Recipe ingredient with standardized structure."""

    name: str
    amount: str
    unit: Optional[str] = None


class ExtractedImage(pg.Object):
    """Extracted image with metadata."""

    url: str
    alt_text: Optional[str] = None
    title: Optional[str] = None
    relevance_score: Optional[float] = None
    is_primary: bool = False


class RecipeExtraction(pg.Object):
    """Simplified recipe extraction model using pyglove."""

    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient] = []
    instructions: List[str] = []
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str] = []
    meal_times: List[MealTime] = []
    images: List[ExtractedImage] = []
    source_url: Optional[str] = None


# Alias for compatibility with tests
ExtractedRecipe = RecipeExtraction
