/**
 * Speaker Service - Main entry point
 */

import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { getServicePort } from '@draft-genie/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

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
  app.enableCors({
    origin: process.env.CORS_ORIGIN || '*',
    credentials: true,
  });

  // Swagger documentation
  if (process.env.SWAGGER_ENABLED !== 'false') {
    const config = new DocumentBuilder()
      .setTitle('Speaker Service API')
      .setDescription('API for managing speakers and their quality buckets')
      .setVersion('1.0')
      .addTag('speakers', 'Speaker management operations')
      .addTag('evaluations', 'Evaluation management operations')
      .addTag('health', 'Health check endpoints')
      .addBearerAuth()
      .build();

    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup(
      process.env.SWAGGER_PATH || 'api/docs',
      app,
      document,
      {
        swaggerOptions: {
          persistAuthorization: true,
        },
      },
    );

    logger.log(
      `Swagger documentation available at http://localhost:${process.env.PORT || 3001}/${process.env.SWAGGER_PATH || 'api/docs'}`,
    );
  }

  const port = getServicePort('speaker-service', 3001);
  await app.listen(port, '0.0.0.0');

  logger.log(`🚀 Speaker Service is running on: http://0.0.0.0:${port}/api/v1`);
  logger.log(`📚 API Documentation: http://0.0.0.0:${port}/${process.env.SWAGGER_PATH || 'api/docs'}`);
}

bootstrap();

