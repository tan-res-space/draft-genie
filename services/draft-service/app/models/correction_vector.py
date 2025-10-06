"""
Correction Vector model for MongoDB
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

from app.models.draft import PyObjectId


class CorrectionPattern(BaseModel):
    """Individual correction pattern"""

    original: str = Field(..., description="Original text")
    corrected: str = Field(..., description="Corrected text")
    category: str = Field(..., description="Correction category")
    frequency: int = Field(default=1, description="Frequency of this pattern")
    context: Optional[str] = Field(default=None, description="Surrounding context")


class CorrectionVectorModel(BaseModel):
    """Correction vector document model"""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    vector_id: str = Field(..., description="Unique vector ID")
    speaker_id: str = Field(..., description="Speaker UUID")
    draft_id: str = Field(..., description="Associated draft ID")
    
    # Correction patterns
    patterns: List[CorrectionPattern] = Field(default_factory=list, description="Correction patterns")
    
    # Statistics
    total_corrections: int = Field(default=0, description="Total number of corrections")
    unique_patterns: int = Field(default=0, description="Number of unique patterns")
    
    # Categories breakdown
    category_counts: Dict[str, int] = Field(
        default_factory=dict, description="Count by category"
    )
    
    # Embedding vector (stored in Qdrant, reference here)
    qdrant_point_id: Optional[str] = Field(default=None, description="Qdrant point ID")
    embedding_model: str = Field(default="gemini-embedding-001", description="Embedding model used")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When record was updated")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "vector_id": "vec_123456",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "draft_id": "draft_123456",
                "patterns": [
                    {
                        "original": "diabetis",
                        "corrected": "diabetes",
                        "category": "spelling",
                        "frequency": 3,
                        "context": "history of diabetis and",
                    }
                ],
                "total_corrections": 5,
                "unique_patterns": 3,
                "category_counts": {"spelling": 3, "grammar": 2},
                "qdrant_point_id": "point_123",
                "embedding_model": "gemini-embedding-001",
            }
        }


class CorrectionVectorCreate(BaseModel):
    """Schema for creating a correction vector"""

    vector_id: str
    speaker_id: str
    draft_id: str
    patterns: List[CorrectionPattern]
    total_corrections: int
    unique_patterns: int
    category_counts: Dict[str, int]
    qdrant_point_id: Optional[str] = None
    embedding_model: str = "gemini-embedding-001"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CorrectionVectorUpdate(BaseModel):
    """Schema for updating a correction vector"""

    patterns: Optional[List[CorrectionPattern]] = None
    total_corrections: Optional[int] = None
    unique_patterns: Optional[int] = None
    category_counts: Optional[Dict[str, int]] = None
    qdrant_point_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CorrectionVectorResponse(BaseModel):
    """Schema for correction vector response"""

    id: str = Field(..., alias="_id")
    vector_id: str
    speaker_id: str
    draft_id: str
    patterns: List[CorrectionPattern]
    total_corrections: int
    unique_patterns: int
    category_counts: Dict[str, int]
    qdrant_point_id: Optional[str]
    embedding_model: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

