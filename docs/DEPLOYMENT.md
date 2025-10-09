# Draft Genie Deployment Guide

This guide covers deploying the Draft Genie system to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Database Setup](#database-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** 24.0+ and Docker Compose 2.20+
- **Node.js** 20+ and npm 10+
- **Python** 3.11+
- **Poetry** 1.7.1+
- **PostgreSQL** 16+ (for production)
- **MongoDB** 7+ (for production)
- **Redis** 7+ (for production)
- **RabbitMQ** 3.13+ (for production)
- **Qdrant** 1.7+ (for production)

### API Keys

- **Google Gemini API Key** - Required for AI features
  - Get from: https://makersuite.google.com/app/apikey

---

## Environment Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Environment
NODE_ENV=production
ENVIRONMENT=production

# API Gateway
PORT=3000
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=24h
API_KEYS=service-key-1,service-key-2,service-key-3
CORS_ORIGIN=https://yourdomain.com
THROTTLE_TTL=60000
THROTTLE_LIMIT=100

# Service URLs (Internal)
SPEAKER_SERVICE_URL=http://speaker-service:3001
DRAFT_SERVICE_URL=http://draft-service:3002
RAG_SERVICE_URL=http://rag-service:3003
EVALUATION_SERVICE_URL=http://evaluation-service:3004

# PostgreSQL
POSTGRES_USER=draftgenie
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=draftgenie
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# MongoDB
MONGO_USER=draftgenie
MONGO_PASSWORD=your-secure-password
MONGO_DB=draftgenie
MONGO_PORT=27017
MONGODB_URL=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/${MONGO_DB}?authSource=admin

# Qdrant
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_URL=http://qdrant:6333

# Redis
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

# RabbitMQ
RABBITMQ_USER=draftgenie
RABBITMQ_PASSWORD=your-secure-password
RABBITMQ_VHOST=/
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672
RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672/${RABBITMQ_VHOST}

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# Logging
LOG_LEVEL=info

# Swagger
SWAGGER_ENABLED=true
SWAGGER_PATH=api/docs
```

### Security Considerations

**⚠️ IMPORTANT: Change these in production:**

1. Generate strong passwords for all databases
2. Use a strong, random JWT_SECRET (min 32 characters)
3. Generate unique API_KEYS for service-to-service communication
4. Restrict CORS_ORIGIN to your actual domain
5. Use environment-specific secrets management (AWS Secrets Manager, Azure Key Vault, etc.)

---

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/tan-res-space/draft-genie.git
cd draft-genie

# 2. Install dependencies
npm install

# 3. Install Python dependencies for each service
cd services/draft-service && poetry install && cd ../..
cd services/rag-service && poetry install && cd ../..
cd services/evaluation-service && poetry install && cd ../..

# 4. Start infrastructure services
docker-compose up -d postgres mongodb qdrant redis rabbitmq

# 5. Run database migrations
npm run db:migrate

# 6. Start services in separate terminals
npm run dev:speaker      # Terminal 1
npm run dev:gateway      # Terminal 2
cd services/draft-service && poetry run uvicorn app.main:app --port 3002  # Terminal 3
cd services/rag-service && poetry run uvicorn app.main:app --port 3003    # Terminal 4
cd services/evaluation-service && poetry run uvicorn app.main:app --port 3004  # Terminal 5
```

### Verify Services

```bash
# Check all services are healthy
curl http://localhost:3000/api/v1/health  # API Gateway
curl http://localhost:3001/health         # Speaker Service
curl http://localhost:3002/health         # Draft Service
curl http://localhost:3003/health         # RAG Service
curl http://localhost:3004/health         # Evaluation Service
```

---

## Docker Deployment

### Build Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build speaker-service
```

### Start All Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-gateway

# Check service status
docker-compose ps
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## Production Deployment

### Option 1: Docker Compose (Single Server)

```bash
# 1. Copy production compose file
cp docker-compose.prod.yml docker-compose.yml

# 2. Set environment variables
cp .env.example .env
# Edit .env with production values

# 3. Pull latest images
docker-compose pull

# 4. Start services
docker-compose up -d

# 5. Run migrations
docker-compose exec speaker-service npm run db:migrate

# 6. Verify deployment
curl https://yourdomain.com/api/v1/health
```

### Option 2: Kubernetes

```bash
# 1. Create namespace
kubectl create namespace draft-genie

# 2. Create secrets
kubectl create secret generic draft-genie-secrets \
  --from-literal=jwt-secret=your-secret \
  --from-literal=postgres-password=your-password \
  --from-literal=gemini-api-key=your-key \
  -n draft-genie

# 3. Apply configurations
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/qdrant.yaml

# 4. Deploy services
kubectl apply -f k8s/speaker-service.yaml
kubectl apply -f k8s/draft-service.yaml
kubectl apply -f k8s/rag-service.yaml
kubectl apply -f k8s/evaluation-service.yaml
kubectl apply -f k8s/api-gateway.yaml

# 5. Verify deployment
kubectl get pods -n draft-genie
kubectl get services -n draft-genie
```

### Option 3: Cloud Platforms

#### AWS ECS

```bash
# 1. Push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag draft-genie-api-gateway:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/draft-genie-api-gateway:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/draft-genie-api-gateway:latest

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name draft-genie-cluster

# 3. Register task definitions
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 4. Create services
aws ecs create-service --cluster draft-genie-cluster --service-name api-gateway --task-definition draft-genie-api-gateway
```

#### Google Cloud Run

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/draft-genie-api-gateway

# 2. Deploy to Cloud Run
gcloud run deploy draft-genie-api-gateway \
  --image gcr.io/PROJECT_ID/draft-genie-api-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# 1. Push to Azure Container Registry
az acr build --registry draftgenieacr --image draft-genie-api-gateway:latest .

# 2. Deploy to ACI
az container create \
  --resource-group draft-genie-rg \
  --name draft-genie-api-gateway \
  --image draftgenieacr.azurecr.io/draft-genie-api-gateway:latest \
  --dns-name-label draft-genie \
  --ports 3000
```

---

## Database Setup

### PostgreSQL

```bash
# Create database
psql -U postgres -c "CREATE DATABASE draftgenie;"

# Run migrations
npm run db:migrate

# Seed initial data (optional)
npm run db:seed
```

### MongoDB

```bash
# Create database and collections
mongosh --eval "use draftgenie"

# Create indexes
mongosh draftgenie --eval "db.drafts.createIndex({speaker_id: 1, created_at: -1})"
mongosh draftgenie --eval "db.evaluations.createIndex({speaker_id: 1, created_at: -1})"
```

### Qdrant

```bash
# Collections are created automatically by services
# Verify collections
curl http://localhost:6333/collections
```

---

## Monitoring & Logging

### Health Checks

```bash
# API Gateway
curl http://localhost:3000/api/v1/health
curl http://localhost:3000/api/v1/health/services

# Individual services
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
curl http://localhost:3004/health
```

### Logs

```bash
# Docker Compose
docker-compose logs -f [service-name]

# Kubernetes
kubectl logs -f deployment/api-gateway -n draft-genie

# View last 100 lines
docker-compose logs --tail=100 api-gateway
```

### Metrics

Access service metrics:
- RabbitMQ Management: http://localhost:15672
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## Troubleshooting

### Services Not Starting

```bash
# Check service logs
docker-compose logs [service-name]

# Check if ports are available
lsof -i :3000  # API Gateway
lsof -i :3001  # Speaker Service
lsof -i :5432  # PostgreSQL
lsof -i :27017 # MongoDB

# Restart specific service
docker-compose restart [service-name]
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U draftgenie -d draftgenie

# Test MongoDB connection
mongosh mongodb://draftgenie:password@localhost:27017/draftgenie

# Check database logs
docker-compose logs postgres
docker-compose logs mongodb
```

### API Gateway Authentication Issues

```bash
# Verify JWT_SECRET is set
echo $JWT_SECRET

# Test login endpoint
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@draftgenie.com","password":"admin123"}'
```

### Service Communication Issues

```bash
# Check network connectivity
docker-compose exec api-gateway ping speaker-service
docker-compose exec api-gateway ping draft-service

# Verify service URLs
docker-compose exec api-gateway env | grep SERVICE_URL
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check database connections
docker-compose exec postgres psql -U draftgenie -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker-compose exec redis redis-cli INFO memory
```

---

## Backup & Recovery

### Database Backups

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U draftgenie draftgenie > backup_$(date +%Y%m%d).sql

# MongoDB backup
docker-compose exec mongodb mongodump --out=/backup --db=draftgenie

# Restore PostgreSQL
docker-compose exec -T postgres psql -U draftgenie draftgenie < backup_20251006.sql

# Restore MongoDB
docker-compose exec mongodb mongorestore /backup
```

---

## Next Steps

1. Set up monitoring (Prometheus, Grafana)
2. Configure log aggregation (ELK Stack, Loki)
3. Set up alerting (PagerDuty, Opsgenie)
4. Configure backups (automated daily backups)
5. Set up SSL/TLS certificates (Let's Encrypt)
6. Configure CDN (CloudFlare, AWS CloudFront)
7. Set up disaster recovery plan

---

For more information, see:
- [System Architecture](system_architecture_and_implementation_plan.md)
- [API Documentation](../schemas/openapi/)
- [Contributing Guide](../CONTRIBUTING.md)

