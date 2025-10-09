import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import {
  HealthCheck,
  HealthCheckService,
  HttpHealthIndicator,
  HealthCheckResult,
} from '@nestjs/terminus';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(
    private health: HealthCheckService,
    private http: HttpHealthIndicator,
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
      () => this.http.pingCheck('speaker-service', `${speakerUrl}/health`),
      () => this.http.pingCheck('draft-service', `${draftUrl}/health`),
      () => this.http.pingCheck('rag-service', `${ragUrl}/health`),
      () => this.http.pingCheck('evaluation-service', `${evaluationUrl}/health`),
    ]);
  }
}
