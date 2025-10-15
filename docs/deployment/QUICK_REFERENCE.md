# DraftGenie Deployment Quick Reference

A quick reference card for deploying DraftGenie to Azure, GCP, or Zoho Cloud.

---

## Platform Selection (30-Second Decision)

| If you need... | Choose |
|----------------|--------|
| Lowest cost for development | **Zoho** ($0-10/mo) |
| Best serverless experience | **GCP** ($77-102/mo) |
| Enterprise features | **Azure** ($93-143/mo) |
| Microsoft ecosystem | **Azure** |
| Google ecosystem | **GCP** |
| Zoho ecosystem | **Zoho** |
| Fastest deployment | **GCP** |
| Most free tiers | **Zoho** |

---

## Essential Prerequisites (All Platforms)

```bash
# 1. Get Gemini API Key
https://makersuite.google.com/app/apikey

# 2. Install Git
brew install git  # macOS
# or download from https://git-scm.com/

# 3. Install Docker
# Download from https://www.docker.com/products/docker-desktop

# 4. Clone DraftGenie
git clone https://github.com/tan-res-space/draft-genie.git
cd draft-genie
```

---

## Azure Quick Start

```bash
# 1. Install Azure CLI
brew install azure-cli  # macOS

# 2. Login
az login

# 3. Set variables
export RESOURCE_GROUP="draftgenie-rg"
export LOCATION="eastus"
export GEMINI_API_KEY="your-key-here"

# 4. Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# 5. Follow full guide
# See: docs/deployment/azure-deployment-guide.md
```

**Full Guide:** [azure-deployment-guide.md](./azure-deployment-guide.md)

**Estimated Time:** 2-3 hours

**Monthly Cost:** $93-143 (dev), $150-300 (prod)

---

## GCP Quick Start

```bash
# 1. Install gcloud CLI
brew install --cask google-cloud-sdk  # macOS

# 2. Login
gcloud auth login

# 3. Create project
export PROJECT_ID="draftgenie-prod-$(date +%s)"
gcloud projects create $PROJECT_ID

# 4. Set project
gcloud config set project $PROJECT_ID

# 5. Enable billing
gcloud billing accounts list
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ID

# 6. Follow full guide
# See: docs/deployment/gcp-deployment-guide.md
```

**Full Guide:** [gcp-deployment-guide.md](./gcp-deployment-guide.md)

**Estimated Time:** 2-3 hours

**Monthly Cost:** $77-102 (dev), $120-250 (prod)

---

## Zoho Cloud Quick Start

```bash
# 1. Install Catalyst CLI
npm install -g zcatalyst-cli

# 2. Login
zcatalyst login

# 3. Set up third-party services
# - PostgreSQL: https://render.com/ (free tier)
# - MongoDB: https://www.mongodb.com/cloud/atlas (free tier)
# - Redis: https://upstash.com/ (free tier)
# - RabbitMQ: https://www.cloudamqp.com/ (free tier)

# 4. Follow full guide
# See: docs/deployment/zoho-deployment-guide.md
```

**Full Guide:** [zoho-deployment-guide.md](./zoho-deployment-guide.md)

**Estimated Time:** 3-4 hours

**Monthly Cost:** $0-10 (dev), $100-200 (prod)

---

## Required Services by Platform

### Azure
- ✅ Azure Container Apps (compute)
- ✅ Azure Database for PostgreSQL
- ✅ Azure Cache for Redis
- ✅ MongoDB Atlas (third-party)
- ✅ Azure Container Registry
- ✅ Azure Key Vault

### GCP
- ✅ Cloud Run (compute)
- ✅ Cloud SQL for PostgreSQL
- ✅ Memorystore for Redis
- ✅ MongoDB Atlas (third-party)
- ✅ Artifact Registry
- ✅ Secret Manager

### Zoho (Hybrid)
- ✅ Zoho Catalyst (functions)
- ✅ Render.com (PostgreSQL + containers)
- ✅ MongoDB Atlas (database)
- ✅ Upstash (Redis)
- ✅ CloudAMQP (RabbitMQ)

---

## Environment Variables Checklist

All platforms need these environment variables:

```bash
# Required for all services
GEMINI_API_KEY=your-gemini-api-key

# Database connections
DATABASE_URL=postgresql://...
MONGODB_URL=mongodb+srv://...
REDIS_URL=redis://...
RABBITMQ_URL=amqp://...
QDRANT_URL=http://...

# Application config
NODE_ENV=production
JWT_SECRET=random-secure-string
CORS_ORIGIN=*
LOG_LEVEL=info
```

---

## Deployment Verification

After deployment, verify with these commands:

```bash
# Test API Gateway health
curl https://your-api-gateway-url/api/v1/health

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2024-01-15T10:30:00.000Z",
#   "services": {
#     "speaker": "healthy",
#     "draft": "healthy",
#     "rag": "healthy",
#     "evaluation": "healthy"
#   }
# }

# Test individual services
curl https://speaker-service-url/health
curl https://draft-service-url/health
curl https://rag-service-url/health
curl https://evaluation-service-url/health
```

---

## Common Issues Quick Fix

### Issue: Service won't start
```bash
# Check logs
# Azure: az containerapp logs show --name SERVICE_NAME --resource-group RG
# GCP: gcloud logging read "resource.labels.service_name=SERVICE_NAME"
# Zoho: zcatalyst logs --function-name SERVICE_NAME
```

### Issue: Database connection failed
```bash
# Verify connection string format
# PostgreSQL: postgresql://user:pass@host:port/db
# MongoDB: mongodb+srv://user:pass@host/db
# Redis: redis://host:port or rediss://host:port (SSL)
```

### Issue: Out of memory
```bash
# Increase memory allocation
# Azure: --memory=2Gi
# GCP: --memory=2Gi
# Render: Upgrade to larger plan
```

### Issue: Cold starts (Zoho/Render free tier)
```bash
# Solution 1: Upgrade to paid tier ($7/mo per service)
# Solution 2: Use uptime monitoring to keep warm
# - Sign up: https://uptimerobot.com/
# - Ping service every 10 minutes
```

---

## Cost Optimization Quick Tips

### All Platforms
1. ✅ Use free tiers for development
2. ✅ Set up budget alerts
3. ✅ Scale to zero when possible
4. ✅ Use caching aggressively
5. ✅ Monitor usage weekly

### Azure Specific
```bash
# Set min instances to 0 for non-critical services
az containerapp update --min-replicas=0
```

### GCP Specific
```bash
# Enable scale-to-zero
gcloud run services update SERVICE --min-instances=0
```

### Zoho Specific
```bash
# Maximize free tiers
# - Catalyst: 100K requests/month
# - Render: 750 hours/month
# - MongoDB Atlas: 512 MB
# - Upstash: 10K commands/day
```

---

## Monitoring Quick Setup

### Azure
```bash
# View logs
az containerapp logs show --name api-gateway --resource-group RG --follow

# View metrics in portal
https://portal.azure.com → Application Insights
```

### GCP
```bash
# View logs
gcloud logging tail "resource.labels.service_name=api-gateway"

# View metrics in console
https://console.cloud.google.com/monitoring
```

### Zoho
```bash
# View logs
zcatalyst logs --function-name api-gateway --tail

# View in console
https://console.catalyst.zoho.com
```

---

## Security Checklist

- [ ] All secrets stored in platform secret manager (not in code)
- [ ] HTTPS enabled (automatic on all platforms)
- [ ] Database connections use SSL
- [ ] API authentication configured (JWT)
- [ ] CORS configured appropriately
- [ ] Rate limiting enabled
- [ ] Regular security updates scheduled

---

## Backup Checklist

- [ ] PostgreSQL automated backups enabled
- [ ] MongoDB Atlas backups configured
- [ ] Manual backup script created
- [ ] Backup restoration tested
- [ ] Backup retention policy set

---

## Next Steps After Deployment

1. **Set up CI/CD**
   - GitHub Actions for automated deployments
   - See guide for platform-specific examples

2. **Configure monitoring**
   - Set up alerts for errors
   - Create dashboards for key metrics

3. **Optimize costs**
   - Review usage after 1 week
   - Adjust resource allocation
   - Enable auto-scaling

4. **Security hardening**
   - Review access controls
   - Enable audit logging
   - Implement rate limiting

5. **Performance testing**
   - Load test with expected traffic
   - Identify bottlenecks
   - Optimize as needed

---

## Getting Help

### Documentation
- **Azure Guide:** [azure-deployment-guide.md](./azure-deployment-guide.md)
- **GCP Guide:** [gcp-deployment-guide.md](./gcp-deployment-guide.md)
- **Zoho Guide:** [zoho-deployment-guide.md](./zoho-deployment-guide.md)
- **Main README:** [README.md](./README.md)

### Support
- **GitHub Issues:** https://github.com/tan-res-space/draft-genie/issues
- **Azure Support:** https://azure.microsoft.com/support/
- **GCP Support:** https://cloud.google.com/support
- **Zoho Support:** https://catalyst.zoho.com/support

---

## Useful Commands Reference

### Azure
```bash
az login                                    # Login
az group list                               # List resource groups
az containerapp list                        # List container apps
az containerapp logs show --name NAME       # View logs
az group delete --name RG                   # Delete everything
```

### GCP
```bash
gcloud auth login                           # Login
gcloud projects list                        # List projects
gcloud run services list                    # List services
gcloud logging tail "filter"                # View logs
gcloud projects delete PROJECT_ID           # Delete everything
```

### Zoho
```bash
zcatalyst login                             # Login
zcatalyst functions:list                    # List functions
zcatalyst logs --function-name NAME         # View logs
zcatalyst env:list                          # List env vars
```

---

**For detailed instructions, always refer to the full deployment guide for your chosen platform.**


