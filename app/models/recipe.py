from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from beanie import Document
from pymongo import IndexModel, TEXT

class Ingredient(BaseModel):
    name: str
    amount: str
    unit: Optional[str] = None

class Source(BaseModel):
    type: str = "manual"  # tiktok, website, book, manual, etc.
    url: Optional[str] = None
    name: Optional[str] = None

class Recipe(Document):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    prep_time: Optional[int] = Field(None, ge=0)  # minutes
    cook_time: Optional[int] = Field(None, ge=0)  # minutes
    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: List[str] = Field(default_factory=list)
    source: Source = Field(default_factory=Source)
    images: List[str] = Field(default_factory=list)  # URLs or paths
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # for future extensibility

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['easy', 'medium', 'hard']:
            raise ValueError('difficulty must be easy, medium, or hard')
        return v

    class Settings:
        name = "recipes"
        indexes = [
            IndexModel([("title", TEXT), ("description", TEXT), ("ingredients.name", TEXT)]),
            IndexModel([("tags", 1)]),
            IndexModel([("difficulty", 1)]),
            IndexModel([("created_at", -1)]),
        ]

class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: List[str] = Field(default_factory=list)
    source: Source = Field(default_factory=Source)
    images: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['easy', 'medium', 'hard']:
            raise ValueError('difficulty must be easy, medium, or hard')
        return v

class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[int] = Field(None, ge=0)
    cook_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    tags: Optional[List[str]] = None
    source: Optional[Source] = None
    images: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['easy', 'medium', 'hard']:
            raise ValueError('difficulty must be easy, medium, or hard')
        return v

# Response model that includes the ID from Beanie
class RecipeResponse(BaseModel):
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
    source: Source = Field(default_factory=Source)
    images: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)