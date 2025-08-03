"""Simplified langfun models for structured recipe data extraction."""

from typing import List, Optional, Literal, Union
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
    is_primary: bool  # Remove default - let AI decide


class Utensil(pg.Object):
    """Utensil information for appliances that require specific cookware."""
    
    type: str  # e.g., "pan", "tray", "pot"
    size: Optional[str] = None  # e.g., "12-inch", "large", "medium"
    material: Optional[str] = None  # e.g., "non-stick", "cast iron", "stainless steel"
    notes: Optional[str] = None  # additional notes


class GasBurnerSettings(pg.Object):
    """Settings for gas burner cooking."""
    
    appliance_type: Literal["gas_burner"] = "gas_burner"
    flame_level: str  # e.g., "high", "medium-high", "medium", "low", "simmer"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class AirfryerSettings(pg.Object):
    """Settings for airfryer cooking."""
    
    appliance_type: Literal["airfryer"] = "airfryer"
    temperature_celsius: int
    duration_minutes: int
    preheat_required: bool  # Remove default - let AI decide
    shake_interval_minutes: Optional[int] = None
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class ElectricGrillSettings(pg.Object):
    """Settings for electric grill with temperature control."""
    
    appliance_type: Literal["electric_grill"] = "electric_grill"
    temperature_celsius: int
    duration_minutes: Optional[int] = None
    preheat_required: bool  # Remove default - let AI decide
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class ElectricStoveSettings(pg.Object):
    """Settings for electric stove without temperature control."""
    
    appliance_type: Literal["electric_stove"] = "electric_stove"
    heat_level: str  # e.g., "high", "medium-high", "medium", "low"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class InductionStoveSettings(pg.Object):
    """Settings for electric induction stove."""
    
    appliance_type: Literal["induction_stove"] = "induction_stove"
    power_level: int  # induction typically has power levels 1-10
    temperature_celsius: Optional[int] = None
    duration_minutes: Optional[int] = None
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class OvenSettings(pg.Object):
    """Settings for kitchen oven."""
    
    appliance_type: Literal["oven"] = "oven"
    temperature_celsius: int
    duration_minutes: int
    preheat_required: bool  # Remove default - let AI decide
    rack_position: Optional[str] = None  # e.g., "middle", "top", "bottom"
    convection: bool  # Remove default - let AI decide
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class CharcoalGrillSettings(pg.Object):
    """Settings for charcoal grill."""
    
    appliance_type: Literal["charcoal_grill"] = "charcoal_grill"
    heat_zone: str  # e.g., "direct high", "indirect medium", "low and slow"
    duration_minutes: Optional[int] = None
    lid_position: Optional[str] = None  # e.g., "open", "closed", "vented"
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class GeneralStoveSettings(pg.Object):
    """Settings for general stove (when specific type not known)."""
    
    appliance_type: Literal["stove"] = "stove"
    heat_level: str  # e.g., "high", "medium", "low"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil]  # Remove default - let AI populate
    notes: Optional[str] = None


class RecipeExtraction(pg.Object):
    """Simplified recipe extraction model using pyglove."""

    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient]  # Remove default - let AI populate
    instructions: List[str]  # Remove default - let AI populate
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str]  # Remove default - let AI populate
    meal_times: List[
        Literal["breakfast", "lunch", "dinner", "snack", "brunch", "dessert"]
    ]  # Remove default - let AI populate
    images: List[ExtractedImage]  # Remove default - let AI populate
    source_url: Optional[str] = None
    # Properly typed appliance settings list with Union types for langfun
    appliance_settings: List[Union[
        GasBurnerSettings,
        AirfryerSettings,
        ElectricGrillSettings,
        ElectricStoveSettings,
        InductionStoveSettings,
        OvenSettings,
        CharcoalGrillSettings,
        GeneralStoveSettings
    ]]  # Remove default - let AI populate with proper type information


# Helper function to create appliance settings choice for PyGlove
def create_appliance_settings_choice():
    """Create a PyGlove oneof choice for appliance settings."""
    return pg.oneof([
        GasBurnerSettings,
        AirfryerSettings,
        ElectricGrillSettings,
        ElectricStoveSettings,
        InductionStoveSettings,
        OvenSettings,
        CharcoalGrillSettings,
        GeneralStoveSettings
    ])


# Export all appliance setting types for easy access
__all__ = [
    'Ingredient', 'ExtractedImage', 'RecipeExtraction', 'ExtractedRecipe',
    'Utensil', 'GasBurnerSettings', 'AirfryerSettings', 'ElectricGrillSettings',
    'ElectricStoveSettings', 'InductionStoveSettings', 'OvenSettings',
    'CharcoalGrillSettings', 'GeneralStoveSettings', 'create_appliance_settings_choice'
]


# Alias for compatibility with tests
ExtractedRecipe = RecipeExtraction
