#!/usr/bin/env python3
"""
Production startup script that tries MongoDB first, falls back to mock database.
"""

import os
import logging
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.logging_config import setup_logging, RequestLogger
from app.routers import recipes
from app.routers import ai_import

# Setup logging for production with structured output
setup_logging(
    log_level=settings.log_level,
    use_structured=True  # Always use structured logging in production
)

logger = logging.getLogger("app.production")

# Try to import MongoDB version first
try:
    from app.mongodb_database import connect_to_mongo, close_mongo_connection
    logger.info("Using MongoDB database with Beanie ODM")
    DATABASE_TYPE = "mongodb"
except ImportError:
    from app.mock_database import connect_to_mongo, close_mongo_connection
    logger.warning("Using mock database (in-memory) - MongoDB not available")
    DATABASE_TYPE = "mock"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Production application startup initiated", extra={
        "extra_data": {
            "database_type": DATABASE_TYPE,
            "environment": "production"
        }
    })
    
    try:
        await connect_to_mongo()
        logger.info("Database connected successfully", extra={
            "extra_data": {"database_type": DATABASE_TYPE}
        })
    except Exception as e:
        logger.error("Database connection failed", exc_info=e, extra={
            "extra_data": {"database_type": DATABASE_TYPE}
        })
        
        if DATABASE_TYPE == "mongodb":
            logger.warning("Falling back to mock database")
            try:
                # Import and use mock database as fallback
                from app.mock_database import connect_to_mongo as mock_connect
                await mock_connect()
                logger.info("Mock database initialized successfully")
                global DATABASE_TYPE
                DATABASE_TYPE = "mock_fallback"
            except Exception as fallback_error:
                logger.critical("Mock database fallback also failed", exc_info=fallback_error)
                raise
    
    logger.info("Production application startup completed")
    yield
    
    # Shutdown
    logger.info("Production application shutdown initiated")
    try:
        await close_mongo_connection()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error("Error closing database connection", exc_info=e)
    
    logger.info("Production application shutdown completed")

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Recipe Management Application - Easy recipe storage with AI-powered import",
    lifespan=lifespan
)

# Production request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log incoming request
    RequestLogger.log_request(
        logger,
        method=request.method,
        url=str(request.url),
        request_id=request_id,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Log response
        RequestLogger.log_response(
            logger,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            response_time=response_time,
            request_id=request_id
        )
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("Request processing failed", exc_info=e, extra={
            "method": request.method,
            "url": str(request.url),
            "response_time": response_time,
            "request_id": request_id
        })
        raise

# Mount static files
logger.info("Mounting static files")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
logger.info("Including API routers")
app.include_router(recipes.router)
app.include_router(ai_import.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    logger.debug("Serving home page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "database": DATABASE_TYPE,
        "timestamp": time.time()
    }

@app.get("/api/info")
async def app_info():
    """Application information endpoint"""
    logger.debug("Application info requested")
    return {
        "title": settings.app_title,
        "version": settings.app_version,
        "database_type": DATABASE_TYPE,
        "environment": "production",
        "features": [
            "Recipe CRUD operations",
            "AI-powered recipe import",
            "Intelligent image extraction",
            "Search and filtering",
            "TikTok URL support",
            "Tag-based categorization",
            "Responsive UI",
            "RESTful API",
            "Structured logging"
        ]
    }

# Production error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for production"""
    request_id = getattr(request.state, 'request_id', None)
    logger.error("Unhandled exception in production", exc_info=exc, extra={
        "url": str(request.url),
        "method": request.method,
        "request_id": request_id,
        "extra_data": {
            "environment": "production",
            "database_type": DATABASE_TYPE
        }
    })
    
    return {
        "error": "Internal server error",
        "request_id": request_id,
        "status_code": 500,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting production application with uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000)