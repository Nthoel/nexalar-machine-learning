"""
Health check endpoint for monitoring and Railway deployment
"""

from fastapi import APIRouter, Request
from datetime import datetime, timedelta
import time
import psutil
import os

from app.config import settings
from app.schemas.responses import HealthResponse
from app.utils.logger import logger


router = APIRouter()


def get_uptime(start_time: float) -> str:
    """Calculate uptime from start time"""
    uptime_seconds = time.time() - start_time
    uptime_delta = timedelta(seconds=int(uptime_seconds))
    
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"


def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return round(memory_info.rss / 1024 / 1024, 2)  # Convert to MB
    except:
        return 0.0


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and model status"
)
async def health_check(request: Request):
    """
    Health check endpoint for monitoring
    
    Returns:
        - Service status
        - Model load status
        - Uptime
        - Memory usage
    """
    
    # Get model status from app state
    model_status = getattr(request.app.state, "model_status", {})
    startup_time = getattr(request.app.state, "startup_time", time.time())
    
    # Calculate uptime
    uptime_str = get_uptime(startup_time)
    
    # Get memory usage
    memory_mb = get_memory_usage()
    
    # Determine overall status
    all_models_loaded = all(model_status.values()) if model_status else False
    status = "healthy" if all_models_loaded else "degraded"
    
    response = {
        "status": status,
        "version": settings.app_version,
        "models_loaded": model_status,
        "uptime": uptime_str,
        "memory_usage_mb": memory_mb,
        "timestamp": datetime.utcnow()
    }
    
    logger.debug(f"💚 Health check: {status}")
    
    return response


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if service is ready to accept requests"
)
async def readiness_check(request: Request):
    """
    Readiness probe for Kubernetes/Railway
    Returns 200 if all models are loaded
    """
    
    model_status = getattr(request.app.state, "model_status", {})
    
    if not model_status or not all(model_status.values()):
        logger.warning("⚠️  Service not ready - models not loaded")
        return {"ready": False, "models": model_status}
    
    return {"ready": True}


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if service is alive"
)
async def liveness_check():
    """
    Liveness probe for Kubernetes/Railway
    Simple check if the service is running
    """
    return {"alive": True}
