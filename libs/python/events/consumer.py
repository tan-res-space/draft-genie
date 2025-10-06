"""Event consumer for RabbitMQ."""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Protocol

import aio_pika
from aio_pika import Connection, Channel, Queue, IncomingMessage
from aio_pika.abc import AbstractRobustConnection

from common.logger import LoggerMixin


class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def __call__(self, event_data: Dict[str, Any]) -> None:
        """Handle an event.

        Args:
            event_data: Event data as dictionary
        """
        ...


class EventConsumer(LoggerMixin):
    """Event consumer for consuming domain events from RabbitMQ."""

    def __init__(
        self,
        rabbitmq_url: str,
        queue_name: str,
        prefetch_count: int = 10,
    ):
        """Initialize event consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Name of the queue to consume from
            prefetch_count: Number of messages to prefetch
        """
        super().__init__()
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[Channel] = None
        self._queue: Optional[Queue] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._running = False

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self.logger.info(
                "Connecting to RabbitMQ",
                queue=self.queue_name,
            )
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.prefetch_count)
            self._queue = await self._channel.declare_queue(
                self.queue_name,
                durable=True,
            )
            self.logger.info(
                "Connected to RabbitMQ",
                queue=self.queue_name,
            )
        except Exception as e:
            self.logger.error(
                "Failed to connect to RabbitMQ",
                error=str(e),
                queue=self.queue_name,
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        try:
            self._running = False
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

    def register_handler(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.logger.info(
            "Registered event handler",
            event_type=event_type,
            handler=handler.__name__,
        )

    async def _process_message(self, message: IncomingMessage) -> None:
        """Process a message from the queue.

        Args:
            message: Incoming message
        """
        async with message.process():
            try:
                # Parse message body
                event_data = json.loads(message.body.decode())
                event_type = event_data.get("event_type")

                self.logger.info(
                    "Processing event",
                    event_id=event_data.get("event_id"),
                    event_type=event_type,
                    correlation_id=event_data.get("correlation_id"),
                )

                # Get handlers for this event type
                handlers = self._handlers.get(event_type, [])
                if not handlers:
                    self.logger.warning(
                        "No handlers registered for event type",
                        event_type=event_type,
                    )
                    return

                # Execute all handlers
                for handler in handlers:
                    try:
                        await handler(event_data)
                        self.logger.info(
                            "Handler executed successfully",
                            event_type=event_type,
                            handler=handler.__name__,
                        )
                    except Exception as e:
                        self.logger.error(
                            "Handler failed",
                            event_type=event_type,
                            handler=handler.__name__,
                            error=str(e),
                        )
                        # Re-raise to trigger message requeue
                        raise

            except json.JSONDecodeError as e:
                self.logger.error(
                    "Failed to parse message body",
                    error=str(e),
                )
                # Don't requeue invalid messages
            except Exception as e:
                self.logger.error(
                    "Failed to process message",
                    error=str(e),
                )
                raise

    async def start(self) -> None:
        """Start consuming messages."""
        if not self._queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        self._running = True
        self.logger.info(
            "Starting event consumer",
            queue=self.queue_name,
        )

        try:
            await self._queue.consume(self._process_message)
            self.logger.info(
                "Event consumer started",
                queue=self.queue_name,
            )

            # Keep running until stopped
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(
                "Error in event consumer",
                error=str(e),
            )
            raise

    async def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False
        self.logger.info("Stopping event consumer")

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the consumer.

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
                "queue": self.queue_name,
                "running": self._running,
                "handlers": {
                    event_type: len(handlers)
                    for event_type, handlers in self._handlers.items()
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }

