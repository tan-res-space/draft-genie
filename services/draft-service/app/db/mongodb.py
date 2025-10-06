"""
MongoDB client and connection management
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDB:
    """MongoDB client wrapper"""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
            
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                minPoolSize=settings.mongodb_min_pool_size,
                maxPoolSize=settings.mongodb_max_pool_size,
                serverSelectionTimeoutMS=5000,
            )
            
            # Test connection
            await self.client.admin.command("ping")
            
            self.db = self.client[settings.mongodb_database]
            
            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_database}")
            
            # Create indexes
            await self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            logger.info("Disconnecting from MongoDB")
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        """Create database indexes"""
        if not self.db:
            return

        logger.info("Creating MongoDB indexes")

        # Drafts collection indexes
        await self.db.drafts.create_index("speaker_id")
        await self.db.drafts.create_index("draft_id", unique=True)
        await self.db.drafts.create_index("draft_type")
        await self.db.drafts.create_index("created_at")
        await self.db.drafts.create_index([("speaker_id", 1), ("created_at", -1)])

        # Correction vectors collection indexes
        await self.db.correction_vectors.create_index("speaker_id")
        await self.db.correction_vectors.create_index("draft_id")
        await self.db.correction_vectors.create_index("created_at")
        await self.db.correction_vectors.create_index([("speaker_id", 1), ("created_at", -1)])

        logger.info("MongoDB indexes created successfully")

    async def health_check(self) -> bool:
        """Check MongoDB connection health"""
        try:
            if not self.client:
                return False
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False


# Global MongoDB instance
mongodb = MongoDB()


async def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if not mongodb.db:
        raise RuntimeError("MongoDB not connected")
    return mongodb.db

