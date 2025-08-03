"""Simplified AI-powered recipe extraction using langfun - compatibility module."""

# Import the new simplified implementation
from .bridge import RecipeExtractor, RecipeExtractionResult

# Re-export for backward compatibility
__all__ = ["RecipeExtractor", "RecipeExtractionResult"]