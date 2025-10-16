"""
DFN API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dfn import DFNResponse
from app.services.dfn_service import DFNService, get_dfn_service
from app.db.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/dfn", tags=["dfn"])


async def get_dfn_service_dependency(session: AsyncSession = Depends(get_db)) -> DFNService:
    """Dependency to get DFNService instance"""
    return get_dfn_service(session)


@router.get("/{dfn_id}", response_model=DFNResponse)
async def get_dfn(
    dfn_id: str,
    service: DFNService = Depends(get_dfn_service_dependency),
) -> DFNResponse:
    """
    Get a specific DFN by ID
    """
    try:
        logger.info(f"GET /api/v1/dfn/{dfn_id}")
        
        dfn = await service.get_dfn_by_id(dfn_id)
        
        if not dfn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DFN {dfn_id} not found",
            )
        
        return DFNResponse(
            _id=str(dfn.id),
            dfn_id=dfn.dfn_id,
            speaker_id=dfn.speaker_id,
            session_id=dfn.session_id,
            ifn_draft_id=dfn.ifn_draft_id,
            generated_text=dfn.generated_text,
            word_count=dfn.word_count,
            confidence_score=dfn.confidence_score,
            context_used=dfn.context_used,
            metadata=dfn.metadata,
            created_at=dfn.created_at,
            updated_at=dfn.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DFN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DFN: {str(e)}",
        )


@router.get("/speaker/{speaker_id}", response_model=List[DFNResponse])
async def get_speaker_dfns(
    speaker_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DFNService = Depends(get_dfn_service_dependency),
) -> List[DFNResponse]:
    """
    Get all DFNs for a specific speaker
    """
    try:
        logger.info(f"GET /api/v1/dfn/speaker/{speaker_id}")
        
        dfns = await service.get_dfns_by_speaker(speaker_id, skip, limit)
        
        return [
            DFNResponse(
                _id=str(d.id),
                dfn_id=d.dfn_id,
                speaker_id=d.speaker_id,
                session_id=d.session_id,
                ifn_draft_id=d.ifn_draft_id,
                generated_text=d.generated_text,
                word_count=d.word_count,
                confidence_score=d.confidence_score,
                context_used=d.context_used,
                metadata=d.metadata,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in dfns
        ]
        
    except Exception as e:
        logger.error(f"Error getting speaker DFNs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker DFNs: {str(e)}",
        )


@router.get("/", response_model=List[DFNResponse])
async def list_dfns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DFNService = Depends(get_dfn_service_dependency),
) -> List[DFNResponse]:
    """
    List all DFNs with pagination
    """
    try:
        logger.info(f"GET /api/v1/dfn")
        
        dfns = await service.get_all_dfns(skip, limit)
        
        return [
            DFNResponse(
                _id=str(d.id),
                dfn_id=d.dfn_id,
                speaker_id=d.speaker_id,
                session_id=d.session_id,
                ifn_draft_id=d.ifn_draft_id,
                generated_text=d.generated_text,
                word_count=d.word_count,
                confidence_score=d.confidence_score,
                context_used=d.context_used,
                metadata=d.metadata,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in dfns
        ]
        
    except Exception as e:
        logger.error(f"Error listing DFNs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list DFNs: {str(e)}",
        )


@router.delete("/{dfn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dfn(
    dfn_id: str,
    service: DFNService = Depends(get_dfn_service_dependency),
) -> None:
    """
    Delete a DFN
    """
    try:
        logger.info(f"DELETE /api/v1/dfn/{dfn_id}")
        
        deleted = await service.delete_dfn(dfn_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DFN {dfn_id} not found",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting DFN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DFN: {str(e)}",
        )

