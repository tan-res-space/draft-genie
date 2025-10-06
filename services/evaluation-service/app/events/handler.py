"""
Event Handler - Processes DFNGeneratedEvent
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import database
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


class EventHandler:
    """Handles DFNGeneratedEvent"""

    def __init__(self):
        self.comparison_service = get_comparison_service()
        self.similarity_service = get_similarity_service()
        self.evaluation_service = get_evaluation_service(
            self.comparison_service,
            self.similarity_service,
        )
        self.bucket_service = get_bucket_service()
        self.draft_client = get_draft_client()
        self.rag_client = get_rag_client()
        self.speaker_client = get_speaker_client()

    async def handle_dfn_generated_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle DFNGeneratedEvent
        
        Args:
            event_data: Event data from RabbitMQ
        """
        try:
            logger.info(f"Processing DFNGeneratedEvent: {event_data.get('dfn_id')}")
            
            # Extract event data
            dfn_id = event_data.get("dfn_id")
            speaker_id = event_data.get("speaker_id")
            session_id = event_data.get("session_id")
            ifn_draft_id = event_data.get("ifn_draft_id")
            
            if not all([dfn_id, speaker_id, session_id, ifn_draft_id]):
                logger.error("Missing required fields in event data")
                return
            
            # Fetch speaker data
            logger.debug(f"Fetching speaker {speaker_id}")
            speaker_data = await self.speaker_client.get_speaker_by_id(speaker_id)
            if not speaker_data:
                logger.error(f"Speaker {speaker_id} not found")
                return
            
            current_bucket = speaker_data.get("bucket", "C")
            
            # Fetch IFN draft
            logger.debug(f"Fetching IFN draft {ifn_draft_id}")
            ifn_draft = await self.draft_client.get_draft_by_id(ifn_draft_id)
            if not ifn_draft:
                logger.error(f"IFN draft {ifn_draft_id} not found")
                return
            
            ifn_text = ifn_draft.get("original_text", "")
            if not ifn_text:
                logger.error("IFN text is empty")
                return
            
            # Fetch DFN
            logger.debug(f"Fetching DFN {dfn_id}")
            dfn_data = await self.rag_client.get_dfn_by_id(dfn_id)
            if not dfn_data:
                logger.error(f"DFN {dfn_id} not found")
                return
            
            dfn_text = dfn_data.get("generated_text", "")
            if not dfn_text:
                logger.error("DFN text is empty")
                return
            
            # Create evaluation
            logger.info("Creating evaluation...")
            async for session in database.get_session():
                evaluation = await self.evaluation_service.create_evaluation(
                    db=session,
                    speaker_id=speaker_id,
                    ifn_draft_id=ifn_draft_id,
                    dfn_id=dfn_id,
                    session_id=session_id,
                    ifn_text=ifn_text,
                    dfn_text=dfn_text,
                    current_bucket=current_bucket,
                )
                
                logger.info(
                    f"Evaluation created successfully: {evaluation.evaluation_id} "
                    f"(quality={evaluation.quality_score:.3f})"
                )

                # Determine recommended bucket
                logger.debug("Determining recommended bucket...")
                recommended_bucket = await self.bucket_service.determine_recommended_bucket(
                    db=session,
                    speaker_id=speaker_id,
                    current_quality_score=evaluation.quality_score,
                )

                # Check if bucket should be reassigned
                speaker_eval_count = await self.evaluation_service.count_evaluations_by_speaker(
                    db=session,
                    speaker_id=speaker_id,
                )

                should_reassign = await self.bucket_service.should_reassign_bucket(
                    current_bucket=current_bucket,
                    recommended_bucket=recommended_bucket,
                    speaker_evaluation_count=speaker_eval_count,
                )

                # Update evaluation with recommended bucket
                evaluation.recommended_bucket = recommended_bucket
                evaluation.bucket_changed = should_reassign
                await session.commit()
                await session.refresh(evaluation)

                # Publish EvaluationCompletedEvent
                logger.debug("Publishing EvaluationCompletedEvent...")
                await event_publisher.publish_evaluation_completed_event(
                    evaluation_id=evaluation.evaluation_id,
                    speaker_id=speaker_id,
                    dfn_id=dfn_id,
                    quality_score=evaluation.quality_score,
                    improvement_score=evaluation.improvement_score,
                    bucket_changed=should_reassign,
                )

                # If bucket should be reassigned, publish BucketReassignedEvent
                if should_reassign:
                    logger.info(
                        f"Publishing BucketReassignedEvent: {current_bucket} -> {recommended_bucket}"
                    )
                    await event_publisher.publish_bucket_reassigned_event(
                        speaker_id=speaker_id,
                        evaluation_id=evaluation.evaluation_id,
                        old_bucket=current_bucket,
                        new_bucket=recommended_bucket,
                        quality_score=evaluation.quality_score,
                        improvement_score=evaluation.improvement_score,
                    )

                    # TODO: Call Speaker Service to update bucket
                    # This will be implemented when Speaker Service has the update endpoint
                    logger.info(
                        f"Bucket reassignment recommended for speaker {speaker_id}: "
                        f"{current_bucket} -> {recommended_bucket}"
                    )

                break  # Exit after first iteration
            
        except Exception as e:
            logger.error(f"Error handling DFNGeneratedEvent: {e}", exc_info=True)


# Global instance
event_handler = EventHandler()


async def handle_event(event_data: Dict[str, Any]) -> None:
    """
    Handle incoming event
    
    Args:
        event_data: Event data from RabbitMQ
    """
    event_type = event_data.get("event_type")
    
    if event_type == "DFNGenerated":
        await event_handler.handle_dfn_generated_event(event_data)
    else:
        logger.warning(f"Unknown event type: {event_type}")

