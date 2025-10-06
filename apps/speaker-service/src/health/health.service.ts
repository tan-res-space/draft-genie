/**
 * Health Service - Health check logic
 */

import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { HealthCheckDto, DependencyHealth } from './dto/health-check.dto';

@Injectable()
export class HealthService {
  private readonly logger = new Logger(HealthService.name);

  constructor(private readonly prisma: PrismaService) {}

  async check(): Promise<HealthCheckDto> {
    const dependencies: Record<string, DependencyHealth> = {};

    // Check database
    dependencies.database = await this.checkDatabase();

    // Check RabbitMQ (if configured)
    if (process.env.RABBITMQ_URL) {
      dependencies.rabbitmq = await this.checkRabbitMQ();
    }

    // Determine overall status
    const allHealthy = Object.values(dependencies).every(
      (dep) => dep.status === 'healthy',
    );

    return {
      status: allHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      dependencies,
    };
  }

  private async checkDatabase(): Promise<DependencyHealth> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return {
        status: 'healthy',
        message: 'Database connection is healthy',
      };
    } catch (error) {
      this.logger.error('Database health check failed', error);
      return {
        status: 'unhealthy',
        message: error instanceof Error ? error.message : 'Database connection failed',
      };
    }
  }

  private async checkRabbitMQ(): Promise<DependencyHealth> {
    // TODO: Implement RabbitMQ health check when event module is ready
    return {
      status: 'healthy',
      message: 'RabbitMQ check not implemented yet',
    };
  }
}

