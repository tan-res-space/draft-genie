#!/bin/bash

# Deploy Services to Azure Container Apps
# This script deploys only the application services (not infrastructure)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration from config.yaml
RESOURCE_GROUP="draftgenie-rg"
CONTAINER_ENV="dg-backend-env"
ACR_NAME="acrdgbackendv01"
ACR_SERVER="${ACR_NAME}.azurecr.io"
LOCATION="southindia"

# Print functions
print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

print_header "Deploying DraftGenie Services to Azure"

print_info "Resource Group: $RESOURCE_GROUP"
print_info "Container Environment: $CONTAINER_ENV"
print_info "Container Registry: $ACR_SERVER"

# Get ACR credentials
print_info "Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
print_success "ACR credentials retrieved"

# Get database connection strings
print_info "Getting database connection strings..."
POSTGRES_SERVER="dg-backend-postgres"
POSTGRES_DB="dg-backend"
POSTGRES_USER="dg-backend"

# Get PostgreSQL password from Key Vault
POSTGRES_PASSWORD=$(az keyvault secret show --vault-name dg-backend-kv-v01 --name postgres-password --query value --output tsv 2>/dev/null || echo "")
if [ -z "$POSTGRES_PASSWORD" ]; then
    print_warning "PostgreSQL password not found in Key Vault, using default"
    POSTGRES_PASSWORD="AdminPass"
fi

# Get Redis connection string
REDIS_HOST=$(az redis show --name dg-backend-redis --resource-group $RESOURCE_GROUP --query hostName --output tsv)
REDIS_KEY=$(az redis list-keys --name dg-backend-redis --resource-group $RESOURCE_GROUP --query primaryKey --output tsv)

# Get Gemini API key
GEMINI_API_KEY=$(az keyvault secret show --vault-name dg-backend-kv-v01 --name gemini-api-key --query value --output tsv 2>/dev/null || echo "AIzaSyCv5ZMukJVMthBTnJXDPegAeCWulYd0cL0")

# Get JWT secret
JWT_SECRET=$(az keyvault secret show --vault-name dg-backend-kv-v01 --name jwt-secret --query value --output tsv 2>/dev/null || echo "your-super-secret-jwt-key-change-this-in-production")

print_success "Database credentials retrieved"

# Deploy Speaker Service
print_header "Deploying Speaker Service"

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
    PORT=3001 \
    DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}.postgres.database.azure.com:5432/${POSTGRES_DB}?sslmode=require" \
    REDIS_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380" \
    LOG_LEVEL=info

print_success "Speaker Service deployed"

# Deploy Draft Service
print_header "Deploying Draft Service"

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
    PORT=3002 \
    GEMINI_API_KEY=$GEMINI_API_KEY \
    LOG_LEVEL=info

print_success "Draft Service deployed"

# Deploy RAG Service
print_header "Deploying RAG Service"

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
    PORT=3003 \
    GEMINI_API_KEY=$GEMINI_API_KEY \
    LOG_LEVEL=info

print_success "RAG Service deployed"

# Deploy Evaluation Service
print_header "Deploying Evaluation Service"

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
    PORT=3004 \
    LOG_LEVEL=info

print_success "Evaluation Service deployed"

# Deploy API Gateway (with external ingress)
print_header "Deploying API Gateway"

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
    PORT=3000 \
    SPEAKER_SERVICE_URL=http://speaker-service:3001 \
    DRAFT_SERVICE_URL=http://draft-service:3002 \
    RAG_SERVICE_URL=http://rag-service:3003 \
    EVALUATION_SERVICE_URL=http://eval-service:3004 \
    JWT_SECRET=$JWT_SECRET \
    CORS_ORIGIN=* \
    SWAGGER_ENABLED=true \
    LOG_LEVEL=info

print_success "API Gateway deployed"

# Get API Gateway URL
print_header "Deployment Summary"

API_GATEWAY_URL=$(az containerapp show --name api-gateway --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" --output tsv)

if [ -n "$API_GATEWAY_URL" ]; then
    print_success "API Gateway URL: https://$API_GATEWAY_URL"
    print_info "Health Check: https://$API_GATEWAY_URL/health"
    print_info "Services Health: https://$API_GATEWAY_URL/health/services"
    print_info "API Docs: https://$API_GATEWAY_URL/api/docs"
else
    print_warning "Could not retrieve API Gateway URL"
fi

print_success "All services deployed successfully! 🚀"

echo ""
print_info "Next steps:"
echo "  1. Test services: ./scripts/azure/test-deployed-services.sh"
echo "  2. View logs: az containerapp logs show --name api-gateway --resource-group $RESOURCE_GROUP --tail 50"
echo "  3. Monitor: az containerapp list --resource-group $RESOURCE_GROUP --output table"
echo ""

