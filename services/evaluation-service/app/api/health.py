"""
Health check endpoints
"""
from fastapi import APIRouter, status
from typing import Dict, Any

from app.core.config import settings
from app.db.database import database

router = APIRouter(tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Basic health check"""
    return {"status": "healthy"}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe - checks dependencies"""
    dependencies = {
        "database": await database.health_check(),
    }

    all_healthy = all(dependencies.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_healthy else "not ready",
        "dependencies": dependencies,
    }

