/**
 * Evaluation Repository
 */

import { Injectable } from '@nestjs/common';
import { Evaluation, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { BaseRepository, PaginatedResult, PaginationOptions } from '../../common/repositories/base.repository';

export interface EvaluationFilters {
  speakerId?: string;
  status?: string;
}

@Injectable()
export class EvaluationRepository extends BaseRepository<Evaluation> {
  constructor(prisma: PrismaService) {
    super(prisma, 'Evaluation');
  }

  protected getModel() {
    return this.prisma.evaluation;
  }

  /**
   * Find by speaker ID
   */
  async findBySpeakerId(speakerId: string): Promise<Evaluation[]> {
    try {
      return await this.prisma.evaluation.findMany({
        where: { speakerId },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error(`Failed to find evaluations by speaker ID: ${speakerId}`, error);
      throw error;
    }
  }

  /**
   * Find all with filters
   */
  async findAllWithFilters(
    filters: EvaluationFilters,
    options: PaginationOptions = {},
  ): Promise<PaginatedResult<Evaluation>> {
    const {
      page = 1,
      limit = 20,
      sortBy = 'createdAt',
      sortOrder = 'desc',
    } = options;

    const skip = (page - 1) * limit;

    // Build where clause
    const where: Prisma.EvaluationWhereInput = {};

    if (filters.speakerId) {
      where.speakerId = filters.speakerId;
    }

    if (filters.status) {
      where.status = filters.status;
    }

    try {
      const [data, total] = await Promise.all([
        this.prisma.evaluation.findMany({
          where,
          skip,
          take: limit,
          orderBy: { [sortBy]: sortOrder },
          include: {
            speaker: {
              select: {
                id: true,
                name: true,
                bucket: true,
              },
            },
          },
        }),
        this.prisma.evaluation.count({ where }),
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
      this.logger.error('Failed to find evaluations with filters', error);
      throw error;
    }
  }

  /**
   * Update status
   */
  async updateStatus(id: string, status: string, completedAt?: Date): Promise<Evaluation> {
    try {
      return await this.prisma.evaluation.update({
        where: { id },
        data: {
          status,
          completedAt,
          updatedAt: new Date(),
        },
      });
    } catch (error) {
      this.logger.error(`Failed to update evaluation status: ${id}`, error);
      throw error;
    }
  }

  /**
   * Update metrics
   */
  async updateMetrics(id: string, metrics: any): Promise<Evaluation> {
    try {
      return await this.prisma.evaluation.update({
        where: { id },
        data: {
          metrics,
          updatedAt: new Date(),
        },
      });
    } catch (error) {
      this.logger.error(`Failed to update evaluation metrics: ${id}`, error);
      throw error;
    }
  }

  /**
   * Get latest evaluation for speaker
   */
  async getLatestForSpeaker(speakerId: string): Promise<Evaluation | null> {
    try {
      return await this.prisma.evaluation.findFirst({
        where: { speakerId },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error(`Failed to get latest evaluation for speaker: ${speakerId}`, error);
      throw error;
    }
  }

  /**
   * Get evaluation statistics
   */
  async getStatistics(): Promise<{
    total: number;
    byStatus: Record<string, number>;
  }> {
    try {
      const [total, byStatus] = await Promise.all([
        this.prisma.evaluation.count(),
        this.prisma.evaluation.groupBy({
          by: ['status'],
          _count: true,
        }),
      ]);

      return {
        total,
        byStatus: byStatus.reduce((acc, item) => {
          acc[item.status] = item._count;
          return acc;
        }, {} as Record<string, number>),
      };
    } catch (error) {
      this.logger.error('Failed to get evaluation statistics', error);
      throw error;
    }
  }
}

