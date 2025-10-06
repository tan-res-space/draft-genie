import { BucketType, SpeakerStatus } from '@draft-genie/common';

export interface SpeakerMetadata {
  ser?: number; // Sentence Edit Rate
  wer?: number; // Word Error Rate
  totalDrafts?: number;
  totalEvaluations?: number;
  averageQualityScore?: number;
  lastProcessedAt?: Date;
  [key: string]: any;
}

export interface Speaker {
  id: string;
  externalId?: string; // ID from InstaNote or other external system
  name: string;
  email?: string;
  bucket: BucketType;
  status: SpeakerStatus;
  metadata: SpeakerMetadata;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;
}

export interface CreateSpeakerDto {
  externalId?: string;
  name: string;
  email?: string;
  bucket: BucketType;
  metadata?: Partial<SpeakerMetadata>;
  notes?: string;
}

export interface UpdateSpeakerDto {
  name?: string;
  email?: string;
  bucket?: BucketType;
  status?: SpeakerStatus;
  metadata?: Partial<SpeakerMetadata>;
  notes?: string;
}

export interface SpeakerFilter {
  bucket?: BucketType;
  status?: SpeakerStatus;
  search?: string; // Search by name or email
  createdAfter?: Date;
  createdBefore?: Date;
}

