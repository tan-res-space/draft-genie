/**
 * Audit Log Repository Tests
 */

import { Test, TestingModule } from '@nestjs/testing';
import { AuditLogRepository } from './audit-log.repository';
import { PrismaService } from '../../prisma/prisma.service';

describe('AuditLogRepository', () => {
  let repository: AuditLogRepository;

  const mockPrismaService = {
    auditLog: {
      create: jest.fn(),
      findMany: jest.fn(),
      count: jest.fn(),
    },
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuditLogRepository,
        {
          provide: PrismaService,
          useValue: mockPrismaService,
        },
      ],
    }).compile();

    repository = module.get<AuditLogRepository>(AuditLogRepository);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('log', () => {
    it('should create an audit log entry', async () => {
      const logData = {
        entityType: 'Speaker',
        entityId: '123',
        action: 'CREATE',
        userId: 'user-123',
        changes: { name: 'John Doe' },
        metadata: { source: 'api' },
      };

      const mockAuditLog = {
        id: 'log-123',
        ...logData,
        createdAt: new Date(),
      };

      mockPrismaService.auditLog.create.mockResolvedValue(mockAuditLog);

      const result = await repository.log(logData);

      expect(result).toEqual(mockAuditLog);
      expect(mockPrismaService.auditLog.create).toHaveBeenCalledWith({
        data: {
          entityType: 'Speaker',
          entityId: '123',
          action: 'CREATE',
          userId: 'user-123',
          changes: { name: 'John Doe' },
          metadata: { source: 'api' },
        },
      });
    });

    it('should create audit log with default empty objects', async () => {
      const logData = {
        entityType: 'Speaker',
        entityId: '123',
        action: 'DELETE',
      };

      const mockAuditLog = {
        id: 'log-123',
        ...logData,
        userId: undefined,
        changes: {},
        metadata: {},
        createdAt: new Date(),
      };

      mockPrismaService.auditLog.create.mockResolvedValue(mockAuditLog);

      const result = await repository.log(logData);

      expect(result).toEqual(mockAuditLog);
      expect(mockPrismaService.auditLog.create).toHaveBeenCalledWith({
        data: {
          entityType: 'Speaker',
          entityId: '123',
          action: 'DELETE',
          userId: undefined,
          changes: {},
          metadata: {},
        },
      });
    });
  });

  describe('findByEntity', () => {
    it('should find audit logs by entity', async () => {
      const mockLogs = [
        {
          id: 'log-123',
          entityType: 'Speaker',
          entityId: '123',
          action: 'CREATE',
          userId: 'user-123',
          changes: {},
          metadata: {},
          createdAt: new Date(),
        },
        {
          id: 'log-124',
          entityType: 'Speaker',
          entityId: '123',
          action: 'UPDATE',
          userId: 'user-123',
          changes: {},
          metadata: {},
          createdAt: new Date(),
        },
      ];

      mockPrismaService.auditLog.findMany.mockResolvedValue(mockLogs);

      const result = await repository.findByEntity('Speaker', '123');

      expect(result).toEqual(mockLogs);
      expect(mockPrismaService.auditLog.findMany).toHaveBeenCalledWith({
        where: {
          entityType: 'Speaker',
          entityId: '123',
        },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('findByUser', () => {
    it('should find audit logs by user', async () => {
      const mockLogs = [
        {
          id: 'log-123',
          entityType: 'Speaker',
          entityId: '123',
          action: 'CREATE',
          userId: 'user-123',
          changes: {},
          metadata: {},
          createdAt: new Date(),
        },
      ];

      mockPrismaService.auditLog.findMany.mockResolvedValue(mockLogs);

      const result = await repository.findByUser('user-123');

      expect(result).toEqual(mockLogs);
      expect(mockPrismaService.auditLog.findMany).toHaveBeenCalledWith({
        where: { userId: 'user-123' },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('findRecent', () => {
    it('should find recent audit logs with default limit', async () => {
      const mockLogs = [
        {
          id: 'log-123',
          entityType: 'Speaker',
          entityId: '123',
          action: 'CREATE',
          userId: 'user-123',
          changes: {},
          metadata: {},
          createdAt: new Date(),
        },
      ];

      mockPrismaService.auditLog.findMany.mockResolvedValue(mockLogs);

      const result = await repository.findRecent();

      expect(result).toEqual(mockLogs);
      expect(mockPrismaService.auditLog.findMany).toHaveBeenCalledWith({
        take: 100,
        orderBy: { createdAt: 'desc' },
      });
    });

    it('should find recent audit logs with custom limit', async () => {
      const mockLogs = [];

      mockPrismaService.auditLog.findMany.mockResolvedValue(mockLogs);

      const result = await repository.findRecent(50);

      expect(result).toEqual(mockLogs);
      expect(mockPrismaService.auditLog.findMany).toHaveBeenCalledWith({
        take: 50,
        orderBy: { createdAt: 'desc' },
      });
    });
  });
});

