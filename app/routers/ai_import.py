"""API router for AI-powered recipe import functionality."""

import logging
import os
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl, Field

from app.repositories.recipe_repository import RecipeRepository
from app.ai.importer import RecipeImporter, ImportResult
from app.models.recipe import RecipeResponse
from app.logging_config import AILogger

logger = logging.getLogger("app.routers.ai_import")

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
    scrapegraphai_recipe_dict: Optional[Dict[str, Any]] = None


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
    """Dependency to get recipe importer with OpenAI API key from environment."""
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    logger.info("Creating recipe importer", extra={
        "extra_data": {
            "api_key_present": bool(openai_api_key),
            "api_key_length": len(openai_api_key) if openai_api_key else 0
        }
    })
    return RecipeImporter(repo, openai_api_key=openai_api_key)


@router.post("/import", response_model=ImportStatusResponse)
async def import_recipe(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    importer: RecipeImporter = Depends(get_recipe_importer)
):
    """
    Import a single recipe from a URL using AI extraction.
    
    This endpoint scrapes the provided URL, uses AI to extract recipe data,
    and saves it to the database with retry logic for robustness.
    """
    start_time = time.time()
    url_str = str(request.url)
    request_id = getattr(http_request.state, 'request_id', None)
    
    AILogger.log_extraction_start(
        logger, 
        url=url_str, 
        method="ai_import",
        request_id=request_id,
        metadata=request.metadata
    )
    
    try:
        logger.info("Starting recipe import", extra={
            "extra_data": {
                "url": url_str,
                "has_metadata": bool(request.metadata),
                "request_id": request_id
            }
        })
        
        # Import the recipe
        result = await importer.import_recipe_from_url(url_str, request.metadata)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
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
            extraction_metadata=result.extraction_result.extraction_metadata if result.extraction_result else None,
            scrapegraphai_recipe_dict=result.extraction_result.recipe if result.extraction_result else None
        )
        
        if result.success:
            AILogger.log_extraction_success(
                logger, 
                url=url_str, 
                method="ai_import",
                duration=duration_ms,
                recipe_id=result.recipe_id,
                attempts=result.attempts,
                request_id=request_id
            )
        else:
            logger.warning("Import failed", extra={
                "extra_data": {
                    "url": url_str,
                    "error": result.error,
                    "attempts": result.attempts,
                    "duration_ms": duration_ms,
                    "request_id": request_id
                }
            })
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        AILogger.log_extraction_error(
            logger, 
            url=url_str, 
            method="ai_import", 
            error=e,
            duration_ms=duration_ms,
            request_id=request_id
        )
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/batch", response_model=BatchImportResponse)
async def batch_import_recipes(
    request: BatchImportRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    importer: RecipeImporter = Depends(get_recipe_importer)
):
    """
    Import multiple recipes from URLs concurrently.
    
    This endpoint allows batch importing of up to 10 recipes at once
    with configurable concurrency limits.
    """
    start_time = time.time()
    request_id = getattr(http_request.state, 'request_id', None)
    
    logger.info("Starting batch import", extra={
        "extra_data": {
            "url_count": len(request.urls),
            "max_concurrent": request.max_concurrent,
            "has_metadata": bool(request.metadata),
            "request_id": request_id
        }
    })
    
    try:
        # Convert URLs to strings
        url_strings = [str(url) for url in request.urls]
        
        # Perform batch import
        results = await importer.batch_import(
            url_strings, 
            request.metadata,
            request.max_concurrent
        )
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
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
                extraction_metadata=result.extraction_result.extraction_metadata if result.extraction_result else None,
                scrapegraphai_recipe_dict=result.extraction_result.recipe if result.extraction_result else None
            )
            
            if result.success:
                successful_count += 1
        
        response = BatchImportResponse(
            total_urls=len(request.urls),
            successful_imports=successful_count,
            failed_imports=len(request.urls) - successful_count,
            results=response_results
        )
        
        logger.info("Batch import completed", extra={
            "extra_data": {
                "total_urls": len(request.urls),
                "successful": successful_count,
                "failed": len(request.urls) - successful_count,
                "duration_ms": duration_ms,
                "request_id": request_id
            }
        })
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Batch import failed", exc_info=e, extra={
            "extra_data": {
                "url_count": len(request.urls),
                "duration_ms": duration_ms,
                "request_id": request_id
            }
        })
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
    logger.debug("Retrieving imported recipe", extra={
        "extra_data": {"recipe_id": recipe_id}
    })
    
    try:
        recipe = await repository.get_by_id(recipe_id)
        if not recipe:
            logger.warning("Recipe not found", extra={
                "extra_data": {"recipe_id": recipe_id}
            })
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        logger.debug("Recipe retrieved successfully", extra={
            "extra_data": {
                "recipe_id": recipe_id,
                "recipe_title": recipe.title
            }
        })
        
        return RecipeResponse.from_recipe(recipe)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving recipe", exc_info=e, extra={
            "extra_data": {"recipe_id": recipe_id}
        })
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
    logger.debug("Checking URL import status", extra={
        "extra_data": {"url": url}
    })
    
    try:
        status = await importer.get_import_status(url)
        return status
        
    except Exception as e:
        logger.error("Error checking URL status", exc_info=e, extra={
            "extra_data": {"url": url}
        })
        raise HTTPException(status_code=500, detail=f"Failed to check URL status: {str(e)}")


@router.get("/import/sources")
async def get_supported_sources():
    """
    Get information about supported recipe sources.
    
    Returns a list of websites and domains that are known to work well
    with the AI extraction system.
    """
    logger.debug("Returning supported sources information")
    
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
            "languages": "Content is automatically translated to English",
            "images": "Image extraction simplified - images field remains empty"
        },
        "limitations": [
            "Dynamic content loaded by JavaScript may not be captured",
            "Some recipe sites may block automated scraping",
            "Extraction quality depends on website structure"
        ]
    }


@router.get("/import/test")
async def test_extraction():
    """
    Test endpoint to verify the AI extraction system is working.
    
    Returns system status and basic functionality test results.
    """
    logger.info("Running extraction system test")
    
    try:
        # Test basic components (scraper removed - now handled by ScrapeGraphAI)
        from app.ai.extractor import RecipeExtractor
        from app.ai.transformer import RecipeTransformer
        
        # Initialize components
        extractor = RecipeExtractor()
        transformer = RecipeTransformer()

        # Determine AI backend status
        ai_backend = "scrapegraphai_crawler" if extractor.use_ai else "rule_based_fallback"
        
        test_result = {
            "status": "healthy",
            "components": {
                "extractor": "initialized",
                "transformer": "initialized",
            },
            "ai_backend": ai_backend,
            "scrapegraphai_crawler_available": True,  # Always True since we have fallback
            "extractor_use_ai": extractor.use_ai,
            "api_key_present": bool(extractor.api_key),
            "version": "1.0.0",
        }

        logger.info("Extraction system test completed", extra={
            "extra_data": test_result
        })
        
        return test_result
        
    except Exception as e:
        logger.error("Extraction system test failed", exc_info=e)
        return {
            "status": "error",
            "error": str(e)
        }