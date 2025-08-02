"""Web scraping module for recipe pages using requests and BeautifulSoup as fallback."""

import asyncio
import logging
from typing import Optional
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class RecipeScraper:
    """Web scraper for recipe pages with fallback to requests/BeautifulSoup."""
    
    def __init__(self, timeout: int = 30):
        """Initialize scraper with timeout settings."""
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
            logger.error(f"Timeout while scraping {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {e}")
            return None

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
            logger.error(f"Error extracting recipe content: {e}")
            return html_content  # Fallback to raw HTML

    async def scrape_and_extract(self, url: str) -> Optional[str]:
        """
        Complete scraping and extraction pipeline.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted recipe content or None if failed
        """
        html_content = await self.scrape_recipe_page(url)
        if not html_content:
            return None
        
        return self.extract_recipe_content(html_content, url)

    def close(self):
        """Clean up resources."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()