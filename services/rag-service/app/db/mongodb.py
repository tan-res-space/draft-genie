"""
MongoDB client using Motor (async driver)
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDB:
    """MongoDB client wrapper"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_uri}")
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                minPoolSize=settings.mongodb_min_pool_size,
                maxPoolSize=settings.mongodb_max_pool_size,
            )
            self.db = self.client[settings.mongodb_database]

            # Test connection
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            logger.info("Disconnecting from MongoDB")
            self.client.close()
            self.client = None
            self.db = None

    async def _create_indexes(self) -> None:
        """Create database indexes"""
        if self.db is None:
            return

        try:
            # DFN indexes
            await self.db.dfns.create_index("dfn_id", unique=True)
            await self.db.dfns.create_index("speaker_id")
            await self.db.dfns.create_index("session_id")
            await self.db.dfns.create_index("created_at")
            await self.db.dfns.create_index([("speaker_id", 1), ("created_at", -1)])

            # RAG session indexes
            await self.db.rag_sessions.create_index("session_id", unique=True)
            await self.db.rag_sessions.create_index("speaker_id")
            await self.db.rag_sessions.create_index("created_at")

            logger.info("Created MongoDB indexes")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def health_check(self) -> bool:
        """Check MongoDB health"""
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
    """Dependency to get database instance"""
    if not mongodb.db:
        raise RuntimeError("MongoDB not connected")
    return mongodb.db

