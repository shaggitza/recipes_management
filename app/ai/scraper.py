"""Web scraping module for recipe pages using requests and BeautifulSoup as fallback."""

import asyncio
import logging
from typing import Optional, List, Tuple
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

    def extract_images(self, html_content: str, base_url: str) -> List[dict]:
        """
        Extract all images from HTML content with metadata.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative image URLs
            
        Returns:
            List of image dictionaries with metadata
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            images = []
            
            # Find all img tags
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                # Get image URL
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if not src:
                    continue
                
                # Resolve relative URLs
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                # Skip very small images, icons, and tracking pixels
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    try:
                        width = int(width)
                        height = int(height)
                        if width < 100 or height < 100:
                            continue
                    except ValueError:
                        pass
                
                # Skip common non-recipe images
                alt_text = img.get('alt', '').lower()
                title = img.get('title', '').lower()
                src_lower = src.lower()
                
                # Skip icons, logos, ads, social media buttons
                skip_patterns = [
                    'icon', 'logo', 'avatar', 'profile', 'social', 'facebook', 'twitter',
                    'instagram', 'pinterest', 'youtube', 'advertisement', 'banner',
                    'header', 'footer', 'sidebar', 'nav', 'menu', 'button'
                ]
                
                if any(pattern in alt_text or pattern in title or pattern in src_lower for pattern in skip_patterns):
                    continue
                
                # Get parent context for better relevance scoring
                parent_text = ''
                parent = img.parent
                if parent:
                    parent_text = parent.get_text()[:200].lower()
                
                image_data = {
                    'url': src,
                    'alt_text': img.get('alt'),
                    'title': img.get('title'),
                    'width': width,
                    'height': height,
                    'parent_context': parent_text,
                    'is_in_recipe_context': self._is_recipe_context(img)
                }
                
                images.append(image_data)
            
            # Sort by relevance (recipe context first, then by size)
            images.sort(key=lambda x: (
                -int(x['is_in_recipe_context']),
                -(x['width'] or 0) * (x['height'] or 0)
            ))
            
            return images[:10]  # Limit to top 10 images
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []

    def _is_recipe_context(self, img_tag) -> bool:
        """
        Check if an image is in a recipe-related context.
        
        Args:
            img_tag: BeautifulSoup img tag
            
        Returns:
            True if image appears to be recipe-related
        """
        # Check parent elements for recipe-related classes/IDs
        current = img_tag
        for _ in range(5):  # Check up to 5 parent levels
            if current is None:
                break
            
            # Check class and id attributes
            classes = current.get('class', [])
            element_id = current.get('id', '')
            
            recipe_indicators = [
                'recipe', 'food', 'dish', 'cooking', 'ingredient', 'preparation',
                'featured', 'hero', 'main', 'content', 'article'
            ]
            
            text_content = ' '.join(classes + [element_id]).lower()
            if any(indicator in text_content for indicator in recipe_indicators):
                return True
            
            current = current.parent
        
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
            logger.error(f"Error extracting recipe content: {e}")
            return html_content  # Fallback to raw HTML

    async def scrape_and_extract(self, url: str) -> Tuple[Optional[str], List[dict]]:
        """
        Complete scraping and extraction pipeline with images.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (extracted recipe content, list of image data) or (None, []) if failed
        """
        html_content = await self.scrape_recipe_page(url)
        if not html_content:
            return None, []
        
        # Extract both text content and images
        text_content = self.extract_recipe_content(html_content, url)
        images = self.extract_images(html_content, url)
        
        return text_content, images

    def close(self):
        """Clean up resources."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()