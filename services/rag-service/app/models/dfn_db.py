"""
SQLAlchemy models for RAG Service - Database-agnostic design
Uses generic SQLAlchemy types for portability to MS SQL Server
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class DFN(Base):
    """DFN (Draft Final Note) model - stores generated final notes"""
    
    __tablename__ = "dfns"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    dfn_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ifn_draft_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Generated content
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Context and metadata stored as JSON (database-agnostic)
    context_used: Mapped[dict] = mapped_column(JSON, nullable=False)
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
        Index('idx_speaker_dfn_created', 'speaker_id', 'created_at'),
        Index('idx_session_dfn', 'session_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<DFN(id={self.id}, dfn_id={self.dfn_id}, "
            f"speaker_id={self.speaker_id}, session_id={self.session_id})>"
        )


class RAGSession(Base):
    """RAG Session model - stores RAG workflow session data"""
    
    __tablename__ = "rag_sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    speaker_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ifn_draft_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Session data stored as JSON (database-agnostic)
    # Structure: {"retrieved_docs": [...], "context_summary": "..."}
    context_retrieved: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Prompts and agent steps stored as JSON arrays (database-agnostic)
    # Structure: ["prompt1", "prompt2", ...]
    prompts_used: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Agent workflow steps stored as JSON array (database-agnostic)
    # Structure: [{"step": "retrieve", "timestamp": "...", "result": "..."}, ...]
    agent_steps: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status fields
    dfn_generated: Mapped[bool] = mapped_column(default=False, nullable=False)
    dfn_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
        Index('idx_speaker_session_created', 'speaker_id', 'created_at'),
        Index('idx_session_status', 'status'),
        Index('idx_session_dfn', 'dfn_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<RAGSession(id={self.id}, session_id={self.session_id}, "
            f"speaker_id={self.speaker_id}, status={self.status})>"
        )

