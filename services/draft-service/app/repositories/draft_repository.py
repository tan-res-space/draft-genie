"""
Draft repository for MongoDB operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.draft import DraftModel, DraftCreate, DraftUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class DraftRepository:
    """Repository for draft operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.drafts

    async def create(self, draft_data: DraftCreate) -> DraftModel:
        """Create a new draft"""
        draft_dict = draft_data.model_dump()
        draft_dict["created_at"] = datetime.utcnow()
        draft_dict["updated_at"] = datetime.utcnow()
        draft_dict["is_processed"] = False
        draft_dict["vector_generated"] = False

        result = await self.collection.insert_one(draft_dict)
        draft_dict["_id"] = result.inserted_id

        logger.info(f"Created draft {draft_data.draft_id} for speaker {draft_data.speaker_id}")
        return DraftModel(**draft_dict)

    async def find_by_id(self, draft_id: str) -> Optional[DraftModel]:
        """Find draft by draft_id"""
        draft = await self.collection.find_one({"draft_id": draft_id})
        if draft:
            return DraftModel(**draft)
        return None

    async def find_by_object_id(self, object_id: str) -> Optional[DraftModel]:
        """Find draft by MongoDB ObjectId"""
        try:
            draft = await self.collection.find_one({"_id": ObjectId(object_id)})
            if draft:
                return DraftModel(**draft)
        except Exception as e:
            logger.error(f"Error finding draft by ObjectId {object_id}: {e}")
        return None

    async def find_by_speaker_id(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DraftModel]:
        """Find all drafts for a speaker"""
        cursor = (
            self.collection.find({"speaker_id": speaker_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        drafts = []
        async for draft in cursor:
            drafts.append(DraftModel(**draft))

        logger.info(f"Found {len(drafts)} drafts for speaker {speaker_id}")
        return drafts

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DraftModel]:
        """Find all drafts with optional filters"""
        query = filters or {}
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        drafts = []
        async for draft in cursor:
            drafts.append(DraftModel(**draft))

        logger.info(f"Found {len(drafts)} drafts")
        return drafts

    async def update(self, draft_id: str, update_data: DraftUpdate) -> Optional[DraftModel]:
        """Update a draft"""
        update_dict = {
            k: v for k, v in update_data.model_dump().items() if v is not None
        }
        update_dict["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"draft_id": draft_id},
            {"$set": update_dict},
            return_document=True,
        )

        if result:
            logger.info(f"Updated draft {draft_id}")
            return DraftModel(**result)
        return None

    async def delete(self, draft_id: str) -> bool:
        """Delete a draft"""
        result = await self.collection.delete_one({"draft_id": draft_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted draft {draft_id}")
            return True
        return False

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count drafts with optional filters"""
        query = filters or {}
        count = await self.collection.count_documents(query)
        return count

    async def mark_as_processed(self, draft_id: str) -> bool:
        """Mark draft as processed"""
        result = await self.collection.update_one(
            {"draft_id": draft_id},
            {"$set": {"is_processed": True, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def mark_vector_generated(self, draft_id: str) -> bool:
        """Mark draft as having vector generated"""
        result = await self.collection.update_one(
            {"draft_id": draft_id},
            {"$set": {"vector_generated": True, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def get_unprocessed_drafts(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that haven't been processed yet"""
        cursor = (
            self.collection.find({"is_processed": False})
            .sort("created_at", 1)
            .limit(limit)
        )

        drafts = []
        async for draft in cursor:
            drafts.append(DraftModel(**draft))

        return drafts

    async def get_drafts_without_vectors(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that don't have vectors generated yet"""
        cursor = (
            self.collection.find({"vector_generated": False})
            .sort("created_at", 1)
            .limit(limit)
        )

        drafts = []
        async for draft in cursor:
            drafts.append(DraftModel(**draft))

        return drafts

