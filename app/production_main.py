#!/usr/bin/env python3
"""
Production startup script that tries MongoDB first, falls back to mock database.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.routers import recipes

# Try to import MongoDB version first
try:
    from app.mongodb_database import connect_to_mongo, close_mongo_connection
    print("🔧 Using MongoDB database")
    DATABASE_TYPE = "mongodb"
except ImportError:
    from app.mock_database import connect_to_mongo, close_mongo_connection
    print("🔧 Using mock database (in-memory)")
    DATABASE_TYPE = "mock"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
        print(f"✅ Database ({DATABASE_TYPE}) connected successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        if DATABASE_TYPE == "mongodb":
            print("🔄 Falling back to mock database...")
            # Import and use mock database as fallback
            from app.mock_database import connect_to_mongo as mock_connect
            await mock_connect()
            print("✅ Mock database initialized")
    
    yield
    
    # Shutdown
    await close_mongo_connection()

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Recipe Management Application - Easy recipe storage with TikTok integration support",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(recipes.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "database": DATABASE_TYPE
    }

@app.get("/api/info")
async def app_info():
    """Application information endpoint"""
    return {
        "title": settings.app_title,
        "version": settings.app_version,
        "database_type": DATABASE_TYPE,
        "features": [
            "Recipe CRUD operations",
            "Search and filtering",
            "TikTok URL support",
            "Tag-based categorization",
            "Responsive UI",
            "RESTful API"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)