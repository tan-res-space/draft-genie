#!/usr/bin/env bash

#
# Build and Push Script for Draft Service
#
# This script builds the Docker image for the Draft Service (Python/FastAPI) and
# pushes it to the configured container registry.
#
# Usage:
#   ./build-push-draft-service.sh
#
# Environment Variables:
#   TAG         - Image tag (default: latest)
#   REGISTRY    - Container registry URL (default: from config.yaml)
#   DRY_RUN     - Dry run mode, don't execute commands (default: false)
#   SKIP_LOGIN  - Skip registry login (default: false)
#   SKIP_BUILD  - Skip build, only push (default: false)
#   SKIP_PUSH   - Build only, skip push (default: false)
#
# Examples:
#   TAG=v1.0.0 ./build-push-draft-service.sh
#   SKIP_PUSH=true ./build-push-draft-service.sh
#   DRY_RUN=true ./build-push-draft-service.sh
#

set -euo pipefail

# Add Docker Desktop bin to PATH if it exists and not already in PATH
if [ -d "/Applications/Docker.app/Contents/Resources/bin" ] && [[ ":$PATH:" != *":/Applications/Docker.app/Contents/Resources/bin:"* ]]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
fi

# Service configuration
SERVICE_NAME="draft-service"
DOCKERFILE="docker/Dockerfile.draft-service"
BUILD_CONTEXT="."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
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

run_command() {
    local cmd="$1"
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        print_info "[DRY RUN] Would execute: $cmd"
        return 0
    else
        print_info "Executing: $cmd"
        eval "$cmd"
    fi
}

# Get project root (two levels up from scripts/docker/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

print_header "Building and Pushing: $SERVICE_NAME"

# Configuration
TAG="${TAG:-latest}"
SKIP_LOGIN="${SKIP_LOGIN:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_PUSH="${SKIP_PUSH:-false}"
DRY_RUN="${DRY_RUN:-false}"

print_info "Service: $SERVICE_NAME"
print_info "Tag: $TAG"
print_info "Dockerfile: $DOCKERFILE"
print_info "Build Context: $BUILD_CONTEXT"

# Get registry from config.yaml or environment variable
if [[ -z "${REGISTRY:-}" ]]; then
    CONFIG_FILE="$PROJECT_ROOT/scripts/azure/config.yaml"
    
    if [[ -f "$CONFIG_FILE" ]]; then
        # Extract registry name from config.yaml
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
        print_error "Please set REGISTRY environment variable or create config.yaml"
        exit 1
    fi
else
    print_info "Registry from environment: $REGISTRY"
fi

# Construct full image name
IMAGE_NAME="${REGISTRY}/${SERVICE_NAME}:${TAG}"
print_info "Full image name: $IMAGE_NAME"

# Verify Dockerfile exists
if [[ ! -f "$DOCKERFILE" ]]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi
print_success "Dockerfile found: $DOCKERFILE"

# Login to registry
if [[ "$SKIP_LOGIN" != "true" ]]; then
    print_header "Logging in to Container Registry"
    
    # Extract registry name (remove .azurecr.io suffix)
    REGISTRY_NAME="${REGISTRY%.azurecr.io}"
    
    if run_command "az acr login --name $REGISTRY_NAME"; then
        print_success "Successfully logged in to $REGISTRY"
    else
        print_error "Failed to login to registry"
        exit 1
    fi
else
    print_warning "Skipping registry login (SKIP_LOGIN=true)"
fi

# Build Docker image
if [[ "$SKIP_BUILD" != "true" ]]; then
    print_header "Building Docker Image"
    
    BUILD_CMD="docker build --platform linux/amd64 -f $DOCKERFILE -t $IMAGE_NAME $BUILD_CONTEXT"
    
    if run_command "$BUILD_CMD"; then
        print_success "Successfully built image: $IMAGE_NAME"
    else
        print_error "Failed to build image"
        exit 1
    fi
else
    print_warning "Skipping build (SKIP_BUILD=true)"
fi

# Push Docker image
if [[ "$SKIP_PUSH" != "true" ]]; then
    print_header "Pushing Docker Image"
    
    PUSH_CMD="docker push $IMAGE_NAME"
    
    if run_command "$PUSH_CMD"; then
        print_success "Successfully pushed image: $IMAGE_NAME"
    else
        print_error "Failed to push image"
        exit 1
    fi
else
    print_warning "Skipping push (SKIP_PUSH=true)"
fi

# Summary
print_header "Summary"
print_success "Service: $SERVICE_NAME"
print_success "Image: $IMAGE_NAME"
print_success "Registry: $REGISTRY"

if [[ "$DRY_RUN" == "true" ]]; then
    print_warning "DRY RUN MODE - No actual changes were made"
fi

print_success "Done!"

