"""Simplified AI-powered recipe extraction using langfun - compatibility module."""

# Import the new simplified implementation
from .bridge import RecipeExtractor, RecipeExtractionResult

# Compatibility attribute for tests
LANGFUN_AVAILABLE = True

# Re-export for backward compatibility
__all__ = ["RecipeExtractor", "RecipeExtractionResult", "LANGFUN_AVAILABLE"]