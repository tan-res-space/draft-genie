/**
 * Speakers Module
 */

import { Module } from '@nestjs/common';
import { SpeakersController } from './speakers.controller';
import { SpeakersService } from './speakers.service';
import { SpeakerRepository } from './repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { EvaluationsModule } from '../evaluations/evaluations.module';

@Module({
  imports: [EvaluationsModule],
  controllers: [SpeakersController],
  providers: [SpeakersService, SpeakerRepository, AuditLogRepository],
  exports: [SpeakersService, SpeakerRepository],
})
export class SpeakersModule {}

