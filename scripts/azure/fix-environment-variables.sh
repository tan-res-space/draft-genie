#!/bin/bash

# Fix Environment Variables for Azure Container Apps
# This script updates all container apps with the correct environment variables

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="draftgenie-rg"
KEY_VAULT_NAME="dg-backend-kv-v01"
POSTGRES_SERVER="dg-backend-postgres"
REDIS_NAME="dg-backend-redis"

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

# Get secrets from Key Vault
get_secret() {
    local secret_name=$1
    az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "$secret_name" --query "value" -o tsv 2>/dev/null || echo ""
}

# Get PostgreSQL connection string
get_postgres_connection_string() {
    local db_name=${1:-"draftgenie"}
    local admin_user=$(az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$POSTGRES_SERVER" --query "administratorLogin" -o tsv)
    local admin_password=$(get_secret "postgres-admin-password")
    
    if [ -z "$admin_password" ]; then
        print_error "PostgreSQL admin password not found in Key Vault"
        return 1
    fi
    
    echo "postgresql://${admin_user}:${admin_password}@${POSTGRES_SERVER}.postgres.database.azure.com:5432/${db_name}?sslmode=require"
}

# Get Redis connection string
get_redis_connection_string() {
    local redis_key=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query "primaryKey" -o tsv)
    echo "rediss://:${redis_key}@${REDIS_NAME}.redis.cache.windows.net:6380"
}

# Get RabbitMQ connection string
get_rabbitmq_connection_string() {
    local rabbitmq_password=$(get_secret "rabbitmq-password")
    if [ -z "$rabbitmq_password" ]; then
        rabbitmq_password="guest"
        print_warning "Using default RabbitMQ password"
    fi
    echo "amqp://guest:${rabbitmq_password}@rabbitmq:5672/"
}

# Get Gemini API key
get_gemini_api_key() {
    local api_key=$(get_secret "gemini-api-key")
    if [ -z "$api_key" ]; then
        print_error "Gemini API key not found in Key Vault"
        return 1
    fi
    echo "$api_key"
}

# Update API Gateway
update_api_gateway() {
    print_header "Updating API Gateway Environment Variables"
    
    local jwt_secret=$(get_secret "jwt-secret")
    
    az containerapp update \
        --name api-gateway \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "NODE_ENV=production" \
            "PORT=3000" \
            "SPEAKER_SERVICE_URL=http://speaker-service:3001" \
            "DRAFT_SERVICE_URL=http://draft-service:3002" \
            "RAG_SERVICE_URL=http://rag-service:3003" \
            "EVALUATION_SERVICE_URL=http://eval-service:3004" \
            "JWT_SECRET=${jwt_secret}" \
            "CORS_ORIGIN=*" \
            "SWAGGER_ENABLED=true" \
            "LOG_LEVEL=info" \
        --output none
    
    print_success "API Gateway environment variables updated"
}

# Update Speaker Service
update_speaker_service() {
    print_header "Updating Speaker Service Environment Variables"
    
    local database_url=$(get_postgres_connection_string "draftgenie")
    local redis_url=$(get_redis_connection_string)
    local rabbitmq_url=$(get_rabbitmq_connection_string)
    local jwt_secret=$(get_secret "jwt-secret")
    
    az containerapp update \
        --name speaker-service \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "NODE_ENV=production" \
            "PORT=3001" \
            "DATABASE_URL=${database_url}" \
            "REDIS_URL=${redis_url}" \
            "RABBITMQ_URL=${rabbitmq_url}" \
            "JWT_SECRET=${jwt_secret}" \
            "LOG_LEVEL=info" \
        --output none
    
    print_success "Speaker Service environment variables updated"
}

# Update Draft Service
update_draft_service() {
    print_header "Updating Draft Service Environment Variables"
    
    local database_url=$(get_postgres_connection_string "draftgenie")
    local rabbitmq_url=$(get_rabbitmq_connection_string)
    local gemini_api_key=$(get_gemini_api_key)
    
    az containerapp update \
        --name draft-service \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "ENVIRONMENT=production" \
            "PORT=3002" \
            "DATABASE_URL=${database_url}" \
            "QDRANT_URL=http://qdrant:6333" \
            "GEMINI_API_KEY=${gemini_api_key}" \
            "RABBITMQ_URL=${rabbitmq_url}" \
            "LOG_LEVEL=info" \
        --output none
    
    print_success "Draft Service environment variables updated"
}

# Update RAG Service
update_rag_service() {
    print_header "Updating RAG Service Environment Variables"
    
    local database_url=$(get_postgres_connection_string "draftgenie")
    local gemini_api_key=$(get_gemini_api_key)
    
    az containerapp update \
        --name rag-service \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "ENVIRONMENT=production" \
            "PORT=3003" \
            "DATABASE_URL=${database_url}" \
            "QDRANT_URL=http://qdrant:6333" \
            "GEMINI_API_KEY=${gemini_api_key}" \
            "SPEAKER_SERVICE_URL=http://speaker-service:3001" \
            "DRAFT_SERVICE_URL=http://draft-service:3002" \
            "LOG_LEVEL=info" \
        --output none
    
    print_success "RAG Service environment variables updated"
}

# Update Evaluation Service
update_evaluation_service() {
    print_header "Updating Evaluation Service Environment Variables"
    
    local database_url=$(get_postgres_connection_string "draftgenie")
    local gemini_api_key=$(get_gemini_api_key)
    
    az containerapp update \
        --name eval-service \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "ENVIRONMENT=production" \
            "PORT=3004" \
            "DATABASE_URL=${database_url}" \
            "GEMINI_API_KEY=${gemini_api_key}" \
            "DRAFT_SERVICE_URL=http://draft-service:3002" \
            "LOG_LEVEL=info" \
        --output none
    
    print_success "Evaluation Service environment variables updated"
}

# Verify updates
verify_updates() {
    print_header "Verifying Updates"
    
    local services=("api-gateway" "speaker-service" "draft-service" "rag-service" "eval-service")
    
    for service in "${services[@]}"; do
        print_info "Checking $service..."
        local env_count=$(az containerapp show --name "$service" --resource-group "$RESOURCE_GROUP" --query "properties.template.containers[0].env | length(@)" -o tsv)
        print_info "$service has $env_count environment variables"
    done
}

# Main execution
main() {
    print_header "Fixing Azure Container Apps Environment Variables"
    
    print_info "Resource Group: $RESOURCE_GROUP"
    print_info "Key Vault: $KEY_VAULT_NAME"
    print_info "PostgreSQL Server: $POSTGRES_SERVER"
    print_info "Redis Cache: $REDIS_NAME"
    
    # Confirm before proceeding
    echo ""
    read -p "Do you want to proceed with updating environment variables? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled"
        exit 0
    fi
    
    # Update each service
    update_api_gateway
    update_speaker_service
    update_draft_service
    update_rag_service
    update_evaluation_service
    
    # Verify updates
    verify_updates
    
    print_header "Environment Variables Update Complete"
    print_success "All services have been updated!"
    print_info ""
    print_info "Next steps:"
    print_info "1. Wait for services to restart (1-2 minutes)"
    print_info "2. Run: ./scripts/azure/test-deployed-services.sh"
    print_info "3. Check logs if any issues: az containerapp logs show --name <service-name> --resource-group $RESOURCE_GROUP"
}

# Run main function
main

