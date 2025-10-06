export enum ErrorCode {
  // General errors
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  CONFLICT = 'CONFLICT',
  BAD_REQUEST = 'BAD_REQUEST',

  // Speaker errors
  SPEAKER_NOT_FOUND = 'SPEAKER_NOT_FOUND',
  SPEAKER_ALREADY_EXISTS = 'SPEAKER_ALREADY_EXISTS',
  SPEAKER_VALIDATION_FAILED = 'SPEAKER_VALIDATION_FAILED',

  // Draft errors
  DRAFT_NOT_FOUND = 'DRAFT_NOT_FOUND',
  DRAFT_INGESTION_FAILED = 'DRAFT_INGESTION_FAILED',
  INSTANOTE_API_ERROR = 'INSTANOTE_API_ERROR',

  // Vector errors
  VECTOR_GENERATION_FAILED = 'VECTOR_GENERATION_FAILED',
  VECTOR_SEARCH_FAILED = 'VECTOR_SEARCH_FAILED',
  VECTOR_NOT_FOUND = 'VECTOR_NOT_FOUND',

  // RAG errors
  RAG_GENERATION_FAILED = 'RAG_GENERATION_FAILED',
  LLM_API_ERROR = 'LLM_API_ERROR',
  DFN_GENERATION_FAILED = 'DFN_GENERATION_FAILED',

  // Evaluation errors
  EVALUATION_FAILED = 'EVALUATION_FAILED',
  METRICS_CALCULATION_FAILED = 'METRICS_CALCULATION_FAILED',
}

export interface ErrorDetails {
  code: ErrorCode;
  message: string;
  statusCode: number;
  details?: any;
  stack?: string;
}

export class BaseError extends Error {
  public readonly code: ErrorCode;
  public readonly statusCode: number;
  public readonly details?: any;
  public readonly isOperational: boolean;

  constructor(
    code: ErrorCode,
    message: string,
    statusCode: number = 500,
    details?: any,
    isOperational: boolean = true,
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);

    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.isOperational = isOperational;

    Error.captureStackTrace(this);
  }

  toJSON(): ErrorDetails {
    return {
      code: this.code,
      message: this.message,
      statusCode: this.statusCode,
      details: this.details,
      stack: process.env.NODE_ENV === 'development' ? this.stack : undefined,
    };
  }
}

