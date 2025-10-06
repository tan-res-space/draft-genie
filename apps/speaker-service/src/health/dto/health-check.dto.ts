/**
 * Health Check DTOs
 */

import { ApiProperty } from '@nestjs/swagger';

export class DependencyHealth {
  @ApiProperty({
    description: 'Dependency status',
    enum: ['healthy', 'unhealthy'],
  })
  status: 'healthy' | 'unhealthy';

  @ApiProperty({
    description: 'Status message',
    required: false,
  })
  message?: string;
}

export class HealthCheckDto {
  @ApiProperty({
    description: 'Overall health status',
    enum: ['healthy', 'unhealthy'],
  })
  status: 'healthy' | 'unhealthy';

  @ApiProperty({
    description: 'Timestamp of health check',
    example: '2024-01-15T10:30:00Z',
  })
  timestamp: string;

  @ApiProperty({
    description: 'Service version',
    example: '1.0.0',
    required: false,
  })
  version?: string;

  @ApiProperty({
    description: 'Health status of dependencies',
    type: 'object',
    additionalProperties: {
      type: 'object',
    },
  })
  dependencies: Record<string, DependencyHealth>;
}

