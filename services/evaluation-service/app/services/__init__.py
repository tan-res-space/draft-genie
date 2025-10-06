"""
Services module - Business logic
"""
from app.services.comparison_service import ComparisonService, get_comparison_service
from app.services.similarity_service import SimilarityService, get_similarity_service
from app.services.evaluation_service import EvaluationService, get_evaluation_service
from app.services.draft_client import DraftClient, get_draft_client
from app.services.rag_client import RAGClient, get_rag_client
from app.services.speaker_client import SpeakerClient, get_speaker_client

__all__ = [
    "ComparisonService",
    "get_comparison_service",
    "SimilarityService",
    "get_similarity_service",
    "EvaluationService",
    "get_evaluation_service",
    "DraftClient",
    "get_draft_client",
    "RAGClient",
    "get_rag_client",
    "SpeakerClient",
    "get_speaker_client",
]

