"""
Event publisher for RabbitMQ
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import aio_pika
from aio_pika import Message, DeliveryMode

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """Event publisher for RabbitMQ"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url}")
            
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            
            logger.info(f"Connected to RabbitMQ exchange: {settings.rabbitmq_exchange}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        if self.connection:
            logger.info("Disconnecting from RabbitMQ")
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None
            logger.info("Disconnected from RabbitMQ")

    async def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        routing_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to RabbitMQ
        
        Args:
            event_type: Type of event (e.g., 'DraftIngested')
            event_data: Event payload
            routing_key: Optional routing key (defaults to event_type)
            correlation_id: Optional correlation ID for tracing
        """
        if not self.exchange:
            logger.error("Cannot publish event: Not connected to RabbitMQ")
            return

        try:
            # Create event envelope
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "service": settings.app_name,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "data": event_data,
            }

            # Serialize to JSON
            message_body = json.dumps(event).encode()

            # Create message
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                correlation_id=event["correlation_id"],
                message_id=event["event_id"],
                timestamp=datetime.utcnow(),
            )

            # Publish message
            routing_key = routing_key or f"draft.{event_type.lower()}"
            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )

            logger.info(
                f"Published event {event_type} with ID {event['event_id']} "
                f"to routing key {routing_key}"
            )

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise

    async def publish_draft_ingested_event(
        self,
        draft_id: str,
        speaker_id: str,
        draft_type: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish DraftIngestedEvent"""
        event_data = {
            "draft_id": draft_id,
            "speaker_id": speaker_id,
            "draft_type": draft_type,
        }
        await self.publish_event(
            "DraftIngested",
            event_data,
            routing_key="draft.ingested",
            correlation_id=correlation_id,
        )

    async def publish_correction_vector_created_event(
        self,
        vector_id: str,
        speaker_id: str,
        draft_id: str,
        total_corrections: int,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish CorrectionVectorCreatedEvent"""
        event_data = {
            "vector_id": vector_id,
            "speaker_id": speaker_id,
            "draft_id": draft_id,
            "total_corrections": total_corrections,
        }
        await self.publish_event(
            "CorrectionVectorCreated",
            event_data,
            routing_key="draft.vector.created",
            correlation_id=correlation_id,
        )

    async def health_check(self) -> bool:
        """Check RabbitMQ connection health"""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            return True
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False


# Global event publisher instance
event_publisher = EventPublisher()

