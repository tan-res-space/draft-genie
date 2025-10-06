import { Test, TestingModule } from '@nestjs/testing';
import { EvaluationsService } from './evaluations.service';
import { EvaluationRepository } from './repositories/evaluation.repository';
import { SpeakerRepository } from '../speakers/repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { EventsService } from '../events/events.service';
import { EvaluationStatus } from '../common/constants/enums';
import { SpeakerNotFoundError } from '@draft-genie/common';

describe('EvaluationsService', () => {
  let service: EvaluationsService;
  let evaluationRepository: jest.Mocked<EvaluationRepository>;
  let speakerRepository: jest.Mocked<SpeakerRepository>;
  let auditLogRepository: jest.Mocked<AuditLogRepository>;
  let eventsService: jest.Mocked<EventsService>;

  const mockSpeaker = {
    id: 'speaker-123',
    externalId: 'ext-123',
    name: 'John Doe',
    email: 'john@example.com',
    bucket: 'GOOD',
    status: 'ACTIVE',
    notes: null,
    metadata: {},
    createdAt: new Date(),
    updatedAt: new Date(),
    deletedAt: null,
  };

  const mockEvaluation = {
    id: 'eval-123',
    speakerId: 'speaker-123',
    draftId: 'draft-123',
    status: EvaluationStatus.COMPLETED,
    metrics: { clarity: 8.5 },
    results: { summary: 'Good' },
    notes: 'Test notes',
    createdAt: new Date(),
    updatedAt: new Date(),
    deletedAt: null,
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EvaluationsService,
        {
          provide: EvaluationRepository,
          useValue: {
            create: jest.fn(),
            findAll: jest.fn(),
            findAllWithFilters: jest.fn(),
            findById: jest.fn(),
            findBySpeakerId: jest.fn(),
            update: jest.fn(),
            delete: jest.fn(),
            getStatistics: jest.fn(),
          },
        },
        {
          provide: SpeakerRepository,
          useValue: {
            findById: jest.fn(),
          },
        },
        {
          provide: AuditLogRepository,
          useValue: {
            log: jest.fn(),
          },
        },
        {
          provide: EventsService,
          useValue: {
            publishObject: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<EvaluationsService>(EvaluationsService);
    evaluationRepository = module.get(EvaluationRepository);
    speakerRepository = module.get(SpeakerRepository);
    auditLogRepository = module.get(AuditLogRepository);
    eventsService = module.get(EventsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('create', () => {
    it('should create an evaluation', async () => {
      speakerRepository.findById.mockResolvedValue(mockSpeaker as any);
      evaluationRepository.create.mockResolvedValue(mockEvaluation as any);

      const result = await service.create({
        speakerId: 'speaker-123',
        draftId: 'draft-123',
        status: EvaluationStatus.PENDING,
      });

      expect(result).toEqual(mockEvaluation);
      expect(speakerRepository.findById).toHaveBeenCalledWith('speaker-123');
      expect(evaluationRepository.create).toHaveBeenCalled();
      expect(eventsService.publishObject).toHaveBeenCalled();
      expect(auditLogRepository.log).toHaveBeenCalled();
    });

    it('should throw error if speaker not found', async () => {
      speakerRepository.findById.mockResolvedValue(null);

      await expect(
        service.create({
          speakerId: 'non-existent',
          draftId: 'draft-123',
        }),
      ).rejects.toThrow(SpeakerNotFoundError);
    });
  });

  describe('findAll', () => {
    it('should return paginated evaluations', async () => {
      const mockPaginatedResult = {
        data: [mockEvaluation],
        pagination: {
          page: 1,
          limit: 10,
          total: 1,
          totalPages: 1,
          hasNext: false,
          hasPrevious: false,
        },
      };

      evaluationRepository.findAllWithFilters.mockResolvedValue(mockPaginatedResult as any);

      const result = await service.findAll({ page: 1, limit: 10 });

      expect(result.data).toEqual([mockEvaluation]);
      expect(result.pagination.hasNext).toBe(false);
      expect(result.pagination.hasPrevious).toBe(false);
    });
  });

  describe('findOne', () => {
    it('should return an evaluation by ID', async () => {
      evaluationRepository.findById.mockResolvedValue(mockEvaluation as any);

      const result = await service.findOne('eval-123');

      expect(result).toEqual(mockEvaluation);
      expect(evaluationRepository.findById).toHaveBeenCalledWith('eval-123');
    });

    it('should throw error if evaluation not found', async () => {
      evaluationRepository.findById.mockResolvedValue(null);

      await expect(service.findOne('non-existent')).rejects.toThrow();
    });
  });

  describe('findBySpeakerId', () => {
    it('should return evaluations for a speaker', async () => {
      speakerRepository.findById.mockResolvedValue(mockSpeaker as any);
      evaluationRepository.findBySpeakerId.mockResolvedValue([mockEvaluation] as any);

      const result = await service.findBySpeakerId('speaker-123');

      expect(result).toEqual([mockEvaluation]);
      expect(speakerRepository.findById).toHaveBeenCalledWith('speaker-123');
      expect(evaluationRepository.findBySpeakerId).toHaveBeenCalledWith('speaker-123');
    });

    it('should throw error if speaker not found', async () => {
      speakerRepository.findById.mockResolvedValue(null);

      await expect(service.findBySpeakerId('non-existent')).rejects.toThrow(SpeakerNotFoundError);
    });
  });

  describe('update', () => {
    it('should update an evaluation', async () => {
      const updatedEvaluation = { ...mockEvaluation, status: EvaluationStatus.IN_PROGRESS };
      evaluationRepository.findById.mockResolvedValue(mockEvaluation as any);
      evaluationRepository.update.mockResolvedValue(updatedEvaluation as any);

      const result = await service.update('eval-123', { status: EvaluationStatus.IN_PROGRESS });

      expect(result).toEqual(updatedEvaluation);
      expect(evaluationRepository.update).toHaveBeenCalledWith('eval-123', {
        status: EvaluationStatus.IN_PROGRESS,
      });
      expect(eventsService.publishObject).toHaveBeenCalled();
      expect(auditLogRepository.log).toHaveBeenCalled();
    });

    it('should throw error if evaluation not found', async () => {
      evaluationRepository.findById.mockResolvedValue(null);

      await expect(service.update('non-existent', { status: EvaluationStatus.IN_PROGRESS })).rejects.toThrow();
    });
  });

  describe('remove', () => {
    it('should soft delete an evaluation', async () => {
      evaluationRepository.findById.mockResolvedValue(mockEvaluation as any);
      evaluationRepository.delete.mockResolvedValue(mockEvaluation as any);

      const result = await service.remove('eval-123');

      expect(result).toEqual(mockEvaluation);
      expect(evaluationRepository.delete).toHaveBeenCalledWith('eval-123');
      expect(auditLogRepository.log).toHaveBeenCalled();
    });

    it('should throw error if evaluation not found', async () => {
      evaluationRepository.findById.mockResolvedValue(null);

      await expect(service.remove('non-existent')).rejects.toThrow();
    });
  });

  describe('getStatistics', () => {
    it('should return evaluation statistics', async () => {
      const mockStats = {
        total: 100,
        byStatus: {
          PENDING: 20,
          IN_PROGRESS: 30,
          COMPLETED: 45,
          FAILED: 5,
        },
      };

      evaluationRepository.getStatistics.mockResolvedValue(mockStats as any);

      const result = await service.getStatistics();

      expect(result).toEqual(mockStats);
      expect(evaluationRepository.getStatistics).toHaveBeenCalled();
    });
  });
});

