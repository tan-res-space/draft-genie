"""
Draft API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.models.draft import DraftCreate, DraftUpdate, DraftResponse
from app.services.draft_service import DraftService, get_draft_service
from app.repositories.draft_repository import DraftRepository
from app.db.mongodb import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/drafts", tags=["drafts"])


async def get_draft_service_dependency() -> DraftService:
    """Dependency to get DraftService instance"""
    db = await get_database()
    draft_repository = DraftRepository(db)
    return get_draft_service(draft_repository)


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_drafts(
    speaker_id: str = Query(..., description="Speaker UUID"),
    limit: int = Query(10, ge=1, le=100, description="Number of drafts to ingest"),
    service: DraftService = Depends(get_draft_service_dependency),
) -> dict:
    """
    Manually trigger draft ingestion for a speaker
    
    Fetches drafts from InstaNote and stores them in MongoDB
    """
    try:
        logger.info(f"POST /api/v1/drafts/ingest - speaker_id={speaker_id}, limit={limit}")
        
        drafts = await service.ingest_drafts_for_speaker(speaker_id, limit)
        
        return {
            "message": f"Successfully ingested {len(drafts)} drafts",
            "speaker_id": speaker_id,
            "count": len(drafts),
            "draft_ids": [draft.draft_id for draft in drafts],
        }
        
    except Exception as e:
        logger.error(f"Error ingesting drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest drafts: {str(e)}",
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DraftResponse)
async def create_draft(
    draft_data: DraftCreate,
    service: DraftService = Depends(get_draft_service_dependency),
) -> DraftResponse:
    """
    Create a single draft manually
    """
    try:
        logger.info(f"POST /api/v1/drafts - draft_id={draft_data.draft_id}")
        
        draft = await service.create_draft(draft_data)
        
        return DraftResponse(
            _id=str(draft.id),
            draft_id=draft.draft_id,
            speaker_id=draft.speaker_id,
            draft_type=draft.draft_type,
            original_text=draft.original_text,
            corrected_text=draft.corrected_text,
            word_count=draft.word_count,
            correction_count=draft.correction_count,
            metadata=draft.metadata,
            dictated_at=draft.dictated_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
            is_processed=draft.is_processed,
            vector_generated=draft.vector_generated,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}",
        )


@router.get("", response_model=List[DraftResponse])
async def list_drafts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    draft_type: Optional[str] = Query(None, description="Filter by draft type"),
    is_processed: Optional[bool] = Query(None, description="Filter by processing status"),
    service: DraftService = Depends(get_draft_service_dependency),
) -> List[DraftResponse]:
    """
    List all drafts with optional filters
    """
    try:
        logger.info(f"GET /api/v1/drafts - skip={skip}, limit={limit}")
        
        drafts = await service.get_all_drafts(skip, limit, draft_type, is_processed)
        
        return [
            DraftResponse(
                _id=str(draft.id),
                draft_id=draft.draft_id,
                speaker_id=draft.speaker_id,
                draft_type=draft.draft_type,
                original_text=draft.original_text,
                corrected_text=draft.corrected_text,
                word_count=draft.word_count,
                correction_count=draft.correction_count,
                metadata=draft.metadata,
                dictated_at=draft.dictated_at,
                created_at=draft.created_at,
                updated_at=draft.updated_at,
                is_processed=draft.is_processed,
                vector_generated=draft.vector_generated,
            )
            for draft in drafts
        ]
        
    except Exception as e:
        logger.error(f"Error listing drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list drafts: {str(e)}",
        )


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    service: DraftService = Depends(get_draft_service_dependency),
) -> DraftResponse:
    """
    Get a specific draft by ID
    """
    try:
        logger.info(f"GET /api/v1/drafts/{draft_id}")
        
        draft = await service.get_draft_by_id(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Draft {draft_id} not found",
            )
        
        return DraftResponse(
            _id=str(draft.id),
            draft_id=draft.draft_id,
            speaker_id=draft.speaker_id,
            draft_type=draft.draft_type,
            original_text=draft.original_text,
            corrected_text=draft.corrected_text,
            word_count=draft.word_count,
            correction_count=draft.correction_count,
            metadata=draft.metadata,
            dictated_at=draft.dictated_at,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
            is_processed=draft.is_processed,
            vector_generated=draft.vector_generated,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft: {str(e)}",
        )


@router.get("/speaker/{speaker_id}", response_model=List[DraftResponse])
async def get_speaker_drafts(
    speaker_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DraftService = Depends(get_draft_service_dependency),
) -> List[DraftResponse]:
    """
    Get all drafts for a specific speaker
    """
    try:
        logger.info(f"GET /api/v1/drafts/speaker/{speaker_id}")
        
        drafts = await service.get_drafts_by_speaker(speaker_id, skip, limit)
        
        return [
            DraftResponse(
                _id=str(draft.id),
                draft_id=draft.draft_id,
                speaker_id=draft.speaker_id,
                draft_type=draft.draft_type,
                original_text=draft.original_text,
                corrected_text=draft.corrected_text,
                word_count=draft.word_count,
                correction_count=draft.correction_count,
                metadata=draft.metadata,
                dictated_at=draft.dictated_at,
                created_at=draft.created_at,
                updated_at=draft.updated_at,
                is_processed=draft.is_processed,
                vector_generated=draft.vector_generated,
            )
            for draft in drafts
        ]
        
    except Exception as e:
        logger.error(f"Error getting speaker drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker drafts: {str(e)}",
        )


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: str,
    service: DraftService = Depends(get_draft_service_dependency),
) -> None:
    """
    Delete a draft
    """
    try:
        logger.info(f"DELETE /api/v1/drafts/{draft_id}")
        
        deleted = await service.delete_draft(draft_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Draft {draft_id} not found",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {str(e)}",
        )

