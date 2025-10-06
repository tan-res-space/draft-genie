"""
Events module - RabbitMQ event publishing
"""
from app.events.publisher import EventPublisher, event_publisher

__all__ = ["EventPublisher", "event_publisher"]

