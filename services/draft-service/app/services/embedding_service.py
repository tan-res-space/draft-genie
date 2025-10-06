"""
Embedding service - Generate embeddings using Gemini API
"""
from typing import List, Optional
import google.generativeai as genai
from qdrant_client.models import PointStruct

from app.models.correction_vector import CorrectionVectorModel, CorrectionPattern
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Gemini API"""

    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        logger.info(f"Initialized Gemini embedding service with model {self.model_name}")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Gemini API
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            
            # Generate embedding using Gemini
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document",
            )
            
            embedding = result["embedding"]
            logger.debug(f"Generated embedding with dimension {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_correction_embedding(
        self, patterns: List[CorrectionPattern]
    ) -> List[float]:
        """
        Generate embedding for correction patterns
        
        Combines all correction patterns into a single text representation
        and generates an embedding
        
        Args:
            patterns: List of correction patterns
            
        Returns:
            Embedding vector
        """
        if not patterns:
            logger.warning("No patterns provided for embedding generation")
            return [0.0] * settings.gemini_embedding_dimension

        # Create text representation of patterns
        pattern_texts = []
        for pattern in patterns:
            # Format: "original -> corrected (category)"
            pattern_text = f"{pattern.original} -> {pattern.corrected} ({pattern.category})"
            pattern_texts.append(pattern_text)

        # Combine all patterns
        combined_text = " | ".join(pattern_texts)
        
        logger.info(f"Generating embedding for {len(patterns)} correction patterns")
        return self.generate_embedding(combined_text)

    def create_qdrant_point(
        self,
        vector_model: CorrectionVectorModel,
        embedding: List[float],
    ) -> PointStruct:
        """
        Create a Qdrant point from correction vector and embedding
        
        Args:
            vector_model: Correction vector model
            embedding: Embedding vector
            
        Returns:
            Qdrant PointStruct
        """
        # Create payload with metadata
        payload = {
            "vector_id": vector_model.vector_id,
            "speaker_id": vector_model.speaker_id,
            "draft_id": vector_model.draft_id,
            "total_corrections": vector_model.total_corrections,
            "unique_patterns": vector_model.unique_patterns,
            "category_counts": vector_model.category_counts,
            "created_at": vector_model.created_at.isoformat(),
        }

        # Create Qdrant point
        point = PointStruct(
            id=vector_model.vector_id,
            vector=embedding,
            payload=payload,
        )

        logger.info(f"Created Qdrant point for vector {vector_model.vector_id}")
        return point

    async def search_similar_patterns(
        self,
        query_patterns: List[CorrectionPattern],
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> List[dict]:
        """
        Search for similar correction patterns in Qdrant
        
        Args:
            query_patterns: Patterns to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar patterns with scores
        """
        from app.db.qdrant import qdrant

        # Generate embedding for query patterns
        query_embedding = self.generate_correction_embedding(query_patterns)

        # Search in Qdrant
        results = await qdrant.search_vectors(
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
        )

        logger.info(f"Found {len(results)} similar patterns")
        return results

    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings


# Global embedding service instance
embedding_service = EmbeddingService()

