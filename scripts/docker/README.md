# Docker Build and Push Scripts

This directory contains individual scripts for building and pushing Docker images for each service in the Draft Genie project.

## Overview

Each service has its own dedicated script that:
1. Builds the Docker image for that specific service
2. Tags the image appropriately
3. Pushes the image to the container registry

This modular approach enables:
- **Independent troubleshooting**: Debug and fix issues with individual services
- **Selective deployment**: Build and push only the services that have changed
- **Parallel execution**: Build multiple services simultaneously
- **Better error isolation**: Failures in one service don't affect others

## Available Scripts

- `build-push-api-gateway.sh` - API Gateway (Node.js/NestJS)
- `build-push-speaker-service.sh` - Speaker Service (Node.js/NestJS)
- `build-push-draft-service.sh` - Draft Service (Python/FastAPI)
- `build-push-rag-service.sh` - RAG Service (Python/FastAPI + LangChain)
- `build-push-evaluation-service.sh` - Evaluation Service (Python/FastAPI)
- `build-all-services.sh` - Convenience script to build all services

## Usage

### Prerequisites

1. **Docker**: Ensure Docker is installed and running
2. **Azure CLI**: Required for Azure Container Registry authentication
3. **Configuration**: Set up `scripts/azure/config.yaml` with your registry details

### Building Individual Services

Each script can be run independently:

```bash
# Build and push API Gateway
./scripts/docker/build-push-api-gateway.sh

# Build and push Speaker Service
./scripts/docker/build-push-speaker-service.sh

# Build and push Draft Service
./scripts/docker/build-push-draft-service.sh

# Build and push RAG Service
./scripts/docker/build-push-rag-service.sh

# Build and push Evaluation Service
./scripts/docker/build-push-evaluation-service.sh
```

### Building All Services

To build and push all services at once:

```bash
./scripts/docker/build-all-services.sh
```

### Custom Tags

All scripts support custom image tags via the `TAG` environment variable:

```bash
# Build with a specific tag
TAG=v1.2.3 ./scripts/docker/build-push-api-gateway.sh

# Build all services with a specific tag
TAG=v1.2.3 ./scripts/docker/build-all-services.sh
```

Default tag is `latest` if not specified.

### Custom Registry

Override the registry using the `REGISTRY` environment variable:

```bash
# Use a different registry
REGISTRY=myregistry.azurecr.io ./scripts/docker/build-push-api-gateway.sh
```

By default, the registry is read from `scripts/azure/config.yaml`.

### Dry Run Mode

Test the build process without actually building or pushing:

```bash
DRY_RUN=true ./scripts/docker/build-push-api-gateway.sh
```

## Script Options

Each script supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TAG` | Image tag | `latest` |
| `REGISTRY` | Container registry URL | From `config.yaml` |
| `DRY_RUN` | Dry run mode (true/false) | `false` |
| `SKIP_LOGIN` | Skip registry login (true/false) | `false` |
| `SKIP_BUILD` | Skip build, only push (true/false) | `false` |
| `SKIP_PUSH` | Build only, skip push (true/false) | `false` |

## Examples

### Build without pushing

```bash
SKIP_PUSH=true ./scripts/docker/build-push-draft-service.sh
```

### Push existing image

```bash
SKIP_BUILD=true ./scripts/docker/build-push-rag-service.sh
```

### Build for local testing

```bash
SKIP_PUSH=true TAG=local ./scripts/docker/build-push-api-gateway.sh
```

### Build multiple services in parallel

```bash
# In separate terminals or using background jobs
./scripts/docker/build-push-api-gateway.sh &
./scripts/docker/build-push-speaker-service.sh &
./scripts/docker/build-push-draft-service.sh &
wait
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
# Login to Azure Container Registry manually
az acr login --name <registry-name>

# Then run the script with SKIP_LOGIN=true
SKIP_LOGIN=true ./scripts/docker/build-push-api-gateway.sh
```

### Build Failures

1. Check Docker daemon is running: `docker info`
2. Verify Dockerfile exists: `ls -la docker/Dockerfile.<service>`
3. Check build context: Ensure you're in the project root
4. Review build logs for specific errors

### Push Failures

1. Verify registry credentials: `az acr credential show --name <registry-name>`
2. Check network connectivity to registry
3. Ensure image was built successfully: `docker images | grep <service-name>`

## Integration with CI/CD

These scripts can be easily integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Build and Push API Gateway
  run: ./scripts/docker/build-push-api-gateway.sh
  env:
    TAG: ${{ github.sha }}
```

### Azure DevOps Example

```yaml
- script: |
    export TAG=$(Build.BuildId)
    ./scripts/docker/build-push-api-gateway.sh
  displayName: 'Build and Push API Gateway'
```

## Maintenance

When adding new services:

1. Create a new `build-push-<service-name>.sh` script based on existing templates
2. Update `build-all-services.sh` to include the new service
3. Add the service to this README
4. Update the Dockerfile path in the script

## Related Documentation

- [Deployment Handbook](../../docs/DEPLOYMENT_HANDBOOK.md)
- [Docker Build Issues](../../docs/DOCKER_BUILD_ISSUES.md)
- [Azure Deployment](../../azure-deployment-summary.md)

