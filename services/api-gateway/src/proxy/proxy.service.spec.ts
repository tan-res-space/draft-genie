import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { HttpException, HttpStatus } from '@nestjs/common';
import { of, throwError } from 'rxjs';
import { AxiosResponse, AxiosError } from 'axios';
import { ProxyService, ServiceType } from './proxy.service';

describe('ProxyService', () => {
  let service: ProxyService;
  let httpService: HttpService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ProxyService,
        {
          provide: HttpService,
          useValue: {
            request: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config = {
                SPEAKER_SERVICE_URL: 'http://localhost:3001',
                DRAFT_SERVICE_URL: 'http://localhost:3002',
                RAG_SERVICE_URL: 'http://localhost:3003',
                EVALUATION_SERVICE_URL: 'http://localhost:3004',
              };
              return config[key];
            }),
          },
        },
      ],
    }).compile();

    service = module.get<ProxyService>(ProxyService);
    httpService = module.get<HttpService>(HttpService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('get', () => {
    it('should successfully proxy GET request', async () => {
      const mockResponse: AxiosResponse = {
        data: { id: '123', name: 'Test' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const result = await service.get(ServiceType.SPEAKER, '/api/v1/speakers/123');

      expect(result).toEqual(mockResponse.data);
      expect(httpService.request).toHaveBeenCalledWith({
        method: 'GET',
        url: 'http://localhost:3001/api/v1/speakers/123',
        headers: {
          'Content-Type': 'application/json',
        },
        params: undefined,
      });
    });

    it('should pass query parameters', async () => {
      const mockResponse: AxiosResponse = {
        data: [{ id: '1' }, { id: '2' }],
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const params = { page: 1, limit: 10 };
      await service.get(ServiceType.SPEAKER, '/api/v1/speakers', params);

      expect(httpService.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params,
        })
      );
    });
  });

  describe('post', () => {
    it('should successfully proxy POST request', async () => {
      const mockResponse: AxiosResponse = {
        data: { id: '123', created: true },
        status: 201,
        statusText: 'Created',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const postData = { name: 'New Speaker' };
      const result = await service.post(ServiceType.SPEAKER, '/api/v1/speakers', postData);

      expect(result).toEqual(mockResponse.data);
      expect(httpService.request).toHaveBeenCalledWith({
        method: 'POST',
        url: 'http://localhost:3001/api/v1/speakers',
        headers: {
          'Content-Type': 'application/json',
        },
        data: postData,
      });
    });
  });

  describe('error handling', () => {
    it('should handle service unavailable error', async () => {
      const axiosError = {
        request: {},
        message: 'Network Error',
      } as AxiosError;

      jest.spyOn(httpService, 'request').mockReturnValue(throwError(() => axiosError));

      await expect(
        service.get(ServiceType.SPEAKER, '/api/v1/speakers')
      ).rejects.toThrow(HttpException);

      try {
        await service.get(ServiceType.SPEAKER, '/api/v1/speakers');
      } catch (error) {
        expect(error.getStatus()).toBe(HttpStatus.SERVICE_UNAVAILABLE);
      }
    });

    it('should handle service error response', async () => {
      const axiosError = {
        response: {
          status: 404,
          data: { message: 'Not found' },
        },
        message: 'Request failed',
      } as AxiosError;

      jest.spyOn(httpService, 'request').mockReturnValue(throwError(() => axiosError));

      await expect(
        service.get(ServiceType.SPEAKER, '/api/v1/speakers/999')
      ).rejects.toThrow(HttpException);

      try {
        await service.get(ServiceType.SPEAKER, '/api/v1/speakers/999');
      } catch (error) {
        expect(error.getStatus()).toBe(404);
      }
    });
  });

  describe('all HTTP methods', () => {
    it('should support PUT requests', async () => {
      const mockResponse: AxiosResponse = {
        data: { updated: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const result = await service.put(ServiceType.SPEAKER, '/api/v1/speakers/123', { name: 'Updated' });

      expect(result).toEqual(mockResponse.data);
    });

    it('should support PATCH requests', async () => {
      const mockResponse: AxiosResponse = {
        data: { patched: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const result = await service.patch(ServiceType.SPEAKER, '/api/v1/speakers/123', { bucket: 'A' });

      expect(result).toEqual(mockResponse.data);
    });

    it('should support DELETE requests', async () => {
      const mockResponse: AxiosResponse = {
        data: { deleted: true },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      };

      jest.spyOn(httpService, 'request').mockReturnValue(of(mockResponse));

      const result = await service.delete(ServiceType.SPEAKER, '/api/v1/speakers/123');

      expect(result).toEqual(mockResponse.data);
    });
  });
});

