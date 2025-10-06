"""
SQLAlchemy models for Evaluation Service
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Evaluation(Base):
    """Evaluation model - stores draft comparison results"""
    
    __tablename__ = "evaluations"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    evaluation_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    ifn_draft_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dfn_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Draft content
    ifn_text: Mapped[str] = mapped_column(Text, nullable=False)
    dfn_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Word counts
    ifn_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dfn_word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Metrics
    sentence_edit_rate: Mapped[float] = mapped_column(Float, nullable=False)  # SER
    word_error_rate: Mapped[float] = mapped_column(Float, nullable=False)  # WER
    semantic_similarity: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    improvement_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    
    # Bucket information
    current_bucket: Mapped[str] = mapped_column(String(10), nullable=False)  # A, B, C
    recommended_bucket: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # A, B, C
    bucket_changed: Mapped[bool] = mapped_column(default=False)
    
    # Detailed metrics
    metrics_detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )

    # Indexes for common queries
    __table_args__ = (
        Index('idx_speaker_created', 'speaker_id', 'created_at'),
        Index('idx_quality_score', 'quality_score'),
        Index('idx_bucket', 'current_bucket', 'recommended_bucket'),
    )

    def __repr__(self) -> str:
        return (
            f"<Evaluation(id={self.id}, evaluation_id={self.evaluation_id}, "
            f"speaker_id={self.speaker_id}, quality_score={self.quality_score})>"
        )


class Metric(Base):
    """Metric model - stores aggregated metrics per speaker"""
    
    __tablename__ = "metrics"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    metric_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Aggregated metrics
    total_evaluations: Mapped[int] = mapped_column(Integer, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_improvement_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_semantic_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    avg_ser: Mapped[float] = mapped_column(Float, default=0.0)
    avg_wer: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Bucket statistics
    current_bucket: Mapped[str] = mapped_column(String(10), nullable=False)
    bucket_changes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Trend data
    trend_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )

    # Indexes
    __table_args__ = (
        Index('idx_speaker_bucket', 'speaker_id', 'current_bucket'),
        Index('idx_avg_quality', 'avg_quality_score'),
    )

    def __repr__(self) -> str:
        return (
            f"<Metric(id={self.id}, metric_id={self.metric_id}, "
            f"speaker_id={self.speaker_id}, avg_quality_score={self.avg_quality_score})>"
        )

