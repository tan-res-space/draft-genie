"""
Evaluation API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import database
from app.models.schemas import (
    EvaluationResponse,
    EvaluationSummary,
    TriggerEvaluationRequest,
    TriggerEvaluationResponse,
)
from app.services.comparison_service import get_comparison_service
from app.services.similarity_service import get_similarity_service
from app.services.evaluation_service import get_evaluation_service
from app.services.bucket_service import get_bucket_service
from app.services.draft_client import get_draft_client
from app.services.rag_client import get_rag_client
from app.services.speaker_client import get_speaker_client
from app.events.publisher import event_publisher
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


async def get_db() -> AsyncSession:
    """Get database session"""
    async for session in database.get_session():
        yield session


@router.post("/trigger", response_model=TriggerEvaluationResponse, status_code=201)
async def trigger_evaluation(
    request: TriggerEvaluationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger evaluation for a DFN
    
    This endpoint allows manual triggering of evaluation,
    useful for testing or re-evaluation scenarios.
    """
    try:
        logger.info(f"Manual evaluation triggered for DFN {request.dfn_id}")
        
        # Get services
        comparison_service = get_comparison_service()
        similarity_service = get_similarity_service()
        evaluation_service = get_evaluation_service(comparison_service, similarity_service)
        bucket_service = get_bucket_service()
        draft_client = get_draft_client()
        rag_client = get_rag_client()
        speaker_client = get_speaker_client()
        
        # Fetch speaker data
        speaker_data = await speaker_client.get_speaker_by_id(request.speaker_id)
        if not speaker_data:
            raise HTTPException(status_code=404, detail="Speaker not found")
        
        current_bucket = speaker_data.get("bucket", "C")
        
        # Fetch IFN draft
        ifn_draft = await draft_client.get_draft_by_id(request.ifn_draft_id)
        if not ifn_draft:
            raise HTTPException(status_code=404, detail="IFN draft not found")
        
        ifn_text = ifn_draft.get("original_text", "")
        if not ifn_text:
            raise HTTPException(status_code=400, detail="IFN text is empty")
        
        # Fetch DFN
        dfn_data = await rag_client.get_dfn_by_id(request.dfn_id)
        if not dfn_data:
            raise HTTPException(status_code=404, detail="DFN not found")
        
        dfn_text = dfn_data.get("generated_text", "")
        if not dfn_text:
            raise HTTPException(status_code=400, detail="DFN text is empty")
        
        # Create evaluation
        evaluation = await evaluation_service.create_evaluation(
            db=db,
            speaker_id=request.speaker_id,
            ifn_draft_id=request.ifn_draft_id,
            dfn_id=request.dfn_id,
            session_id=request.session_id,
            ifn_text=ifn_text,
            dfn_text=dfn_text,
            current_bucket=current_bucket,
        )
        
        # Determine recommended bucket
        recommended_bucket = await bucket_service.determine_recommended_bucket(
            db=db,
            speaker_id=request.speaker_id,
            current_quality_score=evaluation.quality_score,
        )
        
        # Check if bucket should be reassigned
        speaker_eval_count = await evaluation_service.count_evaluations_by_speaker(
            db=db,
            speaker_id=request.speaker_id,
        )
        
        should_reassign = await bucket_service.should_reassign_bucket(
            current_bucket=current_bucket,
            recommended_bucket=recommended_bucket,
            speaker_evaluation_count=speaker_eval_count,
        )
        
        # Update evaluation
        evaluation.recommended_bucket = recommended_bucket
        evaluation.bucket_changed = should_reassign
        await db.commit()
        await db.refresh(evaluation)
        
        # Publish events
        await event_publisher.publish_evaluation_completed_event(
            evaluation_id=evaluation.evaluation_id,
            speaker_id=request.speaker_id,
            dfn_id=request.dfn_id,
            quality_score=evaluation.quality_score,
            improvement_score=evaluation.improvement_score,
            bucket_changed=should_reassign,
        )
        
        if should_reassign:
            await event_publisher.publish_bucket_reassigned_event(
                speaker_id=request.speaker_id,
                evaluation_id=evaluation.evaluation_id,
                old_bucket=current_bucket,
                new_bucket=recommended_bucket,
                quality_score=evaluation.quality_score,
                improvement_score=evaluation.improvement_score,
            )
        
        return TriggerEvaluationResponse(
            evaluation_id=evaluation.evaluation_id,
            message="Evaluation completed successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[EvaluationSummary])
async def get_evaluations(
    speaker_id: Optional[str] = Query(None, description="Filter by speaker ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get evaluations with optional filtering
    
    Returns a list of evaluation summaries.
    """
    try:
        comparison_service = get_comparison_service()
        similarity_service = get_similarity_service()
        evaluation_service = get_evaluation_service(comparison_service, similarity_service)
        
        if speaker_id:
            evaluations = await evaluation_service.get_evaluations_by_speaker(
                db=db,
                speaker_id=speaker_id,
                limit=limit,
                offset=offset,
            )
        else:
            evaluations = await evaluation_service.get_all_evaluations(
                db=db,
                limit=limit,
                offset=offset,
            )
        
        return [
            EvaluationSummary(
                evaluation_id=e.evaluation_id,
                speaker_id=e.speaker_id,
                dfn_id=e.dfn_id,
                quality_score=e.quality_score,
                improvement_score=e.improvement_score,
                current_bucket=e.current_bucket,
                recommended_bucket=e.recommended_bucket,
                bucket_changed=e.bucket_changed,
                created_at=e.created_at,
            )
            for e in evaluations
        ]
        
    except Exception as e:
        logger.error(f"Error getting evaluations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get evaluation by ID
    
    Returns detailed evaluation information.
    """
    try:
        comparison_service = get_comparison_service()
        similarity_service = get_similarity_service()
        evaluation_service = get_evaluation_service(comparison_service, similarity_service)
        
        evaluation = await evaluation_service.get_evaluation_by_id(
            db=db,
            evaluation_id=evaluation_id,
        )
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return EvaluationResponse.model_validate(evaluation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

