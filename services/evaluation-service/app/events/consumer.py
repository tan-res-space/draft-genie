"""
RabbitMQ Event Consumer
"""
import json
import asyncio
from typing import Optional, Callable, Awaitable
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractQueue

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventConsumer:
    """RabbitMQ event consumer"""

    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.queue: Optional[AbstractQueue] = None
        self.consumer_tag: Optional[str] = None

    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}")
            
            self.connection = await connect_robust(
                settings.rabbitmq_url,
                client_properties={"connection_name": "evaluation-service-consumer"},
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                "evaluation_service_queue",
                durable=True,
            )
            
            # Bind queue to exchange with routing key
            await self.queue.bind(exchange, routing_key="dfn.generated")
            
            logger.info("RabbitMQ consumer connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        try:
            if self.consumer_tag and self.queue:
                await self.queue.cancel(self.consumer_tag)
            
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
            
            logger.info("RabbitMQ consumer disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")

    async def start_consuming(
        self,
        callback: Callable[[dict], Awaitable[None]],
    ) -> None:
        """
        Start consuming messages
        
        Args:
            callback: Async function to handle messages
        """
        try:
            if not self.queue:
                raise RuntimeError("Consumer not connected")
            
            logger.info("Starting to consume messages...")
            
            async def process_message(message: IncomingMessage) -> None:
                """Process incoming message"""
                async with message.process():
                    try:
                        # Parse message body
                        body = json.loads(message.body.decode())
                        
                        logger.info(
                            f"Received message: {body.get('event_type', 'unknown')} "
                            f"(correlation_id={message.correlation_id})"
                        )
                        
                        # Call callback
                        await callback(body)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
            
            # Start consuming
            self.consumer_tag = await self.queue.consume(process_message)
            
            logger.info("Consumer started successfully")
            
        except Exception as e:
            logger.error(f"Error starting consumer: {e}")
            raise

    async def health_check(self) -> bool:
        """Check consumer health"""
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
event_consumer = EventConsumer()

