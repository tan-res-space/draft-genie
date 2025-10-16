"""
SQLAlchemy models for Draft Service - Database-agnostic design
Uses generic SQLAlchemy types for portability to MS SQL Server
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Draft(Base):
    """Draft model - stores draft documents"""
    
    __tablename__ = "drafts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    draft_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    draft_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # Draft content
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional data stored as JSON (database-agnostic)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    dictated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
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
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vector_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_speaker_created', 'speaker_id', 'created_at'),
        Index('idx_draft_type', 'draft_type'),
        Index('idx_is_processed', 'is_processed'),
        Index('idx_vector_generated', 'vector_generated'),
    )

    def __repr__(self) -> str:
        return (
            f"<Draft(id={self.id}, draft_id={self.draft_id}, "
            f"speaker_id={self.speaker_id}, draft_type={self.draft_type})>"
        )


class CorrectionVector(Base):
    """Correction Vector model - stores correction patterns and metadata"""
    
    __tablename__ = "correction_vectors"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    vector_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    draft_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Correction patterns stored as JSON (database-agnostic)
    # Structure: [{"original": str, "corrected": str, "category": str, "frequency": int, "context": str}]
    patterns: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Statistics
    total_corrections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_patterns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Category counts stored as JSON (database-agnostic)
    # Structure: {"spelling": 3, "grammar": 2, ...}
    category_counts: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Embedding reference
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_model: Mapped[str] = mapped_column(
        String(100), 
        default="gemini-embedding-001", 
        nullable=False
    )
    
    # Additional metadata stored as JSON (database-agnostic)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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
        Index('idx_speaker_vector_created', 'speaker_id', 'created_at'),
        Index('idx_draft_vector', 'draft_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<CorrectionVector(id={self.id}, vector_id={self.vector_id}, "
            f"speaker_id={self.speaker_id}, draft_id={self.draft_id})>"
        )

