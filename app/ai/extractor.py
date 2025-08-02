"""AI-powered recipe extraction module with langfun integration and fallback to structured parsing."""

import asyncio
import logging
import re
from typing import Optional, List, Dict, Any
import json
import os

logger = logging.getLogger(__name__)

try:
    import langfun as lf
    from langfun.core import llm
    LANGFUN_AVAILABLE = True
except ImportError:
    LANGFUN_AVAILABLE = False
    logger.warning("langfun not available, falling back to rule-based extraction")

from .models import ExtractedRecipe, ExtractedIngredient, RecipeExtractionResult


class RecipeExtractor:
    """AI-powered recipe extractor with langfun integration and fallback to rule-based extraction."""
    
    def __init__(self, use_ai: bool = True, api_key: Optional[str] = None):
        """
        Initialize the recipe extractor.
        
        Args:
            use_ai: Whether to use AI extraction (langfun integration)
            api_key: OpenAI API key for langfun. If None, will try environment variable
        """
        self.use_ai = use_ai and LANGFUN_AVAILABLE
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        
        if self.use_ai and self.api_key:
            self._configure_langfun()
        elif self.use_ai and not self.api_key:
            logger.warning("AI extraction requested but no API key provided, falling back to rule-based")
            self.use_ai = False
            
    def _configure_langfun(self):
        """Configure langfun with OpenAI backend."""
        try:
            # Configure OpenAI as the default language model
            lf.use_init_args(
                llm.OpenAI(
                    api_key=self.api_key,
                    model='gpt-3.5-turbo',
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=2000
                )
            )
            logger.info("Langfun configured with OpenAI backend")
        except Exception as e:
            logger.error(f"Failed to configure langfun: {e}")
            self.use_ai = False
        
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
                # Use langfun AI extraction
                result = await self._extract_with_ai(content, source_url)
                # If AI extraction fails, fall back to rule-based
                if not result.success:
                    logger.info("AI extraction failed, falling back to rule-based")
                    return await self._extract_with_rules(content, source_url)
                return result
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
        Extract recipe using AI (langfun) with structured output.
        
        Args:
            content: Content to extract from
            source_url: Source URL
            
        Returns:
            Extraction result
        """
        if not LANGFUN_AVAILABLE:
            raise ValueError("langfun not available")
            
        try:
            logger.info("Using langfun AI extraction")
            
            # Create the langfun extraction function
            @lf.use_init_args(lf.LangFunc)
            def extract_recipe_data(content_text: str) -> Dict[str, Any]:
                """Extract structured recipe data from web content.
                
                Args:
                    content_text: The web page content containing the recipe
                    
                Returns:
                    A dictionary with the extracted recipe data in JSON format
                """
                return lf.query(
                    self._create_langfun_prompt(content_text),
                    lf.Json[Dict[str, Any]]  # Structured JSON output
                )
            
            # Execute the langfun extraction
            loop = asyncio.get_event_loop()
            ai_response = await loop.run_in_executor(
                None, 
                lambda: extract_recipe_data(content[:4000])  # Limit content length for token limits
            )
            
            # Parse the AI response and create ExtractedRecipe
            recipe = self._parse_ai_response(ai_response, source_url)
            
            return RecipeExtractionResult(
                success=True,
                recipe=recipe,
                error=None,
                source_url=source_url,
                extraction_metadata={
                    "method": "langfun_ai", 
                    "content_length": len(content),
                    "model": "gpt-3.5-turbo"
                }
            )
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return RecipeExtractionResult(
                success=False,
                recipe=None,
                error=f"AI extraction failed: {str(e)}",
                source_url=source_url
            )

    def _create_langfun_prompt(self, content: str) -> str:
        """
        Create a prompt optimized for langfun structured extraction.
        
        Args:
            content: Web content to extract from
            
        Returns:
            Formatted prompt for langfun
        """
        return f"""
Extract recipe information from the following web content. The content may be in Romanian or other languages - please translate everything to English.

Please return the data in this exact JSON structure:
{{
    "title": "Recipe title in English",
    "description": "Brief description in English (optional)",
    "ingredients": [
        {{"name": "ingredient name", "amount": "quantity", "unit": "measurement unit"}}
    ],
    "instructions": ["Step 1 in English", "Step 2 in English"],
    "prep_time": 30,
    "cook_time": 45,
    "servings": 4,
    "difficulty": "easy",
    "tags": ["cuisine_type", "meal_type"]
}}

Rules:
- Translate all text to English
- For missing prep_time/cook_time, estimate reasonable values
- For missing servings, estimate based on ingredient quantities
- Difficulty should be "easy", "medium", or "hard"
- Extract meaningful tags like cuisine type, meal type, etc.
- Ensure all ingredient amounts include units when possible

Web Content:
{content}
"""

    def _parse_ai_response(self, ai_response: Dict[str, Any], source_url: str) -> ExtractedRecipe:
        """
        Parse AI response and create ExtractedRecipe object.
        
        Args:
            ai_response: Dictionary response from AI
            source_url: Source URL
            
        Returns:
            ExtractedRecipe object
        """
        try:
            # Convert ingredients list to ExtractedIngredient objects
            ingredients = []
            for ing_data in ai_response.get('ingredients', []):
                if isinstance(ing_data, dict):
                    ingredient = ExtractedIngredient(
                        name=ing_data.get('name', ''),
                        amount=str(ing_data.get('amount', '1')),
                        unit=ing_data.get('unit')
                    )
                    ingredients.append(ingredient)
            
            # Create the recipe object
            recipe = ExtractedRecipe(
                title=ai_response.get('title', 'AI Extracted Recipe'),
                description=ai_response.get('description'),
                ingredients=ingredients,
                instructions=ai_response.get('instructions', []),
                prep_time=ai_response.get('prep_time'),
                cook_time=ai_response.get('cook_time'), 
                servings=ai_response.get('servings'),
                difficulty=ai_response.get('difficulty'),
                tags=ai_response.get('tags', []),
                source_url=source_url
            )
            
            return recipe
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Return a minimal recipe if parsing fails
            return ExtractedRecipe(
                title="AI Extraction Error",
                description="Failed to parse AI response",
                ingredients=[],
                instructions=[],
                source_url=source_url
            )

    def _create_extraction_prompt(self, content: str) -> str:
        """
        Create a prompt for AI extraction (legacy method for compatibility).
        
        Args:
            content: Web content to extract from
            
        Returns:
            Formatted prompt for AI
        """
        return self._create_langfun_prompt(content)

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