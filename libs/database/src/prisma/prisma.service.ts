import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { createLogger } from '@draft-genie/common';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = createLogger({ service: 'PrismaService' });

  constructor() {
    super({
      log: [
        { emit: 'event', level: 'query' },
        { emit: 'event', level: 'error' },
        { emit: 'event', level: 'warn' },
      ],
    });

    // Log queries in development
    if (process.env.NODE_ENV === 'development') {
      this.$on('query' as never, (e: any) => {
        this.logger.debug('Query executed', {
          query: e.query,
          params: e.params,
          duration: e.duration,
        });
      });
    }

    this.$on('error' as never, (e: any) => {
      this.logger.error('Prisma error', e);
    });

    this.$on('warn' as never, (e: any) => {
      this.logger.warn('Prisma warning', e);
    });
  }

  async onModuleInit() {
    try {
      await this.$connect();
      this.logger.info('Connected to PostgreSQL database');
    } catch (error) {
      this.logger.error('Failed to connect to PostgreSQL database', error as Error);
      throw error;
    }
  }

  async onModuleDestroy() {
    await this.$disconnect();
    this.logger.info('Disconnected from PostgreSQL database');
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.$queryRaw`SELECT 1`;
      return true;
    } catch (error) {
      this.logger.error('PostgreSQL health check failed', error as Error);
      return false;
    }
  }
}

