import { BaseDomainEvent } from './base.event';
import { Evaluation } from '../models';

export class EvaluationStartedEvent extends BaseDomainEvent {
  constructor(evaluationId: string, speakerId: string, metadata?: Record<string, any>) {
    super(
      'EvaluationStarted',
      evaluationId,
      'Evaluation',
      { evaluationId, speakerId },
      metadata,
    );
  }
}

export class EvaluationCompletedEvent extends BaseDomainEvent {
  constructor(evaluation: Evaluation, metadata?: Record<string, any>) {
    super(
      'EvaluationCompleted',
      evaluation.id,
      'Evaluation',
      { evaluation },
      metadata,
    );
  }
}

export class EvaluationFailedEvent extends BaseDomainEvent {
  constructor(
    evaluationId: string,
    speakerId: string,
    error: string,
    metadata?: Record<string, any>,
  ) {
    super(
      'EvaluationFailed',
      evaluationId,
      'Evaluation',
      { evaluationId, speakerId, error },
      metadata,
    );
  }
}

