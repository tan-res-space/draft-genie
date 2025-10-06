import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import request = require('supertest');
import { SpeakersController } from './speakers.controller';
import { SpeakersService } from './speakers.service';
import { EvaluationsService } from '../evaluations/evaluations.service';
import { BucketType, SpeakerStatus } from '../common/constants/enums';

describe('SpeakersController (Integration)', () => {
  let app: INestApplication;
  let speakersService: jest.Mocked<SpeakersService>;

  const mockSpeaker = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    externalId: 'ext-123',
    name: 'John Doe',
    email: 'john@example.com',
    bucket: BucketType.GOOD,
    status: SpeakerStatus.ACTIVE,
    notes: 'Test notes',
    metadata: { source: 'test' },
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
    deletedAt: null,
  };

  const mockPaginatedResponse = {
    data: [mockSpeaker],
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
    byBucket: {
      [BucketType.EXCELLENT]: 20,
      [BucketType.GOOD]: 30,
      [BucketType.AVERAGE]: 25,
      [BucketType.POOR]: 15,
      [BucketType.NEEDS_IMPROVEMENT]: 10,
    },
    byStatus: {
      [SpeakerStatus.ACTIVE]: 80,
      [SpeakerStatus.INACTIVE]: 15,
      [SpeakerStatus.PENDING]: 3,
      [SpeakerStatus.ARCHIVED]: 2,
    },
  };

  beforeEach(async () => {
    const mockService = {
      create: jest.fn(),
      findAll: jest.fn(),
      findOne: jest.fn(),
      update: jest.fn(),
      updateBucket: jest.fn(),
      remove: jest.fn(),
      getStatistics: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [SpeakersController],
      providers: [
        {
          provide: SpeakersService,
          useValue: mockService,
        },
        {
          provide: EvaluationsService,
          useValue: {
            findBySpeakerId: jest.fn(),
          },
        },
      ],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ transform: true, whitelist: true }));
    await app.init();

    speakersService = module.get(SpeakersService);
  });

  afterEach(async () => {
    await app.close();
  });

  describe('POST /speakers', () => {
    it('should create a new speaker', async () => {
      speakersService.create.mockResolvedValue(mockSpeaker as any);

      const response = await request(app.getHttpServer())
        .post('/speakers')
        .send({
          name: 'John Doe',
          email: 'john@example.com',
          bucket: BucketType.GOOD,
        })
        .expect(201);

      expect(response.body).toEqual(mockSpeaker);
      expect(speakersService.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'John Doe',
          email: 'john@example.com',
          bucket: BucketType.GOOD,
        }),
      );
    });

    it('should return 400 for invalid data', async () => {
      await request(app.getHttpServer())
        .post('/speakers')
        .send({
          name: 'J', // Too short
          bucket: 'INVALID_BUCKET',
        })
        .expect(400);
    });

    it('should return 409 for duplicate speaker', async () => {
      speakersService.create.mockRejectedValue({
        code: 'SPEAKER_ALREADY_EXISTS',
        statusCode: 409,
        message: 'Speaker already exists',
      });

      await request(app.getHttpServer())
        .post('/speakers')
        .send({
          externalId: 'ext-123',
          name: 'John Doe',
          bucket: BucketType.GOOD,
        })
        .expect(409);
    });
  });

  describe('GET /speakers', () => {
    it('should return paginated speakers', async () => {
      speakersService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      const response = await request(app.getHttpServer())
        .get('/speakers')
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body).toEqual(mockPaginatedResponse);
      expect(speakersService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          limit: 10,
        }),
      );
    });

    it('should filter by bucket', async () => {
      speakersService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      await request(app.getHttpServer())
        .get('/speakers')
        .query({ bucket: BucketType.GOOD })
        .expect(200);

      expect(speakersService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          bucket: BucketType.GOOD,
        }),
      );
    });

    it('should filter by status', async () => {
      speakersService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      await request(app.getHttpServer())
        .get('/speakers')
        .query({ status: SpeakerStatus.ACTIVE })
        .expect(200);

      expect(speakersService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          status: SpeakerStatus.ACTIVE,
        }),
      );
    });

    it('should search by name', async () => {
      speakersService.findAll.mockResolvedValue(mockPaginatedResponse as any);

      await request(app.getHttpServer())
        .get('/speakers')
        .query({ search: 'John' })
        .expect(200);

      expect(speakersService.findAll).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'John',
        }),
      );
    });
  });

  describe('GET /speakers/statistics', () => {
    it('should return speaker statistics', async () => {
      speakersService.getStatistics.mockResolvedValue(mockStatistics);

      const response = await request(app.getHttpServer())
        .get('/speakers/statistics')
        .expect(200);

      expect(response.body).toEqual(mockStatistics);
      expect(speakersService.getStatistics).toHaveBeenCalled();
    });
  });

  describe('GET /speakers/:id', () => {
    it('should return a speaker by ID', async () => {
      speakersService.findOne.mockResolvedValue(mockSpeaker as any);

      const response = await request(app.getHttpServer())
        .get(`/speakers/${mockSpeaker.id}`)
        .expect(200);

      expect(response.body).toEqual(mockSpeaker);
      expect(speakersService.findOne).toHaveBeenCalledWith(mockSpeaker.id);
    });

    it('should return 404 for non-existent speaker', async () => {
      speakersService.findOne.mockRejectedValue({
        code: 'SPEAKER_NOT_FOUND',
        statusCode: 404,
        message: 'Speaker not found',
      });

      await request(app.getHttpServer())
        .get('/speakers/non-existent-id')
        .expect(404);
    });
  });

  describe('PATCH /speakers/:id', () => {
    it('should update a speaker', async () => {
      const updatedSpeaker = { ...mockSpeaker, name: 'Jane Doe' };
      speakersService.update.mockResolvedValue(updatedSpeaker as any);

      const response = await request(app.getHttpServer())
        .patch(`/speakers/${mockSpeaker.id}`)
        .send({ name: 'Jane Doe' })
        .expect(200);

      expect(response.body).toEqual(updatedSpeaker);
      expect(speakersService.update).toHaveBeenCalledWith(
        mockSpeaker.id,
        expect.objectContaining({ name: 'Jane Doe' }),
      );
    });

    it('should return 404 for non-existent speaker', async () => {
      speakersService.update.mockRejectedValue({
        code: 'SPEAKER_NOT_FOUND',
        statusCode: 404,
        message: 'Speaker not found',
      });

      await request(app.getHttpServer())
        .patch('/speakers/non-existent-id')
        .send({ name: 'Jane Doe' })
        .expect(404);
    });
  });

  describe('PUT /speakers/:id/bucket', () => {
    it('should update speaker bucket', async () => {
      const updatedSpeaker = { ...mockSpeaker, bucket: BucketType.EXCELLENT };
      speakersService.updateBucket.mockResolvedValue(updatedSpeaker as any);

      const response = await request(app.getHttpServer())
        .put(`/speakers/${mockSpeaker.id}/bucket`)
        .send({
          bucket: BucketType.EXCELLENT,
          reason: 'Improved performance',
        })
        .expect(200);

      expect(response.body).toEqual(updatedSpeaker);
      expect(speakersService.updateBucket).toHaveBeenCalledWith(
        mockSpeaker.id,
        expect.objectContaining({
          bucket: BucketType.EXCELLENT,
          reason: 'Improved performance',
        }),
      );
    });

    it('should return 400 for invalid bucket', async () => {
      await request(app.getHttpServer())
        .put(`/speakers/${mockSpeaker.id}/bucket`)
        .send({ bucket: 'INVALID_BUCKET' })
        .expect(400);
    });
  });

  describe('DELETE /speakers/:id', () => {
    it('should soft delete a speaker', async () => {
      speakersService.remove.mockResolvedValue(mockSpeaker as any);

      await request(app.getHttpServer())
        .delete(`/speakers/${mockSpeaker.id}`)
        .expect(204);

      expect(speakersService.remove).toHaveBeenCalledWith(mockSpeaker.id);
    });

    it('should return 404 for non-existent speaker', async () => {
      speakersService.remove.mockRejectedValue({
        code: 'SPEAKER_NOT_FOUND',
        statusCode: 404,
        message: 'Speaker not found',
      });

      await request(app.getHttpServer())
        .delete('/speakers/non-existent-id')
        .expect(404);
    });
  });
});

