/**
 * Speaker Repository
 */

import { Injectable } from '@nestjs/common';
import { Speaker, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { BaseRepository, PaginatedResult, PaginationOptions } from '../../common/repositories/base.repository';

export interface SpeakerFilters {
  bucket?: string;
  status?: string;
  search?: string;
}

@Injectable()
export class SpeakerRepository extends BaseRepository<Speaker> {
  constructor(prisma: PrismaService) {
    super(prisma, 'Speaker');
  }

  protected getModel() {
    return this.prisma.speaker;
  }

  /**
   * Find by external ID
   */
  async findByExternalId(externalId: string): Promise<Speaker | null> {
    try {
      return await this.prisma.speaker.findUnique({
        where: { externalId },
      });
    } catch (error) {
      this.logger.error(`Failed to find speaker by external ID: ${externalId}`, error);
      throw error;
    }
  }

  /**
   * Find all with filters
   */
  async findAllWithFilters(
    filters: SpeakerFilters,
    options: PaginationOptions = {},
  ): Promise<PaginatedResult<Speaker>> {
    const {
      page = 1,
      limit = 20,
      sortBy = 'createdAt',
      sortOrder = 'desc',
    } = options;

    const skip = (page - 1) * limit;

    // Build where clause
    const where: Prisma.SpeakerWhereInput = {
      deletedAt: null, // Exclude soft-deleted speakers
    };

    if (filters.bucket) {
      where.bucket = filters.bucket;
    }

    if (filters.status) {
      where.status = filters.status;
    }

    if (filters.search) {
      where.OR = [
        { name: { contains: filters.search, mode: 'insensitive' } },
        { email: { contains: filters.search, mode: 'insensitive' } },
        { externalId: { contains: filters.search, mode: 'insensitive' } },
      ];
    }

    try {
      const [data, total] = await Promise.all([
        this.prisma.speaker.findMany({
          where,
          skip,
          take: limit,
          orderBy: { [sortBy]: sortOrder },
        }),
        this.prisma.speaker.count({ where }),
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
      this.logger.error('Failed to find speakers with filters', error);
      throw error;
    }
  }

  /**
   * Find by bucket
   */
  async findByBucket(bucket: string): Promise<Speaker[]> {
    try {
      return await this.prisma.speaker.findMany({
        where: {
          bucket,
          deletedAt: null,
        },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error(`Failed to find speakers by bucket: ${bucket}`, error);
      throw error;
    }
  }

  /**
   * Update bucket
   */
  async updateBucket(id: string, bucket: string): Promise<Speaker> {
    try {
      return await this.prisma.speaker.update({
        where: { id },
        data: {
          bucket,
          updatedAt: new Date(),
        },
      });
    } catch (error) {
      this.logger.error(`Failed to update speaker bucket: ${id}`, error);
      throw error;
    }
  }

  /**
   * Update metadata
   */
  async updateMetadata(id: string, metadata: any): Promise<Speaker> {
    try {
      return await this.prisma.speaker.update({
        where: { id },
        data: {
          metadata,
          updatedAt: new Date(),
        },
      });
    } catch (error) {
      this.logger.error(`Failed to update speaker metadata: ${id}`, error);
      throw error;
    }
  }

  /**
   * Get speaker statistics
   */
  async getStatistics(): Promise<{
    total: number;
    byBucket: Record<string, number>;
    byStatus: Record<string, number>;
  }> {
    try {
      const [total, byBucket, byStatus] = await Promise.all([
        this.prisma.speaker.count({
          where: { deletedAt: null },
        }),
        this.prisma.speaker.groupBy({
          by: ['bucket'],
          where: { deletedAt: null },
          _count: true,
        }),
        this.prisma.speaker.groupBy({
          by: ['status'],
          where: { deletedAt: null },
          _count: true,
        }),
      ]);

      return {
        total,
        byBucket: byBucket.reduce((acc, item) => {
          acc[item.bucket] = item._count;
          return acc;
        }, {} as Record<string, number>),
        byStatus: byStatus.reduce((acc, item) => {
          acc[item.status] = item._count;
          return acc;
        }, {} as Record<string, number>),
      };
    } catch (error) {
      this.logger.error('Failed to get speaker statistics', error);
      throw error;
    }
  }
}

