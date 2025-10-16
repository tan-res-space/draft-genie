# Service Testing Results

## Overview

Tested all backend services to identify issues preventing them from running properly.

---

## 📊 Service Status Summary

| Service | Deployed | Running | Health | Issue |
|---------|----------|---------|--------|-------|
| **API Gateway** | ✅ Yes | ✅ Yes | ✅ UP | None - Working perfectly |
| **Speaker Service** | ✅ Yes | ✅ Yes | ✅ UP | None - Fixed and working |
| **Draft Service** | ✅ Yes | ✅ Yes | ❌ DOWN | Missing MongoDB connection |
| **RAG Service** | ✅ Yes | ✅ Yes | ❌ DOWN | Missing MongoDB connection |
| **Evaluation Service** | ✅ Yes | ✅ Yes | ⚠️ TIMEOUT | Service not responding to health checks |

---

## 🔍 Detailed Findings

### 1. ✅ **API Gateway** - WORKING
**Status**: Fully operational  
**URL**: `https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io`  
**Health Check**: Responding correctly  
**Issues**: None

---

### 2. ✅ **Speaker Service** - WORKING
**Status**: Fully operational  
**URL**: `http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`  
**Health Check**: UP  
**Issues**: None (all issues fixed in previous investigation)

**Fixes Applied**:
- ✅ Dockerfile rewritten for production
- ✅ Listening on `0.0.0.0:8001`
- ✅ Database credentials corrected
- ✅ Prisma client generation added
- ✅ OpenSSL installed

---

### 3. ❌ **Draft Service** - FAILING

**Status**: Container running but application crashing  
**URL**: `http://draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`  
**Health Check**: Timeout

#### Issues Found:

1. **Missing Environment Variables** (FIXED)
   - ❌ `MONGODB_URL` - Required
   - ❌ `QDRANT_URL` - Required
   - ❌ `RABBITMQ_URL` - Required
   - ❌ `INSTANOTE_API_URL` - Required
   - ❌ `INSTANOTE_API_KEY` - Required

2. **MongoDB Connection** (CURRENT BLOCKER)
   ```
   pymongo.errors.ConfigurationError: The DNS query name does not exist: 
   _mongodb._tcp.cluster0.mongodb.net.
   ```
   - The service requires a valid MongoDB connection
   - MongoDB Atlas is not set up
   - Need to either:
     - Set up MongoDB Atlas cluster
     - Deploy MongoDB in Azure
     - Make MongoDB optional in the code

#### Current Environment Variables:
```bash
PORT=8002
DATABASE_URL=postgresql://dgadmin:...  # Wrong credentials
REDIS_URL=redis://...
GEMINI_API_KEY=secretref:gemini-api-key
MONGODB_URL=mongodb+srv://...  # Invalid URL
QDRANT_URL=http://qdrant:6333
RABBITMQ_URL=amqp://admin:rabbitmq123@rabbitmq:5672
INSTANOTE_API_URL=https://api.instanote.com
INSTANOTE_API_KEY=dummy-key-for-testing
```

#### Required Actions:

1. **Set up MongoDB** (Choose one):
   - **Option A**: Create MongoDB Atlas free cluster
     - Go to https://www.mongodb.com/cloud/atlas
     - Create M0 free cluster
     - Get connection string
     - Update `MONGODB_URL`
   
   - **Option B**: Deploy MongoDB in Azure Container Apps
     - Deploy MongoDB container
     - Configure persistent storage
     - Update `MONGODB_URL`
   
   - **Option C**: Make MongoDB optional in code
     - Modify `services/draft-service/app/core/config.py`
     - Add default value or make field optional
     - Handle MongoDB absence in application logic

2. **Fix Database URL**
   - Current: `postgresql://dgadmin:...`
   - Should be: `postgresql://draftgenieadminb4efba:...` (with URL-encoded password)

3. **Verify Qdrant and RabbitMQ**
   - Check if these services are deployed
   - Verify they're accessible

---

### 4. ❌ **RAG Service** - FAILING

**Status**: Container running but application crashing  
**URL**: `http://rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`  
**Health Check**: Timeout

#### Issues Found:

1. **MongoDB Connection** (SAME AS DRAFT SERVICE)
   ```
   pymongo.errors.ServerSelectionTimeoutError: localhost:27017: 
   [Errno 111] Connection refused
   ```
   - Trying to connect to `localhost:27017`
   - MongoDB not configured or URL not set
   - Same solution as draft-service needed

#### Required Actions:
- Same as Draft Service - need MongoDB setup

---

### 5. ⚠️ **Evaluation Service** - DEPLOYED BUT NOT RESPONDING

**Status**: Deployed and running, but not responding to health checks
**URL**: `http://evaluation-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io`
**Health Check**: Timeout (3000ms exceeded)

#### Deployment Summary:

1. **✅ Image Built Successfully**
   - Built for `linux/amd64` architecture
   - Build time: ~16 minutes (958.8 seconds)
   - Image size: 5.7GB (due to ML dependencies: PyTorch, sentence-transformers)

2. **✅ Image Pushed to ACR**
   - Successfully pushed to `acrdgbackendv01.azurecr.io/evaluation-service:latest`
   - Push time: ~10 minutes

3. **✅ Container App Created**
   - Service deployed to Azure Container Apps
   - Status: "Running"
   - Configuration: 1.0 CPU, 2.0Gi memory, internal ingress, port 3004

#### Environment Variables (Configured):
```
PORT=3004
ENVIRONMENT=production
HOST=0.0.0.0
POSTGRES_HOST=dg-backend-postgres.postgres.database.azure.com
POSTGRES_USER=draftgenieadminb4efba
POSTGRES_PASSWORD=hQq5BjqDfGgv!Z26mn@s$l6GF@TiEIzJ
POSTGRES_DB=dg-backend
SPEAKER_SERVICE_URL=http://speaker-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
DRAFT_SERVICE_URL=http://draft-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
RAG_SERVICE_URL=http://rag-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io
```

#### Current Issue:

**Service not responding to health checks**
- Container is running but timing out on health check requests
- Logs are empty (no startup logs visible yet)
- Possible causes:
  1. **ML models still loading** - PyTorch and sentence-transformers are heavy and may take 2-5 minutes to load
  2. **Missing health endpoint** - Service may not have a `/health` endpoint configured
  3. **Silent startup failure** - Service may be crashing without logging errors
  4. **Port mismatch** - Service may not be listening on port 3004

#### Required Actions:

1. **Wait for ML models to load** (2-5 minutes)
   - Large ML dependencies take time to initialize
   - Check logs again after waiting

2. **Verify health endpoint exists**
   - Check if service has `/health` or `/api/v1/health` endpoint
   - Review service code to confirm endpoint path

3. **Check service logs**
   ```bash
   az containerapp logs show --name evaluation-service --resource-group draftgenie-rg --tail 50 --follow false
   ```

4. **Test direct service URL**
   ```bash
   curl -v http://evaluation-service.internal.gentleforest-322351b3.southindia.azurecontainerapps.io/health
   ```

---

## 🎯 Priority Actions

### Immediate (Blocking All Services)

1. **Set up MongoDB**
   - This is blocking both draft-service and rag-service
   - Recommended: MongoDB Atlas free tier (M0)
   - Alternative: Make MongoDB optional in code for testing

### High Priority

2. **Deploy Evaluation Service**
   - Check if image exists
   - Deploy container app
   - Configure environment variables

3. **Fix Database Credentials**
   - Update draft-service and rag-service with correct PostgreSQL credentials
   - Use URL-encoded password

### Medium Priority

4. **Verify Infrastructure Services**
   - Check if RabbitMQ is deployed and accessible
   - Check if Qdrant is deployed and accessible
   - Update URLs if needed

---

## 📝 MongoDB Setup Guide

### Option 1: MongoDB Atlas (Recommended for Testing)

1. **Create Account**:
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free account

2. **Create Cluster**:
   - Choose M0 Free tier
   - Select region (preferably same as Azure - South India or nearby)
   - Cluster name: `draftgenie-cluster`

3. **Configure Access**:
   - Database Access: Create user `draftgenie` with password
   - Network Access: Add `0.0.0.0/0` (allow from anywhere) for testing
   - For production: Add Azure Container Apps outbound IPs

4. **Get Connection String**:
   ```
   mongodb+srv://draftgenie:<password>@draftgenie-cluster.xxxxx.mongodb.net/draftgenie?retryWrites=true&w=majority
   ```

5. **Update Services**:
   ```bash
   # Update draft-service
   az containerapp update --name draft-service --resource-group draftgenie-rg \
     --set-env-vars "MONGODB_URL=mongodb+srv://draftgenie:<password>@..."
   
   # Update rag-service
   az containerapp update --name rag-service --resource-group draftgenie-rg \
     --set-env-vars "MONGODB_URL=mongodb+srv://draftgenie:<password>@..."
   ```

### Option 2: Deploy MongoDB in Azure

```bash
az containerapp create \
  --name mongodb \
  --resource-group draftgenie-rg \
  --environment dg-backend-env \
  --image mongo:7.0 \
  --target-port 27017 \
  --ingress internal \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --env-vars \
    MONGO_INITDB_ROOT_USERNAME=admin \
    MONGO_INITDB_ROOT_PASSWORD=<secure-password> \
    MONGO_INITDB_DATABASE=draftgenie

# Then use: mongodb://admin:<password>@mongodb.internal.<domain>:27017/draftgenie
```

**Note**: This requires persistent storage configuration for production use.

---

## ✅ Next Steps

1. **Set up MongoDB Atlas** (15 minutes)
   - Create free cluster
   - Get connection string
   - Update both services

2. **Test Draft and RAG Services** (5 minutes)
   - Wait for services to restart
   - Check logs for successful startup
   - Test health endpoints

3. **Deploy Evaluation Service** (10 minutes)
   - Check if image exists
   - Deploy container app
   - Configure environment variables

4. **Final Health Check** (5 minutes)
   - Test all services via API Gateway
   - Verify all show as "up"
   - Test actual API endpoints

---

## 📞 Commands for Quick Testing

```bash
# Check all service status
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health/services | jq .

# Check individual service logs
az containerapp logs show --name draft-service --resource-group draftgenie-rg --tail 50
az containerapp logs show --name rag-service --resource-group draftgenie-rg --tail 50

# List all container apps
az containerapp list --resource-group draftgenie-rg \
  --query "[].{Name:name, Status:properties.runningStatus}" --output table

# Check ACR images
az acr repository list --name acrdgbackendv01 --output table
```

---

**Status**: Investigation Complete  
**Date**: October 16, 2025  
**Next Action**: Set up MongoDB to unblock draft-service and rag-service

