"""MongoDB client for DraftGenie."""

from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from common.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class MongoDBClient(LoggerMixin):
    """MongoDB client with async support."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_pool_size: int = 100,
        min_pool_size: int = 10,
    ):
        """
        Initialize MongoDB client.

        Args:
            host: MongoDB host
            port: MongoDB port
            database: Database name
            username: Optional username
            password: Optional password
            max_pool_size: Maximum connection pool size
            min_pool_size: Minimum connection pool size
        """
        self.host = host
        self.port = port
        self.database_name = database
        self.username = username
        self.password = password
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size

        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    @property
    def connection_string(self) -> str:
        """Get MongoDB connection string."""
        if self.username and self.password:
            return (
                f"mongodb://{self.username}:{self.password}"
                f"@{self.host}:{self.port}/{self.database_name}"
            )
        return f"mongodb://{self.host}:{self.port}/{self.database_name}"

    async def connect(self) -> None:
        """Connect to MongoDB."""
        if self._client is not None:
            self.log_warning("MongoDB client already connected")
            return

        try:
            self._client = AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                serverSelectionTimeoutMS=5000,
            )

            # Test connection
            await self._client.admin.command("ping")

            self._database = self._client[self.database_name]

            self.log_info(
                "Connected to MongoDB",
                host=self.host,
                port=self.port,
                database=self.database_name,
            )
        except Exception as e:
            self.log_error("Failed to connect to MongoDB", error=e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client is None:
            return

        try:
            self._client.close()
            self._client = None
            self._database = None
            self.log_info("Disconnected from MongoDB")
        except Exception as e:
            self.log_error("Failed to disconnect from MongoDB", error=e)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health."""
        try:
            if self._client is None:
                return {"status": "disconnected", "healthy": False}

            await self._client.admin.command("ping")

            return {
                "status": "connected",
                "healthy": True,
                "host": self.host,
                "port": self.port,
                "database": self.database_name,
            }
        except Exception as e:
            self.log_error("MongoDB health check failed", error=e)
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if self._database is None:
            raise RuntimeError("MongoDB client not connected")
        return self._database

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get the MongoDB client instance."""
        if self._client is None:
            raise RuntimeError("MongoDB client not connected")
        return self._client

    async def create_indexes(self, collection_name: str, indexes: List[Dict[str, Any]]) -> None:
        """
        Create indexes for a collection.

        Args:
            collection_name: Name of the collection
            indexes: List of index specifications
        """
        try:
            collection = self.database[collection_name]
            for index_spec in indexes:
                await collection.create_index(**index_spec)
            self.log_info(
                "Created indexes",
                collection=collection_name,
                count=len(indexes),
            )
        except Exception as e:
            self.log_error(
                "Failed to create indexes",
                error=e,
                collection=collection_name,
            )
            raise

    async def drop_collection(self, collection_name: str) -> None:
        """Drop a collection."""
        try:
            await self.database.drop_collection(collection_name)
            self.log_info("Dropped collection", collection=collection_name)
        except Exception as e:
            self.log_error(
                "Failed to drop collection",
                error=e,
                collection=collection_name,
            )
            raise

    async def list_collections(self) -> List[str]:
        """List all collections in the database."""
        try:
            collections = await self.database.list_collection_names()
            return collections
        except Exception as e:
            self.log_error("Failed to list collections", error=e)
            raise

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        try:
            stats = await self.database.command("collStats", collection_name)
            return {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avg_obj_size": stats.get("avgObjSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0),
            }
        except Exception as e:
            self.log_error(
                "Failed to get collection stats",
                error=e,
                collection=collection_name,
            )
            raise


# Global client instance
_mongodb_client: Optional[MongoDBClient] = None


def get_mongodb_client() -> MongoDBClient:
    """Get the global MongoDB client instance."""
    global _mongodb_client
    if _mongodb_client is None:
        raise RuntimeError("MongoDB client not initialized")
    return _mongodb_client


def init_mongodb_client(
    host: str,
    port: int,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs: Any,
) -> MongoDBClient:
    """Initialize the global MongoDB client."""
    global _mongodb_client
    _mongodb_client = MongoDBClient(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        **kwargs,
    )
    return _mongodb_client

