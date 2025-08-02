"""PyGlove models for structured recipe data extraction."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedImage(BaseModel):
    """Extracted image with metadata."""
    url: str = Field(..., description="Image URL")
    alt_text: Optional[str] = Field(None, description="Alt text description")
    title: Optional[str] = Field(None, description="Image title")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    relevance_score: Optional[float] = Field(None, description="AI-determined relevance score for recipe")
    is_primary: bool = Field(False, description="Whether this is the primary recipe image")


class ExtractedIngredient(BaseModel):
    """Extracted ingredient with standardized structure."""
    name: str = Field(..., description="Name of the ingredient")
    amount: str = Field(..., description="Amount/quantity of the ingredient")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class ExtractedRecipe(BaseModel):
    """PyGlove-style model for extracted recipe data."""
    title: str = Field(..., description="Recipe title in English")
    description: Optional[str] = Field(None, description="Recipe description in English")
    ingredients: List[ExtractedIngredient] = Field(default_factory=list, description="List of ingredients")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step cooking instructions in English")
    prep_time: Optional[int] = Field(None, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(None, description="Cooking time in minutes")
    servings: Optional[int] = Field(None, description="Number of servings")
    difficulty: Optional[str] = Field(None, description="Difficulty level: easy, medium, or hard")
    tags: List[str] = Field(default_factory=list, description="Recipe tags/categories")
    source_url: Optional[str] = Field(None, description="Original URL of the recipe")
    images: List[ExtractedImage] = Field(default_factory=list, description="Recipe images")
    
    class Config:
        """Pydantic configuration."""
        str_strip_whitespace = True
        extra = "forbid"


class RecipeExtractionResult(BaseModel):
    """Result of recipe extraction with success/failure information."""
    success: bool = Field(..., description="Whether extraction was successful")
    recipe: Optional[ExtractedRecipe] = Field(None, description="Extracted recipe data")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    source_url: str = Field(..., description="URL that was processed")
    extraction_metadata: dict = Field(default_factory=dict, description="Additional metadata about extraction")