"""
Events module - RabbitMQ event handling
"""
from app.events.consumer import event_consumer
from app.events.handler import event_handler, handle_event

__all__ = ["event_consumer", "event_handler", "handle_event"]

