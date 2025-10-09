import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { AggregationService } from './aggregation.service';
import { ProxyService, ServiceType } from '../proxy/proxy.service';

describe('AggregationService', () => {
  let service: AggregationService;
  let proxyService: ProxyService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AggregationService,
        {
          provide: ProxyService,
          useValue: {
            get: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<AggregationService>(AggregationService);
    proxyService = module.get<ProxyService>(ProxyService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('getSpeakerComplete', () => {
    it('should aggregate complete speaker data successfully', async () => {
      const speakerId = '123';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker', bucket: 'A' };
      const mockDrafts = [{ id: '1', content: 'Draft 1' }, { id: '2', content: 'Draft 2' }];
      const mockEvaluations = [{ id: '1', score: 0.9 }];
      const mockMetrics = { averageScore: 0.85, totalEvaluations: 5 };

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockResolvedValueOnce(mockDrafts)
        .mockResolvedValueOnce(mockEvaluations)
        .mockResolvedValueOnce(mockMetrics);

      const result = await service.getSpeakerComplete(speakerId);

      expect(result.speaker).toEqual(mockSpeaker);
      expect(result.drafts.data).toEqual(mockDrafts);
      expect(result.evaluations.data).toEqual(mockEvaluations);
      expect(result.metrics.data).toEqual(mockMetrics);
      expect(result.summary.totalDrafts).toBe(2);
      expect(result.summary.totalEvaluations).toBe(1);
      expect(result).toHaveProperty('aggregatedAt');
    });

    it('should throw NotFoundException if speaker not found', async () => {
      jest.spyOn(proxyService, 'get').mockRejectedValue(new Error('Not found'));

      await expect(service.getSpeakerComplete('999')).rejects.toThrow(NotFoundException);
    });

    it('should handle partial failures gracefully', async () => {
      const speakerId = '123';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker' };

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockRejectedValueOnce(new Error('Drafts service down'))
        .mockRejectedValueOnce(new Error('Evaluations service down'))
        .mockRejectedValueOnce(new Error('Metrics service down'));

      const result = await service.getSpeakerComplete(speakerId);

      expect(result.speaker).toEqual(mockSpeaker);
      expect(result.drafts.error).toBeTruthy();
      expect(result.evaluations.error).toBeTruthy();
      expect(result.metrics.error).toBeTruthy();
    });
  });

  describe('getDashboardMetrics', () => {
    it('should aggregate dashboard metrics successfully', async () => {
      const mockSpeakerStats = { total: 10, byBucket: { A: 3, B: 4, C: 3 } };
      const mockEvaluationMetrics = [{ id: '1' }, { id: '2' }];
      const mockDrafts = [{ id: '1', status: 'completed' }, { id: '2', status: 'pending' }];

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeakerStats)
        .mockResolvedValueOnce(mockEvaluationMetrics)
        .mockResolvedValueOnce(mockDrafts);

      const result = await service.getDashboardMetrics();

      expect(result.speakers.data).toEqual(mockSpeakerStats);
      expect(result.evaluations.data).toEqual(mockEvaluationMetrics);
      expect(result.drafts.data.total).toBe(2);
      expect(result.summary.totalSpeakers).toBe(10);
      expect(result.summary.servicesHealthy).toBe(3);
      expect(result.summary.healthPercentage).toBe(100);
    });

    it('should handle service failures gracefully', async () => {
      jest.spyOn(proxyService, 'get')
        .mockRejectedValueOnce(new Error('Speaker service down'))
        .mockRejectedValueOnce(new Error('Evaluation service down'))
        .mockRejectedValueOnce(new Error('Draft service down'));

      const result = await service.getDashboardMetrics();

      expect(result.speakers.error).toBeTruthy();
      expect(result.evaluations.error).toBeTruthy();
      expect(result.drafts.error).toBeTruthy();
      expect(result.summary.servicesHealthy).toBe(0);
      expect(result.summary.healthPercentage).toBe(0);
    });
  });
});

