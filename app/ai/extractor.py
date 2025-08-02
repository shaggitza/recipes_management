"""AI-powered recipe extraction module with fallback to structured parsing."""

import asyncio
import logging
import re
from typing import Optional, List, Dict, Any
import json

from .models import ExtractedRecipe, ExtractedIngredient, RecipeExtractionResult

logger = logging.getLogger(__name__)


class RecipeExtractor:
    """AI-powered recipe extractor with fallback to rule-based extraction."""
    
    def __init__(self, use_ai: bool = True):
        """
        Initialize the recipe extractor.
        
        Args:
            use_ai: Whether to use AI extraction (future: langfun integration)
        """
        self.use_ai = use_ai
        
    async def extract_recipe(self, content: str, source_url: str) -> RecipeExtractionResult:
        """
        Extract recipe data from scraped content.
        
        Args:
            content: Scraped web content
            source_url: Original URL
            
        Returns:
            RecipeExtractionResult with extracted data
        """
        try:
            logger.info(f"Extracting recipe from content (length: {len(content)})")
            
            if self.use_ai:
                # TODO: Implement langfun AI extraction when available
                # For now, fall back to rule-based extraction
                return await self._extract_with_rules(content, source_url)
            else:
                return await self._extract_with_rules(content, source_url)
                
        except Exception as e:
            logger.error(f"Error during recipe extraction: {e}")
            return RecipeExtractionResult(
                success=False,
                recipe=None,
                error=str(e),
                source_url=source_url
            )

    async def _extract_with_ai(self, content: str, source_url: str) -> RecipeExtractionResult:
        """
        Extract recipe using AI (langfun) - placeholder for future implementation.
        
        Args:
            content: Content to extract from
            source_url: Source URL
            
        Returns:
            Extraction result
        """
        # TODO: Implement langfun integration
        # This is a placeholder for the AI extraction logic
        
        # For now, create a prompt that would be sent to the AI
        ai_prompt = self._create_extraction_prompt(content)
        
        # Placeholder: In a real implementation, this would call langfun
        # For now, fall back to rule-based extraction
        return await self._extract_with_rules(content, source_url)

    def _create_extraction_prompt(self, content: str) -> str:
        """
        Create a prompt for AI extraction.
        
        Args:
            content: Web content to extract from
            
        Returns:
            Formatted prompt for AI
        """
        prompt = f"""
Extract recipe information from the following web content and return it as structured JSON.
The recipe should be translated to English if it's in another language.

Required JSON format:
{{
    "title": "Recipe title in English",
    "description": "Brief description in English",
    "ingredients": [
        {{"name": "ingredient name", "amount": "quantity", "unit": "measurement unit"}}
    ],
    "instructions": ["Step 1 in English", "Step 2 in English"],
    "prep_time": "preparation time in minutes (number only)",
    "cook_time": "cooking time in minutes (number only)", 
    "servings": "number of servings (number only)",
    "difficulty": "easy, medium, or hard",
    "tags": ["tag1", "tag2"]
}}

Web Content:
{content[:3000]}...  # Truncate for prompt length
"""
        return prompt

    async def _extract_with_rules(self, content: str, source_url: str) -> RecipeExtractionResult:
        """
        Extract recipe using rule-based parsing as fallback.
        
        Args:
            content: Content to extract from
            source_url: Source URL
            
        Returns:
            Extraction result
        """
        try:
            logger.info("Using rule-based extraction")
            
            # Extract title
            title = self._extract_title(content)
            
            # Extract ingredients
            ingredients = self._extract_ingredients(content)
            
            # Extract instructions
            instructions = self._extract_instructions(content)
            
            # Extract timing information
            prep_time = self._extract_time(content, "prep")
            cook_time = self._extract_time(content, "cook")
            
            # Extract servings
            servings = self._extract_servings(content)
            
            # Extract tags/categories
            tags = self._extract_tags(content)
            
            # Create the extracted recipe
            recipe = ExtractedRecipe(
                title=title or "Extracted Recipe",
                description=self._extract_description(content),
                ingredients=ingredients,
                instructions=instructions,
                prep_time=prep_time,
                cook_time=cook_time,
                servings=servings,
                difficulty=self._extract_difficulty(content),
                tags=tags,
                source_url=source_url
            )
            
            return RecipeExtractionResult(
                success=True,
                recipe=recipe,
                error=None,
                source_url=source_url,
                extraction_metadata={"method": "rule_based", "content_length": len(content)}
            )
            
        except Exception as e:
            logger.error(f"Rule-based extraction failed: {e}")
            return RecipeExtractionResult(
                success=False,
                recipe=None,
                error=f"Rule-based extraction failed: {str(e)}",
                source_url=source_url
            )

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract recipe title from content."""
        # Look for title patterns
        title_patterns = [
            r'TITLE:\s*(.+)',
            r'HEADING:\s*(.+)',
            r'^(.+?)(?:\n|$)',  # First line
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 200:  # Reasonable title length
                    return title
        
        return None

    def _extract_ingredients(self, content: str) -> List[ExtractedIngredient]:
        """Extract ingredients from content."""
        ingredients = []
        
        # Look for ingredient sections
        ingredient_section = self._find_section(content, ["ingrediente", "ingredients", "items"])
        
        if ingredient_section:
            # Extract individual ingredients
            ingredient_lines = ingredient_section.split('\n')
            for line in ingredient_lines:
                line = line.strip()
                if line and not line.startswith('HEADING'):
                    ingredient = self._parse_ingredient_line(line)
                    if ingredient:
                        ingredients.append(ingredient)
        
        return ingredients

    def _parse_ingredient_line(self, line: str) -> Optional[ExtractedIngredient]:
        """Parse a single ingredient line."""
        # Remove prefixes like "ITEM:", bullet points, etc.
        line = re.sub(r'^(ITEM:|[-•*]\s*)', '', line).strip()
        
        if len(line) < 3:  # Too short to be meaningful
            return None
        
        # Try to extract amount, unit, and name
        # Pattern: amount unit ingredient_name
        amount_pattern = r'^(\d+(?:[.,]\d+)?(?:\s*[-/]\s*\d+(?:[.,]\d+)?)?)\s*([a-zA-Z]*)\s*(.+)'
        match = re.match(amount_pattern, line)
        
        if match:
            amount, unit, name = match.groups()
            return ExtractedIngredient(
                name=name.strip(),
                amount=amount.strip(),
                unit=unit.strip() if unit.strip() else None
            )
        else:
            # If no amount pattern, treat entire line as ingredient name
            return ExtractedIngredient(
                name=line,
                amount="1",
                unit=None
            )

    def _extract_instructions(self, content: str) -> List[str]:
        """Extract cooking instructions from content."""
        instructions = []
        
        # Look for instruction sections
        instruction_section = self._find_section(content, ["preparare", "instructions", "method", "steps"])
        
        if instruction_section:
            # Split into steps
            lines = instruction_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('HEADING') and len(line) > 10:
                    # Clean up the instruction
                    instruction = re.sub(r'^(ITEM:|[-•*]\s*|\d+\.\s*)', '', line).strip()
                    if instruction:
                        instructions.append(instruction)
        
        return instructions

    def _find_section(self, content: str, keywords: List[str]) -> Optional[str]:
        """Find a section of content based on keywords."""
        lines = content.split('\n')
        found_section = False
        section_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a heading with our keyword
            if line.startswith('HEADING:'):
                heading_text = line.replace('HEADING:', '').strip().lower()
                if any(keyword.lower() in heading_text for keyword in keywords):
                    found_section = True
                    continue
                elif found_section:
                    # We've hit a different heading, stop collecting
                    break
            
            # If we're in the right section, collect lines
            if found_section and line:
                section_lines.append(line)
        
        return '\n'.join(section_lines) if section_lines else None

    def _extract_time(self, content: str, time_type: str) -> Optional[int]:
        """Extract timing information (prep or cook time)."""
        patterns = [
            rf'{time_type}.*?(\d+)\s*(?:min|minute)',
            rf'(\d+)\s*(?:min|minute).*{time_type}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                return int(match.group(1))
        
        return None

    def _extract_servings(self, content: str) -> Optional[int]:
        """Extract number of servings."""
        patterns = [
            r'servings?.*?(\d+)',
            r'portions?.*?(\d+)',
            r'serves?\s*(\d+)',
            r'(\d+)\s*(?:servings?|portions?|people)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                servings = int(match.group(1))
                if 1 <= servings <= 50:  # Reasonable range
                    return servings
        
        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract recipe description."""
        # Look for the first substantial paragraph after title
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('HEADING:') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith(('HEADING:', 'ITEM:')) and len(next_line) > 20:
                    return next_line[:500]  # Limit description length
        
        return None

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags/categories from content."""
        tags = []
        
        # Look for category indicators
        category_patterns = [
            r'category.*?([a-zA-Z\s,]+)',
            r'tags?.*?([a-zA-Z\s,]+)',
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, content.lower())
            if match:
                tag_text = match.group(1)
                # Split by common separators
                potential_tags = re.split(r'[,;|]', tag_text)
                for tag in potential_tags:
                    tag = tag.strip()
                    if tag and len(tag) > 2:
                        tags.append(tag)
        
        return tags[:10]  # Limit number of tags

    def _extract_difficulty(self, content: str) -> Optional[str]:
        """Extract difficulty level."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['easy', 'simple', 'quick']):
            return 'easy'
        elif any(word in content_lower for word in ['medium', 'moderate', 'intermediate']):
            return 'medium'
        elif any(word in content_lower for word in ['hard', 'difficult', 'advanced', 'complex']):
            return 'hard'
        
        return None