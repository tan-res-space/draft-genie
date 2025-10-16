"""
Health check endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, status
from datetime import datetime

from app.core.config import settings
from app.db.database import database
from app.db.qdrant import qdrant

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns service status and basic information
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    
    Checks if service is ready to accept requests
    Verifies all dependencies are available
    """
    postgres_healthy = await database.health_check()
    qdrant_healthy = await qdrant.health_check()

    all_healthy = postgres_healthy and qdrant_healthy

    response = {
        "status": "ready" if all_healthy else "not_ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "postgresql": {
                "status": "healthy" if postgres_healthy else "unhealthy",
                "required": True,
            },
            "qdrant": {
                "status": "healthy" if qdrant_healthy else "unhealthy",
                "required": True,
            },
        },
    }
    
    if not all_healthy:
        return response
    
    return response


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint
    
    Checks if service is alive and running
    """
    return {
        "status": "alive",
        "service": settings.app_name,
        "timestamp": datetime.utcnow().isoformat(),
    }

