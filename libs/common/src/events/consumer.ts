/**
 * Event consumer for RabbitMQ
 */

import * as amqp from 'amqplib';

export type EventHandler = (eventData: Record<string, any>) => Promise<void>;

export interface EventConsumerConfig {
  url: string;
  queue: string;
  prefetchCount?: number;
}

export class EventConsumer {
  private connection?: amqp.Connection;
  private channel?: amqp.Channel;
  private readonly handlers: Map<string, EventHandler[]> = new Map();
  private running = false;

  constructor(
    private readonly config: EventConsumerConfig,
  ) {}

  /**
   * Connect to RabbitMQ
   */
  async connect(): Promise<void> {
    try {
      console.log('Connecting to RabbitMQ', this.config.queue);

      this.connection = (await amqp.connect(this.config.url)) as any;
      this.channel = (await (this.connection as any).createChannel()) as any;

      await (this.channel as any).prefetch(this.config.prefetchCount || 10);
      await (this.channel as any).assertQueue(this.config.queue, { durable: true });

      console.log('Connected to RabbitMQ', this.config.queue);
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
      this.running = false;
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
   * Register an event handler
   */
  registerHandler(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
    console.log('Registered event handler', eventType);
  }

  /**
   * Process a message from the queue
   */
  private async processMessage(message: amqp.ConsumeMessage): Promise<void> {
    try {
      // Parse message body
      const eventData = JSON.parse(message.content.toString());
      const eventType = eventData.eventType;

      console.log('Processing event', eventType);

      // Get handlers for this event type
      const handlers = this.handlers.get(eventType) || [];
      if (handlers.length === 0) {
        console.warn('No handlers registered for event type', eventType);
        // Acknowledge message even if no handlers
        (this.channel as any)?.ack(message);
        return;
      }

      // Execute all handlers
      for (const handler of handlers) {
        try {
          await handler(eventData);
          console.log('Handler executed successfully', eventType);
        } catch (error) {
          console.error('Handler failed', error);
          // Reject message and requeue
          (this.channel as any)?.nack(message, false, true);
          return;
        }
      }

      // Acknowledge message after all handlers succeed
      (this.channel as any)?.ack(message);
    } catch (error) {
      console.error('Failed to process message', error);
      // Reject message without requeue for invalid messages
      (this.channel as any)?.nack(message, false, false);
    }
  }

  /**
   * Start consuming messages
   */
  async start(): Promise<void> {
    if (!this.channel) {
      throw new Error('Consumer not connected. Call connect() first.');
    }

    this.running = true;
    console.log('Starting event consumer', this.config.queue);

    try {
      await (this.channel as any).consume(
        this.config.queue,
        (message: amqp.ConsumeMessage | null) => {
          if (message) {
            this.processMessage(message).catch((error) => {
              console.error('Error processing message', error);
            });
          }
        },
        { noAck: false },
      );

      console.log('Event consumer started', this.config.queue);
    } catch (error) {
      console.error('Error in event consumer', error);
      throw error;
    }
  }

  /**
   * Stop consuming messages
   */
  async stop(): Promise<void> {
    this.running = false;
    console.log('Stopping event consumer');
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{
    healthy: boolean;
    queue?: string;
    running?: boolean;
    handlers?: Record<string, number>;
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

      const handlerCounts: Record<string, number> = {};
      this.handlers.forEach((handlers, eventType) => {
        handlerCounts[eventType] = handlers.length;
      });

      return {
        healthy: true,
        queue: this.config.queue,
        running: this.running,
        handlers: handlerCounts,
      };
    } catch (error) {
      return {
        healthy: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }
}

