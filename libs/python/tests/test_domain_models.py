"""Tests for domain models."""

import pytest
from datetime import datetime

from common.constants import BucketType, DraftType, EvaluationStatus, SpeakerStatus
from domain.models import (
    Speaker,
    SpeakerMetadata,
    Draft,
    DraftMetadata,
    CorrectionVector,
    CorrectionPattern,
    DraftGenieNote,
    DFNMetadata,
    Evaluation,
    EvaluationMetrics,
    ComparisonDetail,
)


class TestSpeakerMetadata:
    """Tests for SpeakerMetadata."""

    def test_create_speaker_metadata(self):
        """Test creating speaker metadata."""
        metadata = SpeakerMetadata(
            ser=0.15,
            wer=0.12,
            draft_count=10,
            evaluation_count=5,
        )
        assert metadata.ser == 0.15
        assert metadata.wer == 0.12
        assert metadata.draft_count == 10
        assert metadata.evaluation_count == 5

    def test_invalid_ser(self):
        """Test invalid SER value."""
        with pytest.raises(ValueError):
            SpeakerMetadata(ser=1.5)

    def test_invalid_wer(self):
        """Test invalid WER value."""
        with pytest.raises(ValueError):
            SpeakerMetadata(wer=-0.1)


class TestSpeaker:
    """Tests for Speaker model."""

    def test_create_speaker(self):
        """Test creating a speaker."""
        speaker = Speaker(
            id="550e8400-e29b-41d4-a716-446655440000",
            external_id="SPEAKER-001",
            name="Dr. John Smith",
            email="john.smith@example.com",
            bucket=BucketType.AVERAGE,
            status=SpeakerStatus.ACTIVE,
        )
        assert speaker.id == "550e8400-e29b-41d4-a716-446655440000"
        assert speaker.external_id == "SPEAKER-001"
        assert speaker.name == "Dr. John Smith"
        assert speaker.bucket == BucketType.AVERAGE
        assert speaker.status == SpeakerStatus.ACTIVE

    def test_speaker_with_metadata(self):
        """Test speaker with metadata."""
        metadata = SpeakerMetadata(ser=0.15, wer=0.12)
        speaker = Speaker(
            id="550e8400-e29b-41d4-a716-446655440000",
            external_id="SPEAKER-001",
            name="Dr. John Smith",
            bucket=BucketType.AVERAGE,
            metadata=metadata,
        )
        assert speaker.metadata.ser == 0.15
        assert speaker.metadata.wer == 0.12


class TestDraft:
    """Tests for Draft model."""

    def test_create_draft(self):
        """Test creating a draft."""
        draft = Draft(
            draft_id="650e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            draft_type=DraftType.ASR_DRAFT,
            content="Patient presents with chest pain...",
        )
        assert draft.draft_id == "650e8400-e29b-41d4-a716-446655440000"
        assert draft.speaker_id == "550e8400-e29b-41d4-a716-446655440000"
        assert draft.draft_type == DraftType.ASR_DRAFT
        assert "chest pain" in draft.content

    def test_draft_with_metadata(self):
        """Test draft with metadata."""
        metadata = DraftMetadata(word_count=150, sentence_count=8)
        draft = Draft(
            draft_id="650e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            draft_type=DraftType.ASR_DRAFT,
            content="Test content",
            metadata=metadata,
        )
        assert draft.metadata.word_count == 150
        assert draft.metadata.sentence_count == 8


class TestCorrectionVector:
    """Tests for CorrectionVector model."""

    def test_create_correction_pattern(self):
        """Test creating a correction pattern."""
        pattern = CorrectionPattern(
            original="pateint",
            corrected="patient",
            category="spelling",
            frequency=5,
            confidence=0.95,
        )
        assert pattern.original == "pateint"
        assert pattern.corrected == "patient"
        assert pattern.category == "spelling"
        assert pattern.frequency == 5
        assert pattern.confidence == 0.95

    def test_invalid_confidence(self):
        """Test invalid confidence value."""
        with pytest.raises(ValueError):
            CorrectionPattern(
                original="test",
                corrected="test",
                category="spelling",
                confidence=1.5,
            )

    def test_create_correction_vector(self):
        """Test creating a correction vector."""
        patterns = [
            CorrectionPattern(
                original="pateint",
                corrected="patient",
                category="spelling",
                frequency=5,
            )
        ]
        vector = CorrectionVector(
            vector_id="750e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            patterns=patterns,
        )
        assert vector.vector_id == "750e8400-e29b-41d4-a716-446655440000"
        assert len(vector.patterns) == 1
        assert vector.patterns[0].original == "pateint"


class TestDraftGenieNote:
    """Tests for DraftGenieNote model."""

    def test_create_dfn(self):
        """Test creating a DFN."""
        dfn = DraftGenieNote(
            dfn_id="850e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            source_draft_id="650e8400-e29b-41d4-a716-446655440000",
            content="Improved patient note...",
        )
        assert dfn.dfn_id == "850e8400-e29b-41d4-a716-446655440000"
        assert dfn.speaker_id == "550e8400-e29b-41d4-a716-446655440000"
        assert dfn.source_draft_id == "650e8400-e29b-41d4-a716-446655440000"

    def test_dfn_with_metadata(self):
        """Test DFN with metadata."""
        metadata = DFNMetadata(
            model="gemini-pro",
            prompt_version="1.0",
            context_vectors_used=5,
            generation_time_ms=1500,
        )
        dfn = DraftGenieNote(
            dfn_id="850e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            source_draft_id="650e8400-e29b-41d4-a716-446655440000",
            content="Test content",
            metadata=metadata,
        )
        assert dfn.metadata.model == "gemini-pro"
        assert dfn.metadata.context_vectors_used == 5


class TestEvaluation:
    """Tests for Evaluation model."""

    def test_create_evaluation_metrics(self):
        """Test creating evaluation metrics."""
        metrics = EvaluationMetrics(
            ser=0.10,
            wer=0.08,
            accuracy=0.92,
            similarity=0.95,
            improvement_score=0.88,
        )
        assert metrics.ser == 0.10
        assert metrics.wer == 0.08
        assert metrics.accuracy == 0.92

    def test_invalid_metric(self):
        """Test invalid metric value."""
        with pytest.raises(ValueError):
            EvaluationMetrics(
                ser=1.5,
                wer=0.08,
                accuracy=0.92,
                similarity=0.95,
                improvement_score=0.88,
            )

    def test_create_evaluation(self):
        """Test creating an evaluation."""
        metrics = EvaluationMetrics(
            ser=0.10,
            wer=0.08,
            accuracy=0.92,
            similarity=0.95,
            improvement_score=0.88,
        )
        evaluation = Evaluation(
            id="950e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            dfn_id="850e8400-e29b-41d4-a716-446655440000",
            ifn_id="750e8400-e29b-41d4-a716-446655440000",
            status=EvaluationStatus.COMPLETED,
            metrics=metrics,
            recommended_bucket=BucketType.GOOD,
        )
        assert evaluation.id == "950e8400-e29b-41d4-a716-446655440000"
        assert evaluation.status == EvaluationStatus.COMPLETED
        assert evaluation.metrics.ser == 0.10
        assert evaluation.recommended_bucket == BucketType.GOOD

    def test_evaluation_with_comparison(self):
        """Test evaluation with comparison details."""
        metrics = EvaluationMetrics(
            ser=0.10,
            wer=0.08,
            accuracy=0.92,
            similarity=0.95,
            improvement_score=0.88,
        )
        comparison = ComparisonDetail(
            total_sentences=10,
            changed_sentences=2,
            total_words=150,
            changed_words=12,
        )
        evaluation = Evaluation(
            id="950e8400-e29b-41d4-a716-446655440000",
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            dfn_id="850e8400-e29b-41d4-a716-446655440000",
            ifn_id="750e8400-e29b-41d4-a716-446655440000",
            status=EvaluationStatus.COMPLETED,
            metrics=metrics,
            comparison=comparison,
        )
        assert evaluation.comparison.total_sentences == 10
        assert evaluation.comparison.changed_sentences == 2

