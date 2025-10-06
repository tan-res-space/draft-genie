import { DraftType } from '@draft-genie/common';

export interface DraftMetadata {
  wordCount?: number;
  characterCount?: number;
  processingTime?: number; // in milliseconds
  confidence?: number; // 0-1 scale
  [key: string]: any;
}

export interface Draft {
  id: string;
  speakerId: string;
  type: DraftType;
  content: string;
  metadata: DraftMetadata;
  sourceId?: string; // ID from InstaNote or other source
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateDraftDto {
  speakerId: string;
  type: DraftType;
  content: string;
  metadata?: Partial<DraftMetadata>;
  sourceId?: string;
}

export interface DraftFilter {
  speakerId?: string;
  type?: DraftType;
  createdAfter?: Date;
  createdBefore?: Date;
}

// Correction pattern extracted from draft comparison
export interface CorrectionPattern {
  original: string;
  corrected: string;
  frequency: number;
  context?: string;
  category?: string; // e.g., 'spelling', 'grammar', 'terminology'
}

export interface CorrectionVector {
  id: string;
  speakerId: string;
  patterns: CorrectionPattern[];
  embedding?: number[]; // Vector embedding
  metadata: {
    totalPatterns: number;
    lastUpdated: Date;
    sourceCount: number; // Number of drafts used to build this vector
    [key: string]: any;
  };
  createdAt: Date;
  updatedAt: Date;
}

