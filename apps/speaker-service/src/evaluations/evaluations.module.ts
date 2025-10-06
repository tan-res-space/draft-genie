/**
 * Evaluations Module
 */

import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { EventsModule } from '../events/events.module';
import { EvaluationRepository } from './repositories/evaluation.repository';
import { SpeakerRepository } from '../speakers/repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { EvaluationsService } from './evaluations.service';
import { EvaluationsController } from './evaluations.controller';

@Module({
  imports: [PrismaModule, EventsModule],
  controllers: [EvaluationsController],
  providers: [
    EvaluationsService,
    EvaluationRepository,
    SpeakerRepository,
    AuditLogRepository,
  ],
  exports: [EvaluationsService, EvaluationRepository],
})
export class EvaluationsModule {}

