from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from fastapi import HTTPException

from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate
from app.repositories.recipe_repository import BaseRepository, recipe_repository


class RecipeService:
    """Service layer for recipe business logic with proper error handling"""
    
    def __init__(self, repository: BaseRepository = recipe_repository):
        self.repository = repository
    
    async def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        """Create a new recipe with business logic validation"""
        # Business validation
        if not recipe_data.title.strip():
            raise HTTPException(status_code=400, detail="Recipe title cannot be empty")
        
        if not recipe_data.ingredients:
            raise HTTPException(status_code=400, detail="Recipe must have at least one ingredient")
        
        if not recipe_data.instructions:
            raise HTTPException(status_code=400, detail="Recipe must have at least one instruction")
        
        try:
            return await self.repository.create(recipe_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")
    
    async def get_recipe_by_id(self, recipe_id: str) -> Recipe:
        """Get recipe by ID with proper error handling"""
        try:
            object_id = PydanticObjectId(recipe_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid recipe ID format")
        
        recipe = await self.repository.get_by_id(object_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return recipe
    
    async def get_recipes(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        tags: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Recipe]:
        """Get recipes with filtering, search, and pagination"""
        # Validate parameters
        if skip < 0:
            raise HTTPException(status_code=400, detail="Skip parameter must be non-negative")
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if difficulty and difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(status_code=400, detail="Invalid difficulty level")
        
        # Build filters
        filters = {}
        if difficulty:
            filters["difficulty"] = difficulty
        
        if tags:
            # Parse comma-separated tags
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                filters["tags"] = tag_list
        
        if search:
            filters["search"] = search.strip()
        
        try:
            return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve recipes: {str(e)}")
    
    async def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Recipe:
        """Update recipe with business logic validation"""
        try:
            object_id = PydanticObjectId(recipe_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid recipe ID format")
        
        # Check if recipe exists
        existing_recipe = await self.repository.get_by_id(object_id)
        if not existing_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Business validation for updates
        if recipe_data.title is not None and not recipe_data.title.strip():
            raise HTTPException(status_code=400, detail="Recipe title cannot be empty")
        
        if recipe_data.ingredients is not None and not recipe_data.ingredients:
            raise HTTPException(status_code=400, detail="Recipe must have at least one ingredient")
        
        if recipe_data.instructions is not None and not recipe_data.instructions:
            raise HTTPException(status_code=400, detail="Recipe must have at least one instruction")
        
        try:
            updated_recipe = await self.repository.update(object_id, recipe_data)
            if not updated_recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")
            return updated_recipe
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")
    
    async def delete_recipe(self, recipe_id: str) -> bool:
        """Delete recipe with proper error handling"""
        try:
            object_id = PydanticObjectId(recipe_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid recipe ID format")
        
        try:
            deleted = await self.repository.delete(object_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Recipe not found")
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")
    
    async def search_recipes(
        self,
        query: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Recipe]:
        """Search recipes with validation"""
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        if skip < 0:
            raise HTTPException(status_code=400, detail="Skip parameter must be non-negative")
        
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        try:
            return await self.repository.search(query.strip(), skip=skip, limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        try:
            return await self.repository.get_all_tags()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve tags: {str(e)}")
    
    async def get_recipe_count(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[str] = None
    ) -> int:
        """Get count of recipes with optional filters"""
        filters = {}
        if difficulty:
            if difficulty not in ["easy", "medium", "hard"]:
                raise HTTPException(status_code=400, detail="Invalid difficulty level")
            filters["difficulty"] = difficulty
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                filters["tags"] = tag_list
        
        try:
            return await self.repository.count(filters)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to count recipes: {str(e)}")
    
    async def get_recipes_by_difficulty(self, difficulty: str) -> List[Recipe]:
        """Get recipes filtered by difficulty with validation"""
        if difficulty not in ["easy", "medium", "hard"]:
            raise HTTPException(status_code=400, detail="Invalid difficulty level")
        
        try:
            return await self.repository.get_recipes_by_difficulty(difficulty)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve recipes: {str(e)}")
    
    async def get_recent_recipes(self, limit: int = 10) -> List[Recipe]:
        """Get recent recipes with validation"""
        if limit <= 0 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        try:
            return await self.repository.get_recent_recipes(limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve recent recipes: {str(e)}")


# Singleton instance
recipe_service = RecipeService()