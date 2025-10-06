/**
 * Event publisher for RabbitMQ
 */

import * as amqp from 'amqplib';
import { DomainEvent } from '../types';

export interface EventPublisherConfig {
  url: string;
  exchange: string;
}

export class EventPublisher {
  private connection?: amqp.Connection;
  private channel?: amqp.Channel;

  constructor(
    private readonly config: EventPublisherConfig,
  ) {}

  /**
   * Connect to RabbitMQ
   */
  async connect(): Promise<void> {
    try {
      console.log('Connecting to RabbitMQ', this.config.exchange);

      this.connection = (await amqp.connect(this.config.url)) as any;
      this.channel = (await (this.connection as any).createChannel()) as any;

      await (this.channel as any).assertExchange(
        this.config.exchange,
        'topic',
        { durable: true },
      );

      console.log('Connected to RabbitMQ', this.config.exchange);
    } catch (error) {
      console.error('Failed to connect to RabbitMQ', error);
      throw error;
    }
  }

  /**
   * Disconnect from RabbitMQ
   */
  async disconnect(): Promise<void> {
    try {
      if (this.channel) {
        await (this.channel as any).close();
      }
      if (this.connection) {
        await (this.connection as any).close();
      }
      console.log('Disconnected from RabbitMQ');
    } catch (error) {
      console.error('Error disconnecting from RabbitMQ', error);
    }
  }

  /**
   * Publish a domain event
   */
  async publish(
    event: DomainEvent,
    routingKey?: string,
  ): Promise<void> {
    if (!this.channel) {
      throw new Error('Publisher not connected. Call connect() first.');
    }

    // Use event type as routing key if not provided
    const key = routingKey || event.eventType;

    try {
      const messageBuffer = Buffer.from(JSON.stringify(event));

      const options: amqp.Options.Publish = {
        persistent: true,
        contentType: 'application/json',
        headers: {
          eventId: event.eventId,
          eventType: event.eventType,
          aggregateId: event.aggregateId,
          correlationId: event.correlationId,
        },
      };

      (this.channel as any).publish(
        this.config.exchange,
        key,
        messageBuffer,
        options,
      );

      console.log('Published event', event.eventType, key);
    } catch (error) {
      console.error('Failed to publish event', error);
      throw error;
    }
  }

  /**
   * Publish an event from a plain object
   */
  async publishObject(
    eventData: Record<string, any>,
    routingKey: string,
  ): Promise<void> {
    if (!this.channel) {
      throw new Error('Publisher not connected. Call connect() first.');
    }

    try {
      const messageBuffer = Buffer.from(JSON.stringify(eventData));

      const options: amqp.Options.Publish = {
        persistent: true,
        contentType: 'application/json',
        headers: {
          eventId: eventData.eventId,
          eventType: eventData.eventType,
          aggregateId: eventData.aggregateId,
          correlationId: eventData.correlationId,
        },
      };

      (this.channel as any).publish(
        this.config.exchange,
        routingKey,
        messageBuffer,
        options,
      );

      console.log('Published event from object', eventData.eventType, routingKey);
    } catch (error) {
      console.error('Failed to publish event from object', error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{
    healthy: boolean;
    exchange?: string;
    message?: string;
    error?: string;
  }> {
    try {
      if (!this.connection || !this.channel) {
        return {
          healthy: false,
          message: 'Not connected to RabbitMQ',
        };
      }

      return {
        healthy: true,
        exchange: this.config.exchange,
      };
    } catch (error) {
      return {
        healthy: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }
}

// Global publisher instance
let eventPublisher: EventPublisher | null = null;

/**
 * Initialize global event publisher
 */
export function initEventPublisher(config: EventPublisherConfig): EventPublisher {
  eventPublisher = new EventPublisher(config);
  return eventPublisher;
}

/**
 * Get global event publisher instance
 */
export function getEventPublisher(): EventPublisher {
  if (!eventPublisher) {
    throw new Error('Event publisher not initialized. Call initEventPublisher() first.');
  }
  return eventPublisher;
}

