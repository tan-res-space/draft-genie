#!/bin/bash

# Test Deployed Services in Azure
# This script tests all deployed services in Azure Container Apps

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="draftgenie-rg"
CONTAINER_ENV="dg-backend-env"

# Service names
SERVICES=(
    "api-gateway"
    "speaker-service"
    "draft-service"
    "rag-service"
    "eval-service"
)

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
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "Azure CLI is installed"
}

# Check if logged in to Azure
check_azure_login() {
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    print_success "Logged in to Azure"
}

# Get container app URL
get_app_url() {
    local app_name=$1
    local url=$(az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null)
    
    if [ -z "$url" ]; then
        echo ""
    else
        echo "https://$url"
    fi
}

# Check if container app exists
check_app_exists() {
    local app_name=$1
    
    if az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --output none 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Get container app status
get_app_status() {
    local app_name=$1
    
    local status=$(az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.runningStatus" \
        --output tsv 2>/dev/null)
    
    echo "$status"
}

# Get container app replica count
get_replica_count() {
    local app_name=$1
    
    local replicas=$(az containerapp replica list \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query "length(@)" \
        --output tsv 2>/dev/null)
    
    echo "$replicas"
}

# Test health endpoint
test_health_endpoint() {
    local app_name=$1
    local url=$2
    
    if [ -z "$url" ]; then
        print_warning "$app_name: No URL available (internal service)"
        return 1
    fi
    
    local health_url="${url}/health"
    
    print_info "Testing health endpoint: $health_url"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$health_url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        print_success "$app_name: Health check passed (HTTP $response)"
        return 0
    else
        print_error "$app_name: Health check failed (HTTP $response)"
        return 1
    fi
}

# Get container app logs
get_app_logs() {
    local app_name=$1
    local lines=${2:-20}
    
    print_info "Fetching last $lines log lines for $app_name..."
    
    az containerapp logs show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --tail "$lines" \
        --follow false 2>/dev/null || print_warning "Could not fetch logs for $app_name"
}

# Test API Gateway services endpoint
test_api_gateway_services() {
    local url=$1
    
    if [ -z "$url" ]; then
        print_warning "API Gateway: No URL available"
        return 1
    fi
    
    local services_url="${url}/health/services"
    
    print_info "Testing API Gateway services health: $services_url"
    
    local response=$(curl -s --max-time 10 "$services_url" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        print_success "API Gateway: Services health check completed"
        return 0
    else
        print_error "API Gateway: Services health check failed"
        return 1
    fi
}

# Main test function
test_service() {
    local app_name=$1
    
    print_header "Testing: $app_name"
    
    # Check if app exists
    if ! check_app_exists "$app_name"; then
        print_error "$app_name: Container app not found"
        return 1
    fi
    print_success "$app_name: Container app exists"
    
    # Get status
    local status=$(get_app_status "$app_name")
    if [ "$status" = "Running" ]; then
        print_success "$app_name: Status is Running"
    else
        print_error "$app_name: Status is $status"
    fi
    
    # Get replica count
    local replicas=$(get_replica_count "$app_name")
    print_info "$app_name: Running replicas: $replicas"
    
    # Get URL
    local url=$(get_app_url "$app_name")
    if [ -n "$url" ]; then
        print_info "$app_name: URL: $url"
        
        # Test health endpoint
        test_health_endpoint "$app_name" "$url"
        
        # Special test for API Gateway
        if [ "$app_name" = "api-gateway" ]; then
            test_api_gateway_services "$url"
        fi
    else
        print_info "$app_name: Internal service (no external URL)"
    fi
    
    echo ""
}

# Main execution
main() {
    print_header "Azure Container Apps - Service Testing"
    
    # Pre-flight checks
    check_azure_cli
    check_azure_login
    
    print_info "Resource Group: $RESOURCE_GROUP"
    print_info "Container Environment: $CONTAINER_ENV"
    
    # Test each service
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        if ! test_service "$service"; then
            failed_services+=("$service")
        fi
    done
    
    # Summary
    print_header "Test Summary"
    
    local total=${#SERVICES[@]}
    local failed=${#failed_services[@]}
    local passed=$((total - failed))
    
    print_info "Total services: $total"
    print_success "Passed: $passed"
    
    if [ $failed -gt 0 ]; then
        print_error "Failed: $failed"
        echo ""
        print_error "Failed services:"
        for service in "${failed_services[@]}"; do
            echo "  - $service"
        done
        echo ""
        
        # Offer to show logs
        read -p "Do you want to see logs for failed services? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for service in "${failed_services[@]}"; do
                print_header "Logs for $service"
                get_app_logs "$service" 50
            done
        fi
        
        exit 1
    else
        print_success "All services are healthy! 🚀"
        exit 0
    fi
}

# Run main function
main

