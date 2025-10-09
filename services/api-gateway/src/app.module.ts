/**
 * API Gateway - Root Application Module
 */

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerModule } from '@nestjs/throttler';
import { HealthModule } from './health/health.module';
import { AuthModule } from './auth/auth.module';
import { ProxyModule } from './proxy/proxy.module';
import { AggregationModule } from './aggregation/aggregation.module';
import { WorkflowModule } from './workflow/workflow.module';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env', '.env.local'],
    }),

    // Rate limiting
    ThrottlerModule.forRoot([{
      ttl: parseInt(process.env['THROTTLE_TTL'] ?? '60000', 10), // 60 seconds
      limit: parseInt(process.env['THROTTLE_LIMIT'] ?? '100', 10), // 100 requests
    }]),

    // Core modules
    HealthModule,
    AuthModule,

    // Feature modules
    ProxyModule,
    AggregationModule,
    WorkflowModule,
  ],
})
export class AppModule {}
