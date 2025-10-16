# Azure Deployment - Quick Fix Guide

## 🚨 Current Status
- ✅ All services deployed and running
- ❌ Missing environment variables
- ⏱️ Time to fix: 5-10 minutes

---

## 🔧 Quick Fix (3 Steps)

### Step 1: Run Fix Script
```bash
./scripts/azure/fix-environment-variables.sh
```

### Step 2: Wait 2 Minutes
Services will automatically restart after environment variable updates.

### Step 3: Test Services
```bash
./scripts/azure/test-deployed-services.sh
```

---

## 🌐 Your Deployed URLs

### API Gateway (Public)
```
https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io
```

**Endpoints:**
- Health: `/api/v1/health`
- Swagger: `/api/docs`
- Services Health: `/api/v1/health/services`

### Test Commands
```bash
# Test API Gateway
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health

# Test all services
curl https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health/services

# Open Swagger UI
open https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/docs
```

---

## 📊 What's Deployed

| Service | Status | Type |
|---------|--------|------|
| API Gateway | ✅ Running | External |
| Speaker Service | ✅ Running | Internal |
| Draft Service | ✅ Running | Internal |
| RAG Service | ✅ Running | Internal |
| Evaluation Service | ✅ Running | Internal |
| PostgreSQL | ✅ Ready | Database |
| Redis | ✅ Running | Cache |
| RabbitMQ | ✅ Running | Message Queue |
| Qdrant | ✅ Running | Vector DB |

---

## 🔍 Troubleshooting

### View Logs
```bash
# API Gateway
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 50

# Any service
az containerapp logs show --name <service-name> --resource-group draftgenie-rg --tail 50
```

### Check Environment Variables
```bash
az containerapp show --name api-gateway --resource-group draftgenie-rg \
  --query "properties.template.containers[0].env" -o json | jq .
```

### Restart Service
```bash
az containerapp revision restart --name api-gateway --resource-group draftgenie-rg
```

---

## 📚 Full Documentation

- **Detailed Test Report:** `AZURE_DEPLOYMENT_TEST_REPORT.md`
- **Complete Summary:** `AZURE_TESTING_SUMMARY.md`
- **Fix Script:** `scripts/azure/fix-environment-variables.sh`
- **Test Script:** `scripts/azure/test-deployed-services.sh`

---

## ✅ Expected Results After Fix

```json
{
  "status": "ok",
  "info": {
    "speaker-service": { "status": "up" },
    "draft-service": { "status": "up" },
    "rag-service": { "status": "up" },
    "evaluation-service": { "status": "up" }
  }
}
```

---

**Need Help?** Check the full documentation files listed above.

