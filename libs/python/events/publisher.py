"""Event publisher for RabbitMQ."""

import json
from typing import Any, Dict, Optional

import aio_pika
from aio_pika import Connection, Channel, Exchange, Message
from aio_pika.abc import AbstractRobustConnection

from common.logger import LoggerMixin
from domain.events import DomainEvent


class EventPublisher(LoggerMixin):
    """Event publisher for publishing domain events to RabbitMQ."""

    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str = "draft-genie.events",
    ):
        """Initialize event publisher.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            exchange_name: Name of the exchange to publish to
        """
        super().__init__()
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[Channel] = None
        self._exchange: Optional[Exchange] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self.logger.info(
                "Connecting to RabbitMQ",
                exchange=self.exchange_name,
            )
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            self.logger.info(
                "Connected to RabbitMQ",
                exchange=self.exchange_name,
            )
        except Exception as e:
            self.logger.error(
                "Failed to connect to RabbitMQ",
                error=str(e),
                exchange=self.exchange_name,
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        try:
            if self._channel:
                await self._channel.close()
            if self._connection:
                await self._connection.close()
            self.logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            self.logger.error(
                "Error disconnecting from RabbitMQ",
                error=str(e),
            )

    async def publish(
        self,
        event: DomainEvent,
        routing_key: Optional[str] = None,
    ) -> None:
        """Publish a domain event.

        Args:
            event: Domain event to publish
            routing_key: Optional routing key (defaults to event type)
        """
        if not self._exchange:
            raise RuntimeError("Publisher not connected. Call connect() first.")

        # Use event type as routing key if not provided
        if routing_key is None:
            routing_key = event.event_type

        try:
            # Serialize event to JSON
            event_data = event.model_dump()
            message_body = json.dumps(event_data).encode()

            # Create message with metadata
            message = Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "aggregate_id": event.aggregate_id,
                    "correlation_id": event.correlation_id,
                },
            )

            # Publish message
            await self._exchange.publish(
                message,
                routing_key=routing_key,
            )

            self.logger.info(
                "Published event",
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                routing_key=routing_key,
                correlation_id=event.correlation_id,
            )
        except Exception as e:
            self.logger.error(
                "Failed to publish event",
                event_id=event.event_id,
                event_type=event.event_type,
                error=str(e),
                correlation_id=event.correlation_id,
            )
            raise

    async def publish_dict(
        self,
        event_data: Dict[str, Any],
        routing_key: str,
    ) -> None:
        """Publish an event from a dictionary.

        Args:
            event_data: Event data as dictionary
            routing_key: Routing key for the event
        """
        if not self._exchange:
            raise RuntimeError("Publisher not connected. Call connect() first.")

        try:
            # Serialize event to JSON
            message_body = json.dumps(event_data).encode()

            # Create message with metadata
            message = Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "event_id": event_data.get("event_id"),
                    "event_type": event_data.get("event_type"),
                    "aggregate_id": event_data.get("aggregate_id"),
                    "correlation_id": event_data.get("correlation_id"),
                },
            )

            # Publish message
            await self._exchange.publish(
                message,
                routing_key=routing_key,
            )

            self.logger.info(
                "Published event from dict",
                event_id=event_data.get("event_id"),
                event_type=event_data.get("event_type"),
                routing_key=routing_key,
            )
        except Exception as e:
            self.logger.error(
                "Failed to publish event from dict",
                error=str(e),
                routing_key=routing_key,
            )
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the publisher.

        Returns:
            Health check result
        """
        try:
            if not self._connection or self._connection.is_closed:
                return {
                    "healthy": False,
                    "message": "Not connected to RabbitMQ",
                }

            return {
                "healthy": True,
                "exchange": self.exchange_name,
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


# Global publisher instance
_event_publisher: Optional[EventPublisher] = None


def init_event_publisher(
    rabbitmq_url: str,
    exchange_name: str = "draft-genie.events",
) -> EventPublisher:
    """Initialize global event publisher.

    Args:
        rabbitmq_url: RabbitMQ connection URL
        exchange_name: Name of the exchange to publish to

    Returns:
        EventPublisher instance
    """
    global _event_publisher
    _event_publisher = EventPublisher(
        rabbitmq_url=rabbitmq_url,
        exchange_name=exchange_name,
    )
    return _event_publisher


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance.

    Returns:
        EventPublisher instance

    Raises:
        RuntimeError: If publisher not initialized
    """
    if _event_publisher is None:
        raise RuntimeError(
            "Event publisher not initialized. Call init_event_publisher() first."
        )
    return _event_publisher

