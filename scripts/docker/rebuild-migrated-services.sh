#!/bin/bash

# Rebuild and push draft-service and rag-service after MongoDB to PostgreSQL migration
# This script builds Docker images for AMD64 architecture and pushes to Azure Container Registry

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ACR_NAME="acrdgbackendv01.azurecr.io"
PLATFORM="linux/amd64"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Rebuilding Migrated Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if logged into ACR
echo -e "${YELLOW}Checking Azure Container Registry login...${NC}"
if ! docker images ${ACR_NAME}/test:latest &> /dev/null; then
    echo -e "${YELLOW}Please login to ACR first:${NC}"
    echo "az acr login --name acrdgbackendv01"
    exit 1
fi

# Function to build and push a service
build_and_push() {
    local service_name=$1
    local service_path=$2
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Building ${service_name}${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check if Dockerfile exists
    if [ ! -f "${service_path}/Dockerfile" ]; then
        echo -e "${RED}Error: Dockerfile not found at ${service_path}/Dockerfile${NC}"
        return 1
    fi
    
    # Build the image
    echo -e "${YELLOW}Building Docker image for ${service_name}...${NC}"
    docker build \
        --platform ${PLATFORM} \
        -t ${ACR_NAME}/${service_name}:latest \
        -t ${ACR_NAME}/${service_name}:postgres-migration \
        ${service_path}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully built ${service_name}${NC}"
    else
        echo -e "${RED}✗ Failed to build ${service_name}${NC}"
        return 1
    fi
    
    # Push the image
    echo -e "${YELLOW}Pushing ${service_name} to ACR...${NC}"
    docker push ${ACR_NAME}/${service_name}:latest
    docker push ${ACR_NAME}/${service_name}:postgres-migration
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully pushed ${service_name}${NC}"
    else
        echo -e "${RED}✗ Failed to push ${service_name}${NC}"
        return 1
    fi
}

# Build and push draft-service
build_and_push "draft-service" "services/draft-service"

# Build and push rag-service
build_and_push "rag-service" "services/rag-service"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All services built and pushed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update container apps with new images"
echo "2. Verify DATABASE_URL environment variable is set"
echo "3. Run database migrations"
echo "4. Test the services"
echo ""
echo -e "${YELLOW}To update container apps:${NC}"
echo "az containerapp update --name draft-service --resource-group rg-dg-backend-v01 --image ${ACR_NAME}/draft-service:latest"
echo "az containerapp update --name rag-service --resource-group rg-dg-backend-v01 --image ${ACR_NAME}/rag-service:latest"
echo ""

