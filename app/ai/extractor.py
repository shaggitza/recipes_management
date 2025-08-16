"""AI-powered recipe extraction using ScrapeGraphAI - compatibility module."""

# Import the new ScrapeGraphAI implementation
from .bridge import RecipeExtractor, RecipeExtractionResult

# Re-export for backward compatibility
__all__ = ["RecipeExtractor", "RecipeExtractionResult"]