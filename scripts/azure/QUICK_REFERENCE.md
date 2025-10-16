# Quick Reference: Updated Deployment Script

## 🚀 Quick Start

```bash
# Standard deployment
python scripts/deploy-azure.py

# With verbose logging
python scripts/deploy-azure.py --verbose

# Resume from failure
python scripts/deploy-azure.py --resume

# Dry run (preview only)
python scripts/deploy-azure.py --dry-run
```

## 🔑 Key Changes

### 1. Docker Build - AMD64 Platform
**Location**: `scripts/azure/docker_builder.py` → `build_image()` method

```python
# Now builds with --platform linux/amd64
cmd = ['docker', 'build', '--platform', 'linux/amd64', ...]
```

### 2. Docker Credential Helper
**Location**: `scripts/azure/docker_builder.py` → `_ensure_docker_desktop_in_path()` method

```python
# Automatically adds Docker Desktop bin to PATH
os.environ['PATH'] = f"{docker_desktop_bin}:{current_path}"
```

### 3. Service Testing
**Location**: `scripts/azure/deployer.py` → `_step_verify_deployment()` method

```python
# Now automatically tests all deployed services
# - Checks running status
# - Gets service URLs
# - Tests health endpoints
# - Displays summary
```

## 📊 Deployment Steps

| Step | Description | Updated |
|------|-------------|---------|
| 1 | Check Prerequisites | No |
| 2 | Create Resource Group | No |
| 3 | Create Monitoring | No |
| 4 | Create Container Registry | No |
| 5 | Create Key Vault | No |
| 6 | Create Databases | No |
| 7 | Store Secrets | No |
| 8 | Create Container Apps Env | No |
| 9 | **Build & Push Images** | **✅ Yes** |
| 10 | Deploy Infrastructure | No |
| 11 | Deploy Applications | No |
| 12 | Run Migrations | No |
| 13 | **Verify Deployment** | **✅ Yes** |
| 14 | Create Summary | No |

## 🎯 What to Expect

### Step 9: Building Images
```
Platform: linux/amd64 (required for Azure Container Apps)
Registry: acrdgbackendv01.azurecr.io
Total services: 5

[1/5] Building and Pushing api-gateway
✓ Successfully built image
✓ Successfully pushed image

Build and Push Summary:
Total services: 5
Successful: 5
Failed: 0
```

### Step 13: Verification
```
Testing deployed services...

✓ api-gateway: Running
✓ speaker-service: Running
✓ draft-service: Running
✓ rag-service: Running
✓ evaluation-service: Running

Services running: 5/5

API Gateway URL: https://api-gateway...azurecontainerapps.io
Health Check: https://api-gateway.../api/v1/health
Swagger Docs: https://api-gateway.../api/docs
```

## 🔧 Troubleshooting

### Build Fails
```bash
# Check logs
cat azure-deployment.log

# Verify Docker is running
docker info

# Check platform support
docker buildx ls
```

### Deployment Fails
```bash
# Check Azure login
az account show

# Resume from last checkpoint
python scripts/deploy-azure.py --resume

# Check state file
cat .azure-deployment-state.json
```

### Services Not Running
```bash
# Check service logs
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --tail 50

# Check service status
az containerapp show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --query properties.runningStatus
```

## 📝 Configuration

### Required in `config.yaml`
```yaml
secrets:
  gemini_api_key: "your-key-here"  # REQUIRED

azure:
  resource_group: "draftgenie-rg"
  
container_registry:
  name: "acrdgbackendv01"
  
key_vault:
  name: "dg-backend-kv-v01"
```

## ✅ Success Indicators

- ✅ Build shows "Platform: linux/amd64"
- ✅ All 5 services build successfully
- ✅ All 5 services push successfully
- ✅ All 5 services show "Running" status
- ✅ Health check returns `{"status": "ok"}`
- ✅ Service URLs are accessible

## 🆘 Getting Help

1. Check the detailed logs: `azure-deployment.log`
2. Review the state file: `.azure-deployment-state.json`
3. See full documentation: `scripts/azure/DEPLOYMENT_SCRIPT_UPDATES.md`
4. Run tests: `./scripts/azure/test-deployed-services.sh`

## 🎉 Post-Deployment

```bash
# Test all services
./scripts/azure/test-deployed-services.sh

# Access API Gateway
curl https://api-gateway.../api/v1/health

# View Swagger docs
open https://api-gateway.../api/docs

# Check service logs
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --follow
```

## 📚 Related Files

- `scripts/deploy-azure.py` - Main deployment script
- `scripts/azure/docker_builder.py` - Docker build logic (UPDATED)
- `scripts/azure/deployer.py` - Deployment orchestrator (UPDATED)
- `scripts/azure/config.yaml` - Configuration file
- `DEPLOYMENT_UPDATE_SUMMARY.md` - Detailed summary
- `scripts/azure/DEPLOYMENT_SCRIPT_UPDATES.md` - Full documentation

