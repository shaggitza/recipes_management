import logging
import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.logging_config import setup_logging, RequestLogger
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import recipes
from app.routers import ai_import

# Setup logging as early as possible
setup_logging(
    log_level=settings.log_level,
    use_structured=settings.use_structured_logging
)

logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup initiated")
    try:
        await connect_to_mongo()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error("Failed to connect to database during startup", exc_info=e)
        raise
    
    logger.info("Application startup completed")
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    try:
        await close_mongo_connection()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error("Error closing database connection during shutdown", exc_info=e)
    
    logger.info("Application shutdown completed")

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan
)

# Request logging middleware
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
        "environment": settings.environment
    }

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, 'request_id', None)
    logger.error("Unhandled exception", exc_info=exc, extra={
        "url": str(request.url),
        "method": request.method,
        "request_id": request_id
    })
    
    return {
        "error": "Internal server error",
        "request_id": request_id,
        "status_code": 500
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application with uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000)