"""Pydantic models for DraftGenie domain entities."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from common.constants import BucketType, DraftType, EvaluationStatus, SpeakerStatus


class SpeakerMetadata(BaseModel):
    """Speaker metadata."""

    ser: Optional[float] = Field(None, description="Sentence Edit Rate")
    wer: Optional[float] = Field(None, description="Word Error Rate")
    draft_count: int = Field(0, description="Total number of drafts")
    evaluation_count: int = Field(0, description="Total number of evaluations")
    last_evaluation_date: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ser", "wer")
    @classmethod
    def validate_rate(cls, v: Optional[float]) -> Optional[float]:
        """Validate rate is between 0 and 1."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Rate must be between 0 and 1")
        return v


class Speaker(BaseModel):
    """Speaker domain model."""

    id: str = Field(..., description="Unique speaker ID")
    external_id: str = Field(..., description="External system ID")
    name: str = Field(..., description="Speaker name")
    email: Optional[str] = Field(None, description="Speaker email")
    bucket: BucketType = Field(..., description="Quality bucket")
    status: SpeakerStatus = Field(
        default=SpeakerStatus.ACTIVE, description="Speaker status"
    )
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: SpeakerMetadata = Field(
        default_factory=SpeakerMetadata, description="Speaker metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "external_id": "SPEAKER-001",
                "name": "Dr. John Smith",
                "email": "john.smith@example.com",
                "bucket": "AVERAGE",
                "status": "ACTIVE",
                "metadata": {
                    "ser": 0.15,
                    "wer": 0.12,
                    "draft_count": 10,
                    "evaluation_count": 5,
                },
            }
        }


class DraftMetadata(BaseModel):
    """Draft metadata."""

    word_count: int = Field(0, description="Number of words")
    sentence_count: int = Field(0, description="Number of sentences")
    source: str = Field("instanote", description="Source system")
    language: str = Field("en", description="Language code")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class Draft(BaseModel):
    """Draft domain model."""

    draft_id: str = Field(..., description="Unique draft ID")
    speaker_id: str = Field(..., description="Speaker ID")
    draft_type: DraftType = Field(..., description="Type of draft")
    content: str = Field(..., description="Draft content")
    metadata: DraftMetadata = Field(
        default_factory=DraftMetadata, description="Draft metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "draft_id": "650e8400-e29b-41d4-a716-446655440000",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "draft_type": "ASR_DRAFT",
                "content": "Patient presents with chest pain...",
                "metadata": {
                    "word_count": 150,
                    "sentence_count": 8,
                    "source": "instanote",
                },
            }
        }


class CorrectionPattern(BaseModel):
    """Individual correction pattern."""

    original: str = Field(..., description="Original text")
    corrected: str = Field(..., description="Corrected text")
    category: str = Field(..., description="Correction category")
    frequency: int = Field(1, description="Frequency of this pattern")
    confidence: float = Field(1.0, description="Confidence score")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class CorrectionVector(BaseModel):
    """Correction vector domain model."""

    vector_id: str = Field(..., description="Unique vector ID")
    speaker_id: str = Field(..., description="Speaker ID")
    patterns: List[CorrectionPattern] = Field(
        default_factory=list, description="Correction patterns"
    )
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "vector_id": "750e8400-e29b-41d4-a716-446655440000",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "patterns": [
                    {
                        "original": "pateint",
                        "corrected": "patient",
                        "category": "spelling",
                        "frequency": 5,
                        "confidence": 0.95,
                    }
                ],
            }
        }


class DFNMetadata(BaseModel):
    """DraftGenie Final Note metadata."""

    model: str = Field("gemini-pro", description="LLM model used")
    prompt_version: str = Field("1.0", description="Prompt version")
    context_vectors_used: int = Field(0, description="Number of context vectors used")
    generation_time_ms: int = Field(0, description="Generation time in milliseconds")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class DraftGenieNote(BaseModel):
    """DraftGenie Final Note (DFN) domain model."""

    dfn_id: str = Field(..., description="Unique DFN ID")
    speaker_id: str = Field(..., description="Speaker ID")
    source_draft_id: str = Field(..., description="Source draft ID (AD or LD)")
    content: str = Field(..., description="Generated content")
    metadata: DFNMetadata = Field(
        default_factory=DFNMetadata, description="DFN metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "dfn_id": "850e8400-e29b-41d4-a716-446655440000",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_draft_id": "650e8400-e29b-41d4-a716-446655440000",
                "content": "Patient presents with chest pain...",
                "metadata": {
                    "model": "gemini-pro",
                    "prompt_version": "1.0",
                    "context_vectors_used": 5,
                    "generation_time_ms": 1500,
                },
            }
        }


class EvaluationMetrics(BaseModel):
    """Evaluation metrics."""

    ser: float = Field(..., description="Sentence Edit Rate")
    wer: float = Field(..., description="Word Error Rate")
    accuracy: float = Field(..., description="Accuracy score")
    similarity: float = Field(..., description="Semantic similarity")
    improvement_score: float = Field(..., description="Overall improvement score")

    @field_validator("ser", "wer", "accuracy", "similarity", "improvement_score")
    @classmethod
    def validate_metric(cls, v: float) -> float:
        """Validate metric is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Metric must be between 0 and 1")
        return v


class ComparisonDetail(BaseModel):
    """Comparison details between DFN and IFN."""

    total_sentences: int = Field(..., description="Total sentences")
    changed_sentences: int = Field(..., description="Changed sentences")
    total_words: int = Field(..., description="Total words")
    changed_words: int = Field(..., description="Changed words")
    changes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed changes"
    )


class Evaluation(BaseModel):
    """Evaluation domain model."""

    id: str = Field(..., description="Unique evaluation ID")
    speaker_id: str = Field(..., description="Speaker ID")
    dfn_id: str = Field(..., description="DFN ID")
    ifn_id: str = Field(..., description="IFN ID (reference)")
    status: EvaluationStatus = Field(..., description="Evaluation status")
    metrics: EvaluationMetrics = Field(..., description="Evaluation metrics")
    comparison: Optional[ComparisonDetail] = Field(
        None, description="Comparison details"
    )
    recommended_bucket: Optional[BucketType] = Field(
        None, description="Recommended bucket"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "950e8400-e29b-41d4-a716-446655440000",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "dfn_id": "850e8400-e29b-41d4-a716-446655440000",
                "ifn_id": "750e8400-e29b-41d4-a716-446655440000",
                "status": "COMPLETED",
                "metrics": {
                    "ser": 0.10,
                    "wer": 0.08,
                    "accuracy": 0.92,
                    "similarity": 0.95,
                    "improvement_score": 0.88,
                },
                "recommended_bucket": "GOOD",
            }
        }

