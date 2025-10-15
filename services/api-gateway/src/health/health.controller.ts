import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import {
  HealthCheck,
  HealthCheckService,
  HealthCheckResult,
  HealthIndicatorResult,
} from '@nestjs/terminus';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private httpService: HttpService,
  ) {}

  @Get()
  @HealthCheck()
  @ApiOperation({ summary: 'Health check for API Gateway' })
  @ApiResponse({ status: 200, description: 'Service is healthy' })
  @ApiResponse({ status: 503, description: 'Service is unhealthy' })
  check(): Promise<HealthCheckResult> {
    return this.health.check([
      () => Promise.resolve({ gateway: { status: 'up' } }),
    ]);
  }

  @Get('services')
  @HealthCheck()
  @ApiOperation({ summary: 'Health check for all backend services' })
  @ApiResponse({ status: 200, description: 'All services are healthy' })
  @ApiResponse({ status: 503, description: 'One or more services are unhealthy' })
  checkServices(): Promise<HealthCheckResult> {
    const speakerUrl = process.env['SPEAKER_SERVICE_URL'] ?? 'http://localhost:3001';
    const draftUrl = process.env['DRAFT_SERVICE_URL'] ?? 'http://localhost:3002';
    const ragUrl = process.env['RAG_SERVICE_URL'] ?? 'http://localhost:3003';
    const evaluationUrl = process.env['EVALUATION_SERVICE_URL'] ?? 'http://localhost:3004';

    return this.health.check([
      () => this.pingCheck('speaker-service', `${speakerUrl}/health`),
      () => this.pingCheck('draft-service', `${draftUrl}/health`),
      () => this.pingCheck('rag-service', `${ragUrl}/health`),
      () => this.pingCheck('evaluation-service', `${evaluationUrl}/health`),
    ]);
  }

  private async pingCheck(key: string, url: string): Promise<HealthIndicatorResult> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(url, { timeout: 3000 })
      );
      const isHealthy = response.status >= 200 && response.status < 300;
      return {
        [key]: {
          status: isHealthy ? 'up' : 'down',
        },
      };
    } catch (error) {
      return {
        [key]: {
          status: 'down',
          message: error.message,
        },
      };
    }
  }
}
