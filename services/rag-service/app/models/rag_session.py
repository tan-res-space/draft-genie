"""
RAG Session model
"""
from typing import Optional, Dict, Any, List
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


class RAGSessionModel(BaseModel):
    """RAG Session database model"""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
    )

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    session_id: str = Field(..., description="Session unique identifier")
    speaker_id: str = Field(..., description="Speaker UUID")
    ifn_draft_id: str = Field(..., description="IFN draft ID")
    context_retrieved: Dict[str, Any] = Field(
        default_factory=dict, description="Retrieved context"
    )
    prompts_used: List[str] = Field(default_factory=list, description="Prompts used")
    agent_steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Agent workflow steps"
    )
    dfn_generated: bool = Field(default=False, description="Whether DFN was generated")
    dfn_id: Optional[str] = Field(None, description="Generated DFN ID")
    status: str = Field(default="pending", description="Session status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RAGSessionCreate(BaseModel):
    """Schema for creating a RAG session"""

    session_id: str
    speaker_id: str
    ifn_draft_id: str
    context_retrieved: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGSessionUpdate(BaseModel):
    """Schema for updating a RAG session"""

    prompts_used: Optional[List[str]] = None
    agent_steps: Optional[List[Dict[str, Any]]] = None
    dfn_generated: Optional[bool] = None
    dfn_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RAGSessionResponse(BaseModel):
    """Schema for RAG session response"""

    _id: str
    session_id: str
    speaker_id: str
    ifn_draft_id: str
    context_retrieved: Dict[str, Any]
    prompts_used: List[str]
    agent_steps: List[Dict[str, Any]]
    dfn_generated: bool
    dfn_id: Optional[str]
    status: str
    error_message: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

