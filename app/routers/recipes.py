from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from beanie import PydanticObjectId

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeResponse

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

@router.post("/", response_model=RecipeResponse)
async def create_recipe(recipe: RecipeCreate) -> RecipeResponse:
    """Create a new recipe"""
    # Create Recipe document from RecipeCreate data
    recipe_doc = Recipe(**recipe.model_dump())
    recipe_doc.created_at = datetime.utcnow()
    recipe_doc.updated_at = datetime.utcnow()
    
    # Save to database using Beanie
    await recipe_doc.insert()
    
    # Convert to response model - ensure ID is properly serialized
    recipe_data = recipe_doc.model_dump(exclude={"id"})
    recipe_data["id"] = str(recipe_doc.id)
    return RecipeResponse(**recipe_data)

@router.get("/", response_model=List[RecipeResponse])
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None)
) -> List[RecipeResponse]:
    """Get recipes with optional filtering"""
    # Build query conditions
    find_query = {}
    
    if search:
        # Use MongoDB text search or regex
        find_query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"ingredients.name": {"$regex": search, "$options": "i"}}
        ]
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        find_query["tags"] = {"$in": tag_list}
    
    if difficulty:
        find_query["difficulty"] = difficulty
    
    # Execute query with Beanie
    recipes = await Recipe.find(find_query).skip(skip).limit(limit).sort(-Recipe.created_at).to_list()
    
    # Convert to response models with proper ID serialization
    response_recipes = []
    for recipe in recipes:
        recipe_data = recipe.model_dump(exclude={"id"})
        recipe_data["id"] = str(recipe.id)
        response_recipes.append(RecipeResponse(**recipe_data))
    
    return response_recipes

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: str) -> RecipeResponse:
    """Get a specific recipe by ID"""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(recipe_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe = await Recipe.get(object_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Convert to response model with proper ID serialization
    recipe_data = recipe.model_dump(exclude={"id"})
    recipe_data["id"] = str(recipe.id)
    return RecipeResponse(**recipe_data)

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(recipe_id: str, recipe_update: RecipeUpdate) -> RecipeResponse:
    """Update a recipe"""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(recipe_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe = await Recipe.get(object_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Update fields that are provided
    update_data = recipe_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the recipe using Beanie's update method
        await recipe.update({"$set": update_data})
        
        # Refresh the recipe to get updated data
        await recipe.sync()
    
    # Convert to response model with proper ID serialization
    recipe_data = recipe.model_dump(exclude={"id"})
    recipe_data["id"] = str(recipe.id)
    return RecipeResponse(**recipe_data)

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str) -> dict:
    """Delete a recipe"""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(recipe_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe = await Recipe.get(object_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Delete recipe using Beanie
    await recipe.delete()
    
    return {"message": "Recipe deleted successfully"}

@router.get("/tags/all", response_model=List[str])
async def get_all_tags() -> List[str]:
    """Get all unique tags"""
    # Use Beanie's aggregation pipeline
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$sort": {"_id": 1}}
    ]
    
    result = await Recipe.aggregate(pipeline).to_list()
    tags = [doc["_id"] for doc in result if doc.get("_id")]
    
    return tags