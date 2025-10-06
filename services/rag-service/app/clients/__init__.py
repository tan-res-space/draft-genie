"""
Clients module - HTTP clients for external services
"""
from app.clients.speaker_client import SpeakerClient
from app.clients.draft_client import DraftClient

__all__ = ["SpeakerClient", "DraftClient"]

