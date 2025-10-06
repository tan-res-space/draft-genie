import { BaseDomainEvent } from './base.event';
import { Speaker } from '../models';
import { BucketType } from '@draft-genie/common';

export class SpeakerOnboardedEvent extends BaseDomainEvent {
  constructor(speaker: Speaker, metadata?: Record<string, any>) {
    super('SpeakerOnboarded', speaker.id, 'Speaker', { speaker }, metadata);
  }
}

export class SpeakerUpdatedEvent extends BaseDomainEvent {
  constructor(
    speakerId: string,
    updates: Partial<Speaker>,
    metadata?: Record<string, any>,
  ) {
    super('SpeakerUpdated', speakerId, 'Speaker', { updates }, metadata);
  }
}

export class SpeakerDeletedEvent extends BaseDomainEvent {
  constructor(speakerId: string, metadata?: Record<string, any>) {
    super('SpeakerDeleted', speakerId, 'Speaker', { speakerId }, metadata);
  }
}

export class BucketReassignedEvent extends BaseDomainEvent {
  constructor(
    speakerId: string,
    oldBucket: BucketType,
    newBucket: BucketType,
    reason: string,
    metadata?: Record<string, any>,
  ) {
    super(
      'BucketReassigned',
      speakerId,
      'Speaker',
      { speakerId, oldBucket, newBucket, reason },
      metadata,
    );
  }
}

