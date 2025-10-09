import { Injectable, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { AxiosError, AxiosRequestConfig } from 'axios';

export enum ServiceType {
  SPEAKER = 'speaker',
  DRAFT = 'draft',
  RAG = 'rag',
  EVALUATION = 'evaluation',
}

@Injectable()
export class ProxyService {
  private readonly logger = new Logger(ProxyService.name);
  private readonly serviceUrls: Map<ServiceType, string>;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.serviceUrls = new Map([
      [ServiceType.SPEAKER, this.configService.get<string>('SPEAKER_SERVICE_URL') || 'http://localhost:3001'],
      [ServiceType.DRAFT, this.configService.get<string>('DRAFT_SERVICE_URL') || 'http://localhost:3002'],
      [ServiceType.RAG, this.configService.get<string>('RAG_SERVICE_URL') || 'http://localhost:3003'],
      [ServiceType.EVALUATION, this.configService.get<string>('EVALUATION_SERVICE_URL') || 'http://localhost:3004'],
    ]);
  }

  async proxyRequest(
    service: ServiceType,
    path: string,
    method: string,
    data?: any,
    headers?: Record<string, string>,
  ): Promise<any> {
    const baseUrl = this.serviceUrls.get(service);
    const url = `${baseUrl}${path}`;

    this.logger.debug(`Proxying ${method} request to ${url}`);

    const config: AxiosRequestConfig = {
      method,
      url,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.data = data;
    }

    if (method === 'GET' && data) {
      config.params = data;
    }

    try {
      const response = await firstValueFrom(this.httpService.request(config));
      return response.data;
    } catch (error) {
      this.handleProxyError(error as AxiosError, service);
    }
  }

  async get(service: ServiceType, path: string, params?: any, headers?: Record<string, string>): Promise<any> {
    return this.proxyRequest(service, path, 'GET', params, headers);
  }

  async post(service: ServiceType, path: string, data?: any, headers?: Record<string, string>): Promise<any> {
    return this.proxyRequest(service, path, 'POST', data, headers);
  }

  async put(service: ServiceType, path: string, data?: any, headers?: Record<string, string>): Promise<any> {
    return this.proxyRequest(service, path, 'PUT', data, headers);
  }

  async patch(service: ServiceType, path: string, data?: any, headers?: Record<string, string>): Promise<any> {
    return this.proxyRequest(service, path, 'PATCH', data, headers);
  }

  async delete(service: ServiceType, path: string, headers?: Record<string, string>): Promise<any> {
    return this.proxyRequest(service, path, 'DELETE', undefined, headers);
  }

  private handleProxyError(error: AxiosError, service: ServiceType): never {
    const serviceName = service.toString();
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      this.logger.error(
        `${serviceName} service error: ${error.response.status} - ${JSON.stringify(error.response.data)}`,
      );
      throw new HttpException(
        error.response.data || `Error from ${serviceName} service`,
        error.response.status,
      );
    } else if (error.request) {
      // The request was made but no response was received
      this.logger.error(`${serviceName} service is not responding`);
      throw new HttpException(
        `${serviceName} service is not available`,
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    } else {
      // Something happened in setting up the request that triggered an Error
      this.logger.error(`Error setting up request to ${serviceName}: ${error.message}`);
      throw new HttpException(
        'Internal server error',
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }
}

