"""Simplified langfun models for structured recipe data extraction."""

from typing import List, Optional, Literal
import pyglove as pg

# Import MealTime enum from recipe models
try:
    from app.models.recipe import MealTime
except ImportError:
    # Fallback for tests or when running standalone
    from enum import Enum
    class MealTime(str, Enum):
        BREAKFAST = "breakfast"
        LUNCH = "lunch" 
        DINNER = "dinner"
        SNACK = "snack"
        BRUNCH = "brunch"
        DESSERT = "dessert"


class Ingredient(pg.Object):
    """Recipe ingredient with standardized structure."""

    name: str
    amount: str | None = None
    unit: Optional[str] = None


class ExtractedImage(pg.Object):
    """Extracted image with metadata."""

    url: str = ""
    alt_text: Optional[str] = None
    title: Optional[str] = None
    relevance_score: Optional[float] = None
    is_primary: bool = False
    # Alternative field names for backward compatibility  
    src: Optional[str] = None
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ScrapedData(pg.Object):
    """Scraped web page data for recipe extraction."""

    url: str
    html_content: str
    title: Optional[str] = None
    status_code: int = 200
    images: List[ExtractedImage] = []
    metadata: Optional[dict] = None
    structured_data: List[dict] = []


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
    extraction_method: Optional[str] = None
    cuisine: Optional[str] = None


# Alias for compatibility with tests
ExtractedRecipe = RecipeExtraction
