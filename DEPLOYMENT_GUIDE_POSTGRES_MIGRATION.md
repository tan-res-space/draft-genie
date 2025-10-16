# PostgreSQL Migration - Deployment Guide

## 🎯 Overview

This guide walks you through deploying the migrated **draft-service** and **rag-service** to Azure Container Apps with PostgreSQL.

---

## ✅ Prerequisites

Before starting, ensure you have:

- [x] Azure CLI installed and logged in (`az login`)
- [x] Docker installed and running
- [x] Access to Azure Container Registry (`acrdgbackendv01.azurecr.io`)
- [x] PostgreSQL Flexible Server running in Azure
- [x] Resource group: `rg-dg-backend-v01`

---

## 📋 Deployment Steps

### **Step 1: Login to Azure Container Registry**

```bash
az acr login --name acrdgbackendv01
```

---

### **Step 2: Build and Push Docker Images**

Use the automated script to build and push both services:

```bash
./scripts/docker/rebuild-migrated-services.sh
```

This script will:
- Build Docker images for `linux/amd64` platform
- Tag images with `latest` and `postgres-migration` tags
- Push to Azure Container Registry

**Manual alternative:**

```bash
# Draft Service
cd services/draft-service
docker build --platform linux/amd64 -t acrdgbackendv01.azurecr.io/draft-service:latest .
docker push acrdgbackendv01.azurecr.io/draft-service:latest
cd ../..

# RAG Service
cd services/rag-service
docker build --platform linux/amd64 -t acrdgbackendv01.azurecr.io/rag-service:latest .
docker push acrdgbackendv01.azurecr.io/rag-service:latest
cd ../..
```

---

### **Step 3: Deploy to Azure Container Apps**

Use the automated deployment script:

```bash
./scripts/azure/deploy-postgres-migration.sh
```

This script will:
- Fetch PostgreSQL connection details
- Retrieve credentials from Azure Key Vault
- Construct `DATABASE_URL` with SSL mode
- Update both container apps with new images and environment variables
- Test health endpoints

**Manual alternative:**

```bash
# Get PostgreSQL details
PG_HOST=$(az postgres flexible-server show \
    --resource-group rg-dg-backend-v01 \
    --name dg-backend-postgres \
    --query "fullyQualifiedDomainName" \
    --output tsv)

# Get password from Key Vault
KEYVAULT_NAME=$(az keyvault list \
    --resource-group rg-dg-backend-v01 \
    --query "[0].name" \
    --output tsv)

PG_PASSWORD=$(az keyvault secret show \
    --vault-name ${KEYVAULT_NAME} \
    --name POSTGRES-PASSWORD \
    --query "value" \
    --output tsv)

# Construct DATABASE_URL
DATABASE_URL="postgresql+asyncpg://dgadmin:${PG_PASSWORD}@${PG_HOST}:5432/draftgenie?sslmode=require"

# Update draft-service
az containerapp update \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --image acrdgbackendv01.azurecr.io/draft-service:latest \
    --replace-env-vars \
        "DATABASE_URL=${DATABASE_URL}" \
        "POSTGRES_POOL_SIZE=10" \
        "POSTGRES_MAX_OVERFLOW=20"

# Update rag-service
az containerapp update \
    --name rag-service \
    --resource-group rg-dg-backend-v01 \
    --image acrdgbackendv01.azurecr.io/rag-service:latest \
    --replace-env-vars \
        "DATABASE_URL=${DATABASE_URL}" \
        "POSTGRES_POOL_SIZE=10" \
        "POSTGRES_MAX_OVERFLOW=20"
```

---

### **Step 4: Run Database Migrations**

The services will auto-create tables on startup, but for production, you should run migrations explicitly:

**Option 1: Run migrations from local machine**

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql+asyncpg://dgadmin:PASSWORD@dg-backend-postgres.postgres.database.azure.com:5432/draftgenie?sslmode=require"

# Draft Service
cd services/draft-service
poetry install
poetry run alembic upgrade head
cd ../..

# RAG Service
cd services/rag-service
poetry install
poetry run alembic upgrade head
cd ../..
```

**Option 2: Run migrations from container**

```bash
# Draft Service
az containerapp exec \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --command "alembic upgrade head"

# RAG Service
az containerapp exec \
    --name rag-service \
    --resource-group rg-dg-backend-v01 \
    --command "alembic upgrade head"
```

**Note**: The services are configured to auto-create tables on startup using `Base.metadata.create_all()`, so migrations are optional for initial deployment.

---

### **Step 5: Verify Deployment**

Use the automated testing script:

```bash
./scripts/azure/test-postgres-migration.sh
```

This script will:
- Test health endpoints (`/health`, `/health/ready`, `/health/live`)
- Verify PostgreSQL connectivity
- Check service logs for errors
- Verify running status

**Manual verification:**

```bash
# Get service URLs
DRAFT_URL=$(az containerapp show \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

RAG_URL=$(az containerapp show \
    --name rag-service \
    --resource-group rg-dg-backend-v01 \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

# Test health endpoints
curl "https://${DRAFT_URL}/health"
curl "https://${DRAFT_URL}/health/ready"

curl "https://${RAG_URL}/health"
curl "https://${RAG_URL}/health/ready"

# Check logs
az containerapp logs show \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --follow

az containerapp logs show \
    --name rag-service \
    --resource-group rg-dg-backend-v01 \
    --follow
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Draft service returns HTTP 200 on `/health`
- [ ] Draft service returns `"postgresql": true` on `/health/ready`
- [ ] RAG service returns HTTP 200 on `/health`
- [ ] RAG service returns `"postgresql": true` on `/health/ready`
- [ ] No MongoDB connection errors in logs
- [ ] Services show `runningStatus: "Running"`
- [ ] Can create drafts via API
- [ ] Can generate DFNs via RAG pipeline

---

## 🚨 Troubleshooting

### Issue: Service fails to start

**Check logs:**
```bash
az containerapp logs show --name draft-service --resource-group rg-dg-backend-v01 --tail 100
```

**Common causes:**
- DATABASE_URL not set or incorrect
- PostgreSQL firewall blocking connections
- Missing database or tables
- SSL certificate issues

**Solutions:**
- Verify DATABASE_URL includes `?sslmode=require`
- Check PostgreSQL firewall rules allow Azure services
- Run database migrations
- Verify PostgreSQL server is running

### Issue: PostgreSQL connection fails

**Check connectivity:**
```bash
# From local machine
psql "postgresql://dgadmin:PASSWORD@dg-backend-postgres.postgres.database.azure.com:5432/draftgenie?sslmode=require"
```

**Common causes:**
- Firewall rules blocking connections
- Incorrect credentials
- SSL mode mismatch

**Solutions:**
- Add firewall rule for Azure services
- Verify credentials in Key Vault
- Ensure `sslmode=require` in connection string

### Issue: Health check shows `"postgresql": false`

**Check:**
- DATABASE_URL environment variable is set
- PostgreSQL server is accessible
- Database exists
- Tables are created

**Solutions:**
- Verify environment variables: `az containerapp show --name draft-service --resource-group rg-dg-backend-v01 --query "properties.template.containers[0].env"`
- Run migrations
- Check PostgreSQL logs

---

## 📊 Monitoring

### View Service Metrics

```bash
# CPU and Memory usage
az monitor metrics list \
    --resource $(az containerapp show --name draft-service --resource-group rg-dg-backend-v01 --query "id" -o tsv) \
    --metric "UsageNanoCores,WorkingSetBytes" \
    --start-time $(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ') \
    --interval PT1M
```

### View Application Insights (if configured)

```bash
# Query recent exceptions
az monitor app-insights query \
    --app <app-insights-name> \
    --analytics-query "exceptions | where timestamp > ago(1h) | project timestamp, type, outerMessage"
```

---

## 🎉 Success Criteria

Migration is successful when:

1. ✅ Both services start without errors
2. ✅ Health checks return `"postgresql": true`
3. ✅ All API endpoints work as expected
4. ✅ Data can be created and retrieved
5. ✅ No MongoDB references in logs
6. ✅ Services are stable for 24+ hours

---

## 🔄 Rollback Plan

If issues arise:

### 1. Revert to Previous Images

```bash
# Use previous MongoDB-based images
az containerapp update \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --image acrdgbackendv01.azurecr.io/draft-service:previous-tag

az containerapp update \
    --name rag-service \
    --resource-group rg-dg-backend-v01 \
    --image acrdgbackendv01.azurecr.io/rag-service:previous-tag
```

### 2. Restore MongoDB Environment Variables

```bash
az containerapp update \
    --name draft-service \
    --resource-group rg-dg-backend-v01 \
    --replace-env-vars "MONGODB_URL=<mongodb-connection-string>"
```

---

## 📚 Additional Resources

- **Migration Documentation**: `MONGODB_TO_POSTGRESQL_MIGRATION.md`
- **Next Steps Guide**: `MIGRATION_NEXT_STEPS.md`
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **Azure Container Apps**: https://learn.microsoft.com/en-us/azure/container-apps/

---

**Last Updated**: 2025-10-16
**Status**: Ready for Deployment

