/**
 * Speakers Service - Business logic for speaker management
 */

import {
  Injectable,
  NotFoundException,
  ConflictException,
  Logger,
  BadRequestException,
} from '@nestjs/common';
import { Speaker } from '@prisma/client';
import { SpeakerRepository } from './repositories/speaker.repository';
import { AuditLogRepository } from '../common/repositories/audit-log.repository';
import { EventsService } from '../events/events.service';
import { CreateSpeakerDto } from './dto/create-speaker.dto';
import { UpdateSpeakerDto } from './dto/update-speaker.dto';
import { UpdateBucketDto } from './dto/update-bucket.dto';
import { QuerySpeakersDto } from './dto/query-speakers.dto';
import { PaginatedSpeakersResponseDto } from './dto/speaker-response.dto';
import { SpeakerStatus, AuditAction } from '../common/constants/enums';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class SpeakersService {
  private readonly logger = new Logger(SpeakersService.name);

  constructor(
    private readonly speakerRepository: SpeakerRepository,
    private readonly auditLogRepository: AuditLogRepository,
    private readonly eventsService: EventsService,
  ) {}

  /**
   * Create a new speaker (SSA - Speaker Self-Addition)
   */
  async create(createSpeakerDto: CreateSpeakerDto, userId?: string): Promise<Speaker> {
    this.logger.log(`Creating speaker: ${createSpeakerDto.name}`);

    // Check if external ID already exists
    if (createSpeakerDto.externalId) {
      const existing = await this.speakerRepository.findByExternalId(
        createSpeakerDto.externalId,
      );
      if (existing) {
        throw new ConflictException(
          `Speaker with external ID ${createSpeakerDto.externalId} already exists`,
        );
      }
    }

    // Create speaker
    const speaker = await this.speakerRepository.create({
      externalId: createSpeakerDto.externalId,
      name: createSpeakerDto.name,
      email: createSpeakerDto.email,
      bucket: createSpeakerDto.bucket,
      status: createSpeakerDto.status || SpeakerStatus.ACTIVE,
      notes: createSpeakerDto.notes,
      metadata: createSpeakerDto.metadata || {},
    });

    // Create audit log
    await this.auditLogRepository.log({
      entityType: 'Speaker',
      entityId: speaker.id,
      action: AuditAction.CREATE,
      userId,
      changes: { created: speaker },
      metadata: { source: 'api' },
    });

    // Publish SpeakerOnboardedEvent
    await this.publishSpeakerOnboardedEvent(speaker);

    this.logger.log(`Speaker created successfully: ${speaker.id}`);
    return speaker;
  }

  /**
   * Get all speakers with pagination and filters
   */
  async findAll(query: QuerySpeakersDto): Promise<PaginatedSpeakersResponseDto> {
    this.logger.debug(`Finding speakers with filters: ${JSON.stringify(query)}`);

    const filters = {
      bucket: query.bucket,
      status: query.status,
      search: query.search,
    };

    const options = {
      page: query.page,
      limit: query.limit,
      sortBy: query.sortBy,
      sortOrder: query.sortOrder,
    };

    const result = await this.speakerRepository.findAllWithFilters(filters, options);
    return result as any; // Prisma returns string for enums, but they match our enum values
  }

  /**
   * Get speaker by ID
   */
  async findOne(id: string): Promise<Speaker> {
    this.logger.debug(`Finding speaker: ${id}`);

    const speaker = await this.speakerRepository.findById(id);
    if (!speaker) {
      throw new NotFoundException(`Speaker with ID ${id} not found`);
    }

    return speaker;
  }

  /**
   * Update speaker
   */
  async update(
    id: string,
    updateSpeakerDto: UpdateSpeakerDto,
    userId?: string,
  ): Promise<Speaker> {
    this.logger.log(`Updating speaker: ${id}`);

    // Check if speaker exists
    const existingSpeaker = await this.findOne(id);

    // Update speaker
    const updatedSpeaker = await this.speakerRepository.update(id, updateSpeakerDto);

    // Create audit log
    await this.auditLogRepository.log({
      entityType: 'Speaker',
      entityId: id,
      action: AuditAction.UPDATE,
      userId,
      changes: {
        before: existingSpeaker,
        after: updatedSpeaker,
      },
      metadata: { source: 'api' },
    });

    // Publish SpeakerUpdatedEvent
    await this.publishSpeakerUpdatedEvent(updatedSpeaker, existingSpeaker);

    this.logger.log(`Speaker updated successfully: ${id}`);
    return updatedSpeaker;
  }

  /**
   * Update speaker bucket
   */
  async updateBucket(
    id: string,
    updateBucketDto: UpdateBucketDto,
    userId?: string,
  ): Promise<Speaker> {
    this.logger.log(`Updating speaker bucket: ${id} -> ${updateBucketDto.bucket}`);

    // Check if speaker exists
    const existingSpeaker = await this.findOne(id);

    // Check if bucket is different
    if (existingSpeaker.bucket === updateBucketDto.bucket) {
      throw new BadRequestException(
        `Speaker is already in bucket ${updateBucketDto.bucket}`,
      );
    }

    // Update bucket
    const updatedSpeaker = await this.speakerRepository.updateBucket(
      id,
      updateBucketDto.bucket,
    );

    // Create audit log
    await this.auditLogRepository.log({
      entityType: 'Speaker',
      entityId: id,
      action: AuditAction.BUCKET_REASSIGN,
      userId,
      changes: {
        oldBucket: existingSpeaker.bucket,
        newBucket: updateBucketDto.bucket,
        reason: updateBucketDto.reason,
      },
      metadata: { source: 'api' },
    });

    // Publish BucketReassignedEvent
    await this.publishBucketReassignedEvent(
      updatedSpeaker,
      existingSpeaker.bucket,
      updateBucketDto.reason,
    );

    this.logger.log(`Speaker bucket updated successfully: ${id}`);
    return updatedSpeaker;
  }

  /**
   * Soft delete speaker
   */
  async remove(id: string, userId?: string): Promise<Speaker> {
    this.logger.log(`Soft deleting speaker: ${id}`);

    // Check if speaker exists
    const existingSpeaker = await this.findOne(id);

    // Soft delete
    const deletedSpeaker = await this.speakerRepository.delete(id);

    // Create audit log
    await this.auditLogRepository.log({
      entityType: 'Speaker',
      entityId: id,
      action: AuditAction.DELETE,
      userId,
      changes: { deleted: existingSpeaker },
      metadata: { source: 'api', softDelete: true },
    });

    this.logger.log(`Speaker soft deleted successfully: ${id}`);
    return deletedSpeaker;
  }

  /**
   * Get speaker statistics
   */
  async getStatistics() {
    this.logger.debug('Getting speaker statistics');
    return await this.speakerRepository.getStatistics();
  }

  /**
   * Publish SpeakerOnboardedEvent
   */
  private async publishSpeakerOnboardedEvent(speaker: Speaker): Promise<void> {
    try {
      const event = {
        eventId: uuidv4(),
        eventType: 'speaker.onboarded',
        aggregateId: speaker.id,
        aggregateType: 'Speaker',
        timestamp: new Date().toISOString(),
        version: 1,
        payload: {
          speakerId: speaker.id,
          externalId: speaker.externalId,
          name: speaker.name,
          bucket: speaker.bucket,
          status: speaker.status,
          metadata: speaker.metadata,
        },
      };

      await this.eventsService.publishObject(event, 'speaker.onboarded');
      this.logger.debug(`Published SpeakerOnboardedEvent: ${speaker.id}`);
    } catch (error) {
      this.logger.error('Failed to publish SpeakerOnboardedEvent', error);
      // Don't throw - event publishing failure shouldn't fail the operation
    }
  }

  /**
   * Publish SpeakerUpdatedEvent
   */
  private async publishSpeakerUpdatedEvent(
    speaker: Speaker,
    previousSpeaker: Speaker,
  ): Promise<void> {
    try {
      const event = {
        eventId: uuidv4(),
        eventType: 'speaker.updated',
        aggregateId: speaker.id,
        aggregateType: 'Speaker',
        timestamp: new Date().toISOString(),
        version: 1,
        payload: {
          speakerId: speaker.id,
          changes: this.getChanges(previousSpeaker, speaker),
          currentState: {
            name: speaker.name,
            email: speaker.email,
            bucket: speaker.bucket,
            status: speaker.status,
          },
        },
      };

      await this.eventsService.publishObject(event, 'speaker.updated');
      this.logger.debug(`Published SpeakerUpdatedEvent: ${speaker.id}`);
    } catch (error) {
      this.logger.error('Failed to publish SpeakerUpdatedEvent', error);
    }
  }

  /**
   * Publish BucketReassignedEvent
   */
  private async publishBucketReassignedEvent(
    speaker: Speaker,
    oldBucket: string,
    reason?: string,
  ): Promise<void> {
    try {
      const event = {
        eventId: uuidv4(),
        eventType: 'speaker.bucket_reassigned',
        aggregateId: speaker.id,
        aggregateType: 'Speaker',
        timestamp: new Date().toISOString(),
        version: 1,
        payload: {
          speakerId: speaker.id,
          oldBucket,
          newBucket: speaker.bucket,
          reason,
        },
      };

      await this.eventsService.publishObject(event, 'speaker.bucket_reassigned');
      this.logger.debug(`Published BucketReassignedEvent: ${speaker.id}`);
    } catch (error) {
      this.logger.error('Failed to publish BucketReassignedEvent', error);
    }
  }

  /**
   * Get changes between two speaker objects
   */
  private getChanges(before: Speaker, after: Speaker): Record<string, any> {
    const changes: Record<string, any> = {};

    if (before.name !== after.name) {
      changes.name = { before: before.name, after: after.name };
    }
    if (before.email !== after.email) {
      changes.email = { before: before.email, after: after.email };
    }
    if (before.status !== after.status) {
      changes.status = { before: before.status, after: after.status };
    }
    if (before.notes !== after.notes) {
      changes.notes = { before: before.notes, after: after.notes };
    }

    return changes;
  }
}

