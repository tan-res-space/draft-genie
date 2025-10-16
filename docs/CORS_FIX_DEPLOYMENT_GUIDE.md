# CORS Fix Deployment Guide

## 🐛 Issue Summary

**Error Message:**
```
Cannot connect to Azure API. Please check if the API is running and CORS is configured.
```

**Root Cause:**
The API Gateway's CORS configuration had `credentials: true` with `origin: '*'`, which is incompatible according to the CORS specification. Browsers reject this combination for security reasons.

**Status:** ✅ **FIXED** in code - Ready to deploy

---

## 🔧 What Was Fixed

**File:** `services/api-gateway/src/main.ts`

**Change:** Updated CORS configuration to use a callback function when `CORS_ORIGIN='*'` to properly allow all origins while maintaining credential support.

**Before:**
```typescript
const corsOrigin = process.env['CORS_ORIGIN']
  ? process.env['CORS_ORIGIN'].split(',').map(origin => origin.trim())
  : '*';

app.enableCors({
  origin: corsOrigin,
  credentials: true,
  // ...
});
```

**After:**
```typescript
const corsOriginEnv = process.env['CORS_ORIGIN'] || '*';

const corsOrigin = corsOriginEnv === '*' 
  ? (origin: string, callback: (err: Error | null, allow?: boolean) => void) => {
      callback(null, true);
    }
  : corsOriginEnv.split(',').map(origin => origin.trim());

app.enableCors({
  origin: corsOrigin,
  credentials: true,
  // ...
});
```

---

## 🚀 Deployment Options

### Option 1: Python Script (Recommended) ⭐

Use the new Python script to build and push just the API Gateway:

```bash
# Navigate to project root
cd /Users/tanmoy/Documents/augment-projects/draft-genie

# Activate virtual environment (if needed)
source scripts/venv/bin/activate

# Build and push API Gateway
python3 scripts/build-push-service.py api-gateway

# Update the running container app
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest
```

**With custom tag:**
```bash
python3 scripts/build-push-service.py api-gateway --tag v1.0.1

az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:v1.0.1
```

**Dry run (see what would happen):**
```bash
python3 scripts/build-push-service.py api-gateway --dry-run
```

---

### Option 2: Bash Script

Use the existing bash script:

```bash
cd /Users/tanmoy/Documents/augment-projects/draft-genie

# Build and push
./scripts/docker/build-push-api-gateway.sh

# Update the running container app
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest
```

---

### Option 3: Quick Environment Variable Fix (Temporary)

If you want a temporary fix without rebuilding, specify your frontend's origin explicitly:

```bash
# Update CORS_ORIGIN to include your frontend URL
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --set-env-vars "CORS_ORIGIN=http://localhost:3000,http://localhost:4200,https://your-frontend-domain.com"
```

**Note:** This is temporary. The code fix (Option 1 or 2) is still recommended for production.

---

## 🧪 Testing Locally First

Test the fix locally before deploying to Azure:

```bash
# 1. Navigate to API Gateway directory
cd services/api-gateway

# 2. Install dependencies (if not already done)
npm install

# 3. Set environment variables
export CORS_ORIGIN="*"
export PORT=3000
export SPEAKER_SERVICE_URL="http://localhost:3001"
export DRAFT_SERVICE_URL="http://localhost:3002"
export RAG_SERVICE_URL="http://localhost:3003"
export EVALUATION_SERVICE_URL="http://localhost:3004"
export JWT_SECRET="test-secret"

# 4. Run the service
npm run start:dev

# 5. In another terminal, test CORS
curl -I -X OPTIONS http://localhost:3000/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"

# You should see: Access-Control-Allow-Origin: http://localhost:3000
```

---

## ✅ Verification After Deployment

### 1. Check CORS Headers

```bash
# Test CORS with your frontend origin
curl -I -X OPTIONS https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

**Expected headers:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,POST,PUT,PATCH,DELETE,OPTIONS
Access-Control-Allow-Headers: Content-Type,Authorization,X-API-Key
```

### 2. Test API Health

```bash
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health
```

**Expected response:**
```json
{
  "status": "ok",
  "info": {
    "gateway": {
      "status": "up"
    }
  },
  "error": {},
  "details": {
    "gateway": {
      "status": "up"
    }
  }
}
```

### 3. Check Container App Status

```bash
az containerapp show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --query "properties.runningStatus" \
  -o tsv
```

**Expected:** `Running`

### 4. View Logs

```bash
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --tail 50
```

---

## 🔍 Troubleshooting

### Issue: Build fails with "docker: command not found"

**Solution:**
```bash
# Check if Docker is running
docker --version

# If not installed, install Docker Desktop
# https://www.docker.com/products/docker-desktop
```

### Issue: "Failed to login to registry"

**Solution:**
```bash
# Login to Azure first
az login

# Verify you're logged in
az account show

# Try logging into ACR manually
az acr login --name acrdgbackendv01
```

### Issue: "Image not found in registry"

**Solution:**
```bash
# List images in registry
az acr repository list --name acrdgbackendv01 --output table

# Check specific image tags
az acr repository show-tags --name acrdgbackendv01 --repository api-gateway --output table
```

### Issue: Container app not updating

**Solution:**
```bash
# Force restart the container app
az containerapp revision restart \
  --name api-gateway \
  --resource-group draftgenie-rg

# Or create a new revision
az containerapp revision copy \
  --name api-gateway \
  --resource-group draftgenie-rg
```

### Issue: CORS still not working after deployment

**Checklist:**
1. ✅ Verify the new image was pushed to ACR
2. ✅ Verify the container app is using the new image
3. ✅ Check container app logs for errors
4. ✅ Verify CORS_ORIGIN environment variable is set correctly
5. ✅ Clear browser cache and try again
6. ✅ Check browser console for exact CORS error

---

## 📋 Complete Deployment Checklist

- [ ] Code fix applied in `services/api-gateway/src/main.ts`
- [ ] Tested locally (optional but recommended)
- [ ] Built new Docker image
- [ ] Pushed image to Azure Container Registry
- [ ] Updated container app with new image
- [ ] Verified CORS headers are correct
- [ ] Tested API health endpoint
- [ ] Tested from frontend application
- [ ] Checked container app logs for errors
- [ ] Documented deployment in team notes

---

## 🎯 Quick Command Reference

```bash
# Build and push (Python)
python3 scripts/build-push-service.py api-gateway

# Build and push (Bash)
./scripts/docker/build-push-api-gateway.sh

# Update container app
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest

# Restart container app
az containerapp revision restart \
  --name api-gateway \
  --resource-group draftgenie-rg

# View logs
az containerapp logs show \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --tail 50

# Test CORS
curl -I -X OPTIONS https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

---

## 📞 Support

If you encounter any issues:

1. Check the logs: `az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 100`
2. Verify the image: `az acr repository show-tags --name acrdgbackendv01 --repository api-gateway`
3. Check container status: `az containerapp show --name api-gateway --resource-group draftgenie-rg`

---

**Last Updated:** 2025-10-16
**Status:** Ready for deployment

