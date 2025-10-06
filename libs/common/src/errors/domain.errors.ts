import { BaseError, ErrorCode } from './base.error';

export class NotFoundError extends BaseError {
  constructor(resource: string, identifier?: string) {
    const message = identifier
      ? `${resource} with identifier '${identifier}' not found`
      : `${resource} not found`;
    super(ErrorCode.NOT_FOUND, message, 404);
  }
}

export class ValidationError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.VALIDATION_ERROR, message, 400, details);
  }
}

export class ConflictError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.CONFLICT, message, 409, details);
  }
}

export class UnauthorizedError extends BaseError {
  constructor(message: string = 'Unauthorized') {
    super(ErrorCode.UNAUTHORIZED, message, 401);
  }
}

export class ForbiddenError extends BaseError {
  constructor(message: string = 'Forbidden') {
    super(ErrorCode.FORBIDDEN, message, 403);
  }
}

export class BadRequestError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.BAD_REQUEST, message, 400, details);
  }
}

export class InternalServerError extends BaseError {
  constructor(message: string = 'Internal server error', details?: any) {
    super(ErrorCode.INTERNAL_SERVER_ERROR, message, 500, details, false);
  }
}

// Speaker-specific errors
export class SpeakerNotFoundError extends BaseError {
  constructor(speakerId: string) {
    super(
      ErrorCode.SPEAKER_NOT_FOUND,
      `Speaker with ID '${speakerId}' not found`,
      404,
    );
  }
}

export class SpeakerAlreadyExistsError extends BaseError {
  constructor(identifier: string) {
    super(
      ErrorCode.SPEAKER_ALREADY_EXISTS,
      `Speaker with identifier '${identifier}' already exists`,
      409,
    );
  }
}

// Draft-specific errors
export class DraftNotFoundError extends BaseError {
  constructor(draftId: string) {
    super(
      ErrorCode.DRAFT_NOT_FOUND,
      `Draft with ID '${draftId}' not found`,
      404,
    );
  }
}

export class DraftIngestionError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.DRAFT_INGESTION_FAILED, message, 500, details);
  }
}

export class InstaNotApiError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.INSTANOTE_API_ERROR, message, 502, details);
  }
}

// Vector-specific errors
export class VectorGenerationError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.VECTOR_GENERATION_FAILED, message, 500, details);
  }
}

export class VectorSearchError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.VECTOR_SEARCH_FAILED, message, 500, details);
  }
}

// RAG-specific errors
export class RagGenerationError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.RAG_GENERATION_FAILED, message, 500, details);
  }
}

export class LlmApiError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.LLM_API_ERROR, message, 502, details);
  }
}

// Evaluation-specific errors
export class EvaluationError extends BaseError {
  constructor(message: string, details?: any) {
    super(ErrorCode.EVALUATION_FAILED, message, 500, details);
  }
}

