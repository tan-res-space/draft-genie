# DraftGenie Azure Deployment - Quick Start Guide

Get DraftGenie deployed to Azure in 30 minutes!

## Prerequisites (5 minutes)

### 1. Install Required Tools

```bash
# Check Python (need 3.8+)
python3 --version

# Install Azure CLI (macOS)
brew install azure-cli

# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop

# Verify installations
az --version
docker --version
```

### 2. Set Up Python Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated and prevents conflicts:

```bash
# Run the setup script
bash scripts/setup-venv.sh

# Activate the virtual environment
source scripts/venv/bin/activate
```

**Note:** You can skip this step and install dependencies globally, but using a virtual environment is recommended.

### 3. Login to Azure

```bash
az login
```

### 4. Get Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Copy it (you'll need it in the next step)

---

## Option 1: Automated Setup (Recommended)

### Run the Setup Wizard

```bash
# Navigate to project root
cd draft-genie

# Run setup wizard
bash scripts/azure/setup.sh
```

The wizard will:
- ✅ Check all prerequisites
- ✅ Guide you through configuration
- ✅ Start deployment automatically

---

## Option 2: Manual Configuration

### Step 1: Set Up Virtual Environment (Recommended)

```bash
# Create and activate virtual environment
bash scripts/setup-venv.sh
source scripts/venv/bin/activate
```

Or install dependencies globally:

```bash
pip3 install PyYAML
```

### Step 2: Create Configuration

```bash
# Copy template
cp scripts/azure/config.template.yaml scripts/azure/config.yaml

# Edit configuration
nano scripts/azure/config.yaml
```

**Required changes:**
- Set `secrets.gemini_api_key` to your Gemini API key
- Optionally customize resource names

### Step 3: Run Deployment

```bash
python3 scripts/deploy-azure.py
```

---

## What Happens During Deployment

The script will:

1. ✅ **Check Prerequisites** (1 min)
   - Verify Azure CLI, Docker, Python
   - Check Azure login status

2. ✅ **Create Infrastructure** (15-20 min)
   - Resource Group
   - Container Registry
   - Key Vault
   - PostgreSQL Database
   - Redis Cache
   - Monitoring (Log Analytics + App Insights)

3. ✅ **Build & Push Images** (5-10 min)
   - Build Docker images for 5 services
   - Push to Azure Container Registry

4. ✅ **Deploy Services** (5-10 min)
   - Deploy RabbitMQ and Qdrant
   - Deploy 5 application services
   - Configure environment variables

5. ✅ **Verify Deployment** (1 min)
   - Check service health
   - Generate summary report

**Total Time:** 30-45 minutes

---

## After Deployment

### 1. Get Your API URL

The deployment summary will show your API Gateway URL:

```
API Gateway: https://api-gateway.{random}.eastus.azurecontainerapps.io
```

### 2. Test the Deployment

```bash
# Health check
curl https://your-api-gateway-url/api/v1/health

# Expected response:
# {
#   "status": "ok",
#   "services": {
#     "speaker": "healthy",
#     "draft": "healthy",
#     "rag": "healthy",
#     "evaluation": "healthy"
#   }
# }
```

### 3. View Deployment Summary

```bash
cat azure-deployment-summary.md
```

### 4. Check Logs

```bash
# View deployment log
cat azure-deployment.log

# View service logs in Azure
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --follow
```

---

## Common Issues & Solutions

### Issue: "Azure CLI not found"

```bash
# macOS
brew install azure-cli

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows
# Download from https://aka.ms/installazurecliwindows
```

### Issue: "Not logged in to Azure"

```bash
az login
```

### Issue: "Docker daemon not running"

```bash
# Start Docker Desktop application
```

### Issue: "Container registry name already exists"

```bash
# Edit config.yaml and change container_registry.name
# Must be globally unique and alphanumeric only
```

### Issue: "Deployment failed at step X"

```bash
# Resume from last checkpoint
python3 scripts/deploy-azure.py --resume
```

---

## Useful Commands

### View Resources

```bash
# List all resources
az resource list \
  --resource-group draftgenie-rg \
  --output table

# View Container Apps
az containerapp list \
  --resource-group draftgenie-rg \
  --output table
```

### View Logs

```bash
# API Gateway logs
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --follow

# All services
for service in api-gateway speaker-service draft-service rag-service evaluation-service; do
  echo "=== $service ==="
  az containerapp logs show --name $service --resource-group draftgenie-rg --tail 10
done
```

### Scale Services

```bash
# Scale API Gateway
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --min-replicas 2 \
  --max-replicas 10
```

### Update Environment Variables

```bash
# Update environment variable
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --set-env-vars "LOG_LEVEL=debug"
```

---

## Cleanup

### Delete All Resources

```bash
# Using cleanup script
python3 scripts/azure/cleanup.py --config scripts/azure/config.yaml

# Or manually
az group delete --name draftgenie-rg --yes --no-wait
```

**Warning:** This deletes everything and cannot be undone!

---

## Cost Optimization

### Development Environment (~$93-143/month)

Current configuration is optimized for development:
- PostgreSQL: Standard_B1ms ($15-20/mo)
- Redis: Basic C0 ($15-20/mo)
- Container Apps: Minimal replicas ($30-50/mo)
- Container Registry: Basic ($5/mo)
- Monitoring: Basic ($5-10/mo)

### Reduce Costs Further

```bash
# Scale down to minimum
az containerapp update --name api-gateway --min-replicas 0 --max-replicas 1
az containerapp update --name speaker-service --min-replicas 0 --max-replicas 1
# ... repeat for other services

# Or stop services when not in use
az containerapp update --name api-gateway --min-replicas 0
```

### Production Environment (~$150-300/month)

For production, consider:
- PostgreSQL: Standard_D2s_v3 ($60-80/mo)
- Redis: Standard C1 ($30-40/mo)
- Container Apps: More replicas ($60-100/mo)
- Container Registry: Standard ($20/mo)
- Monitoring: Enhanced ($10-20/mo)

---

## Next Steps

### 1. Set Up MongoDB Atlas

If you didn't set up MongoDB during deployment:

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free M0 cluster
3. Create database user
4. Whitelist IP: 0.0.0.0/0 (or specific IPs)
5. Get connection string
6. Update Key Vault:

```bash
az keyvault secret set \
  --vault-name draftgenie-kv \
  --name MONGODB-URL \
  --value "mongodb+srv://user:pass@cluster.mongodb.net/db"
```

7. Restart services to pick up new secret

### 2. Set Up Custom Domain (Optional)

```bash
# Add custom domain
az containerapp hostname add \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --hostname api.yourdomain.com

# SSL certificate is automatically provisioned
```

### 3. Configure Monitoring Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group draftgenie-rg \
  --scopes /subscriptions/{sub-id}/resourceGroups/draftgenie-rg \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU > 80%"
```

### 4. Set Up CI/CD

Create `.github/workflows/deploy-azure.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - name: Deploy
        run: |
          python3 scripts/deploy-azure.py --auto-approve
```

---

## Getting Help

- **Documentation**: `scripts/azure/README.md`
- **Deployment Guide**: `docs/deployment/azure-deployment-guide.md`
- **GitHub Issues**: https://github.com/tan-res-space/draft-genie/issues
- **Azure Support**: https://azure.microsoft.com/support/

---

## Summary

✅ **Prerequisites**: Azure CLI, Docker, Python, Gemini API key  
✅ **Deployment**: `bash scripts/azure/setup.sh` or `python3 scripts/deploy-azure.py`  
✅ **Time**: 30-45 minutes  
✅ **Cost**: $93-143/month (development)  
✅ **Cleanup**: `python3 scripts/azure/cleanup.py`  

**You're ready to deploy! 🚀**

