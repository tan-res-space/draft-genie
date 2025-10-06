"""Domain events for DraftGenie."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from common.constants import BucketType, DraftType, EvaluationStatus
from common.utils import generate_correlation_id, generate_id


class DomainEvent(BaseModel):
    """Base domain event."""

    event_id: str = Field(default_factory=generate_id, description="Unique event ID")
    event_type: str = Field(..., description="Event type")
    aggregate_id: str = Field(..., description="Aggregate ID (e.g., speaker_id)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    correlation_id: str = Field(
        default_factory=generate_correlation_id, description="Correlation ID for tracing"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "event_id": "a50e8400-e29b-41d4-a716-446655440000",
                "event_type": "SpeakerOnboarded",
                "aggregate_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-10-03T10:00:00Z",
                "payload": {"speaker_id": "550e8400-e29b-41d4-a716-446655440000"},
                "metadata": {"service": "speaker-service", "user_id": "user-123"},
                "correlation_id": "b60e8400-e29b-41d4-a716-446655440000",
            }
        }


# Speaker Events


class SpeakerOnboardedEvent(DomainEvent):
    """Event emitted when a speaker is onboarded."""

    event_type: str = Field(default="SpeakerOnboarded", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        external_id: str,
        name: str,
        bucket: BucketType,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "SpeakerOnboardedEvent":
        """Create a SpeakerOnboardedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "external_id": external_id,
                "name": name,
                "bucket": bucket.value,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class SpeakerUpdatedEvent(DomainEvent):
    """Event emitted when a speaker is updated."""

    event_type: str = Field(default="SpeakerUpdated", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "SpeakerUpdatedEvent":
        """Create a SpeakerUpdatedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={"speaker_id": speaker_id, "changes": changes},
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class BucketReassignedEvent(DomainEvent):
    """Event emitted when a speaker's bucket is reassigned."""

    event_type: str = Field(default="BucketReassigned", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        old_bucket: BucketType,
        new_bucket: BucketType,
        reason: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "BucketReassignedEvent":
        """Create a BucketReassignedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "old_bucket": old_bucket.value,
                "new_bucket": new_bucket.value,
                "reason": reason,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


# Draft Events


class DraftIngestedEvent(DomainEvent):
    """Event emitted when drafts are ingested."""

    event_type: str = Field(default="DraftIngested", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        draft_ids: list[str],
        draft_types: list[DraftType],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DraftIngestedEvent":
        """Create a DraftIngestedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "draft_ids": draft_ids,
                "draft_types": [dt.value for dt in draft_types],
                "count": len(draft_ids),
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class CorrectionVectorCreatedEvent(DomainEvent):
    """Event emitted when correction vectors are created."""

    event_type: str = Field(default="CorrectionVectorCreated", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        vector_id: str,
        pattern_count: int,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CorrectionVectorCreatedEvent":
        """Create a CorrectionVectorCreatedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "vector_id": vector_id,
                "pattern_count": pattern_count,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class CorrectionVectorUpdatedEvent(DomainEvent):
    """Event emitted when correction vectors are updated."""

    event_type: str = Field(default="CorrectionVectorUpdated", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        vector_id: str,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CorrectionVectorUpdatedEvent":
        """Create a CorrectionVectorUpdatedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "vector_id": vector_id,
                "changes": changes,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


# RAG Events


class DFNGeneratedEvent(DomainEvent):
    """Event emitted when a DFN is generated."""

    event_type: str = Field(default="DFNGenerated", description="Event type")

    @classmethod
    def create(
        cls,
        speaker_id: str,
        dfn_id: str,
        source_draft_id: str,
        generation_time_ms: int,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DFNGeneratedEvent":
        """Create a DFNGeneratedEvent."""
        return cls(
            aggregate_id=speaker_id,
            payload={
                "speaker_id": speaker_id,
                "dfn_id": dfn_id,
                "source_draft_id": source_draft_id,
                "generation_time_ms": generation_time_ms,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


# Evaluation Events


class EvaluationStartedEvent(DomainEvent):
    """Event emitted when an evaluation starts."""

    event_type: str = Field(default="EvaluationStarted", description="Event type")

    @classmethod
    def create(
        cls,
        evaluation_id: str,
        speaker_id: str,
        dfn_id: str,
        ifn_id: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "EvaluationStartedEvent":
        """Create an EvaluationStartedEvent."""
        return cls(
            aggregate_id=evaluation_id,
            payload={
                "evaluation_id": evaluation_id,
                "speaker_id": speaker_id,
                "dfn_id": dfn_id,
                "ifn_id": ifn_id,
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class EvaluationCompletedEvent(DomainEvent):
    """Event emitted when an evaluation completes."""

    event_type: str = Field(default="EvaluationCompleted", description="Event type")

    @classmethod
    def create(
        cls,
        evaluation_id: str,
        speaker_id: str,
        metrics: Dict[str, float],
        recommended_bucket: Optional[BucketType] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "EvaluationCompletedEvent":
        """Create an EvaluationCompletedEvent."""
        payload = {
            "evaluation_id": evaluation_id,
            "speaker_id": speaker_id,
            "metrics": metrics,
        }
        if recommended_bucket:
            payload["recommended_bucket"] = recommended_bucket.value

        return cls(
            aggregate_id=evaluation_id,
            payload=payload,
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )


class EvaluationFailedEvent(DomainEvent):
    """Event emitted when an evaluation fails."""

    event_type: str = Field(default="EvaluationFailed", description="Event type")

    @classmethod
    def create(
        cls,
        evaluation_id: str,
        speaker_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "EvaluationFailedEvent":
        """Create an EvaluationFailedEvent."""
        return cls(
            aggregate_id=evaluation_id,
            payload={
                "evaluation_id": evaluation_id,
                "speaker_id": speaker_id,
                "error_message": error_message,
                "error_details": error_details or {},
            },
            metadata=metadata or {},
            correlation_id=correlation_id or generate_correlation_id(),
        )

