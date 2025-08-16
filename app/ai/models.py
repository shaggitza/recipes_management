"""Pydantic models for structured recipe data extraction."""

from typing import List, Optional, Literal, Union
from pydantic import BaseModel


class Ingredient(BaseModel):
    """Recipe ingredient with standardized structure."""

    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None


class ExtractedImage(BaseModel):
    """Simplified extracted image - kept for compatibility but not used."""

    url: str
    alt_text: Optional[str] = None
    title: Optional[str] = None
    relevance_score: Optional[float] = None
    is_primary: bool = False  # Default to False since not used


class Utensil(BaseModel):
    """Utensil information for appliances that require specific cookware."""
    
    type: str  # e.g., "pan", "tray", "pot"
    size: Optional[str] = None  # e.g., "12-inch", "large", "medium"
    material: Optional[str] = None  # e.g., "non-stick", "cast iron", "stainless steel"
    notes: Optional[str] = None  # additional notes


class GasBurnerSettings(BaseModel):
    """Settings for gas burner cooking."""
    
    appliance_type: Literal["gas_burner"] = "gas_burner"
    flame_level: str  # e.g., "high", "medium-high", "medium", "low", "simmer"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class AirfryerSettings(BaseModel):
    """Settings for airfryer cooking."""
    
    appliance_type: Literal["airfryer"] = "airfryer"
    temperature_celsius: int
    duration_minutes: int
    preheat_required: bool = True  # Default to True
    shake_interval_minutes: Optional[int] = None
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class ElectricGrillSettings(BaseModel):
    """Settings for electric grill with temperature control."""
    
    appliance_type: Literal["electric_grill"] = "electric_grill"
    temperature_celsius: int
    duration_minutes: Optional[int] = None
    preheat_required: bool = True  # Default to True
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class ElectricStoveSettings(BaseModel):
    """Settings for electric stove without temperature control."""
    
    appliance_type: Literal["electric_stove"] = "electric_stove"
    heat_level: str  # e.g., "high", "medium-high", "medium", "low"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class InductionStoveSettings(BaseModel):
    """Settings for electric induction stove."""
    
    appliance_type: Literal["induction_stove"] = "induction_stove"
    power_level: int  # induction typically has power levels 1-10
    temperature_celsius: Optional[int] = None
    duration_minutes: Optional[int] = None
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class OvenSettings(BaseModel):
    """Settings for kitchen oven."""
    
    appliance_type: Literal["oven"] = "oven"
    temperature_celsius: int
    duration_minutes: int
    preheat_required: bool = True  # Default to True
    rack_position: Optional[str] = None  # e.g., "middle", "top", "bottom"
    convection: bool = False  # Default to False
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class CharcoalGrillSettings(BaseModel):
    """Settings for charcoal grill."""
    
    appliance_type: Literal["charcoal_grill"] = "charcoal_grill"
    heat_zone: str  # e.g., "direct high", "indirect medium", "low and slow"
    duration_minutes: Optional[int] = None
    lid_position: Optional[str] = None  # e.g., "open", "closed", "vented"
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class GeneralStoveSettings(BaseModel):
    """Settings for general stove (when specific type not known)."""
    
    appliance_type: Literal["stove"] = "stove"
    heat_level: str  # e.g., "high", "medium", "low"
    duration_minutes: Optional[int] = None
    utensils: List[Utensil] = []  # Default to empty list
    notes: Optional[str] = None


class RecipeExtraction(BaseModel):
    """Recipe extraction model using Pydantic for better ScrapeGraphAI integration."""

    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient] = []  # Default to empty list
    instructions: List[str] = []  # Default to empty list
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str] = []  # Default to empty list
    meal_times: List[
        Literal["breakfast", "lunch", "dinner", "snack", "brunch", "dessert"]
    ] = []  # Default to empty list
    images: List[ExtractedImage] = []  # Always empty in simplified version
    source_url: Optional[str] = None
    # Appliance settings using Union for ScrapeGraphAI compatibility
    appliance_settings: List[Union[
        GasBurnerSettings,
        AirfryerSettings,
        ElectricGrillSettings,
        ElectricStoveSettings,
        InductionStoveSettings,
        OvenSettings,
        CharcoalGrillSettings,
        GeneralStoveSettings
    ]] = []  # Default to empty list


# Export all appliance setting types for easy access
__all__ = [
    'Ingredient', 'ExtractedImage', 'RecipeExtraction', 'ExtractedRecipe',
    'Utensil', 'GasBurnerSettings', 'AirfryerSettings', 'ElectricGrillSettings',
    'ElectricStoveSettings', 'InductionStoveSettings', 'OvenSettings',
    'CharcoalGrillSettings', 'GeneralStoveSettings'
]


# Alias for compatibility with tests
ExtractedRecipe = RecipeExtraction
