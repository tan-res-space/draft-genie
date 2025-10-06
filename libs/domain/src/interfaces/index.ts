import { PaginationRequest, PaginationResponse } from '@draft-genie/common';

// Generic repository interface
export interface IRepository<T, TFilter = any> {
  findById(id: string): Promise<T | null>;
  findAll(filter?: TFilter, pagination?: PaginationRequest): Promise<PaginationResponse<T>>;
  create(data: Partial<T>): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

// Event publisher interface
export interface IEventPublisher {
  publish(event: any): Promise<void>;
  publishBatch(events: any[]): Promise<void>;
}

// Event handler interface
export interface IEventHandler<T = any> {
  handle(event: T): Promise<void>;
}

