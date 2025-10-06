"""
API module - FastAPI routers
"""
from app.api.health import router as health_router
from app.api.evaluations import router as evaluations_router
from app.api.metrics import router as metrics_router

__all__ = ["health_router", "evaluations_router", "metrics_router"]

