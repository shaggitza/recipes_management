from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from beanie import Document, before_event, Insert, Update
from pymongo import IndexModel, TEXT


class MealTime(str, Enum):
    """Enumeration of valid meal times."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch" 
    DINNER = "dinner"
    SNACK = "snack"
    BRUNCH = "brunch"
    DESSERT = "dessert"


class Ingredient(BaseModel):
    """Recipe ingredient with amount and optional unit"""
    name: str = Field(..., min_length=1, max_length=100)
    amount: str = Field(..., min_length=1, max_length=50)
    unit: Optional[str] = Field(None, max_length=50)


class Source(BaseModel):
    """Recipe source information supporting various platforms"""
    type: Literal["manual", "tiktok", "website", "book", "magazine", "other"] = "manual"
    url: Optional[str] = Field(None, max_length=500)
    name: Optional[str] = Field(None, max_length=200)


class Recipe(Document):
    """Recipe document with full type safety and proper Beanie patterns"""
    
    # Core recipe information
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    
    # Timing and serving information
    prep_time: Optional[int] = Field(None, ge=0, le=1440)  # max 24 hours in minutes
    cook_time: Optional[int] = Field(None, ge=0, le=1440)  # max 24 hours in minutes
    servings: Optional[int] = Field(None, ge=1, le=100)
    
    # Classification
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: List[str] = Field(default_factory=list, max_length=20)
    meal_times: List[MealTime] = Field(default_factory=list, max_length=6)
    
    # Source and media
    source: Source = Field(default_factory=lambda: Source(type="manual"))
    images: List[str] = Field(default_factory=list, max_length=10)
    
    # Timestamps - automatically managed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Extensibility
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('meal_times')
    @classmethod
    def validate_meal_times(cls, v: List[MealTime]) -> List[MealTime]:
        """Validate and normalize meal times"""
        if not v:
            return []
        # Remove duplicates while preserving order
        seen = set()
        unique_meal_times = []
        for meal_time in v:
            if meal_time not in seen:
                seen.add(meal_time)
                unique_meal_times.append(meal_time)
        if len(unique_meal_times) > 6:
            raise ValueError('Maximum 6 meal times allowed')
        return unique_meal_times

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags"""
        if not v:
            return []
        # Remove duplicates, normalize to lowercase, strip whitespace
        normalized = list(set(tag.strip().lower() for tag in v if tag.strip()))
        if len(normalized) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return normalized

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v: List[str]) -> List[str]:
        """Validate instructions are not empty"""
        return [instruction.strip() for instruction in v if instruction.strip()]

    @before_event([Insert, Update])
    async def update_timestamp(self):
        """Automatically update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)

    @property
    def total_time(self) -> Optional[int]:
        """Calculate total time (prep + cook)"""
        if self.prep_time is not None and self.cook_time is not None:
            return self.prep_time + self.cook_time
        return None

    class Settings:
        name = "recipes"
        # Proper MongoDB indexes for efficient querying
        indexes = [
            # Text search index
            IndexModel([("title", TEXT), ("description", TEXT), ("ingredients.name", TEXT)]),
            # Individual field indexes
            IndexModel([("tags", 1)]),
            IndexModel([("difficulty", 1)]),
            IndexModel([("created_at", -1)]),
            # Compound indexes for common queries
            IndexModel([("difficulty", 1), ("tags", 1)]),
            IndexModel([("created_at", -1), ("difficulty", 1)]),
            IndexModel([("meal_times", 1)]),
            IndexModel([("difficulty", 1), ("meal_times", 1)]),
        ]


class RecipeCreate(BaseModel):
    """Model for creating new recipes"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    prep_time: Optional[int] = Field(None, ge=0, le=1440)
    cook_time: Optional[int] = Field(None, ge=0, le=1440)
    servings: Optional[int] = Field(None, ge=1, le=100)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: List[str] = Field(default_factory=list, max_length=20)
    meal_times: List[MealTime] = Field(default_factory=list, max_length=6)
    source: Source = Field(default_factory=Source)
    images: List[str] = Field(default_factory=list, max_length=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('meal_times')
    @classmethod
    def validate_meal_times(cls, v: List[MealTime]) -> List[MealTime]:
        """Validate and normalize meal times"""
        if not v:
            return []
        # Remove duplicates while preserving order
        seen = set()
        unique_meal_times = []
        for meal_time in v:
            if meal_time not in seen:
                seen.add(meal_time)
                unique_meal_times.append(meal_time)
        if len(unique_meal_times) > 6:
            raise ValueError('Maximum 6 meal times allowed')
        return unique_meal_times

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags"""
        if not v:
            return []
        normalized = list(set(tag.strip().lower() for tag in v if tag.strip()))
        if len(normalized) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return normalized


class RecipeUpdate(BaseModel):
    """Model for updating existing recipes - all fields optional"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[int] = Field(None, ge=0, le=1440)
    cook_time: Optional[int] = Field(None, ge=0, le=1440)
    servings: Optional[int] = Field(None, ge=1, le=100)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: Optional[List[str]] = Field(None, max_length=20)
    meal_times: Optional[List[MealTime]] = Field(None, max_length=6)
    source: Optional[Source] = None
    images: Optional[List[str]] = Field(None, max_length=10)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('meal_times')
    @classmethod
    def validate_meal_times(cls, v: Optional[List[MealTime]]) -> Optional[List[MealTime]]:
        """Validate and normalize meal times"""
        if v is None:
            return None
        if not v:
            return []
        # Remove duplicates while preserving order
        seen = set()
        unique_meal_times = []
        for meal_time in v:
            if meal_time not in seen:
                seen.add(meal_time)
                unique_meal_times.append(meal_time)
        if len(unique_meal_times) > 6:
            raise ValueError('Maximum 6 meal times allowed')
        return unique_meal_times

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize tags"""
        if v is None:
            return None
        if not v:
            return []
        normalized = list(set(tag.strip().lower() for tag in v if tag.strip()))
        if len(normalized) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return normalized


class RecipeResponse(BaseModel):
    """Response model with proper ID serialization"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meal_times: List[str] = Field(default_factory=list)
    source: Source = Field(default_factory=lambda: Source(type="manual"))
    images: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_recipe(cls, recipe: "Recipe") -> "RecipeResponse":
        """Create RecipeResponse from Recipe document with proper ID conversion"""
        recipe_data = recipe.model_dump()
        recipe_data["id"] = str(recipe.id)
        return cls(**recipe_data)
    
    @property
    def total_time(self) -> Optional[int]:
        """Calculate total time (prep + cook)"""
        if self.prep_time is not None and self.cook_time is not None:
            return self.prep_time + self.cook_time
        return None