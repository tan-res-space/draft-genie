"""
Draft model for MongoDB
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}


class DraftModel(BaseModel):
    """Draft document model"""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    draft_id: str = Field(..., description="Unique draft ID from InstaNote")
    speaker_id: str = Field(..., description="Speaker UUID")
    draft_type: str = Field(..., description="Draft type: AD, LD, or IFN")
    
    # Draft content
    original_text: str = Field(..., description="Original dictated text")
    corrected_text: str = Field(..., description="Corrected/final text")
    
    # Metadata
    word_count: int = Field(default=0, description="Word count of original text")
    correction_count: int = Field(default=0, description="Number of corrections made")
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Timestamps
    dictated_at: Optional[datetime] = Field(default=None, description="When draft was dictated")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When record was updated")
    
    # Processing status
    is_processed: bool = Field(default=False, description="Whether corrections have been extracted")
    vector_generated: bool = Field(default=False, description="Whether embedding vector was generated")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "draft_id": "draft_123456",
                "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                "draft_type": "AD",
                "original_text": "The patient has a history of diabetis and hypertension.",
                "corrected_text": "The patient has a history of diabetes and hypertension.",
                "word_count": 10,
                "correction_count": 1,
                "metadata": {"source": "instanote", "version": "1.0"},
                "dictated_at": "2025-10-06T10:00:00Z",
                "is_processed": False,
                "vector_generated": False,
            }
        }


class DraftCreate(BaseModel):
    """Schema for creating a draft"""

    draft_id: str
    speaker_id: str
    draft_type: str
    original_text: str
    corrected_text: str
    word_count: Optional[int] = None
    correction_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dictated_at: Optional[datetime] = None


class DraftUpdate(BaseModel):
    """Schema for updating a draft"""

    original_text: Optional[str] = None
    corrected_text: Optional[str] = None
    word_count: Optional[int] = None
    correction_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    is_processed: Optional[bool] = None
    vector_generated: Optional[bool] = None


class DraftResponse(BaseModel):
    """Schema for draft response"""

    id: str = Field(..., alias="_id")
    draft_id: str
    speaker_id: str
    draft_type: str
    original_text: str
    corrected_text: str
    word_count: int
    correction_count: int
    metadata: Dict[str, Any]
    dictated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_processed: bool
    vector_generated: bool

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

