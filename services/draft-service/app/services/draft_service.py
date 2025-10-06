"""
Draft service - Business logic for draft operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.draft import DraftModel, DraftCreate, DraftUpdate, DraftResponse
from app.repositories.draft_repository import DraftRepository
from app.clients.instanote_client import InstaNoteMockClient
from app.events.publisher import event_publisher
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class DraftService:
    """Service for draft operations"""

    def __init__(
        self,
        draft_repository: DraftRepository,
        instanote_client: InstaNoteMockClient,
    ):
        self.draft_repository = draft_repository
        self.instanote_client = instanote_client

    async def ingest_drafts_for_speaker(
        self, speaker_id: str, limit: int = 10, correlation_id: Optional[str] = None
    ) -> List[DraftModel]:
        """
        Ingest drafts for a speaker from InstaNote
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of drafts to ingest
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            List of ingested drafts
        """
        logger.info(f"Ingesting drafts for speaker {speaker_id}")

        try:
            # Fetch drafts from InstaNote
            draft_data_list = await self.instanote_client.fetch_speaker_drafts(
                speaker_id, limit
            )

            ingested_drafts = []

            for draft_data in draft_data_list:
                # Check if draft already exists
                existing_draft = await self.draft_repository.find_by_id(
                    draft_data["draft_id"]
                )
                
                if existing_draft:
                    logger.info(f"Draft {draft_data['draft_id']} already exists, skipping")
                    continue

                # Create draft
                draft_create = DraftCreate(**draft_data)
                draft = await self.draft_repository.create(draft_create)
                ingested_drafts.append(draft)

                # Publish event
                await event_publisher.publish_draft_ingested_event(
                    draft_id=draft.draft_id,
                    speaker_id=draft.speaker_id,
                    draft_type=draft.draft_type,
                    correlation_id=correlation_id,
                )

            logger.info(
                f"Ingested {len(ingested_drafts)} drafts for speaker {speaker_id}"
            )
            return ingested_drafts

        except Exception as e:
            logger.error(f"Error ingesting drafts for speaker {speaker_id}: {e}")
            raise

    async def create_draft(
        self, draft_data: DraftCreate, correlation_id: Optional[str] = None
    ) -> DraftModel:
        """Create a single draft"""
        logger.info(f"Creating draft {draft_data.draft_id}")

        # Check if draft already exists
        existing_draft = await self.draft_repository.find_by_id(draft_data.draft_id)
        if existing_draft:
            logger.warning(f"Draft {draft_data.draft_id} already exists")
            raise ValueError(f"Draft {draft_data.draft_id} already exists")

        # Create draft
        draft = await self.draft_repository.create(draft_data)

        # Publish event
        await event_publisher.publish_draft_ingested_event(
            draft_id=draft.draft_id,
            speaker_id=draft.speaker_id,
            draft_type=draft.draft_type,
            correlation_id=correlation_id,
        )

        return draft

    async def get_draft_by_id(self, draft_id: str) -> Optional[DraftModel]:
        """Get draft by ID"""
        return await self.draft_repository.find_by_id(draft_id)

    async def get_drafts_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[DraftModel]:
        """Get all drafts for a speaker"""
        return await self.draft_repository.find_by_speaker_id(speaker_id, skip, limit)

    async def get_all_drafts(
        self,
        skip: int = 0,
        limit: int = 100,
        draft_type: Optional[str] = None,
        is_processed: Optional[bool] = None,
    ) -> List[DraftModel]:
        """Get all drafts with optional filters"""
        filters = {}
        if draft_type:
            filters["draft_type"] = draft_type
        if is_processed is not None:
            filters["is_processed"] = is_processed

        return await self.draft_repository.find_all(skip, limit, filters)

    async def update_draft(
        self, draft_id: str, update_data: DraftUpdate
    ) -> Optional[DraftModel]:
        """Update a draft"""
        return await self.draft_repository.update(draft_id, update_data)

    async def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft"""
        return await self.draft_repository.delete(draft_id)

    async def get_draft_count(
        self, speaker_id: Optional[str] = None, draft_type: Optional[str] = None
    ) -> int:
        """Get count of drafts with optional filters"""
        filters = {}
        if speaker_id:
            filters["speaker_id"] = speaker_id
        if draft_type:
            filters["draft_type"] = draft_type

        return await self.draft_repository.count(filters)

    async def mark_draft_as_processed(self, draft_id: str) -> bool:
        """Mark draft as processed"""
        return await self.draft_repository.mark_as_processed(draft_id)

    async def mark_draft_vector_generated(self, draft_id: str) -> bool:
        """Mark draft as having vector generated"""
        return await self.draft_repository.mark_vector_generated(draft_id)

    async def get_unprocessed_drafts(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that haven't been processed yet"""
        return await self.draft_repository.get_unprocessed_drafts(limit)

    async def get_drafts_without_vectors(self, limit: int = 100) -> List[DraftModel]:
        """Get drafts that don't have vectors generated yet"""
        return await self.draft_repository.get_drafts_without_vectors(limit)


def get_draft_service(draft_repository: DraftRepository) -> DraftService:
    """Factory function to create DraftService"""
    instanote_client = InstaNoteMockClient(
        api_url=settings.instanote_api_url,
        api_key=settings.instanote_api_key,
    )
    return DraftService(draft_repository, instanote_client)

