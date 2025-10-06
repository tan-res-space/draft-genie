"""
Qdrant client and connection management
"""
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantDB:
    """Qdrant client wrapper"""

    def __init__(self) -> None:
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.qdrant_collection_name

    async def connect(self) -> None:
        """Connect to Qdrant"""
        try:
            logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")
            
            # Create Qdrant client
            if settings.qdrant_api_key:
                self.client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                )
            else:
                self.client = QdrantClient(url=settings.qdrant_url)
            
            # Test connection by getting collections
            collections = self.client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Collections: {len(collections.collections)}")
            
            # Create collection if it doesn't exist
            await self._create_collection()
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Qdrant"""
        if self.client:
            logger.info("Disconnecting from Qdrant")
            self.client.close()
            self.client = None
            logger.info("Disconnected from Qdrant")

    async def _create_collection(self) -> None:
        """Create Qdrant collection if it doesn't exist"""
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant_vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                
                logger.info(f"Qdrant collection created: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
            raise

    async def upsert_vectors(
        self,
        points: List[PointStruct],
    ) -> None:
        """Upsert vectors to Qdrant"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Upserted {len(points)} vectors to Qdrant")
        except Exception as e:
            logger.error(f"Failed to upsert vectors to Qdrant: {e}")
            raise

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in Qdrant"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
            )
            
            results = [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in search_result
            ]
            
            logger.info(f"Found {len(results)} similar vectors in Qdrant")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors in Qdrant: {e}")
            raise

    async def delete_vectors(self, point_ids: List[str]) -> None:
        """Delete vectors from Qdrant"""
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
            )
            logger.info(f"Deleted {len(point_ids)} vectors from Qdrant")
        except Exception as e:
            logger.error(f"Failed to delete vectors from Qdrant: {e}")
            raise

    async def health_check(self) -> bool:
        """Check Qdrant connection health"""
        try:
            if not self.client:
                return False
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant instance
qdrant = QdrantDB()

