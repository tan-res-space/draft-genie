"""
DFN Service - Manage Draft Final Notes
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.dfn import DFNModel, DFNCreate, DFNUpdate, DFNResponse
from app.repositories.dfn_repository_sql import DFNRepositorySQL
from app.core.logging import get_logger

logger = get_logger(__name__)


class DFNService:
    """Service for managing DFNs"""

    def __init__(self, repository: DFNRepositorySQL):
        self.repository = repository

    async def create_dfn(self, dfn_create: DFNCreate) -> DFNModel:
        """
        Create a new DFN

        Args:
            dfn_create: DFN creation data

        Returns:
            Created DFN model
        """
        try:
            logger.info(f"Creating DFN {dfn_create.dfn_id}")
            return await self.repository.create(dfn_create)
        except Exception as e:
            logger.error(f"Error creating DFN: {e}")
            raise

    async def get_dfn_by_id(self, dfn_id: str) -> Optional[DFNModel]:
        """Get DFN by ID"""
        try:
            return await self.repository.find_by_id(dfn_id)
        except Exception as e:
            logger.error(f"Error getting DFN {dfn_id}: {e}")
            return None

    async def get_dfns_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DFNModel]:
        """Get all DFNs for a speaker"""
        try:
            return await self.repository.find_by_speaker(speaker_id, skip, limit)
        except Exception as e:
            logger.error(f"Error getting DFNs for speaker {speaker_id}: {e}")
            return []

    async def get_dfns_by_session(self, session_id: str) -> List[DFNModel]:
        """Get all DFNs for a session"""
        try:
            return await self.repository.find_by_session(session_id)
        except Exception as e:
            logger.error(f"Error getting DFNs for session {session_id}: {e}")
            return []

    async def get_all_dfns(
        self, skip: int = 0, limit: int = 100
    ) -> List[DFNModel]:
        """Get all DFNs with pagination"""
        try:
            return await self.repository.find_all(skip, limit)
        except Exception as e:
            logger.error(f"Error getting all DFNs: {e}")
            return []

    async def update_dfn(
        self, dfn_id: str, dfn_update: DFNUpdate
    ) -> Optional[DFNModel]:
        """Update a DFN"""
        try:
            logger.info(f"Updating DFN {dfn_id}")
            return await self.repository.update(dfn_id, dfn_update)
        except Exception as e:
            logger.error(f"Error updating DFN {dfn_id}: {e}")
            raise

    async def delete_dfn(self, dfn_id: str) -> bool:
        """Delete a DFN"""
        try:
            logger.info(f"Deleting DFN {dfn_id}")
            return await self.repository.delete(dfn_id)
        except Exception as e:
            logger.error(f"Error deleting DFN {dfn_id}: {e}")
            return False

    async def count_dfns(self, speaker_id: Optional[str] = None) -> int:
        """Count DFNs, optionally filtered by speaker"""
        try:
            return await self.repository.count(speaker_id)
        except Exception as e:
            logger.error(f"Error counting DFNs: {e}")
            return 0


from sqlalchemy.ext.asyncio import AsyncSession


def get_dfn_service(session: AsyncSession) -> DFNService:
    """Factory function to create DFNService"""
    repository = DFNRepositorySQL(session)
    return DFNService(repository)

