from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeResponse
from app.services.recipe_service import RecipeService, recipe_service

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def get_recipe_service() -> RecipeService:
    """Dependency injection for recipe service"""
    return recipe_service


@router.post("/", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    recipe: RecipeCreate,
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeResponse:
    """Create a new recipe with proper validation"""
    created_recipe = await service.create_recipe(recipe)
    # Use Beanie's built-in serialization with proper alias handling
    return RecipeResponse.model_validate(created_recipe)


@router.get("/", response_model=List[RecipeResponse])
async def get_recipes(
    skip: int = Query(0, ge=0, description="Number of recipes to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of recipes to return"),
    search: Optional[str] = Query(None, description="Search term for recipes"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$", description="Difficulty level filter"),
    service: RecipeService = Depends(get_recipe_service)
) -> List[RecipeResponse]:
    """Get recipes with optional filtering, searching, and pagination"""
    recipes = await service.get_recipes(
        skip=skip,
        limit=limit,
        search=search,
        tags=tags,
        difficulty=difficulty
    )
    
    # Convert using Beanie's proper serialization
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get("/search", response_model=List[RecipeResponse])
async def search_recipes(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
    service: RecipeService = Depends(get_recipe_service)
) -> List[RecipeResponse]:
    """Search recipes by text query"""
    recipes = await service.search_recipes(query=q, skip=skip, limit=limit)
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get("/count")
async def get_recipe_count(
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    service: RecipeService = Depends(get_recipe_service)
) -> JSONResponse:
    """Get count of recipes with optional filters"""
    count = await service.get_recipe_count(difficulty=difficulty, tags=tags)
    return JSONResponse(content={"count": count})


@router.get("/tags", response_model=List[str])
async def get_all_tags(
    service: RecipeService = Depends(get_recipe_service)
) -> List[str]:
    """Get all unique tags"""
    return await service.get_all_tags()


@router.get("/recent", response_model=List[RecipeResponse])
async def get_recent_recipes(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recent recipes"),
    service: RecipeService = Depends(get_recipe_service)
) -> List[RecipeResponse]:
    """Get recently created recipes"""
    recipes = await service.get_recent_recipes(limit=limit)
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get("/difficulty/{difficulty}", response_model=List[RecipeResponse])
async def get_recipes_by_difficulty(
    difficulty: str,
    service: RecipeService = Depends(get_recipe_service)
) -> List[RecipeResponse]:
    """Get recipes filtered by difficulty level"""
    recipes = await service.get_recipes_by_difficulty(difficulty)
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeResponse:
    """Get a specific recipe by ID"""
    recipe = await service.get_recipe_by_id(recipe_id)
    return RecipeResponse.model_validate(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeResponse:
    """Update a recipe with proper validation"""
    updated_recipe = await service.update_recipe(recipe_id, recipe_update)
    return RecipeResponse.model_validate(updated_recipe)


@router.delete("/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    service: RecipeService = Depends(get_recipe_service)
) -> JSONResponse:
    """Delete a recipe"""
    await service.delete_recipe(recipe_id)
    return JSONResponse(
        content={"message": "Recipe deleted successfully"},
        status_code=200
    )