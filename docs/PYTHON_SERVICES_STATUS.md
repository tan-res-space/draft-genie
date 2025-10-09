# Python Services Status Report

**Date:** 2025-10-09  
**Status:** ⚠️ **BLOCKED BY RABBITMQ AUTHENTICATION**

---

## Summary

The Python services (Draft, RAG, Evaluation) are encountering RabbitMQ authentication issues that prevent them from starting. The services are configured to use `draftgenie:draftgenie123` credentials, but RabbitMQ is rejecting these credentials.

---

## Issues Encountered

### 1. MongoDB Boolean Check Issue ✅ FIXED

**Problem:**
```python
if not self.db:  # This doesn't work with PyMongo 4.x+
```

**Error:**
```
NotImplementedError: Database objects do not implement truth value testing or bool(). 
Please compare with None instead: database is not None
```

**Solution Applied:**
```python
if self.db is None:  # Correct way
```

**Files Fixed:**
- `services/draft-service/app/db/mongodb.py`
- `services/rag-service/app/db/mongodb.py`

### 2. Missing Greenlet Dependency ✅ FIXED

**Problem:**
```
ValueError: the greenlet library is required to use this function. No module named 'greenlet'
```

**Solution Applied:**
```bash
cd services/evaluation-service
poetry run pip install greenlet
```

### 3. RabbitMQ Authentication ❌ BLOCKING

**Problem:**
```
aiormq.exceptions.ProbableAuthenticationError: ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN.
```

**Current Configuration:**
- `.env` file: `RABBITMQ_URL=amqp://guest:guest@localhost:5672`
- Python services trying: `amqp://draftgenie:draftgenie123@localhost:5672/`

**Root Cause:**
The Python services are reading RabbitMQ credentials from their own config files, not from the `.env` file in the project root.

---

## Service Status

| Service | Port | Status | Issue |
|---------|------|--------|-------|
| Draft Service | 3002 | ❌ Failed | RabbitMQ auth |
| RAG Service | 3003 | ❌ Failed | RabbitMQ auth |
| Evaluation Service | 3004 | ❌ Failed | RabbitMQ auth + greenlet |

---

## Solutions

### Option 1: Update RabbitMQ Docker Container (RECOMMENDED)

Create a RabbitMQ user with the credentials the services expect:

```bash
# Connect to RabbitMQ container
docker exec -it draft-genie-rabbitmq rabbitmqctl add_user draftgenie draftgenie123

# Set permissions
docker exec -it draft-genie-rabbitmq rabbitmqctl set_permissions -p / draftgenie ".*" ".*" ".*"

# Set user tags
docker exec -it draft-genie-rabbitmq rabbitmqctl set_user_tags draftgenie administrator
```

### Option 2: Update Python Service Configurations

Update the configuration files in each Python service to use `guest:guest`:

**Draft Service:** `services/draft-service/app/config.py`
**RAG Service:** `services/rag-service/app/config.py`
**Evaluation Service:** `services/evaluation-service/app/config.py`

Change:
```python
rabbitmq_url: str = "amqp://draftgenie:draftgenie123@localhost:5672/"
```

To:
```python
rabbitmq_url: str = "amqp://guest:guest@localhost:5672"
```

### Option 3: Make RabbitMQ Connection Optional

Modify the services to continue startup even if RabbitMQ connection fails (for testing purposes):

```python
try:
    await event_publisher.connect()
    logger.info("RabbitMQ connected")
except Exception as e:
    logger.warning(f"RabbitMQ connection failed (non-fatal): {e}")
    # Continue without event publishing
```

---

## Next Steps

1. **Immediate:** Apply Option 1 (create RabbitMQ user)
2. **Restart Python services**
3. **Verify health endpoints**
4. **Run integration tests**

---

## Commands to Fix

```bash
# 1. Create RabbitMQ user
docker exec -it draft-genie-rabbitmq rabbitmqctl add_user draftgenie draftgenie123
docker exec -it draft-genie-rabbitmq rabbitmqctl set_permissions -p / draftgenie ".*" ".*" ".*"
docker exec -it draft-genie-rabbitmq rabbitmqctl set_user_tags draftgenie administrator

# 2. Restart Python services (they should auto-reload, but if not):
# Kill existing processes and restart:
cd services/draft-service && poetry run uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
cd services/rag-service && poetry run uvicorn app.main:app --host 0.0.0.0 --port 3003 --reload
cd services/evaluation-service && poetry run uvicorn app.main:app --host 0.0.0.0 --port 3004 --reload

# 3. Verify services
curl http://localhost:3002/health
curl http://localhost:3003/health
curl http://localhost:3004/health
```

---

## Current Working Services

✅ **Speaker Service** (port 3001) - RUNNING
- Health check: http://localhost:3001/api/v1/health
- API docs: http://localhost:3001/api/docs
- Database: Connected to PostgreSQL
- Status: Fully operational (except RabbitMQ event publishing)

✅ **Infrastructure Services** - ALL RUNNING
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Redis (port 6379)
- RabbitMQ (ports 5672, 15672)
- Qdrant (ports 6333-6334)

---

## Logs

### Draft Service Last Error
```
{"timestamp": "2025-10-09T18:57:55.023255", "level": "ERROR", "logger": "app.events.publisher", "message": "Failed to connect to RabbitMQ: ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN. For details see the broker logfile.", "service": "draft-service", "environment": "development"}
```

### RAG Service Last Error
```
2025-10-10 00:28:08 - app.events.publisher - ERROR - Failed to connect to RabbitMQ: ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN. For details see the broker logfile.
```

### Evaluation Service Last Error
```
{"timestamp": "2025-10-09T18:57:41.752793", "level": "ERROR", "logger": "app.db.database", "message": "Failed to connect to database: the greenlet library is required to use this function. No module named 'greenlet'", "service": "evaluation-service", "environment": "development"}
```

---

## Progress Summary

**Fixed:**
- ✅ MongoDB boolean check issue
- ✅ Greenlet dependency issue

**Remaining:**
- ❌ RabbitMQ authentication (blocking all Python services)

**Estimated Time to Fix:** 5 minutes (create RabbitMQ user)


