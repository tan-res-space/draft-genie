# CORS Fix - Quick Start Guide

## 🎯 TL;DR - Fix the CORS Error in 3 Steps

```bash
# 1. Build and push the fixed API Gateway
python3 scripts/build-push-service.py api-gateway

# 2. Update the running container
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest

# 3. Verify it works
curl -I -X OPTIONS https://api-gateway.gentleforest-322351b3.southindia.azurecontainerapps.io/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

---

## ✅ What's Been Done

1. **Identified the issue:** CORS configuration incompatibility (`credentials: true` with `origin: '*'`)
2. **Fixed the code:** Updated `services/api-gateway/src/main.ts` to use a callback function
3. **Created deployment tools:** New Python script `scripts/build-push-service.py` for easy deployment

---

## 🚀 Deploy Now

### Using Python Script (Recommended)

```bash
cd /Users/tanmoy/Documents/augment-projects/draft-genie
python3 scripts/build-push-service.py api-gateway
```

### Using Bash Script

```bash
cd /Users/tanmoy/Documents/augment-projects/draft-genie
./scripts/docker/build-push-api-gateway.sh
```

### Update Container App

```bash
az containerapp update \
  --name api-gateway \
  --resource-group draftgenie-rg \
  --image acrdgbackendv01.azurecr.io/api-gateway:latest
```

---

## 📚 Documentation

- **Full Guide:** `docs/CORS_FIX_DEPLOYMENT_GUIDE.md`
- **Python Script:** `scripts/build-push-service.py`
- **Bash Script:** `scripts/docker/build-push-api-gateway.sh`

---

## 🆘 Need Help?

**View logs:**
```bash
az containerapp logs show --name api-gateway --resource-group draftgenie-rg --tail 50
```

**Check status:**
```bash
az containerapp show --name api-gateway --resource-group draftgenie-rg --query "properties.runningStatus"
```

---

**Ready to deploy?** Run the commands above! 🚀

