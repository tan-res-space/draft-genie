"""
RAG Session repository for SQLAlchemy operations
Database-agnostic implementation using generic SQLAlchemy types
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.rag_session import RAGSessionModel, RAGSessionCreate, RAGSessionUpdate
from app.models.dfn_db import RAGSession
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGSessionRepositorySQL:
    """Repository for RAG Session operations using SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_model(self, session_obj: RAGSession) -> RAGSessionModel:
        """Convert SQLAlchemy RAGSession to Pydantic RAGSessionModel"""
        # Extract lists from JSON storage
        prompts_used = session_obj.prompts_used.get("prompts", []) if isinstance(session_obj.prompts_used, dict) else []
        agent_steps = session_obj.agent_steps.get("steps", []) if isinstance(session_obj.agent_steps, dict) else []
        
        return RAGSessionModel(
            _id=str(session_obj.id),
            session_id=session_obj.session_id,
            speaker_id=session_obj.speaker_id,
            ifn_draft_id=session_obj.ifn_draft_id,
            context_retrieved=session_obj.context_retrieved,
            prompts_used=prompts_used,
            agent_steps=agent_steps,
            dfn_generated=session_obj.dfn_generated,
            dfn_id=session_obj.dfn_id,
            status=session_obj.status,
            error_message=session_obj.error_message,
            metadata=session_obj.metadata or {},
            created_at=session_obj.created_at,
            updated_at=session_obj.updated_at,
        )

    async def create(self, session_create: RAGSessionCreate) -> RAGSessionModel:
        """Create a new RAG session"""
        try:
            # Check if session already exists
            stmt = select(RAGSession).where(RAGSession.session_id == session_create.session_id)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                raise ValueError(f"Session {session_create.session_id} already exists")

            # Store lists as JSON objects
            session_obj = RAGSession(
                session_id=session_create.session_id,
                speaker_id=session_create.speaker_id,
                ifn_draft_id=session_create.ifn_draft_id,
                context_retrieved=session_create.context_retrieved,
                prompts_used={"prompts": []},  # Initialize as empty list in JSON
                agent_steps={"steps": []},  # Initialize as empty list in JSON
                dfn_generated=False,
                dfn_id=None,
                status="pending",
                error_message=None,
                metadata=session_create.metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.session.add(session_obj)
            await self.session.commit()
            await self.session.refresh(session_obj)

            logger.info(f"Created RAG session {session_create.session_id}")
            return self._to_model(session_obj)

        except ValueError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Session {session_create.session_id} already exists: {e}")
            raise ValueError(f"Session {session_create.session_id} already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating session: {e}")
            raise

    async def find_by_id(self, session_id: str) -> Optional[RAGSessionModel]:
        """Get session by ID"""
        try:
            stmt = select(RAGSession).where(RAGSession.session_id == session_id)
            result = await self.session.execute(stmt)
            session_obj = result.scalar_one_or_none()

            if session_obj:
                return self._to_model(session_obj)
            return None

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def find_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[RAGSessionModel]:
        """Get all sessions for a speaker"""
        try:
            stmt = (
                select(RAGSession)
                .where(RAGSession.speaker_id == speaker_id)
                .order_by(RAGSession.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            sessions = result.scalars().all()

            return [self._to_model(session_obj) for session_obj in sessions]

        except Exception as e:
            logger.error(f"Error getting sessions for speaker {speaker_id}: {e}")
            return []

    async def update(
        self, session_id: str, session_update: RAGSessionUpdate
    ) -> Optional[RAGSessionModel]:
        """Update a session"""
        try:
            # Build update dict
            update_dict = session_update.model_dump(exclude_unset=True)
            if not update_dict:
                return await self.find_by_id(session_id)

            # Convert lists to JSON format for storage
            if "prompts_used" in update_dict:
                update_dict["prompts_used"] = {"prompts": update_dict["prompts_used"]}
            if "agent_steps" in update_dict:
                update_dict["agent_steps"] = {"steps": update_dict["agent_steps"]}

            update_dict["updated_at"] = datetime.utcnow()

            stmt = (
                update(RAGSession)
                .where(RAGSession.session_id == session_id)
                .values(**update_dict)
                .returning(RAGSession)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            session_obj = result.scalar_one_or_none()
            if session_obj:
                logger.info(f"Updated session {session_id}")
                return self._to_model(session_obj)
            
            logger.warning(f"Session {session_id} not found or not modified")
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating session {session_id}: {e}")
            raise

    async def add_agent_step(
        self, session_id: str, step: Dict[str, Any]
    ) -> Optional[RAGSessionModel]:
        """Add an agent step to session"""
        try:
            # Get current session
            session_obj = await self.find_by_id(session_id)
            if not session_obj:
                logger.warning(f"Session {session_id} not found")
                return None

            # Add timestamp to step
            step["timestamp"] = datetime.utcnow().isoformat()

            # Get current steps and append new one
            current_steps = session_obj.agent_steps
            current_steps.append(step)

            # Update session
            stmt = (
                update(RAGSession)
                .where(RAGSession.session_id == session_id)
                .values(
                    agent_steps={"steps": current_steps},
                    updated_at=datetime.utcnow()
                )
                .returning(RAGSession)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            updated_session = result.scalar_one_or_none()
            if updated_session:
                logger.info(f"Added agent step to session {session_id}")
                return self._to_model(updated_session)
            
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding agent step: {e}")
            raise

    async def mark_complete(
        self, session_id: str, dfn_id: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as complete"""
        try:
            stmt = (
                update(RAGSession)
                .where(RAGSession.session_id == session_id)
                .values(
                    dfn_generated=True,
                    dfn_id=dfn_id,
                    status="complete",
                    updated_at=datetime.utcnow()
                )
                .returning(RAGSession)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            session_obj = result.scalar_one_or_none()
            if session_obj:
                logger.info(f"Marked session {session_id} as complete")
                return self._to_model(session_obj)
            
            logger.warning(f"Session {session_id} not found")
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error marking session complete: {e}")
            raise

    async def mark_failed(
        self, session_id: str, error_message: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as failed"""
        try:
            stmt = (
                update(RAGSession)
                .where(RAGSession.session_id == session_id)
                .values(
                    status="failed",
                    error_message=error_message,
                    updated_at=datetime.utcnow()
                )
                .returning(RAGSession)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            session_obj = result.scalar_one_or_none()
            if session_obj:
                logger.info(f"Marked session {session_id} as failed")
                return self._to_model(session_obj)
            
            logger.warning(f"Session {session_id} not found")
            return None

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error marking session failed: {e}")
            raise

