"""
RabbitMQ Event Publisher
"""
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from aio_pika import connect_robust, Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractExchange

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """RabbitMQ event publisher"""

    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange: Optional[AbstractExchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}")
            
            self.connection = await connect_robust(
                settings.rabbitmq_url,
                client_properties={"connection_name": "evaluation-service-publisher"},
            )
            
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            logger.info("RabbitMQ publisher connected successfully")
            
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
            
            logger.info("RabbitMQ publisher disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

    async def publish_event(
        self,
        routing_key: str,
        event_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish event to RabbitMQ
        
        Args:
            routing_key: Routing key for the event
            event_data: Event data dictionary
            correlation_id: Optional correlation ID
        """
        try:
            if not self.exchange:
                raise RuntimeError("Publisher not connected")
            
            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            
            # Create message
            message_body = json.dumps(event_data).encode()
            message = Message(
                message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                correlation_id=correlation_id,
                content_type="application/json",
            )
            
            # Publish message
            await self.exchange.publish(
                message,
                routing_key=routing_key,
            )
            
            logger.info(
                f"Published event: {routing_key} "
                f"(correlation_id={correlation_id})"
            )
            
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            raise

    async def publish_evaluation_completed_event(
        self,
        evaluation_id: str,
        speaker_id: str,
        dfn_id: str,
        quality_score: float,
        improvement_score: float,
        bucket_changed: bool,
    ) -> None:
        """
        Publish EvaluationCompletedEvent
        
        Args:
            evaluation_id: Evaluation ID
            speaker_id: Speaker UUID
            dfn_id: DFN ID
            quality_score: Quality score
            improvement_score: Improvement score
            bucket_changed: Whether bucket was changed
        """
        try:
            event_data = {
                "event_type": "EvaluationCompleted",
                "evaluation_id": evaluation_id,
                "speaker_id": speaker_id,
                "dfn_id": dfn_id,
                "quality_score": quality_score,
                "improvement_score": improvement_score,
                "bucket_changed": bucket_changed,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            await self.publish_event(
                routing_key="evaluation.completed",
                event_data=event_data,
            )
            
        except Exception as e:
            logger.error(f"Error publishing EvaluationCompletedEvent: {e}")

    async def publish_bucket_reassigned_event(
        self,
        speaker_id: str,
        evaluation_id: str,
        old_bucket: str,
        new_bucket: str,
        quality_score: float,
        improvement_score: float,
    ) -> None:
        """
        Publish BucketReassignedEvent
        
        Args:
            speaker_id: Speaker UUID
            evaluation_id: Evaluation ID
            old_bucket: Old bucket
            new_bucket: New bucket
            quality_score: Quality score
            improvement_score: Improvement score
        """
        try:
            event_data = {
                "event_type": "BucketReassigned",
                "speaker_id": speaker_id,
                "evaluation_id": evaluation_id,
                "old_bucket": old_bucket,
                "new_bucket": new_bucket,
                "quality_score": quality_score,
                "improvement_score": improvement_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            await self.publish_event(
                routing_key="bucket.reassigned",
                event_data=event_data,
            )
            
        except Exception as e:
            logger.error(f"Error publishing BucketReassignedEvent: {e}")

    async def health_check(self) -> bool:
        """Check publisher health"""
        try:
            return (
                self.connection is not None
                and not self.connection.is_closed
                and self.channel is not None
                and not self.channel.is_closed
            )
        except Exception:
            return False


# Global instance
event_publisher = EventPublisher()

