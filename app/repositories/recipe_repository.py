from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from app.models.recipe import Recipe, RecipeCreate, RecipeUpdate


class BaseRepository(ABC):
    """Abstract base repository interface"""
    
    @abstractmethod
    async def create(self, data: RecipeCreate) -> Recipe:
        """Create a new recipe"""
        pass
    
    @abstractmethod
    async def get_by_id(self, recipe_id: PydanticObjectId) -> Optional[Recipe]:
        """Get recipe by ID"""
        pass
    
    @abstractmethod
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Recipe]:
        """Get recipes with optional filtering and pagination"""
        pass
    
    @abstractmethod
    async def update(self, recipe_id: PydanticObjectId, data: RecipeUpdate) -> Optional[Recipe]:
        """Update recipe by ID"""
        pass
    
    @abstractmethod
    async def delete(self, recipe_id: PydanticObjectId) -> bool:
        """Delete recipe by ID"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 10
    ) -> List[Recipe]:
        """Search recipes by text"""
        pass
    
    @abstractmethod
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count recipes with optional filters"""
        pass


class RecipeRepository(BaseRepository):
    """Beanie-based recipe repository with proper query patterns"""
    
    async def create(self, data: RecipeCreate) -> Recipe:
        """Create a new recipe using Beanie patterns"""
        recipe = Recipe(**data.model_dump())
        return await recipe.insert()
    
    async def get_by_id(self, recipe_id: PydanticObjectId) -> Optional[Recipe]:
        """Get recipe by ID using Beanie query"""
        return await Recipe.get(recipe_id)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Recipe]:
        """Get recipes with filtering and pagination using Beanie query builder"""
        query_conditions = []
        
        if filters:
            # Build query conditions
            if "difficulty" in filters:
                query_conditions.append(Recipe.difficulty == filters["difficulty"])
            
            if "tags" in filters:
                # Support both single tag and multiple tags
                tags = filters["tags"]
                if isinstance(tags, str):
                    tags = [tags]
                query_conditions.append(Recipe.tags.in_(tags))
            
            if "meal_times" in filters:
                # Support both single meal_time and multiple meal_times
                meal_times = filters["meal_times"]
                if isinstance(meal_times, str):
                    meal_times = [meal_times]
                query_conditions.append(Recipe.meal_times.in_(meal_times))
            
            if "search" in filters:
                # Use text search or regex for multiple fields
                search_term = filters["search"]
                query_conditions.append({
                    "$or": [
                        {"title": {"$regex": search_term, "$options": "i"}},
                        {"description": {"$regex": search_term, "$options": "i"}},
                        {"ingredients.name": {"$regex": search_term, "$options": "i"}}
                    ]
                })
        
        # Apply all conditions to the query
        if query_conditions:
            if len(query_conditions) == 1:
                query = Recipe.find(query_conditions[0])
            else:
                query = Recipe.find({"$and": query_conditions})
        else:
            query = Recipe.find()
        
        return await query.sort(-Recipe.created_at).skip(skip).limit(limit).to_list()
    
    async def update(self, recipe_id: PydanticObjectId, data: RecipeUpdate) -> Optional[Recipe]:
        """Update recipe using Beanie's proper update patterns"""
        recipe = await self.get_by_id(recipe_id)
        if not recipe:
            return None
        
        # Use Beanie's built-in update method with proper field handling
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            return recipe
        
        # Update using Beanie's set method for atomic updates
        await recipe.set(update_data)
        return recipe
    
    async def delete(self, recipe_id: PydanticObjectId) -> bool:
        """Delete recipe using Beanie patterns"""
        recipe = await self.get_by_id(recipe_id)
        if not recipe:
            return False
        
        await recipe.delete()
        return True
    
    async def search(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 10
    ) -> List[Recipe]:
        """Full-text search using MongoDB text search or regex"""
        # Try MongoDB text search first, fall back to regex
        try:
            # Use MongoDB's text search if available
            recipes = await Recipe.find(
                {"$text": {"$search": query}}
            ).sort(-Recipe.created_at).skip(skip).limit(limit).to_list()
            
            if recipes:
                return recipes
        except Exception:
            # Fall back to regex search across multiple fields
            pass
        
        # Regex-based search across title, description, and ingredients
        return await Recipe.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"ingredients.name": {"$regex": query, "$options": "i"}}
            ]
        }).sort(-Recipe.created_at).skip(skip).limit(limit).to_list()
    
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags using Beanie aggregation"""
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sort": {"_id": 1}}
        ]
        
        result = await Recipe.aggregate(pipeline).to_list()
        return [doc["_id"] for doc in result if doc.get("_id")]
    
    async def get_all_meal_times(self) -> List[str]:
        """Get all unique meal times using Beanie aggregation"""
        pipeline = [
            {"$unwind": "$meal_times"},
            {"$group": {"_id": "$meal_times"}},
            {"$sort": {"_id": 1}}
        ]
        
        result = await Recipe.aggregate(pipeline).to_list()
        return [doc["_id"] for doc in result if doc.get("_id")]
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count recipes with optional filters"""
        query_conditions = []
        
        if filters:
            if "difficulty" in filters:
                query_conditions.append(Recipe.difficulty == filters["difficulty"])
            if "tags" in filters:
                tags = filters["tags"]
                if isinstance(tags, str):
                    tags = [tags]
                query_conditions.append(Recipe.tags.in_(tags))
            if "meal_times" in filters:
                meal_times = filters["meal_times"]
                if isinstance(meal_times, str):
                    meal_times = [meal_times]
                query_conditions.append(Recipe.meal_times.in_(meal_times))
        
        # Apply all conditions to the query
        if query_conditions:
            if len(query_conditions) == 1:
                query = Recipe.find(query_conditions[0])
            else:
                query = Recipe.find({"$and": query_conditions})
        else:
            query = Recipe.find()
        
        return await query.count()
    
    async def get_recipes_by_difficulty(self, difficulty: str) -> List[Recipe]:
        """Get recipes filtered by difficulty level"""
        return await Recipe.find(Recipe.difficulty == difficulty).sort(-Recipe.created_at).to_list()
    
    async def get_recipes_by_tags(self, tags: List[str]) -> List[Recipe]:
        """Get recipes that contain any of the specified tags"""
        return await Recipe.find(Recipe.tags.in_(tags)).sort(-Recipe.created_at).to_list()
    
    async def get_recipes_by_meal_times(self, meal_times: List[str]) -> List[Recipe]:
        """Get recipes that contain any of the specified meal times"""
        return await Recipe.find(Recipe.meal_times.in_(meal_times)).sort(-Recipe.created_at).to_list()
    
    async def get_recent_recipes(self, limit: int = 10) -> List[Recipe]:
        """Get the most recently created recipes"""
        return await Recipe.find().sort(-Recipe.created_at).limit(limit).to_list()


# Singleton instance
recipe_repository = RecipeRepository()