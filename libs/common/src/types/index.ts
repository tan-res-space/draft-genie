import { ResponseStatus } from '../constants';

// Generic API response wrapper
export interface ApiResponse<T = any> {
  status: ResponseStatus;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp: string;
    correlationId?: string;
    [key: string]: any;
  };
}

// Pagination request
export interface PaginationRequest {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// Pagination response
export interface PaginationResponse<T> {
  items: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

// Date range filter
export interface DateRangeFilter {
  startDate?: Date | string;
  endDate?: Date | string;
}

// Generic ID type
export type ID = string;

// Timestamp fields
export interface Timestamps {
  createdAt: Date;
  updatedAt: Date;
  deletedAt?: Date;
}

// Soft delete interface
export interface SoftDeletable {
  isDeleted: boolean;
  deletedAt?: Date;
}

// Metadata interface
export interface Metadata {
  [key: string]: any;
}

// Domain Event types
export interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  timestamp: Date | string;
  version: number;
  correlationId?: string;
  causationId?: string;
  payload: Record<string, any>;
  metadata?: Record<string, any>;
}

