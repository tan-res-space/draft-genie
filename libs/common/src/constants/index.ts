// Bucket types for speaker categorization
export enum BucketType {
  EXCELLENT = 'EXCELLENT',
  GOOD = 'GOOD',
  AVERAGE = 'AVERAGE',
  POOR = 'POOR',
  NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT',
}

// Draft types
export enum DraftType {
  ASR_DRAFT = 'ASR_DRAFT', // AD - ASR Drafts from InstaNote
  LLM_DRAFT = 'LLM_DRAFT', // LD - LLM-generated Drafts
  INSTANOTE_FINAL = 'INSTANOTE_FINAL', // IFN - InstaNote Final Notes
  DRAFTGENIE_FINAL = 'DRAFTGENIE_FINAL', // DFN - DraftGenie Final Notes
}

// Speaker status
export enum SpeakerStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  PENDING = 'PENDING',
  ARCHIVED = 'ARCHIVED',
}

// Evaluation status
export enum EvaluationStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

// User roles for RBAC
export enum UserRole {
  ADMIN = 'ADMIN',
  OPERATOR = 'OPERATOR',
  QA_REVIEWER = 'QA_REVIEWER',
  PARTNER = 'PARTNER',
  VIEWER = 'VIEWER',
}

// API response status
export enum ResponseStatus {
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR',
  PARTIAL_SUCCESS = 'PARTIAL_SUCCESS',
}

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Metric thresholds
export const METRIC_THRESHOLDS = {
  EXCELLENT_SER: 0.05, // SER < 5%
  GOOD_SER: 0.10, // SER < 10%
  AVERAGE_SER: 0.20, // SER < 20%
  EXCELLENT_WER: 0.05, // WER < 5%
  GOOD_WER: 0.10, // WER < 10%
  AVERAGE_WER: 0.20, // WER < 20%
};

// Cache TTL (in seconds)
export const CACHE_TTL = {
  SHORT: 300, // 5 minutes
  MEDIUM: 1800, // 30 minutes
  LONG: 3600, // 1 hour
  VERY_LONG: 86400, // 24 hours
};

// Rate limiting
export const RATE_LIMIT = {
  WINDOW_MS: 15 * 60 * 1000, // 15 minutes
  MAX_REQUESTS: 100, // Max requests per window
};

