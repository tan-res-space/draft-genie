"""
DFN (Draft Final Note) model
"""
from typing import Optional, Dict, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class DFNModel(BaseModel):
    """DFN database model"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    dfn_id: str = Field(..., description="DFN unique identifier")
    speaker_id: str = Field(..., description="Speaker UUID")
    session_id: str = Field(..., description="RAG session ID")
    ifn_draft_id: str = Field(..., description="Original IFN draft ID")
    generated_text: str = Field(..., description="Generated DFN text")
    word_count: int = Field(..., description="Word count")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    context_used: Dict[str, Any] = Field(
        default_factory=dict, description="Context used for generation"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DFNCreate(BaseModel):
    """Schema for creating a DFN"""

    dfn_id: str
    speaker_id: str
    session_id: str
    ifn_draft_id: str
    generated_text: str
    word_count: int
    confidence_score: float = Field(ge=0.0, le=1.0)
    context_used: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DFNUpdate(BaseModel):
    """Schema for updating a DFN"""

    generated_text: Optional[str] = None
    word_count: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class DFNResponse(BaseModel):
    """Schema for DFN response"""

    _id: str
    dfn_id: str
    speaker_id: str
    session_id: str
    ifn_draft_id: str
    generated_text: str
    word_count: int
    confidence_score: float
    context_used: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

