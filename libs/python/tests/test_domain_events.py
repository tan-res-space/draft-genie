"""Tests for domain events."""

import pytest
from datetime import datetime

from common.constants import BucketType, DraftType, EvaluationStatus
from domain.events import (
    DomainEvent,
    SpeakerOnboardedEvent,
    SpeakerUpdatedEvent,
    BucketReassignedEvent,
    DraftIngestedEvent,
    CorrectionVectorCreatedEvent,
    CorrectionVectorUpdatedEvent,
    DFNGeneratedEvent,
    EvaluationStartedEvent,
    EvaluationCompletedEvent,
    EvaluationFailedEvent,
)


class TestDomainEvent:
    """Tests for base DomainEvent."""

    def test_create_domain_event(self):
        """Test creating a domain event."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-id",
            payload={"key": "value"},
        )
        assert event.event_type == "TestEvent"
        assert event.aggregate_id == "test-id"
        assert event.payload == {"key": "value"}
        assert event.event_id is not None
        assert event.correlation_id is not None
        assert isinstance(event.timestamp, datetime)


class TestSpeakerEvents:
    """Tests for speaker-related events."""

    def test_speaker_onboarded_event(self):
        """Test SpeakerOnboardedEvent."""
        event = SpeakerOnboardedEvent.create(
            speaker_id="speaker-123",
            external_id="EXT-001",
            name="Dr. Smith",
            bucket=BucketType.AVERAGE,
        )
        assert event.event_type == "SpeakerOnboarded"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["speaker_id"] == "speaker-123"
        assert event.payload["external_id"] == "EXT-001"
        assert event.payload["name"] == "Dr. Smith"
        assert event.payload["bucket"] == "AVERAGE"

    def test_speaker_updated_event(self):
        """Test SpeakerUpdatedEvent."""
        changes = {"name": "Dr. John Smith", "email": "john@example.com"}
        event = SpeakerUpdatedEvent.create(
            speaker_id="speaker-123",
            changes=changes,
        )
        assert event.event_type == "SpeakerUpdated"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["speaker_id"] == "speaker-123"
        assert event.payload["changes"] == changes

    def test_bucket_reassigned_event(self):
        """Test BucketReassignedEvent."""
        event = BucketReassignedEvent.create(
            speaker_id="speaker-123",
            old_bucket=BucketType.AVERAGE,
            new_bucket=BucketType.GOOD,
            reason="Improved quality metrics",
        )
        assert event.event_type == "BucketReassigned"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["old_bucket"] == "AVERAGE"
        assert event.payload["new_bucket"] == "GOOD"
        assert event.payload["reason"] == "Improved quality metrics"


class TestDraftEvents:
    """Tests for draft-related events."""

    def test_draft_ingested_event(self):
        """Test DraftIngestedEvent."""
        draft_ids = ["draft-1", "draft-2", "draft-3"]
        draft_types = [DraftType.ASR_DRAFT, DraftType.LLM_DRAFT, DraftType.INSTANOTE_FINAL]
        
        event = DraftIngestedEvent.create(
            speaker_id="speaker-123",
            draft_ids=draft_ids,
            draft_types=draft_types,
        )
        assert event.event_type == "DraftIngested"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["speaker_id"] == "speaker-123"
        assert event.payload["draft_ids"] == draft_ids
        assert event.payload["count"] == 3
        assert len(event.payload["draft_types"]) == 3

    def test_correction_vector_created_event(self):
        """Test CorrectionVectorCreatedEvent."""
        event = CorrectionVectorCreatedEvent.create(
            speaker_id="speaker-123",
            vector_id="vector-456",
            pattern_count=10,
        )
        assert event.event_type == "CorrectionVectorCreated"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["speaker_id"] == "speaker-123"
        assert event.payload["vector_id"] == "vector-456"
        assert event.payload["pattern_count"] == 10

    def test_correction_vector_updated_event(self):
        """Test CorrectionVectorUpdatedEvent."""
        changes = {"pattern_count": 15, "updated_patterns": ["pattern-1"]}
        event = CorrectionVectorUpdatedEvent.create(
            speaker_id="speaker-123",
            vector_id="vector-456",
            changes=changes,
        )
        assert event.event_type == "CorrectionVectorUpdated"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["vector_id"] == "vector-456"
        assert event.payload["changes"] == changes


class TestRAGEvents:
    """Tests for RAG-related events."""

    def test_dfn_generated_event(self):
        """Test DFNGeneratedEvent."""
        event = DFNGeneratedEvent.create(
            speaker_id="speaker-123",
            dfn_id="dfn-789",
            source_draft_id="draft-456",
            generation_time_ms=1500,
        )
        assert event.event_type == "DFNGenerated"
        assert event.aggregate_id == "speaker-123"
        assert event.payload["speaker_id"] == "speaker-123"
        assert event.payload["dfn_id"] == "dfn-789"
        assert event.payload["source_draft_id"] == "draft-456"
        assert event.payload["generation_time_ms"] == 1500


class TestEvaluationEvents:
    """Tests for evaluation-related events."""

    def test_evaluation_started_event(self):
        """Test EvaluationStartedEvent."""
        event = EvaluationStartedEvent.create(
            evaluation_id="eval-123",
            speaker_id="speaker-456",
            dfn_id="dfn-789",
            ifn_id="ifn-012",
        )
        assert event.event_type == "EvaluationStarted"
        assert event.aggregate_id == "eval-123"
        assert event.payload["evaluation_id"] == "eval-123"
        assert event.payload["speaker_id"] == "speaker-456"
        assert event.payload["dfn_id"] == "dfn-789"
        assert event.payload["ifn_id"] == "ifn-012"

    def test_evaluation_completed_event(self):
        """Test EvaluationCompletedEvent."""
        metrics = {
            "ser": 0.10,
            "wer": 0.08,
            "accuracy": 0.92,
            "similarity": 0.95,
        }
        event = EvaluationCompletedEvent.create(
            evaluation_id="eval-123",
            speaker_id="speaker-456",
            metrics=metrics,
            recommended_bucket=BucketType.GOOD,
        )
        assert event.event_type == "EvaluationCompleted"
        assert event.aggregate_id == "eval-123"
        assert event.payload["evaluation_id"] == "eval-123"
        assert event.payload["speaker_id"] == "speaker-456"
        assert event.payload["metrics"] == metrics
        assert event.payload["recommended_bucket"] == "GOOD"

    def test_evaluation_completed_event_without_bucket(self):
        """Test EvaluationCompletedEvent without recommended bucket."""
        metrics = {"ser": 0.10, "wer": 0.08}
        event = EvaluationCompletedEvent.create(
            evaluation_id="eval-123",
            speaker_id="speaker-456",
            metrics=metrics,
        )
        assert "recommended_bucket" not in event.payload

    def test_evaluation_failed_event(self):
        """Test EvaluationFailedEvent."""
        error_details = {"error_code": "TIMEOUT", "retry_count": 3}
        event = EvaluationFailedEvent.create(
            evaluation_id="eval-123",
            speaker_id="speaker-456",
            error_message="Evaluation timeout",
            error_details=error_details,
        )
        assert event.event_type == "EvaluationFailed"
        assert event.aggregate_id == "eval-123"
        assert event.payload["evaluation_id"] == "eval-123"
        assert event.payload["speaker_id"] == "speaker-456"
        assert event.payload["error_message"] == "Evaluation timeout"
        assert event.payload["error_details"] == error_details


class TestEventCorrelation:
    """Tests for event correlation."""

    def test_custom_correlation_id(self):
        """Test creating event with custom correlation ID."""
        correlation_id = "custom-correlation-123"
        event = SpeakerOnboardedEvent.create(
            speaker_id="speaker-123",
            external_id="EXT-001",
            name="Dr. Smith",
            bucket=BucketType.AVERAGE,
            correlation_id=correlation_id,
        )
        assert event.correlation_id == correlation_id

    def test_custom_metadata(self):
        """Test creating event with custom metadata."""
        metadata = {"user_id": "user-123", "service": "speaker-service"}
        event = SpeakerOnboardedEvent.create(
            speaker_id="speaker-123",
            external_id="EXT-001",
            name="Dr. Smith",
            bucket=BucketType.AVERAGE,
            metadata=metadata,
        )
        assert event.metadata == metadata

    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        event = SpeakerOnboardedEvent.create(
            speaker_id="speaker-123",
            external_id="EXT-001",
            name="Dr. Smith",
            bucket=BucketType.AVERAGE,
        )
        event_dict = event.model_dump()
        
        assert "event_id" in event_dict
        assert "event_type" in event_dict
        assert "aggregate_id" in event_dict
        assert "timestamp" in event_dict
        assert "payload" in event_dict
        assert "correlation_id" in event_dict

