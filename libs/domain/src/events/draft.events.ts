import { BaseDomainEvent } from './base.event';
import { Draft, CorrectionVector } from '../models';

export class DraftIngestedEvent extends BaseDomainEvent {
  constructor(draft: Draft, metadata?: Record<string, any>) {
    super('DraftIngested', draft.id, 'Draft', { draft }, metadata);
  }
}

export class CorrectionVectorCreatedEvent extends BaseDomainEvent {
  constructor(vector: CorrectionVector, metadata?: Record<string, any>) {
    super(
      'CorrectionVectorCreated',
      vector.id,
      'CorrectionVector',
      { vector },
      metadata,
    );
  }
}

export class CorrectionVectorUpdatedEvent extends BaseDomainEvent {
  constructor(
    vectorId: string,
    speakerId: string,
    metadata?: Record<string, any>,
  ) {
    super(
      'CorrectionVectorUpdated',
      vectorId,
      'CorrectionVector',
      { vectorId, speakerId },
      metadata,
    );
  }
}

export class DFNGeneratedEvent extends BaseDomainEvent {
  constructor(draft: Draft, metadata?: Record<string, any>) {
    super('DFNGenerated', draft.id, 'Draft', { draft }, metadata);
  }
}

