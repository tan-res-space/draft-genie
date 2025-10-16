#!/bin/bash

# Deploy only the evaluation service
# Run this after the evaluation service Docker image build completes

set -e

echo ""
echo "========================================"
echo "Deploying Evaluation Service to Azure"
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

# Check if image exists
echo "ℹ Checking if evaluation-service image exists..."
if az acr repository show --name $REGISTRY_NAME --image evaluation-service:latest &>/dev/null; then
  echo "✓ Image found: ${REGISTRY_SERVER}/evaluation-service:latest"
else
  echo "❌ Error: evaluation-service:latest image not found in registry"
  echo "Please run: ./scripts/docker/build-push-evaluation-service.sh"
  exit 1
fi

# Deploy Evaluation Service
echo ""
echo "========================================"
echo "Deploying Evaluation Service"
echo "========================================"
az containerapp create \
  --name evaluation-service \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image ${REGISTRY_SERVER}/evaluation-service:latest \
  --registry-server $REGISTRY_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8004 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 2.0 \
  --memory 4.0Gi \
  --env-vars \
    "PORT=8004" \
    "DATABASE_URL=${DATABASE_URL}" \
    "REDIS_URL=${REDIS_URL}" \
    "GEMINI_API_KEY=secretref:gemini-api-key" \
  --secrets \
    "gemini-api-key=${GEMINI_API_KEY}" \
  --query properties.configuration.ingress.fqdn \
  --output tsv

echo "✓ Evaluation Service deployed"

echo ""
echo "========================================"
echo "Deployment Complete"
echo "========================================"
echo ""

az containerapp show \
  --name evaluation-service \
  --resource-group $RESOURCE_GROUP \
  --query "{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}" \
  --output table

echo ""
echo "✓ Evaluation Service is now deployed!"
echo ""
echo "Run './scripts/azure/test-deployed-services.sh' to test all services."

