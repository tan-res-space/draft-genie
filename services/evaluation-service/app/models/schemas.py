"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Evaluation Schemas

class EvaluationBase(BaseModel):
    """Base evaluation schema"""
    speaker_id: str
    ifn_draft_id: str
    dfn_id: str
    session_id: str


class EvaluationCreate(EvaluationBase):
    """Schema for creating evaluation"""
    evaluation_id: str
    ifn_text: str
    dfn_text: str
    ifn_word_count: int
    dfn_word_count: int
    sentence_edit_rate: float
    word_error_rate: float
    semantic_similarity: float
    quality_score: float
    improvement_score: float
    current_bucket: str
    recommended_bucket: Optional[str] = None
    bucket_changed: bool = False
    metrics_detail: Optional[Dict[str, Any]] = None


class EvaluationResponse(EvaluationBase):
    """Schema for evaluation response"""
    id: int
    evaluation_id: str
    ifn_text: str
    dfn_text: str
    ifn_word_count: int
    dfn_word_count: int
    sentence_edit_rate: float
    word_error_rate: float
    semantic_similarity: float
    quality_score: float
    improvement_score: float
    current_bucket: str
    recommended_bucket: Optional[str]
    bucket_changed: bool
    metrics_detail: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationSummary(BaseModel):
    """Summary schema for evaluation list"""
    id: int
    evaluation_id: str
    speaker_id: str
    dfn_id: str
    quality_score: float
    improvement_score: float
    current_bucket: str
    recommended_bucket: Optional[str]
    bucket_changed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Metric Schemas

class MetricBase(BaseModel):
    """Base metric schema"""
    speaker_id: str


class MetricCreate(MetricBase):
    """Schema for creating metric"""
    metric_id: str
    total_evaluations: int = 0
    avg_quality_score: float = 0.0
    avg_improvement_score: float = 0.0
    avg_semantic_similarity: float = 0.0
    avg_ser: float = 0.0
    avg_wer: float = 0.0
    current_bucket: str
    bucket_changes: int = 0
    trend_data: Optional[Dict[str, Any]] = None


class MetricUpdate(BaseModel):
    """Schema for updating metric"""
    total_evaluations: Optional[int] = None
    avg_quality_score: Optional[float] = None
    avg_improvement_score: Optional[float] = None
    avg_semantic_similarity: Optional[float] = None
    avg_ser: Optional[float] = None
    avg_wer: Optional[float] = None
    current_bucket: Optional[str] = None
    bucket_changes: Optional[int] = None
    trend_data: Optional[Dict[str, Any]] = None


class MetricResponse(MetricBase):
    """Schema for metric response"""
    id: int
    metric_id: str
    total_evaluations: int
    avg_quality_score: float
    avg_improvement_score: float
    avg_semantic_similarity: float
    avg_ser: float
    avg_wer: float
    current_bucket: str
    bucket_changes: int
    trend_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# API Request/Response Schemas

class TriggerEvaluationRequest(BaseModel):
    """Schema for manual evaluation trigger"""
    speaker_id: str = Field(..., description="Speaker UUID")
    dfn_id: str = Field(..., description="DFN ID to evaluate")


class TriggerEvaluationResponse(BaseModel):
    """Schema for evaluation trigger response"""
    evaluation_id: str
    message: str
    status: str


class EvaluationListResponse(BaseModel):
    """Schema for evaluation list response"""
    evaluations: list[EvaluationSummary]
    total: int
    page: int
    page_size: int


class MetricListResponse(BaseModel):
    """Schema for metric list response"""
    metrics: list[MetricResponse]
    total: int


class AggregatedMetricsResponse(BaseModel):
    """Schema for aggregated metrics response"""
    total_evaluations: int
    avg_quality_score: float
    avg_improvement_score: float
    avg_semantic_similarity: float
    bucket_distribution: Dict[str, int]
    recent_evaluations: list[EvaluationSummary]


# Event Schemas

class DFNGeneratedEvent(BaseModel):
    """Schema for DFNGeneratedEvent from RAG Service"""
    event_type: str = "DFNGenerated"
    dfn_id: str
    speaker_id: str
    session_id: str
    ifn_draft_id: str
    generated_text: str
    word_count: int
    confidence_score: float
    timestamp: str


class BucketReassignedEvent(BaseModel):
    """Schema for BucketReassignedEvent"""
    event_type: str = "BucketReassigned"
    speaker_id: str
    evaluation_id: str
    old_bucket: str
    new_bucket: str
    quality_score: float
    improvement_score: float
    timestamp: str


class EvaluationCompletedEvent(BaseModel):
    """Schema for EvaluationCompletedEvent"""
    event_type: str = "EvaluationCompleted"
    evaluation_id: str
    speaker_id: str
    dfn_id: str
    quality_score: float
    improvement_score: float
    bucket_changed: bool
    timestamp: str

