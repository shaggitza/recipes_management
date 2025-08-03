"""Simplified langfun models for structured recipe data extraction."""

from typing import List, Optional, Literal
import pyglove as pg


class Ingredient(pg.Object):
    """Recipe ingredient with standardized structure."""

    name: str
    amount: str | None = None
    unit: Optional[str] = None


class ExtractedImage(pg.Object):
    """Extracted image with metadata."""

    url: str
    alt_text: Optional[str] = None
    title: Optional[str] = None
    relevance_score: Optional[float] = None
    is_primary: bool = False


class GasBurnerSettings(pg.Object):
    """Settings for gas burner appliance."""
    
    flame_level: Literal["low", "medium", "high", "simmer"] = "medium"
    burner_size: Optional[Literal["small", "medium", "large"]] = None
    utensils: List[str] = []
    notes: Optional[str] = None


class ElectricStoveSettings(pg.Object):
    """Settings for electric stovetop appliance."""
    
    heat_level: int = 5  # 1-10 scale
    utensils: List[str] = []
    notes: Optional[str] = None


class InductionStoveSettings(pg.Object):
    """Settings for induction stovetop appliance."""
    
    temperature: Optional[int] = None  # degrees
    power_level: Optional[int] = None  # 1-10 scale
    utensils: List[str] = []
    notes: Optional[str] = None


class AirfryerSettings(pg.Object):
    """Settings for airfryer appliance."""
    
    temperature: int = 350  # degrees Fahrenheit
    time_minutes: Optional[int] = None
    preheat: bool = True
    shake_interval: Optional[int] = None  # minutes
    utensils: List[str] = []
    notes: Optional[str] = None


class ElectricGrillSettings(pg.Object):
    """Settings for electric grill appliance."""
    
    temperature: int = 400  # degrees Fahrenheit
    preheat_time: Optional[int] = None  # minutes
    utensils: List[str] = []
    notes: Optional[str] = None


class OvenSettings(pg.Object):
    """Settings for kitchen oven appliance."""
    
    temperature: int = 350  # degrees Fahrenheit
    cooking_mode: Literal["bake", "broil", "convection", "roast"] = "bake"
    rack_position: Optional[Literal["top", "middle", "bottom"]] = "middle"
    preheat: bool = True
    utensils: List[str] = []
    notes: Optional[str] = None


class CharcoalGrillSettings(pg.Object):
    """Settings for charcoal grill appliance."""
    
    charcoal_amount: Literal["light", "medium", "heavy"] = "medium"
    heat_zone: Literal["direct", "indirect", "mixed"] = "direct"
    cooking_time: Optional[int] = None  # minutes
    utensils: List[str] = []
    notes: Optional[str] = None


class ElectricBasicSettings(pg.Object):
    """Settings for basic electric appliances (no temperature control)."""
    
    power_setting: Literal["low", "medium", "high"] = "medium"
    utensils: List[str] = []
    notes: Optional[str] = None


# Using pg.oneof for union types as required for pyglove
class ApplianceSettings(pg.Object):
    """Appliance-specific cooking settings."""
    
    appliance_type: Literal[
        "gas_burner", "electric_stove", "induction_stove", "airfryer", 
        "electric_grill", "oven", "charcoal_grill", "electric_basic"
    ]
    # For pyglove, we'll use a simpler approach with optional fields
    gas_burner: Optional[GasBurnerSettings] = None
    electric_stove: Optional[ElectricStoveSettings] = None
    induction_stove: Optional[InductionStoveSettings] = None
    airfryer: Optional[AirfryerSettings] = None
    electric_grill: Optional[ElectricGrillSettings] = None
    oven: Optional[OvenSettings] = None
    charcoal_grill: Optional[CharcoalGrillSettings] = None
    electric_basic: Optional[ElectricBasicSettings] = None


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
    meal_times: List[
        Literal["breakfast", "lunch", "dinner", "snack", "brunch", "dessert"]
    ] = []
    images: List[ExtractedImage] = []
    source_url: Optional[str] = None
    appliance_settings: List[ApplianceSettings] = []


# Alias for compatibility with tests
ExtractedRecipe = RecipeExtraction
