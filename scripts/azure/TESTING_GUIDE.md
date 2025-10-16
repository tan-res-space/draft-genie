# Azure Services Testing Guide

## Current Status

Based on the Azure resource check, here's what's deployed:

### ✅ Infrastructure (Deployed)
- **Container Registry**: `acrdgbackendv01`
- **Key Vault**: `dg-backend-kv-v01`
- **PostgreSQL**: `dg-backend-postgres` (Central India)
- **Redis**: `dg-backend-redis`
- **Container Apps Environment**: `dg-backend-env`
- **Log Analytics**: `dg-backend-logs`
- **Application Insights**: `dg-backend-insights`

### ❌ Application Services (Not Deployed)
- API Gateway
- Speaker Service
- Draft Service
- RAG Service
- Evaluation Service

## Step 1: Build and Push Docker Images

Before deploying services, you need to build and push Docker images to Azure Container Registry.

### Build All Services

```bash
# Build and push all services
./scripts/docker/build-all-services.sh
```

Or build individual services:

```bash
# API Gateway (Node.js/NestJS)
./scripts/docker/build-push-api-gateway.sh

# Speaker Service (Node.js/NestJS)
./scripts/docker/build-push-speaker-service.sh

# Draft Service (Python/FastAPI)
./scripts/docker/build-push-draft-service.sh

# RAG Service (Python/FastAPI + LangChain)
./scripts/docker/build-push-rag-service.sh

# Evaluation Service (Python/FastAPI)
./scripts/docker/build-push-evaluation-service.sh
```

### Verify Images in Registry

```bash
# List all images in the registry
az acr repository list --name acrdgbackendv01 --output table

# Check specific image tags
az acr repository show-tags --name acrdgbackendv01 --repository api-gateway --output table
az acr repository show-tags --name acrdgbackendv01 --repository speaker-service --output table
az acr repository show-tags --name acrdgbackendv01 --repository draft-service --output table
az acr repository show-tags --name acrdgbackendv01 --repository rag-service --output table
az acr repository show-tags --name acrdgbackendv01 --repository evaluation-service --output table
```

## Step 2: Deploy Services to Azure

### Option A: Deploy All Services

```bash
# Using the deployment script
python scripts/deploy-azure.py
```

### Option B: Deploy Individual Services

```bash
# Set variables
RESOURCE_GROUP="draftgenie-rg"
CONTAINER_ENV="dg-backend-env"
ACR_NAME="acrdgbackendv01"
ACR_SERVER="${ACR_NAME}.azurecr.io"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Deploy API Gateway
az containerapp create \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_SERVER/api-gateway:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    NODE_ENV=production \
    PORT=3000

# Deploy Speaker Service
az containerapp create \
  --name speaker-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_SERVER/speaker-service:latest \
  --target-port 3001 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    NODE_ENV=production \
    PORT=3001

# Deploy Draft Service
az containerapp create \
  --name draft-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_SERVER/draft-service:latest \
  --target-port 3002 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3002

# Deploy RAG Service
az containerapp create \
  --name rag-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_SERVER/rag-service:latest \
  --target-port 3003 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3003

# Deploy Evaluation Service
az containerapp create \
  --name eval-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_SERVER/evaluation-service:latest \
  --target-port 3004 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3004
```

## Step 3: Test Deployed Services

### Automated Testing

```bash
# Run the comprehensive test script
./scripts/azure/test-deployed-services.sh
```

### Manual Testing

#### Check Service Status

```bash
# List all container apps
az containerapp list --resource-group draftgenie-rg --output table

# Check specific service status
az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.runningStatus"

# Get service URL
az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.configuration.ingress.fqdn" --output tsv
```

#### Test Health Endpoints

```bash
# Get API Gateway URL
API_GATEWAY_URL=$(az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.configuration.ingress.fqdn" --output tsv)

# Test API Gateway health
curl https://$API_GATEWAY_URL/health

# Test all services health (via API Gateway)
curl https://$API_GATEWAY_URL/health/services
```

#### View Logs

```bash
# View logs for a specific service
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 50

# Stream logs in real-time
az containerapp logs tail --name api-gateway --resource-group draftgenie-rg --follow
```

#### Check Replicas

```bash
# List replicas for a service
az containerapp replica list --name api-gateway --resource-group draftgenie-rg --output table
```

## Step 4: Troubleshooting

### Service Not Starting

```bash
# Check container app events
az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.latestRevisionName"

# Get revision details
az containerapp revision show --name <revision-name> --app api-gateway --resource-group draftgenie-rg
```

### Image Pull Errors

```bash
# Verify ACR credentials
az acr credential show --name acrdgbackendv01

# Test ACR login
az acr login --name acrdgbackendv01

# Check if image exists
az acr repository show --name acrdgbackendv01 --image api-gateway:latest
```

### Health Check Failures

```bash
# Check logs for errors
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 100

# Check environment variables
az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.template.containers[0].env"
```

## Step 5: Update Services

### Update Service Image

```bash
# Build and push new image
./scripts/docker/build-push-api-gateway.sh

# Update container app
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest
```

### Update Environment Variables

```bash
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --set-env-vars "NEW_VAR=value"
```

## Quick Reference

### Service Ports
- API Gateway: 3000 (external)
- Speaker Service: 3001 (internal)
- Draft Service: 3002 (internal)
- RAG Service: 3003 (internal)
- Evaluation Service: 3004 (internal)

### Health Endpoints
All services expose `/health` endpoint for health checks.

### Resource Group
`draftgenie-rg` (South India)

### Container Apps Environment
`dg-backend-env`

### Container Registry
`acrdgbackendv01.azurecr.io`

