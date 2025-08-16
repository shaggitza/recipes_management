"""Recipe import service with retry logic and error handling."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.models.recipe import Recipe, RecipeCreate
from app.repositories.recipe_repository import RecipeRepository
from .extractor import RecipeExtractor
from .transformer import RecipeTransformer
from .bridge import RecipeExtractionResult

logger = logging.getLogger(__name__)


class ImportResult:
    """Result of recipe import operation."""
    
    def __init__(
        self,
        success: bool,
        recipe_id: Optional[str] = None,
        error: Optional[str] = None,
        url: Optional[str] = None,
        attempts: int = 0,
        extraction_result: Optional[RecipeExtractionResult] = None
    ):
        self.success = success
        self.recipe_id = recipe_id
        self.error = error
        self.url = url
        self.attempts = attempts
        self.extraction_result = extraction_result
        self.timestamp = datetime.now(timezone.utc)


class RecipeImporter:
    """Service for importing recipes from web URLs with retry logic."""
    
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the recipe importer.
        
        Args:
            recipe_repository: Repository for saving recipes
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Timeout for web requests
            openai_api_key: OpenAI API key for AI extraction (optional)
        """
        self.recipe_repository = recipe_repository
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # Remove the separate scraper - ScrapeGraphAI handles this now
        self.extractor = RecipeExtractor(use_ai=True, api_key=openai_api_key)
        self.transformer = RecipeTransformer()

    async def import_recipe_from_url(self, url: str, user_metadata: Optional[Dict[str, Any]] = None) -> ImportResult:
        """
        Import a recipe from a URL with retry logic.
        
        Args:
            url: URL of the recipe to import
            user_metadata: Optional metadata to add to the recipe
            
        Returns:
            ImportResult with success/failure information
        """
        logger.info(f"Starting recipe import from URL: {url}")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Import attempt {attempt}/{self.max_retries} for {url}")
                
                # Step 1: Extract recipe data directly from URL using ScrapeGraphAI's crawler
                extraction_result = await self._extract_with_retry(url, attempt)
                if not extraction_result.success:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * attempt)
                        continue
                    else:
                        return ImportResult(
                            success=False,
                            error=f"Failed to extract recipe data: {extraction_result.error}",
                            url=url,
                            attempts=attempt,
                            extraction_result=extraction_result
                        )
                
                # Step 2: Transform to Recipe model
                recipe_create = await self._transform_with_retry(extraction_result.recipe, user_metadata, attempt)
                if not recipe_create:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * attempt)
                        continue
                    else:
                        return ImportResult(
                            success=False,
                            error="Failed to transform extracted data to recipe model",
                            url=url,
                            attempts=attempt,
                            extraction_result=extraction_result
                        )
                
                # Step 3: Save to database
                recipe = await self._save_with_retry(recipe_create, attempt)
                if not recipe:
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * attempt)
                        continue
                    else:
                        return ImportResult(
                            success=False,
                            error="Failed to save recipe to database",
                            url=url,
                            attempts=attempt,
                            extraction_result=extraction_result
                        )
                
                # Success!
                logger.info(f"Successfully imported recipe {recipe.id} from {url} on attempt {attempt}")
                return ImportResult(
                    success=True,
                    recipe_id=str(recipe.id),
                    url=url,
                    attempts=attempt,
                    extraction_result=extraction_result
                )
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {url}: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                else:
                    return ImportResult(
                        success=False,
                        error=f"Import failed after {attempt} attempts: {str(e)}",
                        url=url,
                        attempts=attempt
                    )
        
        # Should not reach here, but just in case
        return ImportResult(
            success=False,
            error="Import failed for unknown reason",
            url=url,
            attempts=self.max_retries
        )

    # Scraping is now handled by ScrapeGraphAI's crawler - removed _scrape_with_retry method

    async def _extract_with_retry(self, url: str, attempt: int) -> RecipeExtractionResult:
        """Extract recipe data directly from URL with error handling."""
        try:
            logger.debug(f"Extraction attempt {attempt} for {url}")
            return await self.extractor.extract_recipe_from_url(url)
        except Exception as e:
            error_msg = f"Extraction error on attempt {attempt}: {e}"
            logger.error(error_msg)
            if attempt >= self.max_retries:
                raise RuntimeError(error_msg) from e
            return RecipeExtractionResult(
                success=False,
                recipe=None,
                error=str(e),
                source_url=url
            )

    async def _transform_with_retry(
        self, 
        extracted_recipe, 
        user_metadata: Optional[Dict[str, Any]], 
        attempt: int
    ) -> Optional[RecipeCreate]:
        """Transform extracted data with error handling."""
        try:
            if not extracted_recipe:
                error_msg = f"No extracted recipe to transform on attempt {attempt}"
                logger.error(error_msg)
                if attempt >= self.max_retries:
                    raise ValueError(error_msg)
                return None
            
            logger.debug(f"Transformation attempt {attempt}")
            recipe_create = self.transformer.transform_to_recipe_create(extracted_recipe)
            
            # Add user metadata if provided
            if user_metadata:
                recipe_create.metadata.update(user_metadata)
            
            # Validate the transformed recipe
            if self.transformer.validate_recipe_create(recipe_create):
                return recipe_create
            else:
                error_msg = f"Recipe validation failed on attempt {attempt}"
                logger.error(error_msg)
                if attempt >= self.max_retries:
                    raise ValueError(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Transformation error on attempt {attempt}: {e}"
            logger.error(error_msg)
            if attempt >= self.max_retries:
                raise RuntimeError(error_msg) from e
            return None

    async def _save_with_retry(self, recipe_create: RecipeCreate, attempt: int) -> Optional[Recipe]:
        """Save recipe to database with error handling."""
        try:
            logger.debug(f"Database save attempt {attempt}")
            recipe = await self.recipe_repository.create(recipe_create)
            return recipe
        except Exception as e:
            error_msg = f"Database save error on attempt {attempt}: {e}"
            logger.error(error_msg)
            if attempt >= self.max_retries:
                raise RuntimeError(error_msg) from e
            return None

    async def batch_import(
        self, 
        urls: list[str], 
        user_metadata: Optional[Dict[str, Any]] = None,
        max_concurrent: int = 3
    ) -> Dict[str, ImportResult]:
        """
        Import multiple recipes concurrently.
        
        Args:
            urls: List of URLs to import
            user_metadata: Optional metadata for all recipes
            max_concurrent: Maximum concurrent imports
            
        Returns:
            Dictionary mapping URLs to ImportResults
        """
        logger.info(f"Starting batch import of {len(urls)} recipes")
        
        # Use semaphore to limit concurrent imports
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def import_single(url: str) -> tuple[str, ImportResult]:
            async with semaphore:
                result = await self.import_recipe_from_url(url, user_metadata)
                return url, result
        
        # Run imports concurrently
        tasks = [import_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        import_results = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch import task failed: {result}")
                continue
            
            url, import_result = result
            import_results[url] = import_result
        
        # Log summary
        successful = sum(1 for r in import_results.values() if r.success)
        failed = len(import_results) - successful
        logger.info(f"Batch import completed: {successful} successful, {failed} failed")
        
        return import_results

    async def get_import_status(self, url: str) -> Dict[str, Any]:
        """
        Get status information for a URL.
        
        Args:
            url: URL to check
            
        Returns:
            Status information dictionary
        """
        try:
            # Check if we already have a recipe from this URL
            recipes = await self.recipe_repository.get_all(filters={})
            existing_recipe = None
            
            for recipe in recipes:
                if recipe.source.url == url:
                    existing_recipe = recipe
                    break
            
            if existing_recipe:
                return {
                    "status": "exists",
                    "recipe_id": str(existing_recipe.id),
                    "title": existing_recipe.title,
                    "created_at": existing_recipe.created_at.isoformat()
                }
            else:
                return {
                    "status": "not_imported",
                    "url": url
                }
                
        except Exception as e:
            logger.error(f"Error checking import status for {url}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }

    async def cleanup(self):
        """Clean up resources."""
        # No cleanup needed since scraper is now handled by ScrapeGraphAI
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()