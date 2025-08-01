import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Temporary in-memory storage for demonstration
_recipes_store = {}

class MockDatabase:
    """Mock database for testing without MongoDB dependency"""
    
    def __init__(self):
        self.recipes = MockCollection()

class MockCollection:
    """Mock MongoDB collection"""
    
    async def insert_one(self, document: Dict[str, Any]) -> "MockInsertResult":
        recipe_id = str(uuid.uuid4())
        document["_id"] = recipe_id
        _recipes_store[recipe_id] = document
        return MockInsertResult(recipe_id)
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "_id" in filter_dict:
            recipe_id = str(filter_dict["_id"])
            return _recipes_store.get(recipe_id)
        return None
    
    def find(self, filter_dict: Dict[str, Any] = None):
        return MockCursor(filter_dict or {})
    
    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        if "_id" in filter_dict:
            recipe_id = str(filter_dict["_id"])
            if recipe_id in _recipes_store:
                if "$set" in update_dict:
                    _recipes_store[recipe_id].update(update_dict["$set"])
        return MockUpdateResult()
    
    async def delete_one(self, filter_dict: Dict[str, Any]):
        if "_id" in filter_dict:
            recipe_id = str(filter_dict["_id"])
            if recipe_id in _recipes_store:
                del _recipes_store[recipe_id]
                return MockDeleteResult(1)
        return MockDeleteResult(0)
    
    def aggregate(self, pipeline: List[Dict[str, Any]]):
        return MockCursor({}, is_aggregate=True)

class MockCursor:
    """Mock MongoDB cursor"""
    
    def __init__(self, filter_dict: Dict[str, Any], is_aggregate: bool = False):
        self.filter_dict = filter_dict
        self.is_aggregate = is_aggregate
        self._skip = 0
        self._limit = None
        self._sort_field = None
        self._sort_direction = 1
    
    def skip(self, count: int):
        self._skip = count
        return self
    
    def limit(self, count: int):
        self._limit = count
        return self
    
    def sort(self, field: str, direction: int = 1):
        self._sort_field = field
        self._sort_direction = direction
        return self
    
    async def to_list(self, length: int = None):
        if self.is_aggregate:
            # For aggregation queries (like getting tags)
            all_tags = set()
            for recipe in _recipes_store.values():
                all_tags.update(recipe.get("tags", []))
            return [{"_id": tag} for tag in sorted(all_tags) if tag]
        
        # Filter recipes
        recipes = list(_recipes_store.values())
        
        # Apply search filters
        if "search" in self.filter_dict:
            search_term = self.filter_dict["search"].lower()
            recipes = [r for r in recipes if 
                      search_term in r.get("title", "").lower() or
                      search_term in r.get("description", "").lower()]
        
        if "tags" in self.filter_dict:
            tag_filter = self.filter_dict["tags"]
            if isinstance(tag_filter, dict) and "$in" in tag_filter:
                filter_tags = tag_filter["$in"]
                recipes = [r for r in recipes if 
                          any(tag in r.get("tags", []) for tag in filter_tags)]
        
        if "difficulty" in self.filter_dict:
            difficulty = self.filter_dict["difficulty"]
            recipes = [r for r in recipes if r.get("difficulty") == difficulty]
        
        # Sort
        if self._sort_field == "created_at":
            recipes.sort(key=lambda x: x.get("created_at", datetime.min), 
                        reverse=(self._sort_direction == -1))
        
        # Apply skip and limit
        if self._skip:
            recipes = recipes[self._skip:]
        if self._limit:
            recipes = recipes[:self._limit]
        
        return recipes

class MockInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class MockUpdateResult:
    def __init__(self):
        self.modified_count = 1

class MockDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count

class Database:
    client = None
    database = None

db = Database()

async def connect_to_mongo():
    """Mock connection to MongoDB"""
    db.database = MockDatabase()

async def close_mongo_connection():
    """Mock close connection"""
    pass

def get_database():
    """Get mock database instance"""
    return db.database