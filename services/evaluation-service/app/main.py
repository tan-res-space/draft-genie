"""
FastAPI application - Evaluation Service
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.database import database
from app.api import health_router, evaluations_router, metrics_router
from app.events.consumer import event_consumer
from app.events.publisher import event_publisher
from app.events.handler import handle_event

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

        # Connect to RabbitMQ publisher
        await event_publisher.connect()
        logger.info("RabbitMQ publisher connected")

        # Connect to RabbitMQ consumer and start consuming
        await event_consumer.connect()
        logger.info("RabbitMQ consumer connected")

        # Start consuming events in background
        asyncio.create_task(event_consumer.start_consuming(handle_event))
        logger.info("Event consumer started")

        logger.info(f"{settings.app_name} started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    try:
        # Disconnect from RabbitMQ
        await event_consumer.disconnect()
        logger.info("RabbitMQ consumer disconnected")

        await event_publisher.disconnect()
        logger.info("RabbitMQ publisher disconnected")

        # Disconnect from PostgreSQL
        await database.disconnect()
        logger.info("PostgreSQL disconnected")

        logger.info(f"{settings.app_name} shut down successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evaluation Service for Draft Genie - Draft comparison and quality metrics",
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
app.include_router(evaluations_router)
app.include_router(metrics_router)


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

