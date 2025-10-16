#!/bin/bash

# Deploy only the 4 completed services (excluding evaluation-service)
# This script deploys: api-gateway, speaker-service, draft-service, rag-service

set -e

echo ""
echo "========================================"
echo "Deploying 4 DraftGenie Services to Azure"
echo "========================================"
echo ""

# Configuration
RESOURCE_GROUP="draftgenie-rg"
LOCATION="eastus"
ENVIRONMENT="dg-backend-env"
REGISTRY_NAME="acrdgbackendv01"
REGISTRY_SERVER="${REGISTRY_NAME}.azurecr.io"

echo "ℹ Resource Group: $RESOURCE_GROUP"
echo "ℹ Container Environment: $ENVIRONMENT"
echo "ℹ Container Registry: $REGISTRY_SERVER"

# Get ACR credentials
echo "ℹ Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)
echo "✓ ACR credentials retrieved"

# Get database connection strings
echo "ℹ Getting database connection strings..."
DB_HOST=$(az postgres flexible-server show --resource-group $RESOURCE_GROUP --name dg-backend-postgres --query fullyQualifiedDomainName -o tsv)
DB_USER="dgadmin"
DB_PASSWORD="DraftGenie2024!"
DB_NAME="draftgenie"
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?sslmode=require"

REDIS_HOST=$(az redis show --resource-group $RESOURCE_GROUP --name dg-backend-redis --query hostName -o tsv)
REDIS_KEY=$(az redis list-keys --resource-group $RESOURCE_GROUP --name dg-backend-redis --query primaryKey -o tsv)
REDIS_URL="redis://:${REDIS_KEY}@${REDIS_HOST}:6380?ssl=true"
echo "✓ Database credentials retrieved"

# Deploy API Gateway
echo ""
echo "========================================"
echo "Deploying API Gateway"
echo "========================================"
az containerapp create \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image ${REGISTRY_SERVER}/api-gateway:latest \
  --registry-server $REGISTRY_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    "NODE_ENV=production" \
    "PORT=3000" \
    "SPEAKER_SERVICE_URL=http://speaker-service" \
    "DRAFT_SERVICE_URL=http://draft-service" \
    "RAG_SERVICE_URL=http://rag-service" \
    "EVALUATION_SERVICE_URL=http://evaluation-service" \
  --query properties.configuration.ingress.fqdn \
  --output tsv

echo "✓ API Gateway deployed"

# Deploy Speaker Service
echo ""
echo "========================================"
echo "Deploying Speaker Service"
echo "========================================"
az containerapp create \
  --name speaker-service \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image ${REGISTRY_SERVER}/speaker-service:latest \
  --registry-server $REGISTRY_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8001 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    "PORT=8001" \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "GEMINI_API_KEY=secretref:gemini-api-key" \
  --secrets \
    "gemini-api-key=${GEMINI_API_KEY}" \
  --query properties.configuration.ingress.fqdn \
  --output tsv

echo "✓ Speaker Service deployed"

# Deploy Draft Service
echo ""
echo "========================================"
echo "Deploying Draft Service"
echo "========================================"
az containerapp create \
  --name draft-service \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image ${REGISTRY_SERVER}/draft-service:latest \
  --registry-server $REGISTRY_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8002 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    "PORT=8002" \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "GEMINI_API_KEY=secretref:gemini-api-key" \
  --secrets \
    "gemini-api-key=${GEMINI_API_KEY}" \
  --query properties.configuration.ingress.fqdn \
  --output tsv

echo "✓ Draft Service deployed"

# Deploy RAG Service
echo ""
echo "========================================"
echo "Deploying RAG Service"
echo "========================================"
az containerapp create \
  --name rag-service \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image ${REGISTRY_SERVER}/rag-service:latest \
  --registry-server $REGISTRY_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8003 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    "PORT=8003" \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "GEMINI_API_KEY=secretref:gemini-api-key" \
  --secrets \
    "gemini-api-key=${GEMINI_API_KEY}" \
  --query properties.configuration.ingress.fqdn \
  --output tsv

echo "✓ RAG Service deployed"

echo ""
echo "========================================"
echo "Deployment Summary"
echo "========================================"
echo "✓ API Gateway deployed"
echo "✓ Speaker Service deployed"
echo "✓ Draft Service deployed"
echo "✓ RAG Service deployed"
echo "⏳ Evaluation Service - will be deployed after build completes"
echo ""
echo "Getting service URLs..."
echo ""

az containerapp list \
  --resource-group $RESOURCE_GROUP \
  --query "[].{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}" \
  --output table

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Note: Evaluation Service will be deployed separately once its build completes."
echo "Run './scripts/azure/deploy-evaluation-service.sh' when ready."

