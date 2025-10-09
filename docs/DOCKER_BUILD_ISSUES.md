# Docker Build Issues - Troubleshooting Guide

**Date:** 2025-10-08  
**Issue:** Docker builds failing for Python services due to Debian repository hash sum mismatches

---

## Current Status

### ✅ Working
- **Docker is running** - Docker Desktop is operational
- **Infrastructure services are healthy:**
  - ✅ PostgreSQL (port 5432) - healthy
  - ✅ MongoDB (port 27017) - healthy
  - ✅ Redis (port 6379) - healthy
  - ✅ RabbitMQ (ports 5672, 15672) - healthy
  - ✅ Qdrant (ports 6333-6334) - starting
- **Speaker Service Docker image** - ✅ Built successfully
- **Environment file** - ✅ Created at `docker/.env`

### ❌ Issues
- **Python service Docker builds failing** - Debian repository hash sum mismatches
- **API Gateway build hanging** - Build process not completing

---

## Error Details

### Python Services Error

```
Hash Sum mismatch
Hashes of expected file:
 - SHA256:79cbf1459118bce3535133ffbf1fd2adbd57af65271f95c829af5cfa7f474168
Hashes of received file:
 - SHA256:9b41608bbd440d641807ac3c38f862403e382e87fd620c04f0769bc539bc10a3
E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?
```

**Cause:** Temporary Debian repository mirror issues or network problems

---

## Workarounds

### Option 1: Run Services Locally (Recommended for Testing)

Since infrastructure services are running, you can run application services locally:

#### 1. Start Speaker Service
```bash
cd /Users/tanmoy/Documents/augment-projects/draft-genie
npm run dev:speaker
```

#### 2. Start API Gateway
```bash
npm run dev:gateway
```

#### 3. Start Draft Service
```bash
cd services/draft-service
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3002
```

#### 4. Start RAG Service
```bash
cd services/rag-service
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3003
```

#### 5. Start Evaluation Service
```bash
cd services/evaluation-service
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3004
```

### Option 2: Retry Docker Build Later

The Debian repository issues are usually temporary. Try again in a few hours:

```bash
# Clean Docker build cache
docker builder prune -af

# Retry build
docker compose -f docker/docker-compose.yml build --no-cache
```

### Option 3: Use Different Base Image

Modify the Dockerfiles to use a different Python base image:

**Change in `docker/Dockerfile.draft-service`, `docker/Dockerfile.rag-service`, `docker/Dockerfile.evaluation-service`:**

```dockerfile
# Instead of:
FROM python:3.11-slim

# Try:
FROM python:3.11-slim-bookworm
# or
FROM python:3.11-alpine
```

### Option 4: Skip apt-get Install

If curl is not critical, comment out the apt-get step temporarily:

```dockerfile
# Comment out this section:
# RUN apt-get update && apt-get install -y \
#     curl \
#     && rm -rf /var/lib/apt/lists/*
```

---

## Running Integration Tests

Even without Docker builds completing, you can run integration tests with locally running services:

### Prerequisites

1. **Infrastructure services running** (already done ✅)
   ```bash
   docker compose -f docker/docker-compose.yml ps
   ```

2. **Install test dependencies**
   ```bash
   pip install pytest pytest-asyncio httpx python-dotenv motor psycopg2-binary redis qdrant-client aio-pika
   ```

3. **Start application services locally** (see Option 1 above)

4. **Run tests**
   ```bash
   pytest tests/integration/ -v
   ```

---

## Verification Commands

### Check Infrastructure Services
```bash
# Check all services
docker compose -f docker/docker-compose.yml ps

# Check PostgreSQL
docker exec -it draft-genie-postgres psql -U draftgenie -d draftgenie -c "SELECT 1;"

# Check MongoDB
docker exec -it draft-genie-mongodb mongosh --eval "db.runCommand({ping: 1})"

# Check Redis
docker exec -it draft-genie-redis redis-cli ping

# Check RabbitMQ
curl -u guest:guest http://localhost:15672/api/overview

# Check Qdrant
curl http://localhost:6333/collections
```

### Check Application Services (if running locally)
```bash
curl http://localhost:3000/api/v1/health  # API Gateway
curl http://localhost:3001/health         # Speaker Service
curl http://localhost:3002/health         # Draft Service
curl http://localhost:3003/health         # RAG Service
curl http://localhost:3004/health         # Evaluation Service
```

---

## Next Steps

1. **Immediate:** Run services locally and execute integration tests
2. **Short-term:** Retry Docker builds when Debian repositories are stable
3. **Long-term:** Consider using Alpine-based images or multi-stage builds with cached layers

---

## Additional Notes

- **GEMINI_API_KEY:** Make sure to set your actual Gemini API key in `docker/.env`
- **Docker credential helper:** Fixed by removing `credsStore` from `~/.docker/config.json`
- **Infrastructure services:** All working perfectly, no issues

---

## Contact

If issues persist, check:
- Docker Desktop status
- Network connectivity
- Debian repository status: https://www.debian.org/mirror/status
- Docker Hub status: https://status.docker.com/


