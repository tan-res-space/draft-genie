"""Error classes for DraftGenie Python services."""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """Error codes for DraftGenie."""

    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"

    # Speaker errors
    SPEAKER_NOT_FOUND = "SPEAKER_NOT_FOUND"
    SPEAKER_ALREADY_EXISTS = "SPEAKER_ALREADY_EXISTS"
    SPEAKER_VALIDATION_FAILED = "SPEAKER_VALIDATION_FAILED"

    # Draft errors
    DRAFT_NOT_FOUND = "DRAFT_NOT_FOUND"
    DRAFT_INGESTION_FAILED = "DRAFT_INGESTION_FAILED"
    INSTANOTE_API_ERROR = "INSTANOTE_API_ERROR"

    # Vector errors
    VECTOR_GENERATION_FAILED = "VECTOR_GENERATION_FAILED"
    VECTOR_SEARCH_FAILED = "VECTOR_SEARCH_FAILED"
    VECTOR_NOT_FOUND = "VECTOR_NOT_FOUND"

    # RAG errors
    RAG_GENERATION_FAILED = "RAG_GENERATION_FAILED"
    LLM_API_ERROR = "LLM_API_ERROR"
    DFN_GENERATION_FAILED = "DFN_GENERATION_FAILED"

    # Evaluation errors
    EVALUATION_FAILED = "EVALUATION_FAILED"
    METRICS_CALCULATION_FAILED = "METRICS_CALCULATION_FAILED"


class BaseError(Exception):
    """Base error class for DraftGenie."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        is_operational: bool = True,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.is_operational = is_operational

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "code": self.code.value,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class NotFoundError(BaseError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = (
            f"{resource} with identifier '{identifier}' not found"
            if identifier
            else f"{resource} not found"
        )
        super().__init__(ErrorCode.NOT_FOUND, message, 404)


class ValidationError(BaseError):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, 400, details)


class ConflictError(BaseError):
    """Conflict error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.CONFLICT, message, 409, details)


class UnauthorizedError(BaseError):
    """Unauthorized error."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(ErrorCode.UNAUTHORIZED, message, 401)


class ForbiddenError(BaseError):
    """Forbidden error."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(ErrorCode.FORBIDDEN, message, 403)


class BadRequestError(BaseError):
    """Bad request error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.BAD_REQUEST, message, 400, details)


class InternalServerError(BaseError):
    """Internal server error."""

    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INTERNAL_SERVER_ERROR, message, 500, details, False)


# Domain-specific errors

class SpeakerNotFoundError(NotFoundError):
    """Speaker not found error."""

    def __init__(self, speaker_id: str):
        super().__init__("Speaker", speaker_id)
        self.code = ErrorCode.SPEAKER_NOT_FOUND


class SpeakerAlreadyExistsError(ConflictError):
    """Speaker already exists error."""

    def __init__(self, identifier: str):
        super().__init__(f"Speaker with identifier '{identifier}' already exists")
        self.code = ErrorCode.SPEAKER_ALREADY_EXISTS


class DraftNotFoundError(NotFoundError):
    """Draft not found error."""

    def __init__(self, draft_id: str):
        super().__init__("Draft", draft_id)
        self.code = ErrorCode.DRAFT_NOT_FOUND


class DraftIngestionError(BaseError):
    """Draft ingestion error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.DRAFT_INGESTION_FAILED, message, 500, details)


class InstaNotApiError(BaseError):
    """InstaNote API error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INSTANOTE_API_ERROR, message, 502, details)


class VectorGenerationError(BaseError):
    """Vector generation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.VECTOR_GENERATION_FAILED, message, 500, details)


class VectorSearchError(BaseError):
    """Vector search error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.VECTOR_SEARCH_FAILED, message, 500, details)


class RagGenerationError(BaseError):
    """RAG generation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.RAG_GENERATION_FAILED, message, 500, details)


class LlmApiError(BaseError):
    """LLM API error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.LLM_API_ERROR, message, 502, details)


class EvaluationError(BaseError):
    """Evaluation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.EVALUATION_FAILED, message, 500, details)

