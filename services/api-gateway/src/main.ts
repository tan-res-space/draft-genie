/**
 * API Gateway - Main entry point
 * Provides unified entry point for all Draft Genie services
 */

import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { getServicePort } from '@draft-genie/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

  // Security
  app.use(helmet());

  // Global prefix
  app.setGlobalPrefix('api/v1');

  // Validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // CORS
  const corsOriginEnv = process.env['CORS_ORIGIN'] || '*';

  // Handle CORS origin configuration
  // When CORS_ORIGIN is '*', we need to use a function to allow all origins
  // because credentials: true is incompatible with origin: '*'
  const corsOrigin = corsOriginEnv === '*'
    ? (_origin: string, callback: (err: Error | null, allow?: boolean) => void) => {
        // Allow all origins when configured with '*'
        callback(null, true);
      }
    : corsOriginEnv.split(',').map(origin => origin.trim());

  app.enableCors({
    origin: corsOrigin,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
  });

  // Swagger documentation
  if ((process.env['SWAGGER_ENABLED'] ?? 'true') !== 'false') {
    const config = new DocumentBuilder()
      .setTitle('Draft Genie API Gateway')
      .setDescription(
        'Unified API Gateway for Draft Genie microservices. ' +
        'Provides authentication, routing, and data aggregation across all services.'
      )
      .setVersion('1.0')
      .addTag('auth', 'Authentication and authorization')
      .addTag('speakers', 'Speaker management (proxied to Speaker Service)')
      .addTag('drafts', 'Draft management (proxied to Draft Service)')
      .addTag('rag', 'RAG and DFN generation (proxied to RAG Service)')
      .addTag('evaluations', 'Evaluation and metrics (proxied to Evaluation Service)')
      .addTag('aggregation', 'Cross-service data aggregation')
      .addTag('workflow', 'Multi-service workflows')
      .addTag('dashboard', 'Dashboard and analytics')
      .addTag('health', 'Health check endpoints')
      .addBearerAuth(
        {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'Enter JWT token',
        },
        'JWT'
      )
      .addApiKey(
        {
          type: 'apiKey',
          name: 'X-API-Key',
          in: 'header',
          description: 'API Key for service-to-service communication',
        },
        'API-Key'
      )
      .build();

    const document = SwaggerModule.createDocument(app, config);
    const swaggerPath = process.env['SWAGGER_PATH'] ?? 'api/docs';

    SwaggerModule.setup(
      swaggerPath,
      app,
      document,
      {
        swaggerOptions: {
          persistAuthorization: true,
          tagsSorter: 'alpha',
          operationsSorter: 'alpha',
        },
      },
    );

    logger.log(
      `📚 Swagger documentation available at http://localhost:${process.env['PORT'] ?? 3000}/${swaggerPath}`,
    );
  }

  const port = getServicePort('api-gateway', 3000);
  await app.listen(port);

  logger.log(`🚀 API Gateway is running on: http://localhost:${port}/api/v1`);
  logger.log(`🔐 Authentication enabled with JWT`);
  logger.log(`🔄 Proxying to backend services:`);
  logger.log(`   - Speaker Service: ${process.env['SPEAKER_SERVICE_URL'] ?? 'http://localhost:3001'}`);
  logger.log(`   - Draft Service: ${process.env['DRAFT_SERVICE_URL'] ?? 'http://localhost:3002'}`);
  logger.log(`   - RAG Service: ${process.env['RAG_SERVICE_URL'] ?? 'http://localhost:3003'}`);
  logger.log(`   - Evaluation Service: ${process.env['EVALUATION_SERVICE_URL'] ?? 'http://localhost:3004'}`);
}

bootstrap();
