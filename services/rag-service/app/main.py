"""
FastAPI application - RAG Service
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.database import database
from app.db.qdrant import qdrant
from app.api import health_router, rag_router, dfn_router
from app.events.publisher import event_publisher

# Try to import enhanced logging middleware
try:
    from libs.python.common.logging_middleware import (
        RequestLoggingMiddleware,
        ErrorTrackingMiddleware,
    )
    ENHANCED_MIDDLEWARE_AVAILABLE = True
except ImportError:
    ENHANCED_MIDDLEWARE_AVAILABLE = False

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    try:
        # Connect to PostgreSQL
        await database.connect()
        logger.info("PostgreSQL connected")

        # Connect to Qdrant
        await qdrant.connect()
        logger.info("Qdrant connected")

        # Connect to RabbitMQ
        await event_publisher.connect()
        logger.info("RabbitMQ connected")

        logger.info(f"{settings.app_name} started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    try:
        # Disconnect from PostgreSQL
        await database.disconnect()
        logger.info("PostgreSQL disconnected")

        # Disconnect from Qdrant
        await qdrant.disconnect()
        logger.info("Qdrant disconnected")

        # Disconnect from RabbitMQ
        await event_publisher.disconnect()
        logger.info("RabbitMQ disconnected")

        logger.info(f"{settings.app_name} shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG Service for Draft Genie - LangChain + LangGraph + Gemini",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

# Add enhanced logging middleware if available
if ENHANCED_MIDDLEWARE_AVAILABLE:
    app.add_middleware(ErrorTrackingMiddleware)
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=True,
        log_response_body=False,
        max_body_size=10000,
    )
    logger.info("Enhanced logging middleware enabled")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(health_router)
app.include_router(rag_router)
app.include_router(dfn_router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "extra_data": {
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
            }
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "extra_data": {
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            }
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

