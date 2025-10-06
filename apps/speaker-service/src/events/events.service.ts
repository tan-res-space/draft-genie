/**
 * Events Service - Event publishing and consuming
 */

import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { EventPublisher, initEventPublisher } from '@draft-genie/common';

@Injectable()
export class EventsService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(EventsService.name);
  private publisher: EventPublisher;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    try {
      const rabbitmqUrl = this.configService.get<string>('RABBITMQ_URL');
      const exchange = this.configService.get<string>('RABBITMQ_EXCHANGE', 'draft-genie.events');

      if (!rabbitmqUrl) {
        this.logger.warn('RABBITMQ_URL not configured, event publishing disabled');
        return;
      }

      this.publisher = initEventPublisher({
        url: rabbitmqUrl,
        exchange,
      });

      await this.publisher.connect();
      this.logger.log('✅ Event publisher connected');
    } catch (error) {
      this.logger.error('❌ Failed to connect event publisher', error);
      // Don't throw - allow service to start without events
    }
  }

  async onModuleDestroy() {
    if (this.publisher) {
      await this.publisher.disconnect();
      this.logger.log('Event publisher disconnected');
    }
  }

  /**
   * Publish an event
   */
  async publish(event: any, routingKey?: string): Promise<void> {
    if (!this.publisher) {
      this.logger.warn('Event publisher not available, skipping event publication');
      return;
    }

    try {
      await this.publisher.publish(event, routingKey);
      this.logger.debug(`Published event: ${event.eventType}`, {
        eventId: event.eventId,
        routingKey: routingKey || event.eventType,
      });
    } catch (error) {
      this.logger.error('Failed to publish event', error);
      throw error;
    }
  }

  /**
   * Publish event from object
   */
  async publishObject(eventData: Record<string, any>, routingKey: string): Promise<void> {
    if (!this.publisher) {
      this.logger.warn('Event publisher not available, skipping event publication');
      return;
    }

    try {
      await this.publisher.publishObject(eventData, routingKey);
      this.logger.debug(`Published event: ${eventData.eventType}`, {
        eventId: eventData.eventId,
        routingKey,
      });
    } catch (error) {
      this.logger.error('Failed to publish event', error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ healthy: boolean; message?: string }> {
    if (!this.publisher) {
      return {
        healthy: false,
        message: 'Event publisher not initialized',
      };
    }

    return this.publisher.healthCheck();
  }
}

