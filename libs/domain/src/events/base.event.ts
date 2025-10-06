export interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  timestamp: Date;
  version: number;
  payload: any;
  metadata?: {
    correlationId?: string;
    causationId?: string;
    userId?: string;
    [key: string]: any;
  };
}

export abstract class BaseDomainEvent implements DomainEvent {
  public readonly eventId: string;
  public readonly eventType: string;
  public readonly aggregateId: string;
  public readonly aggregateType: string;
  public readonly timestamp: Date;
  public readonly version: number;
  public readonly metadata?: Record<string, any>;

  constructor(
    eventType: string,
    aggregateId: string,
    aggregateType: string,
    public readonly payload: any,
    metadata?: Record<string, any>,
  ) {
    this.eventId = this.generateEventId();
    this.eventType = eventType;
    this.aggregateId = aggregateId;
    this.aggregateType = aggregateType;
    this.timestamp = new Date();
    this.version = 1;
    this.metadata = metadata;
  }

  private generateEventId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  toJSON(): DomainEvent {
    return {
      eventId: this.eventId,
      eventType: this.eventType,
      aggregateId: this.aggregateId,
      aggregateType: this.aggregateType,
      timestamp: this.timestamp,
      version: this.version,
      payload: this.payload,
      metadata: this.metadata,
    };
  }
}

