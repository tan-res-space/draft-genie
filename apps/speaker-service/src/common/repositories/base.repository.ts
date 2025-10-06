/**
 * Base Repository - Abstract repository with common CRUD operations
 */

import { Logger } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

export interface PaginationOptions {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResult<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

export abstract class BaseRepository<T> {
  protected readonly logger: Logger;

  constructor(
    protected readonly prisma: PrismaService,
    protected readonly modelName: string,
  ) {
    this.logger = new Logger(`${modelName}Repository`);
  }

  /**
   * Get Prisma model delegate
   */
  protected abstract getModel(): any;

  /**
   * Find by ID
   */
  async findById(id: string): Promise<T | null> {
    try {
      return await this.getModel().findUnique({
        where: { id },
      });
    } catch (error) {
      this.logger.error(`Failed to find ${this.modelName} by ID: ${id}`, error);
      throw error;
    }
  }

  /**
   * Find all with pagination
   */
  async findAll(options: PaginationOptions = {}): Promise<PaginatedResult<T>> {
    const {
      page = 1,
      limit = 20,
      sortBy = 'createdAt',
      sortOrder = 'desc',
    } = options;

    const skip = (page - 1) * limit;

    try {
      const [data, total] = await Promise.all([
        this.getModel().findMany({
          skip,
          take: limit,
          orderBy: { [sortBy]: sortOrder },
        }),
        this.getModel().count(),
      ]);

      const totalPages = Math.ceil(total / limit);

      return {
        data,
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrevious: page > 1,
        },
      };
    } catch (error) {
      this.logger.error(`Failed to find all ${this.modelName}`, error);
      throw error;
    }
  }

  /**
   * Create
   */
  async create(data: any): Promise<T> {
    try {
      return await this.getModel().create({
        data,
      });
    } catch (error) {
      this.logger.error(`Failed to create ${this.modelName}`, error);
      throw error;
    }
  }

  /**
   * Update
   */
  async update(id: string, data: any): Promise<T> {
    try {
      return await this.getModel().update({
        where: { id },
        data,
      });
    } catch (error) {
      this.logger.error(`Failed to update ${this.modelName}: ${id}`, error);
      throw error;
    }
  }

  /**
   * Delete (soft delete)
   */
  async delete(id: string): Promise<T> {
    try {
      return await this.getModel().update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    } catch (error) {
      this.logger.error(`Failed to delete ${this.modelName}: ${id}`, error);
      throw error;
    }
  }

  /**
   * Hard delete
   */
  async hardDelete(id: string): Promise<T> {
    try {
      return await this.getModel().delete({
        where: { id },
      });
    } catch (error) {
      this.logger.error(`Failed to hard delete ${this.modelName}: ${id}`, error);
      throw error;
    }
  }

  /**
   * Count
   */
  async count(where?: any): Promise<number> {
    try {
      return await this.getModel().count({ where });
    } catch (error) {
      this.logger.error(`Failed to count ${this.modelName}`, error);
      throw error;
    }
  }

  /**
   * Exists
   */
  async exists(where: any): Promise<boolean> {
    try {
      const count = await this.getModel().count({ where });
      return count > 0;
    } catch (error) {
      this.logger.error(`Failed to check if ${this.modelName} exists`, error);
      throw error;
    }
  }
}

