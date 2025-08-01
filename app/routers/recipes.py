from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.mock_database import get_database
from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipeInDB

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

@router.post("/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate):
    """Create a new recipe"""
    db = get_database()
    
    # Convert to dict and add timestamps
    recipe_dict = recipe.dict()
    recipe_dict["created_at"] = datetime.utcnow()
    recipe_dict["updated_at"] = datetime.utcnow()
    
    # Insert into database
    result = await db.recipes.insert_one(recipe_dict)
    
    # Fetch the created recipe
    created_recipe = await db.recipes.find_one({"_id": result.inserted_id})
    return Recipe(**created_recipe)

@router.get("/", response_model=List[Recipe])
async def get_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None)
):
    """Get recipes with optional filtering"""
    db = get_database()
    
    # Build query
    query = {}
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"ingredients.name": {"$regex": search, "$options": "i"}}
        ]
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query["tags"] = {"$in": tag_list}
    
    if difficulty:
        query["difficulty"] = difficulty
    
    # Execute query
    cursor = db.recipes.find(query).skip(skip).limit(limit).sort("created_at", -1)
    recipes = await cursor.to_list(length=limit)
    
    return [Recipe(**recipe) for recipe in recipes]

@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str):
    """Get a specific recipe by ID"""
    db = get_database()
    
    recipe = await db.recipes.find_one({"_id": recipe_id})
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return Recipe(**recipe)

@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: str, recipe_update: RecipeUpdate):
    """Update a recipe"""
    db = get_database()
    
    # Check if recipe exists
    existing_recipe = await db.recipes.find_one({"_id": recipe_id})
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Prepare update data
    update_data = recipe_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in database
        await db.recipes.update_one(
            {"_id": recipe_id},
            {"$set": update_data}
        )
    
    # Fetch updated recipe
    updated_recipe = await db.recipes.find_one({"_id": recipe_id})
    return Recipe(**updated_recipe)

@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str):
    """Delete a recipe"""
    db = get_database()
    
    # Check if recipe exists
    existing_recipe = await db.recipes.find_one({"_id": recipe_id})
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Delete recipe
    await db.recipes.delete_one({"_id": recipe_id})
    
    return {"message": "Recipe deleted successfully"}

@router.get("/tags/all", response_model=List[str])
async def get_all_tags():
    """Get all unique tags"""
    db = get_database()
    
    # Aggregate to get unique tags
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = db.recipes.aggregate(pipeline)
    tags = [doc["_id"] async for doc in cursor if doc["_id"]]
    
    return tags