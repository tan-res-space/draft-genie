"""Qdrant vector database client for DraftGenie."""

from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from common.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class QdrantClientWrapper(LoggerMixin):
    """Qdrant client wrapper with async support."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant host
            port: Qdrant port
            api_key: Optional API key
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.timeout = timeout

        self._client: Optional[QdrantClient] = None

    def connect(self) -> None:
        """Connect to Qdrant."""
        if self._client is not None:
            self.log_warning("Qdrant client already connected")
            return

        try:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                timeout=self.timeout,
            )

            # Test connection
            self._client.get_collections()

            self.log_info(
                "Connected to Qdrant",
                host=self.host,
                port=self.port,
            )
        except Exception as e:
            self.log_error("Failed to connect to Qdrant", error=e)
            raise

    def disconnect(self) -> None:
        """Disconnect from Qdrant."""
        if self._client is None:
            return

        try:
            self._client.close()
            self._client = None
            self.log_info("Disconnected from Qdrant")
        except Exception as e:
            self.log_error("Failed to disconnect from Qdrant", error=e)
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health."""
        try:
            if self._client is None:
                return {"status": "disconnected", "healthy": False}

            collections = self._client.get_collections()

            return {
                "status": "connected",
                "healthy": True,
                "host": self.host,
                "port": self.port,
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            self.log_error("Qdrant health check failed", error=e)
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    @property
    def client(self) -> QdrantClient:
        """Get the Qdrant client instance."""
        if self._client is None:
            raise RuntimeError("Qdrant client not connected")
        return self._client

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
        on_disk_payload: bool = False,
    ) -> None:
        """
        Create a collection.

        Args:
            collection_name: Name of the collection
            vector_size: Size of the vectors
            distance: Distance metric (Cosine, Euclid, Dot)
            on_disk_payload: Store payload on disk
        """
        try:
            # Check if collection exists
            try:
                self.client.get_collection(collection_name)
                self.log_info("Collection already exists", collection=collection_name)
                return
            except UnexpectedResponse:
                pass

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=getattr(models.Distance, distance.upper()),
                ),
                on_disk_payload=on_disk_payload,
            )

            self.log_info(
                "Created Qdrant collection",
                collection=collection_name,
                vector_size=vector_size,
                distance=distance,
            )
        except Exception as e:
            self.log_error(
                "Failed to create Qdrant collection",
                error=e,
                collection=collection_name,
            )
            raise

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            self.log_info("Deleted Qdrant collection", collection=collection_name)
        except Exception as e:
            self.log_error(
                "Failed to delete Qdrant collection",
                error=e,
                collection=collection_name,
            )
            raise

    def upsert_vectors(
        self,
        collection_name: str,
        points: List[models.PointStruct],
    ) -> None:
        """
        Upsert vectors into a collection.

        Args:
            collection_name: Name of the collection
            points: List of points to upsert
        """
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            self.log_info(
                "Upserted vectors",
                collection=collection_name,
                count=len(points),
            )
        except Exception as e:
            self.log_error(
                "Failed to upsert vectors",
                error=e,
                collection=collection_name,
            )
            raise

    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        query_filter: Optional[models.Filter] = None,
    ) -> List[models.ScoredPoint]:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            query_filter: Optional filter

        Returns:
            List of scored points
        """
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
            self.log_info(
                "Searched vectors",
                collection=collection_name,
                results_count=len(results),
            )
            return results
        except Exception as e:
            self.log_error(
                "Failed to search vectors",
                error=e,
                collection=collection_name,
            )
            raise

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            self.log_error(
                "Failed to get collection info",
                error=e,
                collection=collection_name,
            )
            raise

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            self.log_error("Failed to list collections", error=e)
            raise


# Global client instance
_qdrant_client: Optional[QdrantClientWrapper] = None


def get_qdrant_client() -> QdrantClientWrapper:
    """Get the global Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        raise RuntimeError("Qdrant client not initialized")
    return _qdrant_client


def init_qdrant_client(
    host: str,
    port: int,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> QdrantClientWrapper:
    """Initialize the global Qdrant client."""
    global _qdrant_client
    _qdrant_client = QdrantClientWrapper(
        host=host,
        port=port,
        api_key=api_key,
        **kwargs,
    )
    return _qdrant_client

