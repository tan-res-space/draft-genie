# Manual Testing Guide for Draft Genie

**Date:** 2025-10-08  
**Purpose:** Step-by-step guide to manually test the Draft Genie system

---

## Prerequisites

### 1. Infrastructure Services Running ✅

All infrastructure services are already running in Docker:

```bash
docker compose -f docker/docker-compose.yml ps
```

Expected output:
- ✅ PostgreSQL (port 5432) - healthy
- ✅ MongoDB (port 27017) - healthy
- ✅ Redis (port 6379) - healthy
- ✅ RabbitMQ (ports 5672, 15672) - healthy
- ✅ Qdrant (ports 6333-6334) - running

### 2. Environment Configuration

Make sure `docker/.env` has your Gemini API key:
```bash
cat docker/.env | grep GEMINI_API_KEY
```

---

## Option 1: Test Infrastructure Services Only

Since infrastructure services are running, you can test them directly:

### Test PostgreSQL
```bash
docker exec -it draft-genie-postgres psql -U draftgenie -d draftgenie -c "SELECT version();"
```

### Test MongoDB
```bash
docker exec -it draft-genie-mongodb mongosh --eval "db.runCommand({ping: 1})"
```

### Test Redis
```bash
docker exec -it draft-genie-redis redis-cli ping
```

### Test RabbitMQ
```bash
curl -u guest:guest http://localhost:15672/api/overview | jq '.rabbitmq_version'
```

### Test Qdrant
```bash
curl http://localhost:6333/collections
```

---

## Option 2: Fix TypeScript and Run Services

### Step 1: Fix TypeScript Configuration Issues

The Speaker Service has module resolution issues. To fix:

**Option A: Disable TypeScript Checking (Quick Fix)**

Edit `apps/speaker-service/tsconfig.json` and add:
```json
{
  "compilerOptions": {
    "skipLibCheck": true,
    "noEmit": false,
    "allowJs": true
  }
}
```

**Option B: Use ts-node Instead of Webpack**

Run the service directly with ts-node:
```bash
cd apps/speaker-service
npx ts-node -r tsconfig-paths/register src/main.ts
```

### Step 2: Start Services

Once TypeScript issues are resolved:

**Terminal 1 - Speaker Service:**
```bash
npm run dev:speaker
# Should start on port 3001
```

**Terminal 2 - API Gateway:**
```bash
npm run dev:gateway
# Should start on port 3000
```

**Terminal 3 - Draft Service:**
```bash
cd services/draft-service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
```

**Terminal 4 - RAG Service:**
```bash
cd services/rag-service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3003 --reload
```

**Terminal 5 - Evaluation Service:**
```bash
cd services/evaluation-service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3004 --reload
```

### Step 3: Verify Services

```bash
# Check all services
curl http://localhost:3000/api/v1/health  # API Gateway
curl http://localhost:3001/health         # Speaker Service
curl http://localhost:3002/health         # Draft Service
curl http://localhost:3003/health         # RAG Service
curl http://localhost:3004/health         # Evaluation Service
```

---

## Option 3: Run Integration Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio httpx python-dotenv motor psycopg2-binary redis qdrant-client aio-pika
```

### Run Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_complete_workflow.py -v

# Run with coverage
pytest tests/integration/ -v --cov --cov-report=html

# Skip AI-dependent tests
pytest tests/integration/ -v -m "not requires_ai"
```

---

## Manual API Testing

If services are running, you can test the API manually:

### 1. Register a User

```bash
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "name": "Test User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@draftgenie.com",
    "password": "admin123"
  }'
```

Save the `accessToken` from the response.

### 3. Create a Speaker

```bash
TOKEN="your-access-token-here"

curl -X POST http://localhost:3000/api/v1/speakers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "bucket": "A",
    "metadata": {"test": true}
  }'
```

### 4. Create a Draft

```bash
SPEAKER_ID="speaker-id-from-previous-response"

curl -X POST http://localhost:3000/api/v1/drafts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_id": "'$SPEAKER_ID'",
    "content": "This is a test draft",
    "type": "IFN",
    "metadata": {"test": true}
  }'
```

### 5. Get Speaker Complete Data

```bash
curl -X GET "http://localhost:3000/api/v1/speakers/$SPEAKER_ID/complete" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Get Dashboard Metrics

```bash
curl -X GET http://localhost:3000/api/v1/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### Issue: Services Won't Start

**Check logs:**
```bash
# For Docker services
docker compose -f docker/docker-compose.yml logs [service-name]

# For local services
# Check the terminal output where you started the service
```

**Common fixes:**
- Restart infrastructure services: `docker compose -f docker/docker-compose.yml restart`
- Check port availability: `lsof -i :3000` (replace with actual port)
- Clear node_modules: `rm -rf node_modules && npm install`

### Issue: TypeScript Errors

**Quick fix:**
```bash
# Rebuild TypeScript
npm run build

# Or skip type checking
export TS_NODE_TRANSPILE_ONLY=true
npm run dev:speaker
```

### Issue: Database Connection Errors

**Check database status:**
```bash
docker compose -f docker/docker-compose.yml ps
```

**Restart databases:**
```bash
docker compose -f docker/docker-compose.yml restart postgres mongodb redis
```

### Issue: Integration Tests Failing

**Check services are running:**
```bash
curl http://localhost:3000/api/v1/health
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
curl http://localhost:3004/health
```

**Run tests with more verbosity:**
```bash
pytest tests/integration/ -vv -s
```

---

## Success Criteria

✅ **Infrastructure Services:**
- All 5 Docker services running and healthy

✅ **Application Services:**
- All 5 application services responding to health checks

✅ **API Testing:**
- Can register/login users
- Can create speakers
- Can create drafts
- Can retrieve aggregated data

✅ **Integration Tests:**
- At least 40/49 tests passing (some may require AI services)

---

## Next Steps After Testing

Once services are running and tests are passing:

1. **Fix Docker builds** - Retry when Debian repositories are stable
2. **Increase test coverage** - Target 70%+ for Python services
3. **Set up monitoring** - Prometheus + Grafana
4. **Configure backups** - Automated database backups
5. **Deploy to staging** - Test in staging environment

---

## Quick Reference

**Infrastructure Ports:**
- PostgreSQL: 5432
- MongoDB: 27017
- Redis: 6379
- RabbitMQ: 5672, 15672 (management)
- Qdrant: 6333-6334

**Application Ports:**
- API Gateway: 3000
- Speaker Service: 3001
- Draft Service: 3002
- RAG Service: 3003
- Evaluation Service: 3004

**Default Credentials:**
- Admin User: `admin@draftgenie.com` / `admin123`
- RabbitMQ: `guest` / `guest`
- PostgreSQL: `draftgenie` / `draftgenie123`
- MongoDB: `draftgenie` / `draftgenie123`

---

## Documentation

- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Integration Tests:** `tests/integration/README.md`
- **Phase 8 Summary:** `docs/PHASE_8_COMPLETION_SUMMARY.md`
- **Current Status:** `docs/CURRENT_STATUS_AND_NEXT_STEPS.md`
- **Docker Issues:** `docs/DOCKER_BUILD_ISSUES.md`


