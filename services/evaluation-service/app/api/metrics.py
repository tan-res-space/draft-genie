"""
Metrics API endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import database
from app.services.bucket_service import get_bucket_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


async def get_db() -> AsyncSession:
    """Get database session"""
    async for session in database.get_session():
        yield session


@router.get("/speaker/{speaker_id}", response_model=Dict[str, Any])
async def get_speaker_metrics(
    speaker_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated metrics for a speaker
    
    Returns statistics including:
    - Total evaluations
    - Average quality score
    - Average improvement score
    - Bucket change history
    - Recent quality trend
    """
    try:
        bucket_service = get_bucket_service()
        
        stats = await bucket_service.get_bucket_statistics(
            db=db,
            speaker_id=speaker_id,
        )
        
        if stats["total_evaluations"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluations found for speaker {speaker_id}",
            )
        
        return {
            "speaker_id": speaker_id,
            **stats,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting speaker metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=Dict[str, Any])
async def get_overall_metrics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall system metrics
    
    Returns aggregate statistics across all evaluations.
    """
    try:
        from sqlalchemy import select, func
        from app.models.evaluation import Evaluation
        
        # Get total evaluations
        result = await db.execute(select(func.count(Evaluation.id)))
        total_evaluations = result.scalar_one()
        
        if total_evaluations == 0:
            return {
                "total_evaluations": 0,
                "avg_quality_score": 0.0,
                "avg_improvement_score": 0.0,
                "total_bucket_changes": 0,
            }
        
        # Get average scores
        result = await db.execute(
            select(
                func.avg(Evaluation.quality_score),
                func.avg(Evaluation.improvement_score),
                func.sum(func.cast(Evaluation.bucket_changed, func.Integer())),
            )
        )
        row = result.one()
        avg_quality = float(row[0]) if row[0] else 0.0
        avg_improvement = float(row[1]) if row[1] else 0.0
        total_bucket_changes = int(row[2]) if row[2] else 0
        
        return {
            "total_evaluations": total_evaluations,
            "avg_quality_score": avg_quality,
            "avg_improvement_score": avg_improvement,
            "total_bucket_changes": total_bucket_changes,
        }
        
    except Exception as e:
        logger.error(f"Error getting overall metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

