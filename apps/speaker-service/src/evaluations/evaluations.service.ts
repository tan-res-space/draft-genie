import { Injectable, Logger } from '@nestjs/common';
import { EventsService } from '../events/events.service';
import { EvaluationRepository } from './repositories/evaluation.repository';
import { SpeakerRepository } from '../speakers/repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { CreateEvaluationDto } from './dto/create-evaluation.dto';
import { UpdateEvaluationDto } from './dto/update-evaluation.dto';
import { QueryEvaluationsDto } from './dto/query-evaluations.dto';
import { PaginatedEvaluationsResponseDto } from './dto/evaluation-response.dto';
import { EvaluationStatus, AuditAction } from '../common/constants/enums';
import { SpeakerNotFoundError } from '@draft-genie/common';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class EvaluationsService {
  private readonly logger = new Logger(EvaluationsService.name);

  constructor(
    private readonly evaluationRepository: EvaluationRepository,
    private readonly speakerRepository: SpeakerRepository,
    private readonly auditLogRepository: AuditLogRepository,
    private readonly eventsService: EventsService,
  ) {}

  async create(createEvaluationDto: CreateEvaluationDto, userId?: string) {
    this.logger.log(`Creating evaluation for speaker ${createEvaluationDto.speakerId}`);

    // Verify speaker exists
    const speaker = await this.speakerRepository.findById(createEvaluationDto.speakerId);
    if (!speaker) {
      throw new SpeakerNotFoundError(createEvaluationDto.speakerId);
    }

    // Create evaluation
    const evaluation = await this.evaluationRepository.create({
      speakerId: createEvaluationDto.speakerId,
      draftId: createEvaluationDto.draftId,
      status: createEvaluationDto.status || EvaluationStatus.PENDING,
      metrics: createEvaluationDto.metrics || {},
      results: createEvaluationDto.results || {},
      notes: createEvaluationDto.notes || null,
    });

    // Publish event
    await this.eventsService.publishObject(
      {
        eventId: uuidv4(),
        eventType: 'EvaluationCreated',
        aggregateId: evaluation.id,
        timestamp: new Date().toISOString(),
        correlationId: uuidv4(),
        payload: {
          evaluationId: evaluation.id,
          speakerId: evaluation.speakerId,
          draftId: evaluation.draftId,
          status: evaluation.status,
        },
      },
      'evaluation.created',
    );

    // Log audit
    await this.auditLogRepository.log({
      entityType: 'Evaluation',
      entityId: evaluation.id,
      action: AuditAction.CREATE,
      userId: userId || 'system',
      changes: { after: evaluation },
    });

    this.logger.log(`Evaluation created: ${evaluation.id}`);
    return evaluation;
  }

  async findAll(query: QueryEvaluationsDto): Promise<PaginatedEvaluationsResponseDto> {
    this.logger.log(`Finding evaluations with filters: ${JSON.stringify(query)}`);

    const filters = {
      speakerId: query.speakerId,
      draftId: query.draftId,
      status: query.status,
    };

    const options = {
      page: query.page,
      limit: query.limit,
      sortBy: query.sortBy,
      sortOrder: query.sortOrder,
    };

    const result = await this.evaluationRepository.findAllWithFilters(filters, options);
    return result as any;
  }

  async findOne(id: string) {
    this.logger.log(`Finding evaluation: ${id}`);

    const evaluation = await this.evaluationRepository.findById(id);
    if (!evaluation) {
      throw new Error(`Evaluation with ID '${id}' not found`);
    }

    return evaluation;
  }

  async findBySpeakerId(speakerId: string) {
    this.logger.log(`Finding evaluations for speaker: ${speakerId}`);

    // Verify speaker exists
    const speaker = await this.speakerRepository.findById(speakerId);
    if (!speaker) {
      throw new SpeakerNotFoundError(speakerId);
    }

    const evaluations = await this.evaluationRepository.findBySpeakerId(speakerId);
    return evaluations;
  }

  async update(id: string, updateEvaluationDto: UpdateEvaluationDto, userId?: string) {
    this.logger.log(`Updating evaluation: ${id}`);

    // Get existing evaluation
    const existing = await this.evaluationRepository.findById(id);
    if (!existing) {
      throw new Error(`Evaluation with ID '${id}' not found`);
    }

    // Update evaluation
    const updated = await this.evaluationRepository.update(id, updateEvaluationDto);

    // Publish event
    await this.eventsService.publishObject(
      {
        eventId: uuidv4(),
        eventType: 'EvaluationUpdated',
        aggregateId: updated.id,
        timestamp: new Date().toISOString(),
        correlationId: uuidv4(),
        payload: {
          evaluationId: updated.id,
          speakerId: updated.speakerId,
          changes: updateEvaluationDto,
        },
      },
      'evaluation.updated',
    );

    // Log audit
    await this.auditLogRepository.log({
      entityType: 'Evaluation',
      entityId: updated.id,
      action: AuditAction.UPDATE,
      userId: userId || 'system',
      changes: {
        before: existing,
        after: updated,
      },
    });

    this.logger.log(`Evaluation updated: ${id}`);
    return updated;
  }

  async remove(id: string, userId?: string) {
    this.logger.log(`Deleting evaluation: ${id}`);

    // Get existing evaluation
    const existing = await this.evaluationRepository.findById(id);
    if (!existing) {
      throw new Error(`Evaluation with ID '${id}' not found`);
    }

    // Soft delete
    const deleted = await this.evaluationRepository.delete(id);

    // Log audit
    await this.auditLogRepository.log({
      entityType: 'Evaluation',
      entityId: id,
      action: AuditAction.DELETE,
      userId: userId || 'system',
      changes: { before: existing },
    });

    this.logger.log(`Evaluation deleted: ${id}`);
    return deleted;
  }

  async getStatistics() {
    this.logger.log('Getting evaluation statistics');
    return await this.evaluationRepository.getStatistics();
  }
}

