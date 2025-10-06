"""
API module - FastAPI routers
"""
from app.api.health import router as health_router
from app.api.drafts import router as drafts_router
from app.api.vectors import router as vectors_router

__all__ = ["health_router", "drafts_router", "vectors_router"]

