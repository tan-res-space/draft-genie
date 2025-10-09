import { Test, TestingModule } from '@nestjs/testing';
import { BadRequestException } from '@nestjs/common';
import { WorkflowService } from './workflow.service';
import { ProxyService, ServiceType } from '../proxy/proxy.service';

describe('WorkflowService', () => {
  let service: WorkflowService;
  let proxyService: ProxyService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        WorkflowService,
        {
          provide: ProxyService,
          useValue: {
            get: jest.fn(),
            post: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<WorkflowService>(WorkflowService);
    proxyService = module.get<ProxyService>(ProxyService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('generateDfn', () => {
    it('should complete DFN generation workflow successfully', async () => {
      const speakerId = '123';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker', bucket: 'A' };
      const mockDrafts = [{ id: '1', content: 'Draft 1' }];
      const mockGeneration = { dfn_id: 'dfn-123', session_id: 'session-123' };
      const mockDfn = { id: 'dfn-123', content: 'Generated DFN' };

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockResolvedValueOnce(mockDrafts)
        .mockResolvedValueOnce(mockDfn);

      jest.spyOn(proxyService, 'post').mockResolvedValueOnce(mockGeneration);

      const result = await service.generateDfn({
        speakerId,
        prompt: 'Test prompt',
      });

      expect(result.workflow.status).toBe('completed');
      expect(result.speaker.id).toBe(speakerId);
      expect(result.generation).toEqual(mockGeneration);
      expect(result.dfn).toEqual(mockDfn);
      expect(result.metadata.draftCount).toBe(1);
    });

    it('should throw BadRequestException if speaker not found', async () => {
      jest.spyOn(proxyService, 'get').mockRejectedValue(new Error('Not found'));

      const result = await service.generateDfn({
        speakerId: '999',
      });

      expect(result.workflow.status).toBe('failed');
      expect(result.workflow.error).toBeTruthy();
    });

    it('should throw BadRequestException if speaker has no drafts', async () => {
      const speakerId = '123';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker' };

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockResolvedValueOnce([]); // No drafts

      const result = await service.generateDfn({ speakerId });

      expect(result.workflow.status).toBe('failed');
      expect(result.workflow.error).toContain('has no drafts');
    });

    it('should handle RAG service failure', async () => {
      const speakerId = '123';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker' };
      const mockDrafts = [{ id: '1' }];

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockResolvedValueOnce(mockDrafts);

      jest.spyOn(proxyService, 'post').mockRejectedValue(new Error('RAG service error'));

      const result = await service.generateDfn({ speakerId });

      expect(result.workflow.status).toBe('failed');
      expect(result.workflow.error).toContain('RAG service error');
    });

    it('should use custom prompt if provided', async () => {
      const speakerId = '123';
      const customPrompt = 'Custom generation prompt';
      const mockSpeaker = { id: speakerId, name: 'Test Speaker' };
      const mockDrafts = [{ id: '1' }];
      const mockGeneration = { dfn_id: 'dfn-123' };

      jest.spyOn(proxyService, 'get')
        .mockResolvedValueOnce(mockSpeaker)
        .mockResolvedValueOnce(mockDrafts)
        .mockResolvedValueOnce({ id: 'dfn-123' });

      const postSpy = jest.spyOn(proxyService, 'post').mockResolvedValueOnce(mockGeneration);

      await service.generateDfn({
        speakerId,
        prompt: customPrompt,
      });

      expect(postSpy).toHaveBeenCalledWith(
        ServiceType.RAG,
        '/api/v1/rag/generate',
        expect.objectContaining({
          prompt: customPrompt,
        })
      );
    });
  });
});

