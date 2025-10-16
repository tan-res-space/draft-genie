# Docker Build Scripts Architecture

## Overview

This document describes the architecture and design of the individual Docker build scripts for the Draft Genie project.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Draft Genie Project                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    scripts/docker/                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         build-all-services.sh (Orchestrator)           │    │
│  │                                                         │    │
│  │  • Reads configuration                                 │    │
│  │  • Manages service list                                │    │
│  │  • Handles parallel/sequential execution               │    │
│  │  • Tracks build results                                │    │
│  │  • Generates summary report                            │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ build-push-  │ │ build-push-  │ │ build-push-  │  ...      │
│  │ api-gateway  │ │   speaker    │ │    draft     │           │
│  │     .sh      │ │  -service.sh │ │  -service.sh │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                  │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           Common Functionality (Each Script)            │   │
│  │                                                         │   │
│  │  1. Configuration Loading                              │   │
│  │     • Read TAG, REGISTRY, flags from env               │   │
│  │     • Parse config.yaml for registry                   │   │
│  │     • Validate Dockerfile exists                       │   │
│  │                                                         │   │
│  │  2. Registry Authentication                            │   │
│  │     • Extract registry name                            │   │
│  │     • Execute: az acr login                            │   │
│  │     • Handle authentication errors                     │   │
│  │                                                         │   │
│  │  3. Docker Build                                       │   │
│  │     • Construct build command                          │   │
│  │     • Execute: docker build                            │   │
│  │     • Tag with full registry path                      │   │
│  │                                                         │   │
│  │  4. Docker Push                                        │   │
│  │     • Execute: docker push                             │   │
│  │     • Verify push success                              │   │
│  │                                                         │   │
│  │  5. Error Handling & Reporting                         │   │
│  │     • Colored output (✓ ✗ ⚠ ℹ)                        │   │
│  │     • Exit codes                                       │   │
│  │     • Summary report                                   │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  External Dependencies                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Docker    │  │  Azure CLI   │  │  config.yaml │         │
│  │    Engine    │  │     (az)     │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Build Images │  │ ACR Login    │  │ Registry URL │         │
│  │ Push Images  │  │ Get Creds    │  │ Service Info │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure Container Registry (ACR)                      │
│                                                                  │
│  acrdgbackendv01.azurecr.io/                                    │
│    ├── api-gateway:latest                                       │
│    ├── speaker-service:latest                                   │
│    ├── draft-service:latest                                     │
│    ├── rag-service:latest                                       │
│    └── evaluation-service:latest                                │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Individual Service Scripts

Each service has its own dedicated build script:

```bash
build-push-<service-name>.sh
```

**Responsibilities:**
- Load configuration from environment and config.yaml
- Validate prerequisites (Dockerfile exists)
- Authenticate with container registry
- Build Docker image
- Tag image with registry path
- Push image to registry
- Report success/failure

**Configuration:**
```bash
SERVICE_NAME="api-gateway"
DOCKERFILE="docker/Dockerfile.api-gateway"
BUILD_CONTEXT="."
```

### 2. Orchestration Script

The `build-all-services.sh` script coordinates building all services:

**Responsibilities:**
- Manage list of all services
- Authenticate once for all builds
- Execute builds (sequential or parallel)
- Track build results
- Generate summary report
- Handle errors gracefully

**Service List:**
```bash
SERVICES=(
    "api-gateway"
    "speaker-service"
    "draft-service"
    "rag-service"
    "evaluation-service"
)
```

### 3. Helper Functions

Each script includes common helper functions:

```bash
print_header()   # Print section headers
print_info()     # Print informational messages
print_success()  # Print success messages
print_warning()  # Print warnings
print_error()    # Print errors
run_command()    # Execute commands (with dry-run support)
```

## Data Flow

### Sequential Build Flow

```
User runs script
      │
      ▼
Load configuration
      │
      ▼
Validate prerequisites
      │
      ▼
Login to registry
      │
      ▼
Build Docker image
      │
      ▼
Push to registry
      │
      ▼
Display summary
```

### Parallel Build Flow (build-all-services.sh)

```
User runs script
      │
      ▼
Load configuration
      │
      ▼
Login to registry (once)
      │
      ▼
┌─────┴─────┬─────────┬─────────┬─────────┐
│           │         │         │         │
▼           ▼         ▼         ▼         ▼
Service 1   Service 2 Service 3 Service 4 Service 5
(build)     (build)   (build)   (build)   (build)
│           │         │         │         │
└─────┬─────┴─────────┴─────────┴─────────┘
      │
      ▼
Wait for all to complete
      │
      ▼
Collect results
      │
      ▼
Display summary
```

## Configuration Sources

### 1. Environment Variables

```bash
TAG=v1.2.3                          # Image tag
REGISTRY=myregistry.azurecr.io      # Registry URL
DRY_RUN=true                        # Dry run mode
SKIP_LOGIN=true                     # Skip registry login
SKIP_BUILD=true                     # Skip build step
SKIP_PUSH=true                      # Skip push step
PARALLEL=true                       # Parallel execution
CONTINUE_ON_ERROR=true              # Continue on failure
```

### 2. Configuration File

```yaml
# scripts/azure/config.yaml
container_registry:
  name: acrdgbackendv01
  sku: Basic
```

### 3. Script Defaults

```bash
TAG="${TAG:-latest}"
SKIP_LOGIN="${SKIP_LOGIN:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
SKIP_PUSH="${SKIP_PUSH:-false}"
DRY_RUN="${DRY_RUN:-false}"
```

## Error Handling

### Error Propagation

```
Error occurs
      │
      ▼
Print error message
      │
      ▼
Record failure
      │
      ▼
┌─────┴─────┐
│           │
▼           ▼
Exit        Continue
(default)   (CONTINUE_ON_ERROR=true)
```

### Exit Codes

- `0` - Success
- `1` - Failure (configuration, build, push, etc.)

## Execution Modes

### 1. Normal Mode
```bash
./scripts/docker/build-push-api-gateway.sh
```
Executes all steps: login, build, push

### 2. Dry Run Mode
```bash
DRY_RUN=true ./scripts/docker/build-push-api-gateway.sh
```
Prints commands without executing

### 3. Build Only
```bash
SKIP_PUSH=true ./scripts/docker/build-push-api-gateway.sh
```
Builds image but doesn't push

### 4. Push Only
```bash
SKIP_BUILD=true ./scripts/docker/build-push-api-gateway.sh
```
Pushes existing image

### 5. Parallel Build
```bash
PARALLEL=true ./scripts/docker/build-all-services.sh
```
Builds all services simultaneously

## Integration Points

### 1. CI/CD Pipelines

```yaml
# GitHub Actions
- name: Build Service
  run: ./scripts/docker/build-push-api-gateway.sh
  env:
    TAG: ${{ github.sha }}
```

### 2. Azure Deployment Script

```python
# scripts/azure/docker_builder.py
# Can coexist with shell scripts
```

### 3. Docker Compose

```yaml
# docker/docker-compose.yml
# Uses same Dockerfiles
```

## Design Principles

### 1. Self-Contained
Each script can run independently without dependencies on other scripts

### 2. Consistent Interface
All scripts use the same environment variables and command-line interface

### 3. Fail-Safe
Proper error handling, validation, and exit codes

### 4. Informative
Clear, colored output with status indicators

### 5. Flexible
Multiple execution modes (dry-run, skip steps, parallel)

### 6. Cloud-Agnostic
Easy to adapt for other container registries (Docker Hub, GCR, ECR)

## Performance Characteristics

### Sequential Build
- **Time**: ~5-10 minutes per service
- **Total**: ~25-50 minutes for all services
- **Resource**: Low CPU/memory usage

### Parallel Build
- **Time**: ~5-10 minutes total
- **Total**: ~5-10 minutes for all services
- **Resource**: High CPU/memory usage

## Security Considerations

### 1. Credentials
- Registry credentials obtained via Azure CLI
- No hardcoded credentials in scripts
- Credentials not logged or displayed

### 2. Image Tags
- Support for semantic versioning
- Default to `latest` for development
- Custom tags for production

### 3. Registry Access
- Requires Azure CLI authentication
- Uses Azure RBAC for access control

## Maintenance

### Adding New Services

1. Create new script from template
2. Update service configuration
3. Add to build-all-services.sh
4. Update documentation

### Modifying Build Process

1. Update individual script
2. Test with dry-run mode
3. Verify with real build
4. Update documentation

## Future Enhancements

### Potential Improvements

1. **Build Caching** - Implement Docker layer caching
2. **Notifications** - Send alerts on build failures
3. **Metrics** - Track build times and success rates
4. **Validation** - Pre-build dependency checks
5. **Cleanup** - Automatic cleanup of old images
6. **Multi-Registry** - Support for multiple registries
7. **Build Args** - Support for custom build arguments

---

**Last Updated**: 2025-10-15  
**Version**: 1.0.0  
**Status**: Production Ready

