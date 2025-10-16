"""
DFN repository for SQLAlchemy operations
Database-agnostic implementation using generic SQLAlchemy types
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from app.models.dfn import DFNModel, DFNCreate, DFNUpdate
from app.models.dfn_db import DFN
from app.core.logging import get_logger

logger = get_logger(__name__)


class DFNRepositorySQL:
    """Repository for DFN operations using SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, dfn: DFN) -> DFNModel:
        """Convert SQLAlchemy DFN to Pydantic DFNModel"""
        return DFNModel(
            _id=str(dfn.id),
            dfn_id=dfn.dfn_id,
            speaker_id=dfn.speaker_id,
            session_id=dfn.session_id,
            ifn_draft_id=dfn.ifn_draft_id,
            generated_text=dfn.generated_text,
            word_count=dfn.word_count,
            confidence_score=dfn.confidence_score,
            context_used=dfn.context_used,
            metadata=dfn.metadata or {},
            created_at=dfn.created_at,
            updated_at=dfn.updated_at,
        )

    async def create(self, dfn_create: DFNCreate) -> DFNModel:
        """Create a new DFN"""
        try:
            # Check if DFN already exists
            stmt = select(DFN).where(DFN.dfn_id == dfn_create.dfn_id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                raise ValueError(f"DFN {dfn_create.dfn_id} already exists")

            dfn = DFN(
                dfn_id=dfn_create.dfn_id,
                speaker_id=dfn_create.speaker_id,
                session_id=dfn_create.session_id,
                ifn_draft_id=dfn_create.ifn_draft_id,
                generated_text=dfn_create.generated_text,
                word_count=dfn_create.word_count,
                confidence_score=dfn_create.confidence_score,
                context_used=dfn_create.context_used,
                metadata=dfn_create.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(dfn)
            await self.session.commit()
            await self.session.refresh(dfn)

            logger.info(f"Created DFN {dfn_create.dfn_id}")
            return self._to_model(dfn)

        except ValueError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"DFN {dfn_create.dfn_id} already exists: {e}")
            raise ValueError(f"DFN {dfn_create.dfn_id} already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating DFN: {e}")
            raise

    async def find_by_id(self, dfn_id: str) -> Optional[DFNModel]:
        """Get DFN by ID"""
        try:
            stmt = select(DFN).where(DFN.dfn_id == dfn_id)
            result = await self.session.execute(stmt)
            dfn = result.scalar_one_or_none()

            if dfn:
                return self._to_model(dfn)
            return None

        except Exception as e:
            logger.error(f"Error getting DFN {dfn_id}: {e}")
            return None

    async def find_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DFNModel]:
        """Get all DFNs for a speaker"""
        try:
            stmt = (
                select(DFN)
                .where(DFN.speaker_id == speaker_id)
                .order_by(DFN.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            dfns = result.scalars().all()

            return [self._to_model(dfn) for dfn in dfns]

        except Exception as e:
            logger.error(f"Error getting DFNs for speaker {speaker_id}: {e}")
            return []

    async def find_by_session(self, session_id: str) -> List[DFNModel]:
        """Get all DFNs for a session"""
        try:
            stmt = select(DFN).where(DFN.session_id == session_id)
            result = await self.session.execute(stmt)
            dfns = result.scalars().all()

            return [self._to_model(dfn) for dfn in dfns]

        except Exception as e:
            logger.error(f"Error getting DFNs for session {session_id}: {e}")
            return []

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[DFNModel]:
        """Get all DFNs with pagination"""
        try:
            stmt = (
                select(DFN)
                .order_by(DFN.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            dfns = result.scalars().all()

            return [self._to_model(dfn) for dfn in dfns]

        except Exception as e:
            logger.error(f"Error getting all DFNs: {e}")
            return []

    async def update(self, dfn_id: str, dfn_update: DFNUpdate) -> Optional[DFNModel]:
        """Update a DFN"""
        try:
            # Build update dict
            update_dict = dfn_update.model_dump(exclude_unset=True)
            if not update_dict:
                return await self.find_by_id(dfn_id)

            update_dict["updated_at"] = datetime.utcnow()

            stmt = (
                update(DFN)
                .where(DFN.dfn_id == dfn_id)
                .values(**update_dict)
                .returning(DFN)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            dfn = result.scalar_one_or_none()
            if dfn:
                logger.info(f"Updated DFN {dfn_id}")
                return self._to_model(dfn)
            
            logger.warning(f"DFN {dfn_id} not found or not modified")
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating DFN {dfn_id}: {e}")
            raise

    async def delete(self, dfn_id: str) -> bool:
        """Delete a DFN"""
        try:
            stmt = delete(DFN).where(DFN.dfn_id == dfn_id)
            result = await self.session.execute(stmt)
            await self.session.commit()

            if result.rowcount > 0:
                logger.info(f"Deleted DFN {dfn_id}")
                return True
            
            logger.warning(f"DFN {dfn_id} not found")
            return False

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting DFN {dfn_id}: {e}")
            return False

    async def count(self, speaker_id: Optional[str] = None) -> int:
        """Count DFNs, optionally filtered by speaker"""
        try:
            stmt = select(func.count(DFN.id))
            
            if speaker_id:
                stmt = stmt.where(DFN.speaker_id == speaker_id)

            result = await self.session.execute(stmt)
            count = result.scalar_one()
            return count

        except Exception as e:
            logger.error(f"Error counting DFNs: {e}")
            return 0

