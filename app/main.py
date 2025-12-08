"""
Nexalar ML Service - FastAPI Application
Main entry point for the ML microservice
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime

from app.config import settings
from app.utils.logger import logger
from app.services.model_loader import model_loader

# Import routers
from app.routers import health, persona, notification, insight, pomodoro


# Startup time tracking
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Load models at startup, cleanup at shutdown
    """
    # Startup
    logger.info("="*60)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Environment: {settings.environment}")
    logger.info("="*60)
    
    # Load all ML models
    try:
        model_status = model_loader.load_all_models()
        
        if not any(model_status.values()):
            logger.error("❌ No models loaded! Service may not work properly.")
        
        # Store in app state
        app.state.model_status = model_status
        app.state.startup_time = startup_time
        
        logger.info("✅ Application startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ML service...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Machine Learning microservice for Nexalar Learning Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.is_production else settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
    
    # Add timing header
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include routers
app.include_router(health.router, tags=["Health Check"])
app.include_router(persona.router, prefix="/predict", tags=["Persona Prediction"])
app.include_router(notification.router, prefix="/notification", tags=["Notification"])
app.include_router(insight.router, prefix="/insight", tags=["Insights"])
app.include_router(pomodoro.router, prefix="/pomodoro", tags=["Pomodoro"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Nexalar ML Service API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
