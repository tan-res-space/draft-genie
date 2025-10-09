/**
 * Script to generate OpenAPI specification from NestJS application
 * Run with: ts-node services/api-gateway/scripts/generate-openapi.ts
 */

import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from '../src/app.module';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

async function generateOpenAPI() {
  const app = await NestFactory.create(AppModule, { logger: false });

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

  // Save as JSON
  const jsonPath = path.join(__dirname, '../../../schemas/openapi/api-gateway.json');
  fs.mkdirSync(path.dirname(jsonPath), { recursive: true });
  fs.writeFileSync(jsonPath, JSON.stringify(document, null, 2));

  // Save as YAML
  const yamlPath = path.join(__dirname, '../../../schemas/openapi/api-gateway.yaml');
  fs.writeFileSync(yamlPath, yaml.dump(document, { indent: 2 }));

  console.log('✅ OpenAPI specification generated:');
  console.log(`   - JSON: ${jsonPath}`);
  console.log(`   - YAML: ${yamlPath}`);

  await app.close();
}

generateOpenAPI().catch((error) => {
  console.error('❌ Failed to generate OpenAPI specification:', error);
  process.exit(1);
});

