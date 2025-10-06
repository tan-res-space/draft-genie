"""
Event handlers for incoming events
"""
from typing import Dict, Any

from app.services.draft_service import DraftService
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventHandler:
    """Handler for incoming events"""

    def __init__(self, draft_service: DraftService):
        self.draft_service = draft_service

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """
        Route event to appropriate handler
        
        Args:
            event: Event dictionary with event_type and data
        """
        event_type = event.get("event_type")
        
        if not event_type:
            logger.warning("Received event without event_type")
            return

        # Route to handler
        handler_map = {
            "SpeakerOnboarded": self.handle_speaker_onboarded,
            "SpeakerUpdated": self.handle_speaker_updated,
        }

        handler = handler_map.get(event_type)
        if handler:
            await handler(event)
        else:
            logger.info(f"No handler for event type: {event_type}")

    async def handle_speaker_onboarded(self, event: Dict[str, Any]) -> None:
        """
        Handle SpeakerOnboardedEvent
        
        When a speaker is onboarded, automatically ingest their drafts
        """
        try:
            data = event.get("data", {})
            speaker_id = data.get("speaker_id")
            correlation_id = event.get("correlation_id")

            if not speaker_id:
                logger.error("SpeakerOnboardedEvent missing speaker_id")
                return

            logger.info(f"Handling SpeakerOnboardedEvent for speaker {speaker_id}")

            # Ingest drafts for the speaker
            drafts = await self.draft_service.ingest_drafts_for_speaker(
                speaker_id=speaker_id,
                limit=10,  # Ingest 10 drafts initially
                correlation_id=correlation_id,
            )

            logger.info(
                f"Successfully ingested {len(drafts)} drafts for speaker {speaker_id}"
            )

        except Exception as e:
            logger.error(f"Error handling SpeakerOnboardedEvent: {e}", exc_info=True)

    async def handle_speaker_updated(self, event: Dict[str, Any]) -> None:
        """
        Handle SpeakerUpdatedEvent
        
        Currently just logs the event
        """
        try:
            data = event.get("data", {})
            speaker_id = data.get("speaker_id")

            logger.info(f"Handling SpeakerUpdatedEvent for speaker {speaker_id}")
            # Could implement logic to re-ingest drafts or update metadata

        except Exception as e:
            logger.error(f"Error handling SpeakerUpdatedEvent: {e}", exc_info=True)

