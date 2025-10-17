# Speaker Creation 500 Error - Troubleshooting Guide

## Error Details
- **Error Type**: AxiosError
- **Status Code**: 500 (Internal Server Error)
- **Endpoint**: POST /speakers
- **Frontend**: Next.js 15.5.5

## 🔍 Step 1: Check Backend Logs

### If running with Docker:
```bash
# Check if Docker is running
docker ps

# View speaker-service logs
docker logs draft-genie-speaker-service-1 --tail 100 --follow

# Or check all services
docker-compose -f docker/docker-compose.yml logs speaker-service --tail 100
```

### If running locally:
```bash
# Check if the service is running
lsof -i :3001

# If running via npm/yarn, check the terminal where you started it
# Look for error messages in the speaker-service terminal
```

## 🐛 Common Causes & Fixes

### 1. Database Connection Issue (Most Likely)

**Symptoms:**
- 500 error on any database operation
- Error message contains "Prisma" or "database"

**Check:**
```bash
# Verify database is running
docker ps | grep postgres
# OR
psql -h localhost -U draftgenie -d draftgenie -c "SELECT 1;"
```

**Fix:**
```bash
# If using Docker, ensure database is running
cd docker
docker-compose up -d postgres

# Check DATABASE_URL in speaker-service
# Should be: postgresql://draftgenie:draftgenie123@localhost:5432/draftgenie
```

### 2. Database Schema Not Migrated

**Symptoms:**
- Error mentions missing table "speakers"
- Prisma error about schema

**Fix:**
```bash
cd apps/speaker-service

# Run migrations
npx prisma migrate deploy

# Or reset and migrate (WARNING: deletes data)
npx prisma migrate reset
npx prisma migrate dev
```

### 3. RabbitMQ Connection Issue

**Symptoms:**
- Error in event publishing
- "Failed to connect event publisher" in logs

**Note:** This should NOT cause a 500 error because the code catches this error:
```typescript
// In speakers.service.ts line 262-264
catch (error) {
  this.logger.error('Failed to publish SpeakerOnboardedEvent', error);
  // Don't throw - event publishing failure shouldn't fail the operation
}
```

**Fix (if needed):**
```bash
# Start RabbitMQ
docker-compose -f docker/docker-compose.yml up -d rabbitmq

# Check RabbitMQ is running
docker ps | grep rabbitmq
```

### 4. Missing Environment Variables

**Check:**
```bash
cd apps/speaker-service

# Ensure .env file exists
ls -la .env

# If not, copy from example
cp .env.example .env
```

**Required variables:**
```env
DATABASE_URL=postgresql://draftgenie:draftgenie123@localhost:5432/draftgenie
RABBITMQ_URL=amqp://draftgenie:draftgenie123@localhost:5672/
PORT=3001
```

### 5. Validation Error

**Symptoms:**
- Error mentions "validation failed"
- 400 error (not 500)

**Check the request payload:**
The CreateSpeakerDto requires:
- `name`: string (min 2, max 255 characters)
- `bucket`: BucketType enum (EXCELLENT, GOOD, AVERAGE, POOR)
- `email`: valid email (optional)
- `externalId`: string (optional)

**Valid bucket values:**
```typescript
enum BucketType {
  EXCELLENT = 'EXCELLENT',
  GOOD = 'GOOD',
  AVERAGE = 'AVERAGE',
  POOR = 'POOR'
}
```

## 🔧 Quick Fix Commands

### Option 1: Restart Everything (Docker)
```bash
cd docker
docker-compose down
docker-compose up -d
docker-compose logs -f speaker-service
```

### Option 2: Check Service Health
```bash
# Check speaker-service health
curl http://localhost:3001/health

# Check via API Gateway
curl http://localhost:3000/api/v1/health
```

### Option 3: Test Speaker Creation Directly
```bash
# Test directly to speaker-service (bypass API Gateway)
curl -X POST http://localhost:3001/speakers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Speaker",
    "email": "test@example.com",
    "bucket": "GOOD"
  }'
```

## 📋 Debugging Checklist

- [ ] Docker is running (`docker ps` shows containers)
- [ ] PostgreSQL is running and accessible
- [ ] Speaker-service is running on port 3001
- [ ] Database migrations are applied
- [ ] Environment variables are set correctly
- [ ] Backend logs show the actual error message
- [ ] Request payload is valid (correct bucket value, name length, etc.)

## 🎯 Most Likely Solution

Based on the code analysis, the error is most likely:

1. **Database not connected** - Check if PostgreSQL is running
2. **Schema not migrated** - Run `npx prisma migrate deploy`
3. **Wrong bucket value** - Ensure bucket is one of: EXCELLENT, GOOD, AVERAGE, POOR

## 📝 Next Steps

1. **Get the actual error message** from backend logs
2. **Share the error message** for specific diagnosis
3. **Check the request payload** being sent from frontend

## 🔗 Related Files

- Backend Controller: `apps/speaker-service/src/speakers/speakers.controller.ts`
- Backend Service: `apps/speaker-service/src/speakers/speakers.service.ts`
- DTO Validation: `apps/speaker-service/src/speakers/dto/create-speaker.dto.ts`
- Database Schema: `apps/speaker-service/prisma/schema.prisma`

## 💡 Additional Tips

### Enable Debug Logging
```bash
# In apps/speaker-service/.env
LOG_LEVEL=debug
```

### Check Prisma Client
```bash
cd apps/speaker-service
npx prisma generate
```

### Verify Database Connection
```bash
cd apps/speaker-service
npx prisma db pull
```

