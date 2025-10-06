"""
Event Publisher - Publish events to RabbitMQ
"""
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import aio_pika
from aio_pika import Connection, Channel, Exchange

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """Event publisher for RabbitMQ"""

    def __init__(self):
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}")
            
            # Create connection
            self.connection = await aio_pika.connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_password,
                virtualhost=settings.rabbitmq_vhost,
            )

            # Create channel
            self.channel = await self.connection.channel()

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            logger.info("Successfully connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

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
            event_type: Type of event
            event_data: Event data
            routing_key: Optional routing key (defaults to event_type)
            correlation_id: Optional correlation ID for tracing
        """
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

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

            # Serialize event
            message_body = json.dumps(event).encode()

            # Create message
            message = aio_pika.Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                correlation_id=event["correlation_id"],
            )

            # Publish to exchange
            routing_key = routing_key or event_type
            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )

            logger.info(f"Published event {event_type} with ID {event['event_id']}")

        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            raise

    async def publish_dfn_generated_event(
        self,
        dfn_id: str,
        speaker_id: str,
        session_id: str,
        ifn_draft_id: str,
        word_count: int,
        confidence_score: float,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish DFNGeneratedEvent
        
        Args:
            dfn_id: DFN ID
            speaker_id: Speaker UUID
            session_id: RAG session ID
            ifn_draft_id: IFN draft ID
            word_count: Word count
            confidence_score: Confidence score
            correlation_id: Optional correlation ID
        """
        event_data = {
            "dfn_id": dfn_id,
            "speaker_id": speaker_id,
            "session_id": session_id,
            "ifn_draft_id": ifn_draft_id,
            "word_count": word_count,
            "confidence_score": confidence_score,
        }

        await self.publish_event(
            event_type="DFNGeneratedEvent",
            event_data=event_data,
            routing_key="dfn.generated",
            correlation_id=correlation_id,
        )

    async def health_check(self) -> bool:
        """Check if connected to RabbitMQ"""
        try:
            return (
                self.connection is not None
                and not self.connection.is_closed
                and self.channel is not None
                and not self.channel.is_closed
            )
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False


# Global event publisher instance
event_publisher = EventPublisher()

