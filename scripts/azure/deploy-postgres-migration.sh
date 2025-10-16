#!/bin/bash

# Deploy draft-service and rag-service with PostgreSQL configuration
# This script updates the container apps with new images and PostgreSQL environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="rg-dg-backend-v01"
ACR_NAME="acrdgbackendv01.azurecr.io"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PostgreSQL Migration Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    exit 1
fi

# Check if logged in to Azure
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

echo -e "${GREEN}✓ Logged in to Azure${NC}"

# Get PostgreSQL connection details
echo ""
echo -e "${YELLOW}Fetching PostgreSQL connection details...${NC}"

PG_HOST=$(az postgres flexible-server show \
    --resource-group ${RESOURCE_GROUP} \
    --name dg-backend-postgres \
    --query "fullyQualifiedDomainName" \
    --output tsv)

if [ -z "$PG_HOST" ]; then
    echo -e "${RED}Error: Could not fetch PostgreSQL host${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PostgreSQL host: ${PG_HOST}${NC}"

# Get PostgreSQL credentials from Key Vault
echo -e "${YELLOW}Fetching PostgreSQL credentials from Key Vault...${NC}"

KEYVAULT_NAME=$(az keyvault list \
    --resource-group ${RESOURCE_GROUP} \
    --query "[0].name" \
    --output tsv)

if [ -z "$KEYVAULT_NAME" ]; then
    echo -e "${RED}Error: Could not find Key Vault${NC}"
    exit 1
fi

PG_USER=$(az keyvault secret show \
    --vault-name ${KEYVAULT_NAME} \
    --name POSTGRES-USER \
    --query "value" \
    --output tsv 2>/dev/null || echo "dgadmin")

PG_PASSWORD=$(az keyvault secret show \
    --vault-name ${KEYVAULT_NAME} \
    --name POSTGRES-PASSWORD \
    --query "value" \
    --output tsv)

if [ -z "$PG_PASSWORD" ]; then
    echo -e "${RED}Error: Could not fetch PostgreSQL password from Key Vault${NC}"
    exit 1
fi

PG_DB="draftgenie"

# Construct DATABASE_URL
DATABASE_URL="postgresql+asyncpg://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:5432/${PG_DB}?sslmode=require"

echo -e "${GREEN}✓ Database URL constructed${NC}"

# Function to update a container app
update_container_app() {
    local service_name=$1
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Updating ${service_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check if container app exists
    if ! az containerapp show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        &> /dev/null; then
        echo -e "${RED}Error: Container app ${service_name} not found${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Updating ${service_name} with new image and environment variables...${NC}"
    
    az containerapp update \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --image ${ACR_NAME}/${service_name}:latest \
        --set-env-vars \
            "DATABASE_URL=${DATABASE_URL}" \
            "POSTGRES_POOL_SIZE=10" \
            "POSTGRES_MAX_OVERFLOW=20" \
        --replace-env-vars \
            "DATABASE_URL=${DATABASE_URL}" \
            "POSTGRES_POOL_SIZE=10" \
            "POSTGRES_MAX_OVERFLOW=20"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully updated ${service_name}${NC}"
    else
        echo -e "${RED}✗ Failed to update ${service_name}${NC}"
        return 1
    fi
    
    # Wait for the service to be ready
    echo -e "${YELLOW}Waiting for ${service_name} to be ready...${NC}"
    sleep 10
    
    # Check service status
    STATUS=$(az containerapp show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --query "properties.runningStatus" \
        --output tsv)
    
    echo -e "${BLUE}Service status: ${STATUS}${NC}"
    
    # Get service URL
    URL=$(az containerapp show \
        --name ${service_name} \
        --resource-group ${RESOURCE_GROUP} \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv)
    
    if [ ! -z "$URL" ]; then
        echo -e "${GREEN}Service URL: https://${URL}${NC}"
        
        # Test health endpoint
        echo -e "${YELLOW}Testing health endpoint...${NC}"
        if curl -s -f "https://${URL}/health" > /dev/null; then
            echo -e "${GREEN}✓ Health check passed${NC}"
        else
            echo -e "${YELLOW}⚠ Health check failed (service may still be starting)${NC}"
        fi
    fi
}

# Update draft-service
update_container_app "draft-service"

# Update rag-service
update_container_app "rag-service"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Monitor service logs:"
echo "   az containerapp logs show --name draft-service --resource-group ${RESOURCE_GROUP} --follow"
echo "   az containerapp logs show --name rag-service --resource-group ${RESOURCE_GROUP} --follow"
echo ""
echo "2. Test the services:"
echo "   curl https://\$(az containerapp show --name draft-service --resource-group ${RESOURCE_GROUP} --query 'properties.configuration.ingress.fqdn' -o tsv)/health/ready"
echo "   curl https://\$(az containerapp show --name rag-service --resource-group ${RESOURCE_GROUP} --query 'properties.configuration.ingress.fqdn' -o tsv)/health/ready"
echo ""
echo "3. If services fail to start, check logs for errors"
echo ""

