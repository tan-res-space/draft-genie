"""
Qdrant vector database client
"""
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantDB:
    """Qdrant vector database wrapper"""

    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.qdrant_collection_name

    async def connect(self) -> None:
        """Connect to Qdrant"""
        try:
            logger.info(f"Connecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )

            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.qdrant_vector_size,
                        distance=Distance.COSINE,
                    ),
                )

            logger.info("Successfully connected to Qdrant")

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from Qdrant"""
        if self.client:
            logger.info("Disconnecting from Qdrant")
            self.client.close()
            self.client = None

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        speaker_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            speaker_id: Optional speaker ID filter
            
        Returns:
            List of search results with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            # Build filter
            query_filter = None
            if speaker_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="speaker_id",
                            match=MatchValue(value=speaker_id),
                        )
                    ]
                )

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                })

            logger.info(f"Found {len(formatted_results)} similar vectors")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

    async def get_speaker_vectors(
        self,
        speaker_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all vectors for a speaker
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of results
            
        Returns:
            List of vectors
        """
        if not self.client:
            raise RuntimeError("Qdrant not connected")

        try:
            # Scroll through all points for speaker
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="speaker_id",
                            match=MatchValue(value=speaker_id),
                        )
                    ]
                ),
                limit=limit,
            )

            # Format results
            formatted_results = []
            for point in results:
                formatted_results.append({
                    "id": point.id,
                    "payload": point.payload,
                })

            logger.info(f"Retrieved {len(formatted_results)} vectors for speaker {speaker_id}")
            return formatted_results

        except Exception as e:
            logger.error(f"Error getting speaker vectors: {e}")
            raise

    async def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            if not self.client:
                return False
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant instance
qdrant = QdrantDB()

