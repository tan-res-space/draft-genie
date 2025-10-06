"""
Evaluation Service - Orchestrates draft comparison and evaluation
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evaluation import Evaluation
from app.models.schemas import EvaluationCreate
from app.services.comparison_service import ComparisonService
from app.services.similarity_service import SimilarityService
from app.core.logging import get_logger

logger = get_logger(__name__)


class EvaluationService:
    """Service for managing evaluations"""

    def __init__(
        self,
        comparison_service: ComparisonService,
        similarity_service: SimilarityService,
    ):
        self.comparison_service = comparison_service
        self.similarity_service = similarity_service

    async def create_evaluation(
        self,
        db: AsyncSession,
        speaker_id: str,
        ifn_draft_id: str,
        dfn_id: str,
        session_id: str,
        ifn_text: str,
        dfn_text: str,
        current_bucket: str,
    ) -> Evaluation:
        """
        Create evaluation by comparing IFN and DFN
        
        Args:
            db: Database session
            speaker_id: Speaker UUID
            ifn_draft_id: IFN draft ID
            dfn_id: DFN ID
            session_id: RAG session ID
            ifn_text: IFN text
            dfn_text: DFN text
            current_bucket: Current speaker bucket
            
        Returns:
            Created evaluation
        """
        try:
            logger.info(f"Creating evaluation for speaker {speaker_id}, DFN {dfn_id}")
            
            # Generate evaluation ID
            evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
            
            # Calculate word counts
            ifn_word_count = len(ifn_text.split())
            dfn_word_count = len(dfn_text.split())
            
            # Calculate metrics
            logger.debug("Calculating SER...")
            ser = self.comparison_service.calculate_sentence_edit_rate(ifn_text, dfn_text)
            
            logger.debug("Calculating WER...")
            wer = self.comparison_service.calculate_word_error_rate(ifn_text, dfn_text)
            
            logger.debug("Calculating semantic similarity...")
            semantic_similarity = self.similarity_service.calculate_semantic_similarity(
                ifn_text, dfn_text
            )
            
            logger.debug("Calculating quality score...")
            quality_score = self.comparison_service.calculate_quality_score(
                ser, wer, semantic_similarity
            )
            
            logger.debug("Calculating improvement score...")
            improvement_score = self.comparison_service.calculate_improvement_score(
                ifn_word_count, dfn_word_count, quality_score
            )
            
            # Get detailed metrics
            detailed_metrics = self.comparison_service.get_detailed_metrics(
                ifn_text, dfn_text, ser, wer
            )
            
            # Create evaluation
            evaluation_create = EvaluationCreate(
                evaluation_id=evaluation_id,
                speaker_id=speaker_id,
                ifn_draft_id=ifn_draft_id,
                dfn_id=dfn_id,
                session_id=session_id,
                ifn_text=ifn_text,
                dfn_text=dfn_text,
                ifn_word_count=ifn_word_count,
                dfn_word_count=dfn_word_count,
                sentence_edit_rate=ser,
                word_error_rate=wer,
                semantic_similarity=semantic_similarity,
                quality_score=quality_score,
                improvement_score=improvement_score,
                current_bucket=current_bucket,
                metrics_detail=detailed_metrics,
            )
            
            # Save to database
            evaluation = Evaluation(**evaluation_create.model_dump())
            db.add(evaluation)
            await db.commit()
            await db.refresh(evaluation)
            
            logger.info(
                f"Evaluation created: {evaluation_id} "
                f"(quality={quality_score:.3f}, improvement={improvement_score:.3f})"
            )
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error creating evaluation: {e}")
            await db.rollback()
            raise

    async def get_evaluation_by_id(
        self,
        db: AsyncSession,
        evaluation_id: str,
    ) -> Optional[Evaluation]:
        """Get evaluation by ID"""
        try:
            result = await db.execute(
                select(Evaluation).where(Evaluation.evaluation_id == evaluation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting evaluation: {e}")
            return None

    async def get_evaluations_by_speaker(
        self,
        db: AsyncSession,
        speaker_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Evaluation]:
        """Get evaluations for a speaker"""
        try:
            result = await db.execute(
                select(Evaluation)
                .where(Evaluation.speaker_id == speaker_id)
                .order_by(Evaluation.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting speaker evaluations: {e}")
            return []

    async def get_all_evaluations(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Evaluation]:
        """Get all evaluations"""
        try:
            result = await db.execute(
                select(Evaluation)
                .order_by(Evaluation.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting all evaluations: {e}")
            return []

    async def count_evaluations(self, db: AsyncSession) -> int:
        """Count total evaluations"""
        try:
            from sqlalchemy import func
            result = await db.execute(select(func.count(Evaluation.id)))
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting evaluations: {e}")
            return 0

    async def count_evaluations_by_speaker(
        self,
        db: AsyncSession,
        speaker_id: str,
    ) -> int:
        """Count evaluations for a speaker"""
        try:
            from sqlalchemy import func
            result = await db.execute(
                select(func.count(Evaluation.id))
                .where(Evaluation.speaker_id == speaker_id)
            )
            return result.scalar_one()
        except Exception as e:
            logger.error(f"Error counting speaker evaluations: {e}")
            return 0


# Factory function
def get_evaluation_service(
    comparison_service: ComparisonService,
    similarity_service: SimilarityService,
) -> EvaluationService:
    """Get evaluation service instance"""
    return EvaluationService(comparison_service, similarity_service)

