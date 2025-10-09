"""
Draft Service - Main FastAPI application
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.mongodb import mongodb
from app.db.qdrant import qdrant
from app.events.publisher import event_publisher
from app.events.consumer import event_consumer
from app.events.handlers import EventHandler
from app.services.draft_service import get_draft_service
from app.repositories.draft_repository import DraftRepository
from app.api import health_router, drafts_router, vectors_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        # Connect to MongoDB
        await mongodb.connect()

        # Connect to Qdrant
        await qdrant.connect()

        # Connect to RabbitMQ (publisher)
        await event_publisher.connect()

        # Connect to RabbitMQ (consumer)
        await event_consumer.connect()

        # Start consuming events
        db = mongodb.db
        if db is not None:
            draft_repository = DraftRepository(db)
            draft_service = get_draft_service(draft_repository)
            event_handler = EventHandler(draft_service)

            # Start consuming in background
            import asyncio
            asyncio.create_task(event_consumer.start_consuming(event_handler.handle_event))
            logger.info("Started consuming events from RabbitMQ")

        logger.info("All dependencies connected successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    try:
        # Disconnect from RabbitMQ
        await event_consumer.disconnect()
        await event_publisher.disconnect()

        # Disconnect from MongoDB
        await mongodb.disconnect()

        # Disconnect from Qdrant
        await qdrant.disconnect()

        logger.info("All dependencies disconnected successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Draft Service API",
    description="API for ingesting and processing speaker drafts",
    version=settings.app_version,
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


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(health_router)
app.include_router(drafts_router)
app.include_router(vectors_router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": settings.docs_url,
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

