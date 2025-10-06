import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { createClient, RedisClientType } from 'redis';
import { createLogger } from '@draft-genie/common';

@Injectable()
export class RedisService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = createLogger({ service: 'RedisService' });
  private client: RedisClientType | null = null;

  async onModuleInit() {
    try {
      const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

      this.client = createClient({ url: redisUrl }) as RedisClientType;

      this.client.on('error', (error) => {
        this.logger.error('Redis client error', error);
      });

      this.client.on('connect', () => {
        this.logger.info('Redis client connected');
      });

      this.client.on('reconnecting', () => {
        this.logger.warn('Redis client reconnecting');
      });

      await this.client.connect();

      this.logger.info('Connected to Redis', { url: redisUrl });
    } catch (error) {
      this.logger.error('Failed to connect to Redis', error as Error);
      throw error;
    }
  }

  async onModuleDestroy() {
    if (this.client) {
      await this.client.quit();
      this.logger.info('Disconnected from Redis');
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      if (!this.client) return false;
      await this.client.ping();
      return true;
    } catch (error) {
      this.logger.error('Redis health check failed', error as Error);
      return false;
    }
  }

  getClient(): RedisClientType {
    if (!this.client) {
      throw new Error('Redis client not initialized');
    }
    return this.client;
  }

  async get(key: string): Promise<string | null> {
    const client = this.getClient();
    return await client.get(key);
  }

  async set(key: string, value: string, ttlSeconds?: number): Promise<void> {
    const client = this.getClient();
    if (ttlSeconds) {
      await client.setEx(key, ttlSeconds, value);
    } else {
      await client.set(key, value);
    }
  }

  async del(key: string): Promise<void> {
    const client = this.getClient();
    await client.del(key);
  }

  async exists(key: string): Promise<boolean> {
    const client = this.getClient();
    const result = await client.exists(key);
    return result === 1;
  }

  async expire(key: string, ttlSeconds: number): Promise<void> {
    const client = this.getClient();
    await client.expire(key, ttlSeconds);
  }
}

