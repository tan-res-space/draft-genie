# MongoDB to PostgreSQL Migration - Next Steps

## 🎯 Current Status: Phase 4 Complete ✅

Both **draft-service** and **rag-service** have been successfully migrated from MongoDB to PostgreSQL with database-agnostic design.

---

## 📋 Immediate Next Steps

### **Step 1: Local Testing (Recommended)**

Before deploying to Azure, test the migration locally:

#### 1.1 Set Up Local PostgreSQL
```bash
# Option 1: Using Docker
docker run --name postgres-draftgenie \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=draftgenie \
  -p 5432:5432 \
  -d postgres:15

# Option 2: Use existing PostgreSQL installation
# Create database: CREATE DATABASE draftgenie;
```

#### 1.2 Update Environment Variables
Create/update `.env` files:

**`services/draft-service/.env`**:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/draftgenie
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20
```

**`services/rag-service/.env`**:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/draftgenie
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20
```

#### 1.3 Install Dependencies
```bash
# Draft Service
cd services/draft-service
poetry install
cd ../..

# RAG Service
cd services/rag-service
poetry install
cd ../..
```

#### 1.4 Run Database Migrations
```bash
# Draft Service
cd services/draft-service
poetry run alembic upgrade head
cd ../..

# RAG Service
cd services/rag-service
poetry run alembic upgrade head
cd ../..
```

#### 1.5 Start Services Locally
```bash
# Terminal 1 - Draft Service
cd services/draft-service
poetry run uvicorn app.main:app --reload --port 8002

# Terminal 2 - RAG Service
cd services/rag-service
poetry run uvicorn app.main:app --reload --port 8004
```

#### 1.6 Test Endpoints
```bash
# Draft Service Health Check
curl http://localhost:8002/health
curl http://localhost:8002/health/ready

# RAG Service Health Check
curl http://localhost:8004/health
curl http://localhost:8004/health/ready
```

---

### **Step 2: Update Deployment Configuration**

#### 2.1 Remove MongoDB from Deployment Scripts

**File: `scripts/deploy-azure.py`**
- Remove MongoDB configuration prompts (lines 235-240)
- Remove MongoDB connection string handling

**File: `scripts/azure/config.yaml`**
- Remove MongoDB configuration (lines 31-32)

**File: `scripts/azure/deployer.py`**
- Remove MongoDB Atlas setup instructions (lines 251-261)
- Remove MongoDB secret storage (lines 298-301)
- Remove MongoDB environment variables (lines 493-496)

#### 2.2 Add PostgreSQL Environment Variables

Update deployment scripts to add these environment variables for draft-service and rag-service:

```python
{
    "name": "DATABASE_URL",
    "value": f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_host}:5432/{postgres_db}?sslmode=require"
},
{
    "name": "POSTGRES_POOL_SIZE",
    "value": "10"
},
{
    "name": "POSTGRES_MAX_OVERFLOW",
    "value": "20"
}
```

---

### **Step 3: Azure Deployment**

#### 3.1 Rebuild Docker Images
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

#### 3.2 Update Container Apps
```bash
# Update draft-service
az containerapp update \
  --name draft-service \
  --resource-group rg-dg-backend-v01 \
  --image acrdgbackendv01.azurecr.io/draft-service:latest \
  --set-env-vars \
    DATABASE_URL="postgresql+asyncpg://..." \
    POSTGRES_POOL_SIZE=10 \
    POSTGRES_MAX_OVERFLOW=20

# Update rag-service
az containerapp update \
  --name rag-service \
  --resource-group rg-dg-backend-v01 \
  --image acrdgbackendv01.azurecr.io/rag-service:latest \
  --set-env-vars \
    DATABASE_URL="postgresql+asyncpg://..." \
    POSTGRES_POOL_SIZE=10 \
    POSTGRES_MAX_OVERFLOW=20
```

#### 3.3 Verify Deployment
```bash
# Check draft-service logs
az containerapp logs show \
  --name draft-service \
  --resource-group rg-dg-backend-v01 \
  --follow

# Check rag-service logs
az containerapp logs show \
  --name rag-service \
  --resource-group rg-dg-backend-v01 \
  --follow
```

---

### **Step 4: Database Migration (If Existing Data)**

If you have existing data in MongoDB that needs to be migrated:

#### 4.1 Export from MongoDB
```bash
# Export drafts collection
mongoexport --uri="mongodb+srv://..." --db=draftgenie --collection=drafts --out=drafts.json

# Export correction_vectors collection
mongoexport --uri="mongodb+srv://..." --db=draftgenie --collection=correction_vectors --out=vectors.json

# Export dfns collection
mongoexport --uri="mongodb+srv://..." --db=draftgenie --collection=dfns --out=dfns.json

# Export rag_sessions collection
mongoexport --uri="mongodb+srv://..." --db=draftgenie --collection=rag_sessions --out=sessions.json
```

#### 4.2 Create Migration Script
Create a Python script to import data into PostgreSQL:

```python
# migration_script.py
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import your models and repositories
from app.models.draft_db import Draft, CorrectionVector, DFN, RAGSession
from app.repositories.draft_repository_sql import DraftRepositorySQL
# ... etc

async def migrate_data():
    engine = create_async_engine("postgresql+asyncpg://...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Load and migrate drafts
        with open('drafts.json') as f:
            drafts = json.load(f)
            for draft_data in drafts:
                # Transform and insert
                pass
        
        await session.commit()

asyncio.run(migrate_data())
```

---

## 🧹 Optional Cleanup

After successful deployment and testing:

### Remove Old MongoDB Files
```bash
# Draft Service
rm services/draft-service/app/db/mongodb.py
rm services/draft-service/app/repositories/draft_repository.py
rm services/draft-service/app/repositories/vector_repository.py

# RAG Service
rm services/rag-service/app/db/mongodb.py
rm services/rag-service/app/repositories/dfn_repository.py
rm services/rag-service/app/repositories/rag_session_repository.py
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Draft service health endpoint returns `"postgresql": true`
- [ ] RAG service health endpoint returns `"postgresql": true`
- [ ] Can create new drafts via API
- [ ] Can retrieve drafts via API
- [ ] Can create correction vectors
- [ ] Can generate DFNs via RAG pipeline
- [ ] Can retrieve RAG sessions
- [ ] All existing API contracts work as expected
- [ ] No MongoDB connection errors in logs
- [ ] PostgreSQL connection pool is working

---

## 🚨 Rollback Plan (If Needed)

If issues arise during deployment:

### 1. Revert to Previous Docker Images
```bash
# Use previous image tags
az containerapp update \
  --name draft-service \
  --resource-group rg-dg-backend-v01 \
  --image acrdgbackendv01.azurecr.io/draft-service:previous-tag
```

### 2. Restore MongoDB Configuration
- Re-add MongoDB environment variables
- Revert code changes using git

### 3. Investigate Issues
- Check container logs
- Verify database connectivity
- Test locally first

---

## 📞 Support

If you encounter issues:

1. **Check Logs**: Use `az containerapp logs show` to view container logs
2. **Test Locally**: Reproduce the issue in local environment
3. **Verify Database**: Ensure PostgreSQL is accessible and credentials are correct
4. **Check Dependencies**: Ensure all packages are installed correctly

---

## 🎉 Success Criteria

Migration is successful when:

1. ✅ Both services start without errors
2. ✅ Health checks pass (PostgreSQL connection confirmed)
3. ✅ All API endpoints work as expected
4. ✅ Data can be created, read, updated, and deleted
5. ✅ No MongoDB references in logs
6. ✅ Services are stable for 24+ hours

---

## 📚 Additional Resources

- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Azure Container Apps**: https://learn.microsoft.com/en-us/azure/container-apps/

---

**Last Updated**: 2025-10-16
**Migration Status**: Phase 4 Complete - Ready for Testing & Deployment

