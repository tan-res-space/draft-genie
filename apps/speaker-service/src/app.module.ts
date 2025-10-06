/**
 * Speaker Service - Root Application Module
 */

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { HealthModule } from './health/health.module';
import { PrismaModule } from './prisma/prisma.module';
import { SpeakersModule } from './speakers/speakers.module';
import { EvaluationsModule } from './evaluations/evaluations.module';
import { EventsModule } from './events/events.module';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env', '.env.local'],
    }),

    // Core modules
    PrismaModule,
    EventsModule,
    HealthModule,

    // Feature modules
    SpeakersModule,
    EvaluationsModule,
  ],
})
export class AppModule {}

