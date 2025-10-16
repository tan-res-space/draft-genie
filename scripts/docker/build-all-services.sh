#!/usr/bin/env bash

#
# Build and Push All Services
#
# This script builds and pushes Docker images for all services in the Draft Genie project.
# It can run builds sequentially or in parallel.
#
# Usage:
#   ./build-all-services.sh
#
# Environment Variables:
#   TAG         - Image tag for all services (default: latest)
#   REGISTRY    - Container registry URL (default: from config.yaml)
#   DRY_RUN     - Dry run mode, don't execute commands (default: false)
#   SKIP_LOGIN  - Skip registry login (default: false)
#   PARALLEL    - Build services in parallel (default: false)
#   CONTINUE_ON_ERROR - Continue building other services if one fails (default: false)
#
# Examples:
#   TAG=v1.0.0 ./build-all-services.sh
#   PARALLEL=true ./build-all-services.sh
#   CONTINUE_ON_ERROR=true ./build-all-services.sh
#

# Disable pipefail temporarily for compatibility
set -eu

# Add Docker Desktop bin to PATH if it exists and not already in PATH
if [ -d "/Applications/Docker.app/Contents/Resources/bin" ] && [[ ":$PATH:" != *":/Applications/Docker.app/Contents/Resources/bin:"* ]]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

print_header "Building and Pushing All Services"

# Configuration
TAG="${TAG:-latest}"
SKIP_LOGIN="${SKIP_LOGIN:-false}"
DRY_RUN="${DRY_RUN:-false}"
PARALLEL="${PARALLEL:-false}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-false}"

print_info "Tag: $TAG"
print_info "Parallel: $PARALLEL"
print_info "Continue on error: $CONTINUE_ON_ERROR"
print_info "Dry run: $DRY_RUN"

# List of services to build
SERVICES=(
    "api-gateway"
    "speaker-service"
    "draft-service"
    "rag-service"
    "evaluation-service"
)

# Track build results (using simple arrays for compatibility)
BUILD_RESULTS_SERVICES=()
BUILD_RESULTS_STATUS=()
SUCCESSFUL_BUILDS=0
FAILED_BUILDS=0

# Helper function to record build result
record_result() {
    local service=$1
    local status=$2
    BUILD_RESULTS_SERVICES+=("$service")
    BUILD_RESULTS_STATUS+=("$status")
}

# Function to build a single service
build_service() {
    local service=$1
    local script="$SCRIPT_DIR/build-push-${service}.sh"

    if [[ ! -f "$script" ]]; then
        print_error "Build script not found: $script"
        record_result "$service" "FAILED"
        return 1
    fi

    print_info "Building $service..."

    # Export environment variables for the child script
    export TAG
    export REGISTRY
    export DRY_RUN
    export SKIP_LOGIN

    if bash "$script"; then
        record_result "$service" "SUCCESS"
        return 0
    else
        record_result "$service" "FAILED"
        return 1
    fi
}

# Login to registry once (if not skipped)
if [[ "$SKIP_LOGIN" != "true" ]]; then
    print_header "Logging in to Container Registry"
    
    # Get registry from config.yaml or environment variable
    if [[ -z "${REGISTRY:-}" ]]; then
        CONFIG_FILE="$PROJECT_ROOT/scripts/azure/config.yaml"
        
        if [[ -f "$CONFIG_FILE" ]]; then
            REGISTRY_NAME=$(grep -A 2 "^container_registry:" "$CONFIG_FILE" | grep "name:" | awk '{print $2}' | tr -d '"' | tr -d "'")
            
            if [[ -n "$REGISTRY_NAME" ]]; then
                REGISTRY="${REGISTRY_NAME}.azurecr.io"
                print_info "Registry from config: $REGISTRY"
            else
                print_error "Could not extract registry name from $CONFIG_FILE"
                exit 1
            fi
        else
            print_error "Config file not found: $CONFIG_FILE"
            exit 1
        fi
    fi
    
    # Login once
    REGISTRY_NAME="${REGISTRY%.azurecr.io}"
    
    if [[ "${DRY_RUN}" != "true" ]]; then
        if az acr login --name "$REGISTRY_NAME"; then
            print_success "Successfully logged in to $REGISTRY"
            # Skip login in individual scripts
            export SKIP_LOGIN=true
        else
            print_error "Failed to login to registry"
            exit 1
        fi
    else
        print_info "[DRY RUN] Would login to $REGISTRY"
        export SKIP_LOGIN=true
    fi
fi

# Build services
print_header "Building Services"

if [[ "$PARALLEL" == "true" ]]; then
    print_info "Building services in parallel..."
    
    # Array to store background process IDs
    declare -a PIDS
    
    # Start all builds in parallel
    for service in "${SERVICES[@]}"; do
        build_service "$service" &
        PIDS+=($!)
    done
    
    # Wait for all builds to complete
    for i in "${!PIDS[@]}"; do
        pid=${PIDS[$i]}
        service=${SERVICES[$i]}
        
        if wait "$pid"; then
            print_success "$service build completed"
            ((SUCCESSFUL_BUILDS++))
        else
            print_error "$service build failed"
            ((FAILED_BUILDS++))
            
            if [[ "$CONTINUE_ON_ERROR" != "true" ]]; then
                print_error "Stopping due to build failure"
                # Kill remaining processes
                for remaining_pid in "${PIDS[@]}"; do
                    kill "$remaining_pid" 2>/dev/null || true
                done
                exit 1
            fi
        fi
    done
else
    print_info "Building services sequentially..."
    
    # Build services one by one
    for service in "${SERVICES[@]}"; do
        echo ""
        print_header "Building: $service"
        
        if build_service "$service"; then
            print_success "$service build completed"
            ((SUCCESSFUL_BUILDS++))
        else
            print_error "$service build failed"
            ((FAILED_BUILDS++))
            
            if [[ "$CONTINUE_ON_ERROR" != "true" ]]; then
                print_error "Stopping due to build failure"
                exit 1
            fi
        fi
    done
fi

# Summary
print_header "Build Summary"

echo -e "${CYAN}Total Services:${NC} ${#SERVICES[@]}"
echo -e "${GREEN}Successful:${NC} $SUCCESSFUL_BUILDS"
echo -e "${RED}Failed:${NC} $FAILED_BUILDS"
echo ""

# Print detailed results
for i in "${!BUILD_RESULTS_SERVICES[@]}"; do
    service="${BUILD_RESULTS_SERVICES[$i]}"
    status="${BUILD_RESULTS_STATUS[$i]}"
    if [[ "$status" == "SUCCESS" ]]; then
        print_success "$service"
    else
        print_error "$service"
    fi
done

echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    print_warning "DRY RUN MODE - No actual changes were made"
fi

# Exit with appropriate code
if [[ $FAILED_BUILDS -gt 0 ]]; then
    print_error "Some builds failed!"
    exit 1
else
    print_success "All builds completed successfully!"
    exit 0
fi

