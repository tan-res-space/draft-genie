"""
Draft repository for SQLAlchemy operations
Database-agnostic implementation using generic SQLAlchemy types
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from app.models.draft import DraftModel, DraftCreate, DraftUpdate
from app.models.draft_db import Draft
from app.core.logging import get_logger

logger = get_logger(__name__)


class DraftRepositorySQL:
    """Repository for draft operations using SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, draft: Draft) -> DraftModel:
        """Convert SQLAlchemy Draft to Pydantic DraftModel"""
        return DraftModel(
            _id=str(draft.id),
            draft_id=draft.draft_id,
            speaker_id=draft.speaker_id,
            draft_type=draft.draft_type,
            original_text=draft.original_text,
            corrected_text=draft.corrected_text,
            word_count=draft.word_count,
            correction_count=draft.correction_count,
            metadata=draft.metadata or {},
            dictated_at=draft.dictated_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
            is_processed=draft.is_processed,
            vector_generated=draft.vector_generated,
        )

    async def create(self, draft_data: DraftCreate) -> DraftModel:
        """Create a new draft"""
        try:
            draft = Draft(
                draft_id=draft_data.draft_id,
                speaker_id=draft_data.speaker_id,
                draft_type=draft_data.draft_type,
                original_text=draft_data.original_text,
                corrected_text=draft_data.corrected_text,
                word_count=draft_data.word_count or 0,
                correction_count=draft_data.correction_count or 0,
                metadata=draft_data.metadata,
                dictated_at=draft_data.dictated_at,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_processed=False,
                vector_generated=False,
            )

            self.session.add(draft)
            await self.session.commit()
            await self.session.refresh(draft)

            logger.info(f"Created draft {draft_data.draft_id} for speaker {draft_data.speaker_id}")
            return self._to_model(draft)

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Draft {draft_data.draft_id} already exists: {e}")
            raise ValueError(f"Draft {draft_data.draft_id} already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating draft: {e}")
            raise

    async def find_by_id(self, draft_id: str) -> Optional[DraftModel]:
        """Find draft by draft_id"""
        try:
            stmt = select(Draft).where(Draft.draft_id == draft_id)
            result = await self.session.execute(stmt)
            draft = result.scalar_one_or_none()

            if draft:
                return self._to_model(draft)
            return None

        except Exception as e:
            logger.error(f"Error finding draft {draft_id}: {e}")
            return None

    async def find_by_object_id(self, object_id: str) -> Optional[DraftModel]:
        """Find draft by database ID"""
        try:
            stmt = select(Draft).where(Draft.id == int(object_id))
            result = await self.session.execute(stmt)
            draft = result.scalar_one_or_none()

            if draft:
                return self._to_model(draft)
            return None

        except Exception as e:
            logger.error(f"Error finding draft by ID {object_id}: {e}")
            return None

    async def find_by_speaker_id(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DraftModel]:
        """Find all drafts for a speaker"""
        try:
            stmt = (
                select(Draft)
                .where(Draft.speaker_id == speaker_id)
                .order_by(Draft.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            drafts = result.scalars().all()

            draft_models = [self._to_model(draft) for draft in drafts]
            logger.info(f"Found {len(draft_models)} drafts for speaker {speaker_id}")
            return draft_models

        except Exception as e:
            logger.error(f"Error finding drafts for speaker {speaker_id}: {e}")
            return []

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DraftModel]:
        """Find all drafts with optional filters"""
        try:
            stmt = select(Draft).order_by(Draft.created_at.desc())

            # Apply filters
            if filters:
                if "speaker_id" in filters:
                    stmt = stmt.where(Draft.speaker_id == filters["speaker_id"])
                if "draft_type" in filters:
                    stmt = stmt.where(Draft.draft_type == filters["draft_type"])
                if "is_processed" in filters:
                    stmt = stmt.where(Draft.is_processed == filters["is_processed"])
                if "vector_generated" in filters:
                    stmt = stmt.where(Draft.vector_generated == filters["vector_generated"])

            stmt = stmt.offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            drafts = result.scalars().all()

            draft_models = [self._to_model(draft) for draft in drafts]
            logger.info(f"Found {len(draft_models)} drafts")
            return draft_models

        except Exception as e:
            logger.error(f"Error finding drafts: {e}")
            return []

    async def update(self, draft_id: str, update_data: DraftUpdate) -> Optional[DraftModel]:
        """Update a draft"""
        try:
            # Build update dict
            update_dict = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_dict["updated_at"] = datetime.utcnow()

            stmt = (
                update(Draft)
                .where(Draft.draft_id == draft_id)
                .values(**update_dict)
                .returning(Draft)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            draft = result.scalar_one_or_none()
            if draft:
                logger.info(f"Updated draft {draft_id}")
                return self._to_model(draft)
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating draft {draft_id}: {e}")
            raise

    async def delete(self, draft_id: str) -> bool:
        """Delete a draft"""
        try:
            stmt = delete(Draft).where(Draft.draft_id == draft_id)
            result = await self.session.execute(stmt)
            await self.session.commit()

            if result.rowcount > 0:
                logger.info(f"Deleted draft {draft_id}")
                return True
            return False

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting draft {draft_id}: {e}")
            return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count drafts with optional filters"""
        try:
            stmt = select(func.count(Draft.id))

            # Apply filters
            if filters:
                if "speaker_id" in filters:
                    stmt = stmt.where(Draft.speaker_id == filters["speaker_id"])
                if "draft_type" in filters:
                    stmt = stmt.where(Draft.draft_type == filters["draft_type"])
                if "is_processed" in filters:
                    stmt = stmt.where(Draft.is_processed == filters["is_processed"])
                if "vector_generated" in filters:
                    stmt = stmt.where(Draft.vector_generated == filters["vector_generated"])

            result = await self.session.execute(stmt)
            count = result.scalar_one()
            return count

        except Exception as e:
            logger.error(f"Error counting drafts: {e}")
            return 0

    async def mark_as_processed(self, draft_id: str) -> bool:
        """Mark draft as processed"""
        try:
            stmt = (
                update(Draft)
                .where(Draft.draft_id == draft_id)
                .values(is_processed=True, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error marking draft as processed: {e}")
            return False

    async def mark_vector_generated(self, draft_id: str) -> bool:
        """Mark draft as having vector generated"""
        try:
            stmt = (
                update(Draft)
                .where(Draft.draft_id == draft_id)
                .values(vector_generated=True, updated_at=datetime.utcnow())
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error marking vector generated: {e}")
            return False

    async def get_unprocessed_drafts(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that haven't been processed yet"""
        try:
            stmt = (
                select(Draft)
                .where(Draft.is_processed == False)
                .order_by(Draft.created_at.asc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            drafts = result.scalars().all()

            return [self._to_model(draft) for draft in drafts]

        except Exception as e:
            logger.error(f"Error getting unprocessed drafts: {e}")
            return []

    async def get_drafts_without_vectors(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that don't have vectors generated yet"""
        try:
            stmt = (
                select(Draft)
                .where(Draft.vector_generated == False)
                .order_by(Draft.created_at.asc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            drafts = result.scalars().all()

            return [self._to_model(draft) for draft in drafts]

        except Exception as e:
            logger.error(f"Error getting drafts without vectors: {e}")
            return []

