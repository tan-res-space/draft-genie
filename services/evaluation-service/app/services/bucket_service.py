"""
Bucket Service - Determines bucket reassignment based on quality metrics
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.evaluation import Evaluation
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BucketService:
    """Service for bucket reassignment logic"""

    def __init__(self):
        self.bucket_a_threshold = settings.bucket_a_quality_threshold
        self.bucket_b_threshold = settings.bucket_b_quality_threshold
        self.bucket_c_threshold = settings.bucket_c_quality_threshold

    async def determine_recommended_bucket(
        self,
        db: AsyncSession,
        speaker_id: str,
        current_quality_score: float,
        lookback_count: int = 5,
    ) -> str:
        """
        Determine recommended bucket based on recent evaluations
        
        Args:
            db: Database session
            speaker_id: Speaker UUID
            current_quality_score: Quality score of current evaluation
            lookback_count: Number of recent evaluations to consider
            
        Returns:
            Recommended bucket (A, B, or C)
        """
        try:
            logger.debug(f"Determining bucket for speaker {speaker_id}")
            
            # Get recent evaluations
            result = await db.execute(
                select(Evaluation)
                .where(Evaluation.speaker_id == speaker_id)
                .order_by(Evaluation.created_at.desc())
                .limit(lookback_count)
            )
            recent_evaluations = list(result.scalars().all())
            
            # Calculate average quality score
            if recent_evaluations:
                quality_scores = [e.quality_score for e in recent_evaluations]
                avg_quality = sum(quality_scores) / len(quality_scores)
                logger.debug(
                    f"Average quality over {len(quality_scores)} evaluations: {avg_quality:.3f}"
                )
            else:
                # No history, use current score
                avg_quality = current_quality_score
                logger.debug(f"No history, using current score: {avg_quality:.3f}")
            
            # Determine bucket based on thresholds
            if avg_quality >= self.bucket_a_threshold:
                recommended_bucket = "A"
            elif avg_quality >= self.bucket_b_threshold:
                recommended_bucket = "B"
            else:
                recommended_bucket = "C"
            
            logger.info(
                f"Recommended bucket for speaker {speaker_id}: {recommended_bucket} "
                f"(avg_quality={avg_quality:.3f})"
            )
            
            return recommended_bucket
            
        except Exception as e:
            logger.error(f"Error determining recommended bucket: {e}")
            return "C"  # Default to lowest bucket on error

    async def should_reassign_bucket(
        self,
        current_bucket: str,
        recommended_bucket: str,
        min_evaluations: int = 3,
        speaker_evaluation_count: int = 0,
    ) -> bool:
        """
        Determine if bucket should be reassigned
        
        Args:
            current_bucket: Current speaker bucket
            recommended_bucket: Recommended bucket
            min_evaluations: Minimum evaluations before reassignment
            speaker_evaluation_count: Number of evaluations for speaker
            
        Returns:
            True if bucket should be reassigned
        """
        try:
            # Don't reassign if not enough evaluations
            if speaker_evaluation_count < min_evaluations:
                logger.debug(
                    f"Not enough evaluations ({speaker_evaluation_count} < {min_evaluations})"
                )
                return False
            
            # Don't reassign if buckets are the same
            if current_bucket == recommended_bucket:
                logger.debug(f"Bucket unchanged: {current_bucket}")
                return False
            
            logger.info(
                f"Bucket reassignment recommended: {current_bucket} -> {recommended_bucket}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error checking bucket reassignment: {e}")
            return False

    async def get_bucket_statistics(
        self,
        db: AsyncSession,
        speaker_id: str,
    ) -> Dict[str, Any]:
        """
        Get bucket statistics for a speaker
        
        Args:
            db: Database session
            speaker_id: Speaker UUID
            
        Returns:
            Dictionary with bucket statistics
        """
        try:
            # Get all evaluations
            result = await db.execute(
                select(Evaluation)
                .where(Evaluation.speaker_id == speaker_id)
                .order_by(Evaluation.created_at.desc())
            )
            evaluations = list(result.scalars().all())
            
            if not evaluations:
                return {
                    "total_evaluations": 0,
                    "avg_quality_score": 0.0,
                    "avg_improvement_score": 0.0,
                    "bucket_changes": 0,
                }
            
            # Calculate statistics
            quality_scores = [e.quality_score for e in evaluations]
            improvement_scores = [e.improvement_score for e in evaluations]
            bucket_changes = sum(1 for e in evaluations if e.bucket_changed)
            
            return {
                "total_evaluations": len(evaluations),
                "avg_quality_score": sum(quality_scores) / len(quality_scores),
                "avg_improvement_score": sum(improvement_scores) / len(improvement_scores),
                "min_quality_score": min(quality_scores),
                "max_quality_score": max(quality_scores),
                "bucket_changes": bucket_changes,
                "recent_quality_trend": quality_scores[:5],  # Last 5
            }
            
        except Exception as e:
            logger.error(f"Error getting bucket statistics: {e}")
            return {
                "total_evaluations": 0,
                "avg_quality_score": 0.0,
                "avg_improvement_score": 0.0,
                "bucket_changes": 0,
            }


# Factory function
def get_bucket_service() -> BucketService:
    """Get bucket service instance"""
    return BucketService()

