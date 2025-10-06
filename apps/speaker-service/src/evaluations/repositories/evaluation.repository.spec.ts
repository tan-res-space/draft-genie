/**
 * Evaluation Repository Tests
 */

import { Test, TestingModule } from '@nestjs/testing';
import { EvaluationRepository } from './evaluation.repository';
import { PrismaService } from '../../prisma/prisma.service';

describe('EvaluationRepository', () => {
  let repository: EvaluationRepository;

  const mockPrismaService = {
    evaluation: {
      findUnique: jest.fn(),
      findMany: jest.fn(),
      findFirst: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      count: jest.fn(),
      groupBy: jest.fn(),
    },
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EvaluationRepository,
        {
          provide: PrismaService,
          useValue: mockPrismaService,
        },
      ],
    }).compile();

    repository = module.get<EvaluationRepository>(EvaluationRepository);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('findById', () => {
    it('should find an evaluation by ID', async () => {
      const mockEvaluation = {
        id: '123',
        speakerId: 'speaker-123',
        draftId: 'draft-123',
        referenceDraftId: 'ref-draft-123',
        status: 'COMPLETED',
        metrics: {},
        comparison: {},
        recommendedBucket: 'GOOD',
        notes: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: new Date(),
      };

      mockPrismaService.evaluation.findUnique.mockResolvedValue(mockEvaluation);

      const result = await repository.findById('123');

      expect(result).toEqual(mockEvaluation);
      expect(mockPrismaService.evaluation.findUnique).toHaveBeenCalledWith({
        where: { id: '123' },
      });
    });
  });

  describe('findBySpeakerId', () => {
    it('should find evaluations by speaker ID', async () => {
      const mockEvaluations = [
        {
          id: '123',
          speakerId: 'speaker-123',
          draftId: 'draft-123',
          referenceDraftId: 'ref-draft-123',
          status: 'COMPLETED',
          metrics: {},
          comparison: {},
          recommendedBucket: 'GOOD',
          notes: null,
          createdAt: new Date(),
          updatedAt: new Date(),
          completedAt: new Date(),
        },
      ];

      mockPrismaService.evaluation.findMany.mockResolvedValue(mockEvaluations);

      const result = await repository.findBySpeakerId('speaker-123');

      expect(result).toEqual(mockEvaluations);
      expect(mockPrismaService.evaluation.findMany).toHaveBeenCalledWith({
        where: { speakerId: 'speaker-123' },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('create', () => {
    it('should create a new evaluation', async () => {
      const createData = {
        speakerId: 'speaker-123',
        draftId: 'draft-123',
        referenceDraftId: 'ref-draft-123',
        status: 'PENDING',
      };

      const mockEvaluation = {
        id: '123',
        ...createData,
        metrics: {},
        comparison: {},
        recommendedBucket: null,
        notes: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: null,
      };

      mockPrismaService.evaluation.create.mockResolvedValue(mockEvaluation);

      const result = await repository.create(createData);

      expect(result).toEqual(mockEvaluation);
      expect(mockPrismaService.evaluation.create).toHaveBeenCalledWith({
        data: createData,
      });
    });
  });

  describe('updateStatus', () => {
    it('should update evaluation status', async () => {
      const completedAt = new Date();
      const mockEvaluation = {
        id: '123',
        speakerId: 'speaker-123',
        draftId: 'draft-123',
        referenceDraftId: 'ref-draft-123',
        status: 'COMPLETED',
        metrics: {},
        comparison: {},
        recommendedBucket: 'GOOD',
        notes: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt,
      };

      mockPrismaService.evaluation.update.mockResolvedValue(mockEvaluation);

      const result = await repository.updateStatus('123', 'COMPLETED', completedAt);

      expect(result).toEqual(mockEvaluation);
      expect(mockPrismaService.evaluation.update).toHaveBeenCalledWith({
        where: { id: '123' },
        data: {
          status: 'COMPLETED',
          completedAt,
          updatedAt: expect.any(Date),
        },
      });
    });
  });

  describe('getLatestForSpeaker', () => {
    it('should get latest evaluation for speaker', async () => {
      const mockEvaluation = {
        id: '123',
        speakerId: 'speaker-123',
        draftId: 'draft-123',
        referenceDraftId: 'ref-draft-123',
        status: 'COMPLETED',
        metrics: {},
        comparison: {},
        recommendedBucket: 'GOOD',
        notes: null,
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: new Date(),
      };

      mockPrismaService.evaluation.findFirst.mockResolvedValue(mockEvaluation);

      const result = await repository.getLatestForSpeaker('speaker-123');

      expect(result).toEqual(mockEvaluation);
      expect(mockPrismaService.evaluation.findFirst).toHaveBeenCalledWith({
        where: { speakerId: 'speaker-123' },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('getStatistics', () => {
    it('should get evaluation statistics', async () => {
      mockPrismaService.evaluation.count.mockResolvedValue(20);
      mockPrismaService.evaluation.groupBy.mockResolvedValue([
        { status: 'COMPLETED', _count: 15 },
        { status: 'PENDING', _count: 3 },
        { status: 'FAILED', _count: 2 },
      ]);

      const result = await repository.getStatistics();

      expect(result).toEqual({
        total: 20,
        byStatus: {
          COMPLETED: 15,
          PENDING: 3,
          FAILED: 2,
        },
      });
    });
  });
});

