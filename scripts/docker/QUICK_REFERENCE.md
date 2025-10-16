# Docker Build Scripts - Quick Reference

## 🚀 Quick Start

### Build Individual Service
```bash
# From project root
./scripts/docker/build-push-<service-name>.sh
```

### Build All Services
```bash
./scripts/docker/build-all-services.sh
```

## 📋 Available Services

| Service | Script | Port |
|---------|--------|------|
| API Gateway | `build-push-api-gateway.sh` | 3000 |
| Speaker Service | `build-push-speaker-service.sh` | 3001 |
| Draft Service | `build-push-draft-service.sh` | 3002 |
| RAG Service | `build-push-rag-service.sh` | 3003 |
| Evaluation Service | `build-push-evaluation-service.sh` | 3004 |

## 🎯 Common Use Cases

### 1. Build and Push Single Service
```bash
./scripts/docker/build-push-draft-service.sh
```

### 2. Build with Custom Tag
```bash
TAG=v1.2.3 ./scripts/docker/build-push-api-gateway.sh
```

### 3. Build All Services with Tag
```bash
TAG=v1.2.3 ./scripts/docker/build-all-services.sh
```

### 4. Build Only (No Push)
```bash
SKIP_PUSH=true ./scripts/docker/build-push-rag-service.sh
```

### 5. Push Existing Image
```bash
SKIP_BUILD=true ./scripts/docker/build-push-evaluation-service.sh
```

### 6. Dry Run (Test)
```bash
DRY_RUN=true ./scripts/docker/build-push-speaker-service.sh
```

### 7. Build All in Parallel
```bash
PARALLEL=true ./scripts/docker/build-all-services.sh
```

### 8. Continue on Error
```bash
CONTINUE_ON_ERROR=true ./scripts/docker/build-all-services.sh
```

## 🔧 Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `TAG` | Image tag | `latest` | `v1.0.0`, `dev`, `staging` |
| `REGISTRY` | Registry URL | From config.yaml | `myregistry.azurecr.io` |
| `DRY_RUN` | Test mode | `false` | `true`, `false` |
| `SKIP_LOGIN` | Skip registry login | `false` | `true`, `false` |
| `SKIP_BUILD` | Skip build step | `false` | `true`, `false` |
| `SKIP_PUSH` | Skip push step | `false` | `true`, `false` |
| `PARALLEL` | Build in parallel (all services) | `false` | `true`, `false` |
| `CONTINUE_ON_ERROR` | Continue if build fails | `false` | `true`, `false` |

## 💡 Pro Tips

### Combine Multiple Options
```bash
TAG=dev SKIP_PUSH=true ./scripts/docker/build-push-draft-service.sh
```

### Build Multiple Services Manually in Parallel
```bash
# In separate terminals
./scripts/docker/build-push-api-gateway.sh &
./scripts/docker/build-push-speaker-service.sh &
./scripts/docker/build-push-draft-service.sh &
wait
```

### Use Custom Registry
```bash
REGISTRY=myregistry.azurecr.io TAG=prod ./scripts/docker/build-all-services.sh
```

### Local Development Build
```bash
SKIP_PUSH=true TAG=local ./scripts/docker/build-push-api-gateway.sh
```

## 🐛 Troubleshooting

### Check if Docker is Running
```bash
docker info
```

### Manual Registry Login
```bash
az acr login --name <registry-name>
SKIP_LOGIN=true ./scripts/docker/build-push-api-gateway.sh
```

### View Built Images
```bash
docker images | grep draft-genie
```

### Clean Up Old Images
```bash
docker image prune -a
```

### Check Dockerfile Exists
```bash
ls -la docker/Dockerfile.*
```

## 📊 Build Status Indicators

- ✓ = Success
- ✗ = Failed
- ⚠ = Warning
- ℹ = Info

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Build Service
  run: ./scripts/docker/build-push-api-gateway.sh
  env:
    TAG: ${{ github.sha }}
```

### Azure DevOps
```yaml
- script: |
    export TAG=$(Build.BuildId)
    ./scripts/docker/build-push-api-gateway.sh
  displayName: 'Build and Push'
```

## 📁 File Structure

```
scripts/docker/
├── README.md                          # Full documentation
├── QUICK_REFERENCE.md                 # This file
├── build-all-services.sh              # Build all services
├── build-push-api-gateway.sh          # API Gateway
├── build-push-speaker-service.sh      # Speaker Service
├── build-push-draft-service.sh        # Draft Service
├── build-push-rag-service.sh          # RAG Service
└── build-push-evaluation-service.sh   # Evaluation Service
```

## 🔗 Related Files

- **Dockerfiles**: `docker/Dockerfile.*`
- **Config**: `scripts/azure/config.yaml`
- **Docker Compose**: `docker/docker-compose.yml`

## ⚡ Performance Tips

1. **Use Parallel Builds**: `PARALLEL=true ./scripts/docker/build-all-services.sh`
2. **Skip Unchanged Services**: Build only modified services individually
3. **Use BuildKit**: Already enabled in scripts for faster builds
4. **Layer Caching**: Docker automatically caches unchanged layers

## 🎓 Learning Resources

- [Docker Build Documentation](https://docs.docker.com/engine/reference/commandline/build/)
- [Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/)
- [Multi-stage Builds](https://docs.docker.com/develop/develop-images/multistage-build/)

---

**Need Help?** Check the full [README.md](./README.md) for detailed documentation.

