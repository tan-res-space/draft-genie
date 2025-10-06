"""
Similarity Service - Calculates semantic similarity using sentence transformers
"""
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimilarityService:
    """Service for calculating semantic similarity"""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize similarity service
        
        Args:
            model_name: Name of sentence transformer model
        """
        self.model_name = model_name or settings.sentence_transformer_model
        self.model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Uses cosine similarity of sentence embeddings
        Higher is better (0-1 scale)
        
        Args:
            text1: First text (IFN)
            text2: Second text (DFN)
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if not self.model:
                logger.warning("Model not loaded, returning default similarity")
                return 0.7  # Default fallback
            
            # Generate embeddings
            embedding1 = self.model.encode(text1, convert_to_tensor=False)
            embedding2 = self.model.encode(text2, convert_to_tensor=False)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(embedding1, embedding2)
            
            # Ensure 0-1 range
            similarity = max(0.0, min(1.0, similarity))
            
            logger.debug(f"Semantic Similarity: {similarity:.3f}")
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.7  # Default fallback

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (-1 to 1, normalized to 0-1)
        """
        try:
            # Calculate dot product
            dot_product = np.dot(vec1, vec2)
            
            # Calculate magnitudes
            magnitude1 = np.linalg.norm(vec1)
            magnitude2 = np.linalg.norm(vec2)
            
            # Calculate cosine similarity
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            cosine_sim = dot_product / (magnitude1 * magnitude2)
            
            # Normalize from [-1, 1] to [0, 1]
            normalized_sim = (cosine_sim + 1) / 2
            
            return float(normalized_sim)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def calculate_sentence_similarities(self, text1: str, text2: str) -> dict:
        """
        Calculate sentence-level similarities
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Dictionary with sentence-level metrics
        """
        try:
            if not self.model:
                return {"avg_similarity": 0.7, "sentence_count": 0}
            
            # Split into sentences
            sentences1 = self._split_sentences(text1)
            sentences2 = self._split_sentences(text2)
            
            if not sentences1 or not sentences2:
                return {"avg_similarity": 0.0, "sentence_count": 0}
            
            # Encode all sentences
            embeddings1 = self.model.encode(sentences1, convert_to_tensor=False)
            embeddings2 = self.model.encode(sentences2, convert_to_tensor=False)
            
            # Calculate pairwise similarities
            similarities = []
            for emb1 in embeddings1:
                max_sim = 0.0
                for emb2 in embeddings2:
                    sim = self._cosine_similarity(emb1, emb2)
                    max_sim = max(max_sim, sim)
                similarities.append(max_sim)
            
            avg_similarity = np.mean(similarities) if similarities else 0.0
            
            return {
                "avg_similarity": float(avg_similarity),
                "sentence_count": len(sentences1),
                "min_similarity": float(np.min(similarities)) if similarities else 0.0,
                "max_similarity": float(np.max(similarities)) if similarities else 0.0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentence similarities: {e}")
            return {"avg_similarity": 0.7, "sentence_count": 0}

    def _split_sentences(self, text: str) -> list:
        """Split text into sentences"""
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences


# Global instance
_similarity_service: Optional[SimilarityService] = None


def get_similarity_service() -> SimilarityService:
    """Get similarity service instance (singleton)"""
    global _similarity_service
    if _similarity_service is None:
        _similarity_service = SimilarityService()
    return _similarity_service

