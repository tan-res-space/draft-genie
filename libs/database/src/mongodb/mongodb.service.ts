import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import * as mongoose from 'mongoose';
import { createLogger } from '@draft-genie/common';

@Injectable()
export class MongoDBService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = createLogger({ service: 'MongoDBService' });
  private connection: typeof mongoose | null = null;

  async onModuleInit() {
    try {
      const mongoUrl = process.env.MONGODB_URL || 'mongodb://localhost:27017/draftgenie';

      mongoose.set('debug', process.env.NODE_ENV === 'development');

      this.connection = await mongoose.connect(mongoUrl, {
        maxPoolSize: 10,
        minPoolSize: 2,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
      });

      this.logger.info('Connected to MongoDB database', { url: mongoUrl });

      // Handle connection events
      mongoose.connection.on('error', (error) => {
        this.logger.error('MongoDB connection error', error);
      });

      mongoose.connection.on('disconnected', () => {
        this.logger.warn('MongoDB disconnected');
      });

      mongoose.connection.on('reconnected', () => {
        this.logger.info('MongoDB reconnected');
      });
    } catch (error) {
      this.logger.error('Failed to connect to MongoDB database', error as Error);
      throw error;
    }
  }

  async onModuleDestroy() {
    if (this.connection) {
      await mongoose.disconnect();
      this.logger.info('Disconnected from MongoDB database');
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      if (!this.connection) return false;
      const state = mongoose.connection.readyState;
      return state === 1; // 1 = connected
    } catch (error) {
      this.logger.error('MongoDB health check failed', error as Error);
      return false;
    }
  }

  getConnection(): typeof mongoose {
    if (!this.connection) {
      throw new Error('MongoDB connection not initialized');
    }
    return this.connection;
  }
}

