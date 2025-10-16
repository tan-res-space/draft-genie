"""
RAG Session Service - Manage RAG sessions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.rag_session import (
    RAGSessionModel,
    RAGSessionCreate,
    RAGSessionUpdate,
    RAGSessionResponse,
)
from app.repositories.rag_session_repository_sql import RAGSessionRepositorySQL
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGSessionService:
    """Service for managing RAG sessions"""

    def __init__(self, repository: RAGSessionRepositorySQL):
        self.repository = repository

    async def create_session(
        self, session_create: RAGSessionCreate
    ) -> RAGSessionModel:
        """
        Create a new RAG session

        Args:
            session_create: Session creation data

        Returns:
            Created session model
        """
        try:
            logger.info(f"Creating RAG session {session_create.session_id}")
            return await self.repository.create(session_create)
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_session_by_id(self, session_id: str) -> Optional[RAGSessionModel]:
        """Get session by ID"""
        try:
            return await self.repository.find_by_id(session_id)
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def get_sessions_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[RAGSessionModel]:
        """Get all sessions for a speaker"""
        try:
            return await self.repository.find_by_speaker(speaker_id, skip, limit)
        except Exception as e:
            logger.error(f"Error getting sessions for speaker {speaker_id}: {e}")
            return []

    async def update_session(
        self, session_id: str, session_update: RAGSessionUpdate
    ) -> Optional[RAGSessionModel]:
        """Update a session"""
        try:
            logger.info(f"Updating session {session_id}")
            return await self.repository.update(session_id, session_update)
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            raise

    async def add_agent_step(
        self, session_id: str, step: Dict[str, Any]
    ) -> Optional[RAGSessionModel]:
        """Add an agent step to session"""
        try:
            logger.info(f"Adding agent step to session {session_id}")
            return await self.repository.add_agent_step(session_id, step)
        except Exception as e:
            logger.error(f"Error adding agent step: {e}")
            raise

    async def mark_complete(
        self, session_id: str, dfn_id: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as complete"""
        try:
            logger.info(f"Marking session {session_id} as complete")
            return await self.repository.mark_complete(session_id, dfn_id)

        except Exception as e:
            logger.error(f"Error marking session complete: {e}")
            raise

    async def mark_failed(
        self, session_id: str, error_message: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as failed"""
        try:
            logger.info(f"Marking session {session_id} as failed")
            return await self.repository.mark_failed(session_id, error_message)
        except Exception as e:
            logger.error(f"Error marking session failed: {e}")
            raise


from sqlalchemy.ext.asyncio import AsyncSession


def get_rag_session_service(session: AsyncSession) -> RAGSessionService:
    """Factory function to create RAGSessionService"""
    repository = RAGSessionRepositorySQL(session)
    return RAGSessionService(repository)

