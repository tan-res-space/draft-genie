import { EvaluationStatus, BucketType } from '@draft-genie/common';

export interface QualityMetrics {
  ser: number; // Sentence Edit Rate
  wer: number; // Word Error Rate
  accuracy: number; // Overall accuracy score (0-1)
  similarity: number; // Semantic similarity (0-1)
  improvementScore: number; // Improvement over original draft (0-1)
  [key: string]: any;
}

export interface ComparisonResult {
  additions: number;
  deletions: number;
  modifications: number;
  unchanged: number;
  totalChanges: number;
  changePercentage: number;
}

export interface Evaluation {
  id: string;
  speakerId: string;
  draftId: string; // DFN ID
  referenceDraftId: string; // IFN ID
  status: EvaluationStatus;
  metrics: QualityMetrics;
  comparison: ComparisonResult;
  recommendedBucket?: BucketType;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}

export interface CreateEvaluationDto {
  speakerId: string;
  draftId: string;
  referenceDraftId: string;
}

export interface EvaluationFilter {
  speakerId?: string;
  status?: EvaluationStatus;
  createdAfter?: Date;
  createdBefore?: Date;
}

