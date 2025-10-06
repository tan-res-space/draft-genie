/**
 * Speaker Repository Tests
 */

import { Test, TestingModule } from '@nestjs/testing';
import { SpeakerRepository } from './speaker.repository';
import { PrismaService } from '../../prisma/prisma.service';

describe('SpeakerRepository', () => {
  let repository: SpeakerRepository;

  const mockPrismaService = {
    speaker: {
      findUnique: jest.fn(),
      findMany: jest.fn(),
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
        SpeakerRepository,
        {
          provide: PrismaService,
          useValue: mockPrismaService,
        },
      ],
    }).compile();

    repository = module.get<SpeakerRepository>(SpeakerRepository);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('findById', () => {
    it('should find a speaker by ID', async () => {
      const mockSpeaker = {
        id: '123',
        externalId: 'ext-123',
        name: 'John Doe',
        bucket: 'GOOD',
        status: 'ACTIVE',
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        deletedAt: null,
      };

      mockPrismaService.speaker.findUnique.mockResolvedValue(mockSpeaker);

      const result = await repository.findById('123');

      expect(result).toEqual(mockSpeaker);
      expect(mockPrismaService.speaker.findUnique).toHaveBeenCalledWith({
        where: { id: '123' },
      });
    });

    it('should return null if speaker not found', async () => {
      mockPrismaService.speaker.findUnique.mockResolvedValue(null);

      const result = await repository.findById('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('findByExternalId', () => {
    it('should find a speaker by external ID', async () => {
      const mockSpeaker = {
        id: '123',
        externalId: 'ext-123',
        name: 'John Doe',
        bucket: 'GOOD',
        status: 'ACTIVE',
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        deletedAt: null,
      };

      mockPrismaService.speaker.findUnique.mockResolvedValue(mockSpeaker);

      const result = await repository.findByExternalId('ext-123');

      expect(result).toEqual(mockSpeaker);
      expect(mockPrismaService.speaker.findUnique).toHaveBeenCalledWith({
        where: { externalId: 'ext-123' },
      });
    });
  });

  describe('create', () => {
    it('should create a new speaker', async () => {
      const createData = {
        externalId: 'ext-123',
        name: 'John Doe',
        bucket: 'GOOD',
        status: 'ACTIVE',
      };

      const mockSpeaker = {
        id: '123',
        ...createData,
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        deletedAt: null,
      };

      mockPrismaService.speaker.create.mockResolvedValue(mockSpeaker);

      const result = await repository.create(createData);

      expect(result).toEqual(mockSpeaker);
      expect(mockPrismaService.speaker.create).toHaveBeenCalledWith({
        data: createData,
      });
    });
  });

  describe('update', () => {
    it('should update a speaker', async () => {
      const updateData = {
        name: 'Jane Doe',
      };

      const mockSpeaker = {
        id: '123',
        externalId: 'ext-123',
        name: 'Jane Doe',
        bucket: 'GOOD',
        status: 'ACTIVE',
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        deletedAt: null,
      };

      mockPrismaService.speaker.update.mockResolvedValue(mockSpeaker);

      const result = await repository.update('123', updateData);

      expect(result).toEqual(mockSpeaker);
      expect(mockPrismaService.speaker.update).toHaveBeenCalledWith({
        where: { id: '123' },
        data: updateData,
      });
    });
  });

  describe('findByBucket', () => {
    it('should find speakers by bucket', async () => {
      const mockSpeakers = [
        {
          id: '123',
          externalId: 'ext-123',
          name: 'John Doe',
          bucket: 'GOOD',
          status: 'ACTIVE',
          metadata: {},
          createdAt: new Date(),
          updatedAt: new Date(),
          deletedAt: null,
        },
      ];

      mockPrismaService.speaker.findMany.mockResolvedValue(mockSpeakers);

      const result = await repository.findByBucket('GOOD');

      expect(result).toEqual(mockSpeakers);
      expect(mockPrismaService.speaker.findMany).toHaveBeenCalledWith({
        where: {
          bucket: 'GOOD',
          deletedAt: null,
        },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('updateBucket', () => {
    it('should update speaker bucket', async () => {
      const mockSpeaker = {
        id: '123',
        externalId: 'ext-123',
        name: 'John Doe',
        bucket: 'EXCELLENT',
        status: 'ACTIVE',
        metadata: {},
        createdAt: new Date(),
        updatedAt: new Date(),
        deletedAt: null,
      };

      mockPrismaService.speaker.update.mockResolvedValue(mockSpeaker);

      const result = await repository.updateBucket('123', 'EXCELLENT');

      expect(result).toEqual(mockSpeaker);
      expect(mockPrismaService.speaker.update).toHaveBeenCalledWith({
        where: { id: '123' },
        data: {
          bucket: 'EXCELLENT',
          updatedAt: expect.any(Date),
        },
      });
    });
  });

  describe('getStatistics', () => {
    it('should get speaker statistics', async () => {
      mockPrismaService.speaker.count.mockResolvedValue(10);
      mockPrismaService.speaker.groupBy
        .mockResolvedValueOnce([
          { bucket: 'EXCELLENT', _count: 2 },
          { bucket: 'GOOD', _count: 5 },
          { bucket: 'AVERAGE', _count: 3 },
        ])
        .mockResolvedValueOnce([
          { status: 'ACTIVE', _count: 8 },
          { status: 'INACTIVE', _count: 2 },
        ]);

      const result = await repository.getStatistics();

      expect(result).toEqual({
        total: 10,
        byBucket: {
          EXCELLENT: 2,
          GOOD: 5,
          AVERAGE: 3,
        },
        byStatus: {
          ACTIVE: 8,
          INACTIVE: 2,
        },
      });
    });
  });
});

