"""API router for AI-powered recipe import functionality."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field

from app.repositories.recipe_repository import RecipeRepository
from app.ai.importer import RecipeImporter, ImportResult
from app.models.recipe import RecipeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Import"])


class ImportRequest(BaseModel):
    """Request model for importing a recipe from URL."""
    url: HttpUrl = Field(..., description="URL of the recipe to import")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata to add to the recipe")


class BatchImportRequest(BaseModel):
    """Request model for batch importing recipes."""
    urls: List[HttpUrl] = Field(..., description="List of URLs to import", max_length=10)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for all recipes")
    max_concurrent: int = Field(3, description="Maximum concurrent imports", ge=1, le=5)


class ImportStatusResponse(BaseModel):
    """Response model for import status."""
    success: bool
    recipe_id: Optional[str] = None
    error: Optional[str] = None
    url: str
    attempts: int
    timestamp: str
    extraction_metadata: Optional[Dict[str, Any]] = None


class BatchImportResponse(BaseModel):
    """Response model for batch import."""
    total_urls: int
    successful_imports: int
    failed_imports: int
    results: Dict[str, ImportStatusResponse]


async def get_recipe_repository() -> RecipeRepository:
    """Dependency to get recipe repository."""
    return RecipeRepository()


async def get_recipe_importer(repo: RecipeRepository = Depends(get_recipe_repository)) -> RecipeImporter:
    """Dependency to get recipe importer."""
    return RecipeImporter(repo)


@router.post("/import", response_model=ImportStatusResponse)
async def import_recipe(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    importer: RecipeImporter = Depends(get_recipe_importer)
):
    """
    Import a single recipe from a URL using AI extraction.
    
    This endpoint scrapes the provided URL, uses AI to extract recipe data,
    and saves it to the database with retry logic for robustness.
    """
    try:
        logger.info(f"Received import request for URL: {request.url}")
        
        # Convert URL to string
        url_str = str(request.url)
        
        # Import the recipe
        result = await importer.import_recipe_from_url(url_str, request.metadata)
        
        # Clean up importer resources in background
        background_tasks.add_task(importer.cleanup)
        
        # Return the result
        response = ImportStatusResponse(
            success=result.success,
            recipe_id=result.recipe_id,
            error=result.error,
            url=result.url or url_str,
            attempts=result.attempts,
            timestamp=result.timestamp.isoformat(),
            extraction_metadata=result.extraction_result.extraction_metadata if result.extraction_result else None
        )
        
        if not result.success:
            logger.warning(f"Import failed for {url_str}: {result.error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error importing recipe from {request.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/batch", response_model=BatchImportResponse)
async def batch_import_recipes(
    request: BatchImportRequest,
    background_tasks: BackgroundTasks,
    importer: RecipeImporter = Depends(get_recipe_importer)
):
    """
    Import multiple recipes from URLs concurrently.
    
    This endpoint allows batch importing of up to 10 recipes at once
    with configurable concurrency limits.
    """
    try:
        logger.info(f"Received batch import request for {len(request.urls)} URLs")
        
        # Convert URLs to strings
        url_strings = [str(url) for url in request.urls]
        
        # Perform batch import
        results = await importer.batch_import(
            url_strings, 
            request.metadata,
            request.max_concurrent
        )
        
        # Clean up importer resources in background
        background_tasks.add_task(importer.cleanup)
        
        # Convert results to response format
        response_results = {}
        successful_count = 0
        
        for url, result in results.items():
            response_results[url] = ImportStatusResponse(
                success=result.success,
                recipe_id=result.recipe_id,
                error=result.error,
                url=result.url or url,
                attempts=result.attempts,
                timestamp=result.timestamp.isoformat(),
                extraction_metadata=result.extraction_result.extraction_metadata if result.extraction_result else None
            )
            
            if result.success:
                successful_count += 1
        
        response = BatchImportResponse(
            total_urls=len(request.urls),
            successful_imports=successful_count,
            failed_imports=len(request.urls) - successful_count,
            results=response_results
        )
        
        logger.info(f"Batch import completed: {successful_count}/{len(request.urls)} successful")
        return response
        
    except Exception as e:
        logger.error(f"Error in batch import: {e}")
        raise HTTPException(status_code=500, detail=f"Batch import failed: {str(e)}")


@router.get("/import/status/{recipe_id}", response_model=RecipeResponse)
async def get_imported_recipe(
    recipe_id: str,
    repository: RecipeRepository = Depends(get_recipe_repository)
):
    """
    Get details of an imported recipe by ID.
    
    Returns the full recipe data for a previously imported recipe.
    """
    try:
        recipe = await repository.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return RecipeResponse.from_recipe(recipe)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recipe: {str(e)}")


@router.get("/import/check")
async def check_url_status(
    url: str,
    importer: RecipeImporter = Depends(get_recipe_importer)
):
    """
    Check if a URL has already been imported.
    
    Returns status information about whether the URL has been processed.
    """
    try:
        status = await importer.get_import_status(url)
        return status
        
    except Exception as e:
        logger.error(f"Error checking URL status for {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check URL status: {str(e)}")


@router.get("/import/sources")
async def get_supported_sources():
    """
    Get information about supported recipe sources.
    
    Returns a list of websites and domains that are known to work well
    with the AI extraction system.
    """
    return {
        "supported_sources": [
            {
                "domain": "raftulbunicii.ro",
                "name": "Raftul Bunicii",
                "type": "Romanian recipes",
                "extraction_quality": "good",
                "notes": "Romanian recipes, translated to English"
            }
        ],
        "general_support": {
            "structured_data": "Websites with JSON-LD recipe data work best",
            "html_parsing": "Most recipe websites are supported with fallback parsing",
            "languages": "Content is automatically translated to English"
        },
        "limitations": [
            "Dynamic content loaded by JavaScript may not be captured",
            "Some recipe sites may block automated scraping",
            "Image extraction is not yet implemented"
        ]
    }


@router.get("/import/test")
async def test_extraction():
    """
    Test endpoint to verify the AI extraction system is working.
    
    Returns system status and basic functionality test results.
    """
    try:
        # Test basic components
        from app.ai.scraper import RecipeScraper
        from app.ai.extractor import RecipeExtractor
        from app.ai.transformer import RecipeTransformer
        
        # Initialize components
        scraper = RecipeScraper()
        extractor = RecipeExtractor()
        transformer = RecipeTransformer()
        
        return {
            "status": "healthy",
            "components": {
                "scraper": "initialized",
                "extractor": "initialized", 
                "transformer": "initialized"
            },
            "ai_backend": "rule_based_fallback",  # Will be "langfun" when AI is available
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }