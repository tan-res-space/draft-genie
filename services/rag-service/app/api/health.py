"""
Health check endpoints
"""
from fastapi import APIRouter, status
from app.db.mongodb import mongodb
from app.db.qdrant import qdrant
from app.clients.speaker_client import speaker_client
from app.clients.draft_client import draft_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "rag-service",
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """
    Readiness check - verifies all dependencies are available
    """
    mongodb_healthy = await mongodb.health_check()
    qdrant_healthy = await qdrant.health_check()
    speaker_service_healthy = await speaker_client.health_check()
    draft_service_healthy = await draft_client.health_check()

    all_healthy = all([
        mongodb_healthy,
        qdrant_healthy,
        speaker_service_healthy,
        draft_service_healthy,
    ])

    if not all_healthy:
        logger.warning("Readiness check failed")
        return {
            "status": "not_ready",
            "dependencies": {
                "mongodb": mongodb_healthy,
                "qdrant": qdrant_healthy,
                "speaker_service": speaker_service_healthy,
                "draft_service": draft_service_healthy,
            },
        }

    return {
        "status": "ready",
        "dependencies": {
            "mongodb": mongodb_healthy,
            "qdrant": qdrant_healthy,
            "speaker_service": speaker_service_healthy,
            "draft_service": draft_service_healthy,
        },
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict:
    """Liveness check - verifies service is alive"""
    return {
        "status": "alive",
        "service": "rag-service",
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict:
    """Root endpoint"""
    return {
        "service": "rag-service",
        "version": "0.1.0",
        "status": "running",
    }

