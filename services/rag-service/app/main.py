"""
FastAPI application - RAG Service
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.database import database
from app.db.qdrant import qdrant
from app.api import health_router, rag_router, dfn_router
from app.events.publisher import event_publisher

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


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "detail": "Internal server error",
        "error": str(exc) if settings.debug else "An error occurred",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

