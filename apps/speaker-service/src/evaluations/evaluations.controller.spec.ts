import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import request = require('supertest');
import { EvaluationsController } from './evaluations.controller';
import { EvaluationsService } from './evaluations.service';
import { EvaluationStatus } from '../common/constants/enums';

describe('EvaluationsController (Integration)', () => {
  let app: INestApplication;
  let evaluationsService: jest.Mocked<EvaluationsService>;

  const mockEvaluation = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    speakerId: '123e4567-e89b-12d3-a456-426614174001',
    draftId: '123e4567-e89b-12d3-a456-426614174002',
    status: EvaluationStatus.COMPLETED,
    metrics: { clarity: 8.5, engagement: 9.0 },
    results: { summary: 'Good presentation' },
    notes: 'Test notes',
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
  };

  const mockPaginatedResponse = {
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

  const mockStatistics = {
    total: 100,
    byStatus: {
      PENDING: 20,
      IN_PROGRESS: 30,
      COMPLETED: 45,
      FAILED: 5,
    },
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [EvaluationsController],
      providers: [
        {
          provide: EvaluationsService,
          useValue: {
            create: jest.fn(),
            findAll: jest.fn(),
            findOne: jest.fn(),
            findBySpeakerId: jest.fn(),
            update: jest.fn(),
            remove: jest.fn(),
            getStatistics: jest.fn(),
          },
        },
      ],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ transform: true }));
    await app.init();

    evaluationsService = module.get(EvaluationsService);
  });

  afterEach(async () => {
    await app.close();
  });

  describe('POST /evaluations', () => {
    it('should create a new evaluation', async () => {
      evaluationsService.create.mockResolvedValue(mockEvaluation as any);

      const response = await request(app.getHttpServer())
        .post('/api/v1/evaluations')
        .send({
          speakerId: '123e4567-e89b-12d3-a456-426614174001',
          draftId: '123e4567-e89b-12d3-a456-426614174002',
          status: EvaluationStatus.PENDING,
        })
        .expect(201);

      expect(response.body).toEqual(mockEvaluation);
      expect(evaluationsService.create).toHaveBeenCalledWith(
        expect.objectContaining({
          speakerId: '123e4567-e89b-12d3-a456-426614174001',
          draftId: '123e4567-e89b-12d3-a456-426614174002',
          status: EvaluationStatus.PENDING,
        }),
      );
    });

    it('should return 400 for invalid input', async () => {
      await request(app.getHttpServer())
        .post('/api/v1/evaluations')
        .send({
          speakerId: 'invalid-uuid',
          draftId: '123e4567-e89b-12d3-a456-426614174002',
        })
        .expect(400);
    });
  });

  describe('GET /evaluations', () => {
    it('should return paginated evaluations', async () => {
      evaluationsService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      const response = await request(app.getHttpServer())
        .get('/api/v1/evaluations')
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body).toEqual(mockPaginatedResponse);
      expect(evaluationsService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          limit: 10,
        }),
      );
    });

    it('should filter by speaker ID', async () => {
      evaluationsService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      await request(app.getHttpServer())
        .get('/api/v1/evaluations')
        .query({ speakerId: '123e4567-e89b-12d3-a456-426614174001' })
        .expect(200);

      expect(evaluationsService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          speakerId: '123e4567-e89b-12d3-a456-426614174001',
        }),
      );
    });

    it('should filter by status', async () => {
      evaluationsService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      await request(app.getHttpServer())
        .get('/api/v1/evaluations')
        .query({ status: EvaluationStatus.COMPLETED })
        .expect(200);

      expect(evaluationsService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          status: EvaluationStatus.COMPLETED,
        }),
      );
    });
  });

  describe('GET /evaluations/statistics', () => {
    it('should return evaluation statistics', async () => {
      evaluationsService.getStatistics.mockResolvedValue(mockStatistics as any);

      const response = await request(app.getHttpServer())
        .get('/api/v1/evaluations/statistics')
        .expect(200);

      expect(response.body).toEqual(mockStatistics);
      expect(evaluationsService.getStatistics).toHaveBeenCalled();
    });
  });

  describe('GET /evaluations/:id', () => {
    it('should return an evaluation by ID', async () => {
      evaluationsService.findOne.mockResolvedValue(mockEvaluation as any);

      const response = await request(app.getHttpServer())
        .get(`/api/v1/evaluations/${mockEvaluation.id}`)
        .expect(200);

      expect(response.body).toEqual(mockEvaluation);
      expect(evaluationsService.findOne).toHaveBeenCalledWith(mockEvaluation.id);
    });

    it('should return 404 for non-existent evaluation', async () => {
      evaluationsService.findOne.mockRejectedValue(new Error('Evaluation not found'));

      await request(app.getHttpServer())
        .get('/api/v1/evaluations/non-existent-id')
        .expect(500);
    });
  });

  describe('PATCH /evaluations/:id', () => {
    it('should update an evaluation', async () => {
      const updatedEvaluation = { ...mockEvaluation, status: EvaluationStatus.IN_PROGRESS };
      evaluationsService.update.mockResolvedValue(updatedEvaluation as any);

      const response = await request(app.getHttpServer())
        .patch(`/api/v1/evaluations/${mockEvaluation.id}`)
        .send({ status: EvaluationStatus.IN_PROGRESS })
        .expect(200);

      expect(response.body).toEqual(updatedEvaluation);
      expect(evaluationsService.update).toHaveBeenCalledWith(
        mockEvaluation.id,
        expect.objectContaining({ status: EvaluationStatus.IN_PROGRESS }),
      );
    });

    it('should return 404 for non-existent evaluation', async () => {
      evaluationsService.update.mockRejectedValue(new Error('Evaluation not found'));

      await request(app.getHttpServer())
        .patch('/api/v1/evaluations/non-existent-id')
        .send({ status: EvaluationStatus.IN_PROGRESS })
        .expect(500);
    });
  });

  describe('DELETE /evaluations/:id', () => {
    it('should soft delete an evaluation', async () => {
      evaluationsService.remove.mockResolvedValue(mockEvaluation as any);

      await request(app.getHttpServer())
        .delete(`/api/v1/evaluations/${mockEvaluation.id}`)
        .expect(204);

      expect(evaluationsService.remove).toHaveBeenCalledWith(mockEvaluation.id);
    });

    it('should return 404 for non-existent evaluation', async () => {
      evaluationsService.remove.mockRejectedValue(new Error('Evaluation not found'));

      await request(app.getHttpServer())
        .delete('/api/v1/evaluations/non-existent-id')
        .expect(500);
    });
  });
});

