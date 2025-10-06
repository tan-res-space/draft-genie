import { Injectable, OnModuleInit } from '@nestjs/common';
import { QdrantClient } from '@qdrant/js-client-rest';
import { createLogger } from '@draft-genie/common';

@Injectable()
export class QdrantService implements OnModuleInit {
  private readonly logger = createLogger({ service: 'QdrantService' });
  private client: QdrantClient | null = null;

  async onModuleInit() {
    try {
      const qdrantUrl = process.env.QDRANT_URL || 'http://localhost:6333';

      this.client = new QdrantClient({ url: qdrantUrl });

      // Test connection
      await this.client.getCollections();

      this.logger.info('Connected to Qdrant vector database', { url: qdrantUrl });
    } catch (error) {
      this.logger.error('Failed to connect to Qdrant database', error as Error);
      throw error;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      if (!this.client) return false;
      await this.client.getCollections();
      return true;
    } catch (error) {
      this.logger.error('Qdrant health check failed', error as Error);
      return false;
    }
  }

  getClient(): QdrantClient {
    if (!this.client) {
      throw new Error('Qdrant client not initialized');
    }
    return this.client;
  }

  async createCollection(
    collectionName: string,
    vectorSize: number,
    distance: 'Cosine' | 'Euclid' | 'Dot' = 'Cosine',
  ): Promise<void> {
    try {
      const client = this.getClient();

      // Check if collection exists
      const collections = await client.getCollections();
      const exists = collections.collections.some((c) => c.name === collectionName);

      if (!exists) {
        await client.createCollection(collectionName, {
          vectors: {
            size: vectorSize,
            distance,
          },
        });
        this.logger.info('Created Qdrant collection', { collectionName, vectorSize, distance });
      } else {
        this.logger.info('Qdrant collection already exists', { collectionName });
      }
    } catch (error) {
      this.logger.error('Failed to create Qdrant collection', error as Error, {
        collectionName,
      });
      throw error;
    }
  }

  async deleteCollection(collectionName: string): Promise<void> {
    try {
      const client = this.getClient();
      await client.deleteCollection(collectionName);
      this.logger.info('Deleted Qdrant collection', { collectionName });
    } catch (error) {
      this.logger.error('Failed to delete Qdrant collection', error as Error, {
        collectionName,
      });
      throw error;
    }
  }
}

