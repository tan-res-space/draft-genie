"""
Vector service - Manage correction vectors and embeddings
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correction_vector import (
    CorrectionVectorModel,
    CorrectionVectorCreate,
    CorrectionVectorResponse,
)
from app.models.draft import DraftModel
from app.repositories.vector_repository_sql import VectorRepositorySQL
from app.services.correction_service import CorrectionService
from app.services.embedding_service import EmbeddingService
from app.services.draft_service import DraftService
from app.db.qdrant import qdrant
from app.events.publisher import event_publisher
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorService:
    """Service for managing correction vectors"""

    def __init__(
        self,
        vector_repository: VectorRepositorySQL,
        correction_service: CorrectionService,
        embedding_service: EmbeddingService,
        draft_service: DraftService,
    ):
        self.vector_repository = vector_repository
        self.correction_service = correction_service
        self.embedding_service = embedding_service
        self.draft_service = draft_service

    async def generate_vector_for_draft(
        self, draft: DraftModel, correlation_id: Optional[str] = None
    ) -> CorrectionVectorModel:
        """
        Generate correction vector for a draft
        
        Args:
            draft: Draft model
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Created correction vector model
        """
        logger.info(f"Generating correction vector for draft {draft.draft_id}")

        try:
            # Extract correction patterns
            patterns = self.correction_service.extract_corrections(draft)

            if not patterns:
                logger.warning(f"No corrections found in draft {draft.draft_id}")
                # Still create a vector with empty patterns
                patterns = []

            # Create correction vector
            vector_create = self.correction_service.create_correction_vector(draft, patterns)

            # Generate embedding
            embedding = self.embedding_service.generate_correction_embedding(patterns)

            # Store in PostgreSQL
            vector_model = await self.vector_repository.create(vector_create)

            # Store embedding in Qdrant
            point = self.embedding_service.create_qdrant_point(vector_model, embedding)
            await qdrant.upsert_vectors([point])

            # Update vector with Qdrant point ID
            await self.vector_repository.update_qdrant_point_id(
                vector_model.vector_id, vector_model.vector_id
            )
            vector_model.qdrant_point_id = vector_model.vector_id

            # Mark draft as processed and vector generated
            await self.draft_service.mark_draft_as_processed(draft.draft_id)
            await self.draft_service.mark_draft_vector_generated(draft.draft_id)

            # Publish event
            await event_publisher.publish_correction_vector_created_event(
                vector_id=vector_model.vector_id,
                speaker_id=vector_model.speaker_id,
                draft_id=vector_model.draft_id,
                total_corrections=vector_model.total_corrections,
                correlation_id=correlation_id,
            )

            logger.info(
                f"Generated correction vector {vector_model.vector_id} "
                f"with {len(patterns)} patterns"
            )
            return vector_model

        except Exception as e:
            logger.error(f"Error generating vector for draft {draft.draft_id}: {e}")
            raise

    async def generate_vectors_for_speaker(
        self, speaker_id: str, limit: int = 100
    ) -> List[CorrectionVectorModel]:
        """
        Generate vectors for all unprocessed drafts of a speaker
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of drafts to process
            
        Returns:
            List of created correction vectors
        """
        logger.info(f"Generating vectors for speaker {speaker_id}")

        # Get unprocessed drafts for speaker
        drafts = await self.draft_service.get_drafts_by_speaker(speaker_id, limit=limit)
        unprocessed_drafts = [d for d in drafts if not d.vector_generated]

        vectors = []
        for draft in unprocessed_drafts:
            try:
                vector = await self.generate_vector_for_draft(draft)
                vectors.append(vector)
            except Exception as e:
                logger.error(f"Error processing draft {draft.draft_id}: {e}")
                continue

        logger.info(f"Generated {len(vectors)} vectors for speaker {speaker_id}")
        return vectors

    async def get_vector_by_id(self, vector_id: str) -> Optional[CorrectionVectorModel]:
        """Get correction vector by ID"""
        return await self.vector_repository.find_by_id(vector_id)

    async def get_vectors_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[CorrectionVectorModel]:
        """Get all correction vectors for a speaker"""
        return await self.vector_repository.find_by_speaker(speaker_id, skip, limit)

    async def get_vectors_by_draft(self, draft_id: str) -> List[CorrectionVectorModel]:
        """Get all correction vectors for a draft"""
        return await self.vector_repository.find_by_draft(draft_id)

    async def search_similar_vectors(
        self,
        speaker_id: str,
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> List[dict]:
        """
        Search for similar correction patterns for a speaker
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar patterns with scores
        """
        # Get speaker's recent patterns
        vectors = await self.get_vectors_by_speaker(speaker_id, limit=5)
        
        if not vectors:
            logger.warning(f"No vectors found for speaker {speaker_id}")
            return []

        # Use most recent vector's patterns for search
        recent_vector = vectors[0]
        
        # Search for similar patterns
        results = await self.embedding_service.search_similar_patterns(
            query_patterns=recent_vector.patterns,
            limit=limit,
            score_threshold=score_threshold,
        )

        return results

    async def get_speaker_statistics(self, speaker_id: str) -> dict:
        """Get statistics for a speaker's correction vectors"""
        vectors = await self.get_vectors_by_speaker(speaker_id, limit=1000)

        if not vectors:
            return {
                "total_vectors": 0,
                "total_corrections": 0,
                "unique_patterns": 0,
                "category_distribution": {},
            }

        total_corrections = sum(v.total_corrections for v in vectors)
        unique_patterns = sum(v.unique_patterns for v in vectors)

        # Aggregate category counts
        category_totals = {}
        for vector in vectors:
            for category, count in vector.category_counts.items():
                category_totals[category] = category_totals.get(category, 0) + count

        return {
            "total_vectors": len(vectors),
            "total_corrections": total_corrections,
            "unique_patterns": unique_patterns,
            "category_distribution": category_totals,
            "average_corrections_per_draft": (
                total_corrections / len(vectors) if vectors else 0
            ),
        }


def get_vector_service_sql(
    session: AsyncSession, draft_service: DraftService
) -> VectorService:
    """Factory function to create VectorService with SQLAlchemy"""
    vector_repository = VectorRepositorySQL(session)
    correction_service = CorrectionService()
    embedding_service = EmbeddingService()
    return VectorService(vector_repository, correction_service, embedding_service, draft_service)

