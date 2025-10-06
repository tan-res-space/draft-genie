"""
API module - FastAPI routers
"""
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.dfn import router as dfn_router

__all__ = ["health_router", "rag_router", "dfn_router"]

