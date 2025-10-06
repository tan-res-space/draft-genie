/**
 * Speakers Service Tests
 */

import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException, ConflictException, BadRequestException } from '@nestjs/common';
import { SpeakersService } from './speakers.service';
import { SpeakerRepository } from './repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { EventsService } from '../events/events.service';
import { BucketType, SpeakerStatus } from '../common/constants/enums';

describe('SpeakersService', () => {
  let service: SpeakersService;

  const mockSpeaker = {
    id: '123',
    externalId: 'ext-123',
    name: 'John Doe',
    email: 'john@example.com',
    bucket: BucketType.GOOD,
    status: SpeakerStatus.ACTIVE,
    notes: 'Test notes',
    metadata: {},
    createdAt: new Date(),
    updatedAt: new Date(),
    deletedAt: null,
  };

  const mockSpeakerRepository = {
    findByExternalId: jest.fn(),
    create: jest.fn(),
    findById: jest.fn(),
    findAllWithFilters: jest.fn(),
    update: jest.fn(),
    updateBucket: jest.fn(),
    delete: jest.fn(),
    getStatistics: jest.fn(),
  };

  const mockAuditLogRepository = {
    log: jest.fn(),
  };

  const mockEventsService = {
    publishObject: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SpeakersService,
        {
          provide: SpeakerRepository,
          useValue: mockSpeakerRepository,
        },
        {
          provide: AuditLogRepository,
          useValue: mockAuditLogRepository,
        },
        {
          provide: EventsService,
          useValue: mockEventsService,
        },
      ],
    }).compile();

    service = module.get<SpeakersService>(SpeakersService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    const createDto = {
      externalId: 'ext-123',
      name: 'John Doe',
      email: 'john@example.com',
      bucket: BucketType.GOOD,
      status: SpeakerStatus.ACTIVE,
    };

    it('should create a speaker successfully', async () => {
      mockSpeakerRepository.findByExternalId.mockResolvedValue(null);
      mockSpeakerRepository.create.mockResolvedValue(mockSpeaker);
      mockAuditLogRepository.log.mockResolvedValue({});
      mockEventsService.publishObject.mockResolvedValue(undefined);

      const result = await service.create(createDto);

      expect(result).toEqual(mockSpeaker);
      expect(mockSpeakerRepository.findByExternalId).toHaveBeenCalledWith('ext-123');
      expect(mockSpeakerRepository.create).toHaveBeenCalled();
      expect(mockAuditLogRepository.log).toHaveBeenCalled();
      expect(mockEventsService.publishObject).toHaveBeenCalled();
    });

    it('should throw ConflictException if external ID exists', async () => {
      mockSpeakerRepository.findByExternalId.mockResolvedValue(mockSpeaker);

      await expect(service.create(createDto)).rejects.toThrow(ConflictException);
      expect(mockSpeakerRepository.create).not.toHaveBeenCalled();
    });

    it('should create speaker without external ID', async () => {
      const dtoWithoutExternalId = { ...createDto, externalId: undefined };
      mockSpeakerRepository.create.mockResolvedValue(mockSpeaker);
      mockAuditLogRepository.log.mockResolvedValue({});
      mockEventsService.publishObject.mockResolvedValue(undefined);

      const result = await service.create(dtoWithoutExternalId);

      expect(result).toEqual(mockSpeaker);
      expect(mockSpeakerRepository.findByExternalId).not.toHaveBeenCalled();
    });
  });

  describe('findAll', () => {
    it('should return paginated speakers', async () => {
      const query = {
        page: 1,
        limit: 20,
        sortBy: 'createdAt',
        sortOrder: 'desc' as const,
      };

      const paginatedResult = {
        data: [mockSpeaker],
        pagination: {
          page: 1,
          limit: 20,
          total: 1,
          totalPages: 1,
          hasNext: false,
          hasPrevious: false,
        },
      };

      mockSpeakerRepository.findAllWithFilters.mockResolvedValue(paginatedResult);

      const result = await service.findAll(query);

      expect(result).toEqual(paginatedResult);
      expect(mockSpeakerRepository.findAllWithFilters).toHaveBeenCalled();
    });
  });

  describe('findOne', () => {
    it('should return a speaker by ID', async () => {
      mockSpeakerRepository.findById.mockResolvedValue(mockSpeaker);

      const result = await service.findOne('123');

      expect(result).toEqual(mockSpeaker);
      expect(mockSpeakerRepository.findById).toHaveBeenCalledWith('123');
    });

    it('should throw NotFoundException if speaker not found', async () => {
      mockSpeakerRepository.findById.mockResolvedValue(null);

      await expect(service.findOne('nonexistent')).rejects.toThrow(NotFoundException);
    });
  });

  describe('update', () => {
    const updateDto = {
      name: 'Jane Doe',
      email: 'jane@example.com',
    };

    it('should update a speaker successfully', async () => {
      const updatedSpeaker = { ...mockSpeaker, ...updateDto };
      mockSpeakerRepository.findById.mockResolvedValue(mockSpeaker);
      mockSpeakerRepository.update.mockResolvedValue(updatedSpeaker);
      mockAuditLogRepository.log.mockResolvedValue({});
      mockEventsService.publishObject.mockResolvedValue(undefined);

      const result = await service.update('123', updateDto);

      expect(result).toEqual(updatedSpeaker);
      expect(mockSpeakerRepository.update).toHaveBeenCalledWith('123', updateDto);
      expect(mockAuditLogRepository.log).toHaveBeenCalled();
      expect(mockEventsService.publishObject).toHaveBeenCalled();
    });

    it('should throw NotFoundException if speaker not found', async () => {
      mockSpeakerRepository.findById.mockResolvedValue(null);

      await expect(service.update('nonexistent', updateDto)).rejects.toThrow(
        NotFoundException,
      );
    });
  });

  describe('updateBucket', () => {
    const updateBucketDto = {
      bucket: BucketType.EXCELLENT,
      reason: 'Improved quality',
    };

    it('should update speaker bucket successfully', async () => {
      const updatedSpeaker = { ...mockSpeaker, bucket: BucketType.EXCELLENT };
      mockSpeakerRepository.findById.mockResolvedValue(mockSpeaker);
      mockSpeakerRepository.updateBucket.mockResolvedValue(updatedSpeaker);
      mockAuditLogRepository.log.mockResolvedValue({});
      mockEventsService.publishObject.mockResolvedValue(undefined);

      const result = await service.updateBucket('123', updateBucketDto);

      expect(result).toEqual(updatedSpeaker);
      expect(mockSpeakerRepository.updateBucket).toHaveBeenCalledWith(
        '123',
        BucketType.EXCELLENT,
      );
      expect(mockAuditLogRepository.log).toHaveBeenCalled();
      expect(mockEventsService.publishObject).toHaveBeenCalled();
    });

    it('should throw BadRequestException if bucket is the same', async () => {
      const sameBucketDto = { bucket: BucketType.GOOD };
      mockSpeakerRepository.findById.mockResolvedValue(mockSpeaker);

      await expect(service.updateBucket('123', sameBucketDto)).rejects.toThrow(
        BadRequestException,
      );
    });
  });

  describe('remove', () => {
    it('should soft delete a speaker successfully', async () => {
      const deletedSpeaker = { ...mockSpeaker, deletedAt: new Date() };
      mockSpeakerRepository.findById.mockResolvedValue(mockSpeaker);
      mockSpeakerRepository.delete.mockResolvedValue(deletedSpeaker);
      mockAuditLogRepository.log.mockResolvedValue({});

      const result = await service.remove('123');

      expect(result).toEqual(deletedSpeaker);
      expect(mockSpeakerRepository.delete).toHaveBeenCalledWith('123');
      expect(mockAuditLogRepository.log).toHaveBeenCalled();
    });

    it('should throw NotFoundException if speaker not found', async () => {
      mockSpeakerRepository.findById.mockResolvedValue(null);

      await expect(service.remove('nonexistent')).rejects.toThrow(NotFoundException);
    });
  });

  describe('getStatistics', () => {
    it('should return speaker statistics', async () => {
      const stats = {
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
      };

      mockSpeakerRepository.getStatistics.mockResolvedValue(stats);

      const result = await service.getStatistics();

      expect(result).toEqual(stats);
      expect(mockSpeakerRepository.getStatistics).toHaveBeenCalled();
    });
  });
});

