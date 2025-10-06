"""
DFN Service - Manage Draft Final Notes
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.dfn import DFNModel, DFNCreate, DFNUpdate, DFNResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class DFNService:
    """Service for managing DFNs"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.dfns

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

            # Check if DFN already exists
            existing = await self.collection.find_one({"dfn_id": dfn_create.dfn_id})
            if existing:
                raise ValueError(f"DFN {dfn_create.dfn_id} already exists")

            # Create DFN document
            dfn_dict = dfn_create.model_dump()
            dfn_dict["created_at"] = datetime.utcnow()
            dfn_dict["updated_at"] = datetime.utcnow()

            # Insert into database
            result = await self.collection.insert_one(dfn_dict)
            dfn_dict["_id"] = result.inserted_id

            dfn_model = DFNModel(**dfn_dict)
            logger.info(f"Created DFN {dfn_create.dfn_id}")
            return dfn_model

        except Exception as e:
            logger.error(f"Error creating DFN: {e}")
            raise

    async def get_dfn_by_id(self, dfn_id: str) -> Optional[DFNModel]:
        """Get DFN by ID"""
        try:
            dfn = await self.collection.find_one({"dfn_id": dfn_id})
            if dfn:
                return DFNModel(**dfn)
            return None
        except Exception as e:
            logger.error(f"Error getting DFN {dfn_id}: {e}")
            return None

    async def get_dfns_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DFNModel]:
        """Get all DFNs for a speaker"""
        try:
            cursor = (
                self.collection.find({"speaker_id": speaker_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            dfns = []
            async for dfn in cursor:
                dfns.append(DFNModel(**dfn))

            return dfns

        except Exception as e:
            logger.error(f"Error getting DFNs for speaker {speaker_id}: {e}")
            return []

    async def get_dfns_by_session(self, session_id: str) -> List[DFNModel]:
        """Get all DFNs for a session"""
        try:
            cursor = self.collection.find({"session_id": session_id})

            dfns = []
            async for dfn in cursor:
                dfns.append(DFNModel(**dfn))

            return dfns

        except Exception as e:
            logger.error(f"Error getting DFNs for session {session_id}: {e}")
            return []

    async def get_all_dfns(
        self, skip: int = 0, limit: int = 100
    ) -> List[DFNModel]:
        """Get all DFNs with pagination"""
        try:
            cursor = (
                self.collection.find()
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            dfns = []
            async for dfn in cursor:
                dfns.append(DFNModel(**dfn))

            return dfns

        except Exception as e:
            logger.error(f"Error getting all DFNs: {e}")
            return []

    async def update_dfn(
        self, dfn_id: str, dfn_update: DFNUpdate
    ) -> Optional[DFNModel]:
        """Update a DFN"""
        try:
            logger.info(f"Updating DFN {dfn_id}")

            # Get update data
            update_data = dfn_update.model_dump(exclude_unset=True)
            if not update_data:
                return await self.get_dfn_by_id(dfn_id)

            update_data["updated_at"] = datetime.utcnow()

            # Update in database
            result = await self.collection.update_one(
                {"dfn_id": dfn_id},
                {"$set": update_data},
            )

            if result.modified_count == 0:
                logger.warning(f"DFN {dfn_id} not found or not modified")
                return None

            return await self.get_dfn_by_id(dfn_id)

        except Exception as e:
            logger.error(f"Error updating DFN {dfn_id}: {e}")
            raise

    async def delete_dfn(self, dfn_id: str) -> bool:
        """Delete a DFN"""
        try:
            logger.info(f"Deleting DFN {dfn_id}")

            result = await self.collection.delete_one({"dfn_id": dfn_id})

            if result.deleted_count == 0:
                logger.warning(f"DFN {dfn_id} not found")
                return False

            logger.info(f"Deleted DFN {dfn_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting DFN {dfn_id}: {e}")
            return False

    async def count_dfns(self, speaker_id: Optional[str] = None) -> int:
        """Count DFNs, optionally filtered by speaker"""
        try:
            query = {"speaker_id": speaker_id} if speaker_id else {}
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Error counting DFNs: {e}")
            return 0


def get_dfn_service(db: AsyncIOMotorDatabase) -> DFNService:
    """Factory function to create DFNService"""
    return DFNService(db)

