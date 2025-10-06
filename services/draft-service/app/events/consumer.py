"""
Event consumer for RabbitMQ
"""
import json
from typing import Optional, Callable, Awaitable
import aio_pika
from aio_pika import IncomingMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventConsumer:
    """Event consumer for RabbitMQ"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_url}")
            
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.rabbitmq_queue,
                durable=True,
            )
            
            # Bind queue to exchange with routing key
            await self.queue.bind(exchange, routing_key=settings.rabbitmq_routing_key)
            
            logger.info(
                f"Connected to RabbitMQ queue: {settings.rabbitmq_queue} "
                f"with routing key: {settings.rabbitmq_routing_key}"
            )
            
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
            self.queue = None
            logger.info("Disconnected from RabbitMQ")

    async def start_consuming(
        self,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        """
        Start consuming messages from the queue
        
        Args:
            callback: Async function to handle incoming messages
        """
        if not self.queue:
            logger.error("Cannot start consuming: Not connected to RabbitMQ")
            return

        async def process_message(message: IncomingMessage) -> None:
            """Process incoming message"""
            async with message.process():
                try:
                    # Parse message
                    event = json.loads(message.body.decode())
                    
                    logger.info(
                        f"Received event {event.get('event_type')} "
                        f"with ID {event.get('event_id')}"
                    )
                    
                    # Call callback
                    await callback(event)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    raise

        logger.info("Starting to consume messages")
        await self.queue.consume(process_message)

    async def health_check(self) -> bool:
        """Check RabbitMQ connection health"""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            return True
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False


# Global event consumer instance
event_consumer = EventConsumer()

