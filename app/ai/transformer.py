"""Data transformation module to convert AI-extracted data to Recipe models."""

import logging
from typing import Optional, Literal
from datetime import datetime, timezone

from app.models.recipe import (
    RecipeCreate, Ingredient, Source, MealTime, ApplianceSettings,
    GasBurnerSettings, ElectricStoveSettings, InductionStoveSettings,
    AirfryerSettings, ElectricGrillSettings, OvenSettings,
    CharcoalGrillSettings, ElectricBasicSettings
)

logger = logging.getLogger(__name__)


class RecipeTransformer:
    """Transforms AI-extracted recipe data to application Recipe models."""
    
    def __init__(self):
        """Initialize the transformer."""
        pass

    def transform_to_recipe_create(self, extracted_recipe) -> RecipeCreate:
        """
        Transform extracted recipe data to RecipeCreate model.

        Args:
            extracted_recipe: AI-extracted recipe data (dict or RecipeExtraction object)

        Returns:
            RecipeCreate model ready for database insertion
        """
        try:
            # Convert dict to object-like access if needed
            if isinstance(extracted_recipe, dict):
                recipe_data = extracted_recipe
            else:
                # Assume it's a RecipeExtraction object
                recipe_data = {
                    "title": extracted_recipe.title,
                    "description": extracted_recipe.description,
                    "ingredients": extracted_recipe.ingredients,
                    "instructions": extracted_recipe.instructions,
                    "prep_time": extracted_recipe.prep_time,
                    "cook_time": extracted_recipe.cook_time,
                    "servings": extracted_recipe.servings,
                    "difficulty": extracted_recipe.difficulty,
                    "tags": extracted_recipe.tags,
                    "meal_times": extracted_recipe.meal_times,
                    "source_url": getattr(extracted_recipe, "source_url", None),
                    "appliance_settings": getattr(extracted_recipe, "appliance_settings", []),
                }

            logger.info(f"Transforming extracted recipe: {recipe_data['title']}")
            
            # Transform ingredients
            ingredients = self._transform_ingredients(recipe_data["ingredients"])
            
            # Transform instructions
            instructions = self._transform_instructions(recipe_data["instructions"])
            
            # Create source information
            source = Source(
                type="website",
                url=recipe_data.get("source_url"),
                name=self._extract_domain_name(recipe_data.get("source_url")),
            )
            
            # Transform difficulty
            difficulty = self._normalize_difficulty(recipe_data.get("difficulty"))
            
            # Transform appliance settings
            appliance_settings = self._transform_appliance_settings(recipe_data.get("appliance_settings", []))
            
            # Create the RecipeCreate object
            recipe_create = RecipeCreate(
                title=self._clean_title(recipe_data["title"]),
                description=self._clean_description(recipe_data.get("description")),
                ingredients=ingredients,
                instructions=instructions,
                prep_time=recipe_data.get("prep_time"),
                cook_time=recipe_data.get("cook_time"),
                servings=recipe_data.get("servings"),
                difficulty=difficulty,
                tags=self._clean_tags(recipe_data.get("tags", [])),
                meal_times=self._clean_meal_times(recipe_data.get("meal_times", [])),
                source=source,
                images=[],  # No images extracted yet
                appliance_settings=appliance_settings,
                metadata={
                    "ai_extracted": True,
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    "original_source": recipe_data.get("source_url"),
                },
            )
            
            logger.info(f"Successfully transformed recipe: {recipe_create.title}")
            return recipe_create
            
        except Exception as e:
            logger.error(f"Error transforming recipe: {e}")
            raise ValueError(f"Failed to transform extracted recipe: {str(e)}")

    def _transform_ingredients(self, extracted_ingredients) -> list[Ingredient]:
        """Transform extracted ingredients to Ingredient models."""
        ingredients = []

        for ext_ingredient in extracted_ingredients or []:
            try:
                # Handle both dict and object formats
                if isinstance(ext_ingredient, dict):
                    name = ext_ingredient.get("name", "")
                    amount = ext_ingredient.get("amount", "")
                    unit = ext_ingredient.get("unit")
                else:
                    # Assume it's an ExtractedIngredient object
                    name = ext_ingredient.name
                    amount = ext_ingredient.amount
                    unit = ext_ingredient.unit

                ingredient = Ingredient(
                    name=self._clean_ingredient_name(name),
                    amount=self._clean_amount(amount),
                    unit=self._clean_unit(unit),
                )
                ingredients.append(ingredient)
            except Exception as e:
                ingredient_name = (
                    ext_ingredient.get("name", "unknown")
                    if isinstance(ext_ingredient, dict)
                    else getattr(ext_ingredient, "name", "unknown")
                )
                logger.warning(f"Skipping invalid ingredient {ingredient_name}: {e}")
                continue
        
        return ingredients

    def _transform_instructions(self, extracted_instructions: list[str]) -> list[str]:
        """Transform and clean extracted instructions."""
        instructions = []
        
        for i, instruction in enumerate(extracted_instructions):
            cleaned = self._clean_instruction(instruction)
            if cleaned:
                # Add step numbers if not present
                if not cleaned.strip().startswith(str(i + 1)):
                    cleaned = f"{i + 1}. {cleaned}"
                instructions.append(cleaned)
        
        return instructions

    def _clean_title(self, title: str) -> str:
        """Clean and validate recipe title."""
        if not title:
            raise ValueError("Recipe title is required")
        
        # Remove common prefixes
        title = title.replace("TITLE:", "").replace("HEADING:", "").strip()
        
        # Limit length and clean up
        title = title[:200].strip()
        
        if not title:
            raise ValueError("Recipe title cannot be empty after cleaning")
        
        return title

    def _clean_description(self, description: Optional[str]) -> Optional[str]:
        """Clean and validate recipe description."""
        if not description:
            return None
        
        # Clean up and limit length
        description = description.strip()[:1000]
        
        return description if description else None

    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name."""
        if not name:
            raise ValueError("Ingredient name is required")
        
        # Remove prefixes and clean up
        name = name.replace("ITEM:", "").strip()
        name = name[:100]  # Limit length
        
        if not name:
            raise ValueError("Ingredient name cannot be empty")
        
        return name

    def _clean_amount(self, amount: str) -> str:
        """Clean ingredient amount."""
        if not amount:
            return "1"  # Default amount
        
        # Clean up and limit length
        amount = amount.strip()[:50]
        
        return amount if amount else "1"

    def _clean_unit(self, unit: Optional[str]) -> Optional[str]:
        """Clean ingredient unit."""
        if not unit:
            return None
        
        unit = unit.strip()[:50]
        
        # Map common unit variations
        unit_mappings = {
            "cups": "cup",
            "tablespoons": "tbsp",
            "teaspoons": "tsp",
            "pounds": "lb",
            "ounces": "oz",
            "grams": "g",
            "kilograms": "kg",
            "liters": "l",
            "milliliters": "ml",
        }
        
        unit_lower = unit.lower()
        if unit_lower in unit_mappings:
            return unit_mappings[unit_lower]
        
        return unit if unit else None

    def _clean_instruction(self, instruction: str) -> Optional[str]:
        """Clean individual instruction."""
        if not instruction:
            return None
        
        # Remove prefixes
        instruction = instruction.replace("ITEM:", "").strip()
        
        # Remove step numbers at the beginning (we'll add them back)
        instruction = instruction.lstrip("0123456789. ")
        
        if len(instruction) < 5:  # Too short to be meaningful
            return None
        
        return instruction

    def _normalize_difficulty(
        self, difficulty: Optional[str]
    ) -> Optional[Literal["easy", "medium", "hard"]]:
        """Normalize difficulty to valid values."""
        if not difficulty:
            return None
        
        difficulty_lower = difficulty.lower().strip()
        
        if difficulty_lower in ["easy", "simple", "quick"]:
            return "easy"
        elif difficulty_lower in ["medium", "moderate", "intermediate"]:
            return "medium"
        elif difficulty_lower in ["hard", "difficult", "advanced", "complex"]:
            return "hard"
        
        return None

    def _clean_tags(self, tags: list[str]) -> list[str]:
        """Clean and validate tags."""
        cleaned_tags = []
        
        for tag in tags:
            if tag:
                tag = tag.strip().lower()
                if tag and len(tag) > 1 and len(tag) <= 50:
                    cleaned_tags.append(tag)
        
        # Remove duplicates and limit count
        unique_tags = list(dict.fromkeys(cleaned_tags))  # Preserve order
        return unique_tags[:20]  # Limit to 20 tags

    def _clean_meal_times(self, meal_times: list) -> list[MealTime]:
        """Clean and validate meal_times."""
        cleaned_meal_times = []
        
        for meal_time in meal_times:
            if meal_time:
                # Handle both string and MealTime enum inputs
                if isinstance(meal_time, MealTime):
                    meal_time_str = meal_time.value
                else:
                    meal_time_str = str(meal_time).strip().lower()
                
                # Try to convert to MealTime enum
                try:
                    enum_value = MealTime(meal_time_str)
                    cleaned_meal_times.append(enum_value)
                except ValueError:
                    # Skip invalid meal times
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_meal_times = []
        for meal_time in cleaned_meal_times:
            if meal_time not in seen:
                seen.add(meal_time)
                unique_meal_times.append(meal_time)
        
        return unique_meal_times[:6]  # Limit to 6 meal times

    def _transform_appliance_settings(self, extracted_appliance_settings: list) -> list[ApplianceSettings]:
        """Transform AI-extracted appliance settings to Pydantic ApplianceSettings."""
        appliance_settings = []
        
        for ext_appliance in extracted_appliance_settings or []:
            try:
                # Handle both dict and object formats
                if isinstance(ext_appliance, dict):
                    appliance_type = ext_appliance.get("appliance_type")
                    settings_data = ext_appliance
                else:
                    # PyGlove object format
                    appliance_type = ext_appliance.appliance_type
                    settings_data = ext_appliance
                
                if not appliance_type:
                    continue
                    
                # Transform settings based on appliance type
                settings = self._create_appliance_settings(appliance_type, settings_data)
                if settings:
                    appliance_settings.append(ApplianceSettings(
                        appliance_type=appliance_type,
                        settings=settings
                    ))
                    
            except Exception as e:
                logger.warning(f"Skipping invalid appliance setting: {e}")
                continue
        
        return appliance_settings

    def _create_appliance_settings(self, appliance_type: str, settings_data):
        """Create specific appliance settings based on type."""
        try:
            # Extract common fields
            utensils = self._extract_utensils(settings_data)
            notes = self._extract_notes(settings_data)
            
            if appliance_type == "gas_burner":
                return GasBurnerSettings(
                    flame_level=self._extract_field(settings_data, "flame_level", "medium"),
                    burner_size=self._extract_field(settings_data, "burner_size", None),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "electric_stove":
                return ElectricStoveSettings(
                    heat_level=self._extract_field(settings_data, "heat_level", 5),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "induction_stove":
                return InductionStoveSettings(
                    temperature=self._extract_field(settings_data, "temperature", None),
                    power_level=self._extract_field(settings_data, "power_level", None),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "airfryer":
                return AirfryerSettings(
                    temperature=self._extract_field(settings_data, "temperature", 350),
                    time_minutes=self._extract_field(settings_data, "time_minutes", None),
                    preheat=self._extract_field(settings_data, "preheat", True),
                    shake_interval=self._extract_field(settings_data, "shake_interval", None),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "electric_grill":
                return ElectricGrillSettings(
                    temperature=self._extract_field(settings_data, "temperature", 400),
                    preheat_time=self._extract_field(settings_data, "preheat_time", None),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "oven":
                return OvenSettings(
                    temperature=self._extract_field(settings_data, "temperature", 350),
                    cooking_mode=self._extract_field(settings_data, "cooking_mode", "bake"),
                    rack_position=self._extract_field(settings_data, "rack_position", "middle"),
                    preheat=self._extract_field(settings_data, "preheat", True),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "charcoal_grill":
                return CharcoalGrillSettings(
                    charcoal_amount=self._extract_field(settings_data, "charcoal_amount", "medium"),
                    heat_zone=self._extract_field(settings_data, "heat_zone", "direct"),
                    cooking_time=self._extract_field(settings_data, "cooking_time", None),
                    utensils=utensils,
                    notes=notes
                )
            elif appliance_type == "electric_basic":
                return ElectricBasicSettings(
                    power_setting=self._extract_field(settings_data, "power_setting", "medium"),
                    utensils=utensils,
                    notes=notes
                )
            else:
                logger.warning(f"Unknown appliance type: {appliance_type}")
                return None
                
        except Exception as e:
            logger.warning(f"Error creating {appliance_type} settings: {e}")
            return None

    def _extract_field(self, settings_data, field_name: str, default_value=None):
        """Extract field from settings data (dict or object)."""
        if isinstance(settings_data, dict):
            return settings_data.get(field_name, default_value)
        else:
            # PyGlove object with nested appliance-specific settings
            # Try to get from the specific appliance object first
            appliance_obj = getattr(settings_data, settings_data.appliance_type, None)
            if appliance_obj:
                return getattr(appliance_obj, field_name, default_value)
            # Fallback to direct attribute
            return getattr(settings_data, field_name, default_value)

    def _extract_utensils(self, settings_data) -> list[str]:
        """Extract utensils list from settings data."""
        utensils = self._extract_field(settings_data, "utensils", [])
        if isinstance(utensils, str):
            # If it's a string, split by commas
            return [u.strip() for u in utensils.split(",") if u.strip()]
        elif isinstance(utensils, list):
            return [str(u).strip() for u in utensils if str(u).strip()]
        return []

    def _extract_notes(self, settings_data) -> Optional[str]:
        """Extract notes from settings data."""
        notes = self._extract_field(settings_data, "notes", None)
        if notes and isinstance(notes, str):
            notes = notes.strip()
            return notes if notes else None
        return None

    def _extract_domain_name(self, url: Optional[str]) -> Optional[str]:
        """Extract domain name from URL for source name."""
        if not url:
            return None
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]
            
            return domain[:200]  # Limit length
            
        except Exception:
            return None

    def validate_recipe_create(self, recipe_create: RecipeCreate) -> bool:
        """
        Validate that the RecipeCreate object is valid.
        
        Args:
            recipe_create: RecipeCreate object to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not recipe_create.title or len(recipe_create.title.strip()) == 0:
                logger.error("Recipe title is required")
                return False
            
            # Validate ingredient names are not empty
            for ingredient in recipe_create.ingredients:
                if not ingredient.name or len(ingredient.name.strip()) == 0:
                    logger.error(f"Ingredient name cannot be empty: {ingredient}")
                    return False
            
            # Validate at least one instruction
            if not recipe_create.instructions or len(recipe_create.instructions) == 0:
                logger.warning("Recipe has no instructions")
            
            # Validate numeric fields
            if recipe_create.prep_time is not None and recipe_create.prep_time < 0:
                logger.error("Prep time cannot be negative")
                return False
            
            if recipe_create.cook_time is not None and recipe_create.cook_time < 0:
                logger.error("Cook time cannot be negative")
                return False
            
            if recipe_create.servings is not None and recipe_create.servings <= 0:
                logger.error("Servings must be positive")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False