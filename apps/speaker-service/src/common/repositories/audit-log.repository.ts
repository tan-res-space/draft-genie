/**
 * Audit Log Repository
 */

import { Injectable } from '@nestjs/common';
import { AuditLog } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { BaseRepository } from './base.repository';

export interface CreateAuditLogDto {
  entityType: string;
  entityId: string;
  action: string;
  userId?: string;
  changes?: any;
  metadata?: any;
}

@Injectable()
export class AuditLogRepository extends BaseRepository<AuditLog> {
  constructor(prisma: PrismaService) {
    super(prisma, 'AuditLog');
  }

  protected getModel() {
    return this.prisma.auditLog;
  }

  /**
   * Create audit log entry
   */
  async log(data: CreateAuditLogDto): Promise<AuditLog> {
    try {
      return await this.prisma.auditLog.create({
        data: {
          entityType: data.entityType,
          entityId: data.entityId,
          action: data.action,
          userId: data.userId,
          changes: data.changes || {},
          metadata: data.metadata || {},
        },
      });
    } catch (error) {
      this.logger.error('Failed to create audit log', error);
      throw error;
    }
  }

  /**
   * Find by entity
   */
  async findByEntity(entityType: string, entityId: string): Promise<AuditLog[]> {
    try {
      return await this.prisma.auditLog.findMany({
        where: {
          entityType,
          entityId,
        },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error(`Failed to find audit logs for entity: ${entityType}/${entityId}`, error);
      throw error;
    }
  }

  /**
   * Find by user
   */
  async findByUser(userId: string): Promise<AuditLog[]> {
    try {
      return await this.prisma.auditLog.findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error(`Failed to find audit logs for user: ${userId}`, error);
      throw error;
    }
  }

  /**
   * Find recent logs
   */
  async findRecent(limit: number = 100): Promise<AuditLog[]> {
    try {
      return await this.prisma.auditLog.findMany({
        take: limit,
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      this.logger.error('Failed to find recent audit logs', error);
      throw error;
    }
  }
}

