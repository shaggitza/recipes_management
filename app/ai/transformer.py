"""Data transformation module to convert AI-extracted data to Recipe models."""

import logging
from typing import Optional
from datetime import datetime, timezone

from app.models.recipe import RecipeCreate, Ingredient, Source
from .models import ExtractedRecipe, ExtractedIngredient

logger = logging.getLogger(__name__)


class RecipeTransformer:
    """Transforms AI-extracted recipe data to application Recipe models."""
    
    def __init__(self):
        """Initialize the transformer."""
        pass

    def transform_to_recipe_create(self, extracted_recipe: ExtractedRecipe) -> RecipeCreate:
        """
        Transform ExtractedRecipe to RecipeCreate model.
        
        Args:
            extracted_recipe: AI-extracted recipe data
            
        Returns:
            RecipeCreate model ready for database insertion
        """
        try:
            logger.info(f"Transforming extracted recipe: {extracted_recipe.title}")
            
            # Transform ingredients
            ingredients = self._transform_ingredients(extracted_recipe.ingredients)
            
            # Transform instructions
            instructions = self._transform_instructions(extracted_recipe.instructions)
            
            # Create source information
            source = Source(
                type="website",
                url=extracted_recipe.source_url,
                name=self._extract_domain_name(extracted_recipe.source_url)
            )
            
            # Transform difficulty
            difficulty = self._normalize_difficulty(extracted_recipe.difficulty)
            
            # Create the RecipeCreate object
            recipe_create = RecipeCreate(
                title=self._clean_title(extracted_recipe.title),
                description=self._clean_description(extracted_recipe.description),
                ingredients=ingredients,
                instructions=instructions,
                prep_time=extracted_recipe.prep_time,
                cook_time=extracted_recipe.cook_time,
                servings=extracted_recipe.servings,
                difficulty=difficulty,
                tags=self._clean_tags(extracted_recipe.tags),
                source=source,
                images=[],  # No images extracted yet
                metadata={
                    "ai_extracted": True,
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    "original_source": extracted_recipe.source_url
                }
            )
            
            logger.info(f"Successfully transformed recipe: {recipe_create.title}")
            return recipe_create
            
        except Exception as e:
            logger.error(f"Error transforming recipe: {e}")
            raise ValueError(f"Failed to transform extracted recipe: {str(e)}")

    def _transform_ingredients(self, extracted_ingredients: list[ExtractedIngredient]) -> list[Ingredient]:
        """Transform extracted ingredients to Ingredient models."""
        ingredients = []
        
        for ext_ingredient in extracted_ingredients:
            try:
                ingredient = Ingredient(
                    name=self._clean_ingredient_name(ext_ingredient.name),
                    amount=self._clean_amount(ext_ingredient.amount),
                    unit=self._clean_unit(ext_ingredient.unit)
                )
                ingredients.append(ingredient)
            except Exception as e:
                logger.warning(f"Skipping invalid ingredient {ext_ingredient.name}: {e}")
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

    def _normalize_difficulty(self, difficulty: Optional[str]) -> Optional[str]:
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