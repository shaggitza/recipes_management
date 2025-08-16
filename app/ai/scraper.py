"""
DEPRECATED: Web scraping module for recipe pages.

This module is now deprecated. ScrapeGraphAI's SmartScraperGraph handles both
crawling and extraction directly from URLs, eliminating the need for separate
scraping and extraction steps.

Use SimpleRecipeExtractor.extract_recipe_from_url() instead.
"""

# This entire file is deprecated and will be removed in future versions.
# ScrapeGraphAI's crawler functionality replaces this separate scraping step.

import asyncio
import logging
from typing import Optional, List, Tuple
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class RecipeScraper:
    """DEPRECATED: Web scraper for recipe pages. Use ScrapeGraphAI's crawler instead."""
    
    def __init__(self, timeout: int = 30):
        """Initialize scraper with timeout settings."""
        logger.warning("RecipeScraper is deprecated. Use ScrapeGraphAI's SmartScraperGraph instead.")
        self.timeout = timeout
        self.session = requests.Session()
        # Set a realistic user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    async def scrape_recipe_page(self, url: str) -> Optional[str]:
        """
        Scrape a recipe page and return the HTML content.
        
        Args:
            url: URL of the recipe page to scrape
            
        Returns:
            HTML content of the page or None if scraping failed
        """
        try:
            logger.info(f"Scraping recipe from URL: {url}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # Make request in a thread to keep it async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.get(url, timeout=self.timeout)
            )
            
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                raise ValueError(f"URL does not serve HTML content: {content_type}")
            
            return response.text
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout while scraping {url}"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error while scraping {url}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error while scraping {url}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def extract_images(self, html_content: str, base_url: str) -> List[dict]:
        """
        Simplified image extraction - returns empty list.
        
        Image extraction has been removed to simplify the pipeline.
        The images field remains in the Recipe model but is not populated.
        
        Args:
            html_content: Raw HTML content (unused)
            base_url: Base URL for resolving relative image URLs (unused)
            
        Returns:
            Empty list - image extraction is disabled
        """
        logger.debug("Image extraction skipped - feature simplified")
        return []

    def _is_recipe_context(self, img_tag) -> bool:
        """
        Simplified image context check - always returns False.
        
        This method is kept for compatibility but always returns False
        since image extraction has been simplified.
        
        Args:
            img_tag: BeautifulSoup img tag (unused)
            
        Returns:
            False - image context checking is disabled
        """
        return False

    def extract_recipe_content(self, html_content: str, url: str) -> str:
        """
        Extract recipe-relevant content from HTML.
        
        Args:
            html_content: Raw HTML content
            url: Source URL for context
            
        Returns:
            Cleaned text content focusing on recipe information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find recipe-specific content first
            recipe_selectors = [
                '[itemtype*="Recipe"]',
                '.recipe',
                '#recipe',
                '.recipe-content',
                '.recipe-details',
                '.entry-content',
                'article',
                'main'
            ]
            
            recipe_content = None
            for selector in recipe_selectors:
                elements = soup.select(selector)
                if elements:
                    recipe_content = elements[0]
                    break
            
            # If no specific recipe content found, use body
            if not recipe_content:
                recipe_content = soup.find('body') or soup
            
            # Extract text with some structure preservation
            text_parts = []
            
            # Extract title
            title = soup.find('title')
            if title:
                text_parts.append(f"TITLE: {title.get_text().strip()}")
            
            # Extract headings and content
            for element in recipe_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'div']):
                text = element.get_text().strip()
                if text and len(text) > 10:  # Filter out very short text
                    # Add some structure indicators
                    if element.name in ['h1', 'h2', 'h3', 'h4']:
                        text_parts.append(f"HEADING: {text}")
                    elif element.name == 'li':
                        text_parts.append(f"ITEM: {text}")
                    else:
                        text_parts.append(text)
            
            # Join and clean up the text
            extracted_text = '\n'.join(text_parts)
            
            # Clean up whitespace
            extracted_text = re.sub(r'\n\s*\n', '\n\n', extracted_text)
            extracted_text = re.sub(r' +', ' ', extracted_text)
            
            return extracted_text.strip()
            
        except Exception as e:
            error_msg = f"Error extracting recipe content: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def scrape_and_extract(self, url: str) -> Tuple[Optional[str], List[dict]]:
        """
        Complete scraping and extraction pipeline - simplified without image extraction.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (extracted recipe content, empty list) or (None, []) if failed
        """
        html_content = await self.scrape_recipe_page(url)
        if not html_content:
            return None, []
        
        # Extract only text content, skip image extraction
        text_content = self.extract_recipe_content(html_content, url)
        
        return text_content, []  # Always return empty list for images

    def close(self):
        """Clean up resources."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()