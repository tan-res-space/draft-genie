"""
Correction Vector repository for SQLAlchemy operations
Database-agnostic implementation using generic SQLAlchemy types
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.correction_vector import CorrectionVectorModel, CorrectionVectorCreate
from app.models.draft_db import CorrectionVector
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorRepositorySQL:
    """Repository for correction vector operations using SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, vector: CorrectionVector) -> CorrectionVectorModel:
        """Convert SQLAlchemy CorrectionVector to Pydantic CorrectionVectorModel"""
        return CorrectionVectorModel(
            _id=str(vector.id),
            vector_id=vector.vector_id,
            speaker_id=vector.speaker_id,
            draft_id=vector.draft_id,
            patterns=vector.patterns.get("patterns", []) if isinstance(vector.patterns, dict) else vector.patterns,
            total_corrections=vector.total_corrections,
            unique_patterns=vector.unique_patterns,
            category_counts=vector.category_counts,
            qdrant_point_id=vector.qdrant_point_id,
            embedding_model=vector.embedding_model,
            metadata=vector.metadata or {},
            created_at=vector.created_at,
            updated_at=vector.updated_at,
        )

    async def create(self, vector_data: CorrectionVectorCreate) -> CorrectionVectorModel:
        """Create a new correction vector"""
        try:
            # Convert patterns list to dict for JSON storage
            patterns_dict = {
                "patterns": [p.model_dump() for p in vector_data.patterns]
            }

            vector = CorrectionVector(
                vector_id=vector_data.vector_id,
                speaker_id=vector_data.speaker_id,
                draft_id=vector_data.draft_id,
                patterns=patterns_dict,
                total_corrections=vector_data.total_corrections,
                unique_patterns=vector_data.unique_patterns,
                category_counts=vector_data.category_counts,
                qdrant_point_id=vector_data.qdrant_point_id,
                embedding_model=vector_data.embedding_model,
                metadata=vector_data.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(vector)
            await self.session.commit()
            await self.session.refresh(vector)

            logger.info(f"Created correction vector {vector_data.vector_id}")
            return self._to_model(vector)

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Vector {vector_data.vector_id} already exists: {e}")
            raise ValueError(f"Vector {vector_data.vector_id} already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating correction vector: {e}")
            raise

    async def find_by_id(self, vector_id: str) -> Optional[CorrectionVectorModel]:
        """Get correction vector by ID"""
        try:
            stmt = select(CorrectionVector).where(CorrectionVector.vector_id == vector_id)
            result = await self.session.execute(stmt)
            vector = result.scalar_one_or_none()

            if vector:
                return self._to_model(vector)
            return None

        except Exception as e:
            logger.error(f"Error finding vector {vector_id}: {e}")
            return None

    async def find_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[CorrectionVectorModel]:
        """Get all correction vectors for a speaker"""
        try:
            stmt = (
                select(CorrectionVector)
                .where(CorrectionVector.speaker_id == speaker_id)
                .order_by(CorrectionVector.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            vectors = result.scalars().all()

            return [self._to_model(vector) for vector in vectors]

        except Exception as e:
            logger.error(f"Error finding vectors for speaker {speaker_id}: {e}")
            return []

    async def find_by_draft(self, draft_id: str) -> List[CorrectionVectorModel]:
        """Get all correction vectors for a draft"""
        try:
            stmt = select(CorrectionVector).where(CorrectionVector.draft_id == draft_id)
            result = await self.session.execute(stmt)
            vectors = result.scalars().all()

            return [self._to_model(vector) for vector in vectors]

        except Exception as e:
            logger.error(f"Error finding vectors for draft {draft_id}: {e}")
            return []

    async def update_qdrant_point_id(self, vector_id: str, qdrant_point_id: str) -> bool:
        """Update Qdrant point ID for a vector"""
        try:
            stmt = (
                update(CorrectionVector)
                .where(CorrectionVector.vector_id == vector_id)
                .values(qdrant_point_id=qdrant_point_id, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating Qdrant point ID: {e}")
            return False

