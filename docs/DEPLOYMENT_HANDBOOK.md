# DraftGenie Deployment Handbook

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Target Audience:** Developers with beginner-to-intermediate experience

This handbook is the **single source of truth** for all deployment configurations and procedures for the DraftGenie project.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [Docker Container Configuration](#3-docker-container-configuration)
4. [Production Deployment](#4-production-deployment)
5. [Configuration Management](#5-configuration-management)
6. [Quick Reference](#6-quick-reference)

---

## 1. Prerequisites

### 1.1 Required Software

Before you begin, ensure you have the following software installed:

| Software | Minimum Version | Purpose | Installation Guide |
|----------|----------------|---------|-------------------|
| **Node.js** | 20.0.0+ | Runtime for TypeScript services | [nodejs.org](https://nodejs.org/) |
| **npm** | 10.0.0+ | Package manager for Node.js | Comes with Node.js |
| **Docker** | 24.0.0+ | Container runtime | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.20.0+ | Multi-container orchestration | [docker.com](https://docs.docker.com/compose/install/) |
| **Python** | 3.11+ | Runtime for Python services | [python.org](https://www.python.org/downloads/) |
| **Poetry** | 1.7.1+ | Python dependency management | [python-poetry.org](https://python-poetry.org/docs/#installation) |
| **jq** | 1.6+ | JSON processor for scripts | macOS: `brew install jq`<br>Linux: `sudo apt-get install jq` |
| **Git** | 2.0+ | Version control | [git-scm.com](https://git-scm.com/downloads) |

### 1.2 System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free space
- OS: macOS, Linux, or Windows with WSL2

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 50 GB free space (SSD preferred)

### 1.3 Required API Keys and Secrets

#### Google Gemini API Key (Required)

DraftGenie uses Google's Gemini AI for draft generation and improvement.

**How to obtain:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key (starts with `AIza...`)
5. Store it securely - you'll need it for the `.env` file

**Cost:** Free tier available with rate limits. See [Google AI pricing](https://ai.google.dev/pricing) for details.

### 1.4 Verify Prerequisites

Run these commands to verify your setup:

```bash
# Check Node.js version
node --version  # Should be v20.0.0 or higher

# Check npm version
npm --version   # Should be 10.0.0 or higher

# Check Docker version
docker --version  # Should be 24.0.0 or higher

# Check Docker Compose version
docker compose version  # Should be 2.20.0 or higher

# Check Python version
python3 --version  # Should be 3.11.0 or higher

# Check Poetry version
poetry --version  # Should be 1.7.1 or higher

# Check jq version
jq --version  # Should be 1.6 or higher
```

---

## 2. Local Development Setup

### 2.1 Clone the Repository

```bash
# Clone the repository
git clone https://github.com/tan-res-space/draft-genie.git

# Navigate to the project directory
cd draft-genie
```

### 2.2 Install Dependencies

#### Install Node.js Dependencies

```bash
# Install all Node.js dependencies (this may take 5-10 minutes)
npm install
```

This installs dependencies for:
- API Gateway (NestJS)
- Speaker Service (NestJS)
- Shared TypeScript libraries

#### Install Python Dependencies

Each Python service has its own dependencies managed by Poetry:

```bash
# Install Draft Service dependencies
cd services/draft-service
poetry install
cd ../..

# Install RAG Service dependencies
cd services/rag-service
poetry install
cd ../..

# Install Evaluation Service dependencies
cd services/evaluation-service
poetry install
cd ../..
```

**Note:** Poetry will create virtual environments for each service automatically.

### 2.3 Configure Environment Variables

#### Create Docker Environment File

```bash
# Copy the example environment file
cp docker/.env.example docker/.env
```

#### Edit the Environment File

Open `docker/.env` in your text editor and configure the following:

```bash
# REQUIRED: Add your Gemini API key
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Optional: Customize database credentials (defaults are fine for local development)
POSTGRES_USER=draftgenie
POSTGRES_PASSWORD=draftgenie123
POSTGRES_DB=draftgenie

MONGO_USER=draftgenie
MONGO_PASSWORD=draftgenie123
MONGO_DB=draftgenie

REDIS_PASSWORD=draftgenie123

RABBITMQ_USER=draftgenie
RABBITMQ_PASSWORD=draftgenie123

# Optional: Customize JWT secret (default is fine for local development)
JWT_SECRET=draft-genie-secret-change-in-production
```

**⚠️ Security Warning:** The default credentials are for local development only. **Never use these in production!**

### 2.4 Start Docker Infrastructure

Start all infrastructure containers (PostgreSQL, MongoDB, Qdrant, Redis, RabbitMQ):

```bash
# Start all infrastructure services in detached mode
npm run docker:up
```

This command will:
- Pull Docker images (first time only, may take 5-10 minutes)
- Create Docker volumes for data persistence
- Start all infrastructure containers
- Configure health checks

**Verify containers are running:**

```bash
# Check container status
docker ps

# You should see 5 containers running:
# - draft-genie-postgres
# - draft-genie-mongodb
# - draft-genie-qdrant
# - draft-genie-redis
# - draft-genie-rabbitmq
```

**View container logs:**

```bash
# View logs for all containers
npm run docker:logs

# View logs for a specific container
docker logs draft-genie-postgres
docker logs draft-genie-mongodb
```

### 2.5 Initialize Databases

#### Run PostgreSQL Migrations

```bash
# Run Prisma migrations to create database schema
npm run db:migrate
```

This creates the following tables:
- `speakers` - Speaker profiles and metadata
- `evaluations` - Draft evaluation results
- `audit_logs` - Audit trail for changes

#### Seed Mock Data (Optional)

```bash
# Seed the database with sample speakers and data
npm run db:seed
```

This creates:
- 10 sample speakers across different buckets
- Sample evaluation records
- Test data for development

**Note:** MongoDB and Qdrant collections are created automatically by the services on first use.

### 2.6 Start All Services

#### Option 1: Using the Start Script (Recommended)

```bash
# Make the script executable (first time only)
chmod +x scripts/start.sh

# Start all services with dependency management
./scripts/start.sh
```

This script will:
1. ✅ Check all prerequisites
2. ✅ Verify Docker containers are healthy
3. ✅ Start services in the correct order:
   - Speaker Service (port 3001)
   - Draft Service (port 3002)
   - RAG Service (port 3003)
   - Evaluation Service (port 3004)
   - API Gateway (port 3000)
4. ✅ Wait for each service to be healthy before starting the next
5. ✅ Display status of all services

**Service logs are saved to:** `.logs/` directory

#### Option 2: Using npm Scripts

```bash
# Start all services in parallel (less reliable)
npm run dev:all
```

**Note:** This starts all services simultaneously without dependency checks. Use the start script for better reliability.

### 2.7 Verify Setup

#### Check Service Health

```bash
# API Gateway
curl http://localhost:3000/health

# Speaker Service
curl http://localhost:3001/health

# Draft Service
curl http://localhost:3002/health

# RAG Service
curl http://localhost:3003/health

# Evaluation Service
curl http://localhost:3004/health
```

All health checks should return `{"status":"ok"}` or similar.

#### Access Service Documentation

- **API Gateway Swagger UI:** http://localhost:3000/api/docs
- **Speaker Service Swagger UI:** http://localhost:3001/api/docs
- **Draft Service Swagger UI:** http://localhost:3002/docs
- **RAG Service Swagger UI:** http://localhost:3003/docs
- **Evaluation Service Swagger UI:** http://localhost:3004/docs

#### Access Infrastructure UIs

- **RabbitMQ Management:** http://localhost:15672
  - Username: `draftgenie`
  - Password: `draftgenie123`
  
- **Qdrant Dashboard:** http://localhost:6333/dashboard

### 2.8 Stop All Services

```bash
# Make the script executable (first time only)
chmod +x scripts/stop.sh

# Stop all services gracefully
./scripts/stop.sh
```

This will:
1. Stop all microservices
2. Optionally stop Docker infrastructure (you'll be prompted)
3. Clean up PID files

**To stop only Docker infrastructure:**

```bash
npm run docker:down
```

**To stop Docker and remove all data (⚠️ destructive):**

```bash
docker compose -f docker/docker-compose.yml down -v
```

### 2.9 Common Troubleshooting

#### Issue: Port Already in Use

**Symptom:** Error message like `Error: listen EADDRINUSE: address already in use :::3000`

**Solution:**
```bash
# Find process using the port
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use the test-ports script
./scripts/test-ports.sh
```

#### Issue: Docker Containers Not Starting

**Symptom:** Containers exit immediately or show unhealthy status

**Solution:**
```bash
# Check container logs
docker logs draft-genie-postgres

# Restart specific container
docker restart draft-genie-postgres

# Restart all containers
npm run docker:down
npm run docker:up
```

#### Issue: Database Connection Errors

**Symptom:** Services can't connect to PostgreSQL or MongoDB

**Solution:**
```bash
# Verify containers are running
docker ps

# Check if databases are accepting connections
docker exec -it draft-genie-postgres pg_isready -U draftgenie
docker exec -it draft-genie-mongodb mongosh --eval "db.adminCommand('ping')"

# Verify environment variables
cat docker/.env | grep -E "POSTGRES|MONGO"
```

#### Issue: Gemini API Errors

**Symptom:** `401 Unauthorized` or `Invalid API key` errors

**Solution:**
1. Verify your API key in `docker/.env`
2. Check API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Ensure no extra spaces or quotes around the API key
4. Restart the affected services

#### Issue: Poetry Installation Fails

**Symptom:** `poetry: command not found` or dependency installation errors

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version

# Clear Poetry cache and reinstall
cd services/draft-service
poetry cache clear pypi --all
poetry install
```

---

## 3. Docker Container Configuration

This section provides detailed information about each Docker container used in DraftGenie.

### 3.1 PostgreSQL

**Purpose:** Primary relational database for structured data (speakers, evaluations, audit logs)

**Configuration:**

| Property | Value | Description |
|----------|-------|-------------|
| **Image** | `postgres:16-alpine` | Official PostgreSQL 16 Alpine image |
| **Container Name** | `draft-genie-postgres` | Unique container identifier |
| **Port** | `5432:5432` | Host:Container port mapping |
| **Username** | `draftgenie` | Database user (configurable via `.env`) |
| **Password** | `draftgenie123` | Database password (configurable via `.env`) |
| **Database** | `draftgenie` | Default database name |
| **Volume** | `postgres_data:/var/lib/postgresql/data` | Persistent data storage |
| **Health Check** | `pg_isready -U draftgenie` | Checks if database is ready |

**Environment Variables:**
```bash
POSTGRES_USER=draftgenie
POSTGRES_PASSWORD=draftgenie123
POSTGRES_DB=draftgenie
POSTGRES_PORT=5432
```

**Connection String:**
```
postgresql://draftgenie:draftgenie123@localhost:5432/draftgenie
```

**Used By:**
- Speaker Service (via Prisma ORM)
- Evaluation Service (via SQLAlchemy)

**Data Persistence:**
- Data is stored in Docker volume `postgres_data`
- Survives container restarts
- Removed only with `docker compose down -v`

**Access Database:**
```bash
# Using psql inside container
docker exec -it draft-genie-postgres psql -U draftgenie -d draftgenie

# Using psql from host (if installed)
psql -h localhost -U draftgenie -d draftgenie
```

### 3.2 MongoDB

**Purpose:** Document database for unstructured/semi-structured data (drafts, RAG context, embeddings)

**Configuration:**

| Property | Value | Description |
|----------|-------|-------------|
| **Image** | `mongo:7` | Official MongoDB 7 image |
| **Container Name** | `draft-genie-mongodb` | Unique container identifier |
| **Port** | `27017:27017` | Host:Container port mapping |
| **Username** | `draftgenie` | Root user (configurable via `.env`) |
| **Password** | `draftgenie123` | Root password (configurable via `.env`) |
| **Database** | `draftgenie` | Default database name |
| **Volume** | `mongodb_data:/data/db` | Persistent data storage |
| **Health Check** | `mongosh ping` | Checks if database is ready |

**Environment Variables:**
```bash
MONGO_USER=draftgenie
MONGO_PASSWORD=draftgenie123
MONGO_DB=draftgenie
MONGO_PORT=27017
```

**Connection String:**
```
mongodb://draftgenie:draftgenie123@localhost:27017/draftgenie?authSource=admin
```

**Used By:**
- Draft Service (via Motor - async MongoDB driver)
- RAG Service (via Motor)

**Collections (Auto-created):**
- `drafts` - Speaker draft documents
- `rag_contexts` - RAG retrieval contexts
- `correction_vectors_metadata` - Vector metadata

**Access Database:**
```bash
# Using mongosh inside container
docker exec -it draft-genie-mongodb mongosh -u draftgenie -p draftgenie123

# List databases
docker exec -it draft-genie-mongodb mongosh -u draftgenie -p draftgenie123 --eval "show dbs"

# Query drafts collection
docker exec -it draft-genie-mongodb mongosh -u draftgenie -p draftgenie123 draftgenie --eval "db.drafts.find().limit(5)"
```

### 3.3 Qdrant

**Purpose:** Vector database for storing and searching correction vectors (embeddings)

**Configuration:**

| Property | Value | Description |
|----------|-------|-------------|
| **Image** | `qdrant/qdrant:v1.7.4` | Official Qdrant 1.7.4 image |
| **Container Name** | `draft-genie-qdrant` | Unique container identifier |
| **HTTP Port** | `6333:6333` | REST API port |
| **gRPC Port** | `6334:6334` | gRPC API port (optional) |
| **Volume** | `qdrant_data:/qdrant/storage` | Persistent vector storage |
| **Health Check** | `curl http://localhost:6333/healthz` | Checks if service is ready |

**Environment Variables:**
```bash
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_URL=http://localhost:6333
```

**Used By:**
- Draft Service (stores correction vectors)
- RAG Service (retrieves similar correction patterns)

**Collections (Auto-created):**
- `correction_vectors` - 768-dimensional embeddings from Gemini

**Access Dashboard:**
- Web UI: http://localhost:6333/dashboard
- API Docs: http://localhost:6333/docs

**API Examples:**
```bash
# List collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/correction_vectors

# Search vectors (example)
curl -X POST http://localhost:6333/collections/correction_vectors/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 5}'
```

### 3.4 Redis

**Purpose:** In-memory cache for session management, rate limiting, and temporary data

**Configuration:**

| Property | Value | Description |
|----------|-------|-------------|
| **Image** | `redis:7-alpine` | Official Redis 7 Alpine image |
| **Container Name** | `draft-genie-redis` | Unique container identifier |
| **Port** | `6379:6379` | Host:Container port mapping |
| **Password** | `draftgenie123` | Redis password (configurable via `.env`) |
| **Volume** | `redis_data:/data` | Persistent cache storage |
| **Persistence** | AOF (Append-Only File) | Enabled for data durability |
| **Health Check** | `redis-cli ping` | Checks if service is ready |

**Environment Variables:**
```bash
REDIS_PORT=6379
REDIS_PASSWORD=draftgenie123
REDIS_URL=redis://:draftgenie123@localhost:6379
```

**Connection String:**
```
redis://:draftgenie123@localhost:6379
```

**Used By:**
- All services (caching, session management)
- API Gateway (rate limiting, JWT token blacklist)

**Access Redis CLI:**
```bash
# Using redis-cli inside container
docker exec -it draft-genie-redis redis-cli -a draftgenie123

# Common commands
docker exec -it draft-genie-redis redis-cli -a draftgenie123 PING
docker exec -it draft-genie-redis redis-cli -a draftgenie123 INFO
docker exec -it draft-genie-redis redis-cli -a draftgenie123 KEYS '*'
docker exec -it draft-genie-redis redis-cli -a draftgenie123 GET some_key
```

### 3.5 RabbitMQ

**Purpose:** Message broker for event-driven architecture and inter-service communication

**Configuration:**

| Property | Value | Description |
|----------|-------|-------------|
| **Image** | `rabbitmq:3.13-management-alpine` | Official RabbitMQ with management UI |
| **Container Name** | `draft-genie-rabbitmq` | Unique container identifier |
| **AMQP Port** | `5672:5672` | Message broker port |
| **Management Port** | `15672:15672` | Web management UI port |
| **Username** | `draftgenie` | RabbitMQ user (configurable via `.env`) |
| **Password** | `draftgenie123` | RabbitMQ password (configurable via `.env`) |
| **Virtual Host** | `/` | Default vhost |
| **Volume** | `rabbitmq_data:/var/lib/rabbitmq` | Persistent message storage |
| **Health Check** | `rabbitmq-diagnostics ping` | Checks if service is ready |

**Environment Variables:**
```bash
RABBITMQ_USER=draftgenie
RABBITMQ_PASSWORD=draftgenie123
RABBITMQ_VHOST=/
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672
```

**Connection String:**
```
amqp://draftgenie:draftgenie123@localhost:5672/
```

**Pre-configured Exchanges and Queues:**

The system uses a topic exchange for event routing:

| Component | Name | Type | Purpose |
|-----------|------|------|---------|
| **Exchange** | `draft-genie.events` | topic | Main event exchange |
| **Queue** | `speaker.events` | quorum | Speaker service events |
| **Queue** | `draft.events` | quorum | Draft service events |
| **Queue** | `rag.events` | quorum | RAG service events |
| **Queue** | `evaluation.events` | quorum | Evaluation service events |

**Routing Keys:**
- `speaker.*` → `speaker.events` queue
- `draft.*` → `draft.events` queue
- `rag.*` → `rag.events` queue
- `evaluation.*` → `evaluation.events` queue

**Access Management UI:**
- URL: http://localhost:15672
- Username: `draftgenie`
- Password: `draftgenie123`

**Management UI Features:**
- View queues, exchanges, and bindings
- Monitor message rates and throughput
- Publish test messages
- View connections and channels
- Configure policies and parameters

### 3.6 Docker Compose Configuration

**File Location:** `docker/docker-compose.yml`

**Network Configuration:**
- Network Name: `draft-genie-network`
- Driver: `bridge`
- All containers are on the same network for inter-service communication

**Volume Configuration:**

All data is persisted in named Docker volumes:

```bash
# List volumes
docker volume ls | grep draft-genie

# Inspect a volume
docker volume inspect draft-genie_postgres_data

# Backup a volume (example for PostgreSQL)
docker run --rm -v draft-genie_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore a volume
docker run --rm -v draft-genie_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

**Health Checks:**

All containers have health checks configured:
- **Interval:** 10 seconds
- **Timeout:** 5 seconds
- **Retries:** 5
- **Start Period:** Varies by service (10-40 seconds)

**Restart Policy:**
- All containers: `unless-stopped`
- Containers restart automatically unless explicitly stopped

**Resource Limits (Production):**

For production, add resource limits to `docker-compose.yml`:

```yaml
services:
  postgres:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 4. Production Deployment

### 4.1 Cloud-Agnostic Deployment Strategy

DraftGenie is designed to be cloud-agnostic and can be deployed on any platform that supports Docker containers.

**Deployment Options:**

1. **Docker Compose** (Single server, small-scale)
2. **Kubernetes** (Multi-server, scalable)
3. **Cloud Container Services** (AWS ECS, Google Cloud Run, Azure Container Instances)
4. **Platform-as-a-Service** (Heroku, Railway, Render)

### 4.2 Environment-Specific Configuration

#### Development vs. Production Differences

| Configuration | Development | Production |
|--------------|-------------|------------|
| **NODE_ENV** | `development` | `production` |
| **Log Level** | `debug` | `info` or `warn` |
| **Database Passwords** | Simple (e.g., `draftgenie123`) | Strong, randomly generated |
| **JWT Secret** | Default | Strong, randomly generated (32+ chars) |
| **CORS Origin** | `*` (allow all) | Specific domain(s) |
| **Rate Limiting** | Relaxed | Strict |
| **Swagger Docs** | Enabled | Disabled or protected |
| **SSL/TLS** | Not required | Required |
| **Database Connections** | Direct | Connection pooling |
| **Replicas** | 1 per service | Multiple per service |

### 4.3 Security Considerations

#### Secrets Management

**Never commit secrets to version control!**

**Development:**
- Use `.env` files (excluded from Git via `.gitignore`)
- Store API keys locally

**Production Options:**

1. **Environment Variables** (Basic)
   ```bash
   export GEMINI_API_KEY="your-key"
   export JWT_SECRET="your-secret"
   ```

2. **Docker Secrets** (Docker Swarm)
   ```bash
   echo "your-secret" | docker secret create jwt_secret -
   ```

3. **Kubernetes Secrets**
   ```bash
   kubectl create secret generic draft-genie-secrets \
     --from-literal=gemini-api-key=your-key \
     --from-literal=jwt-secret=your-secret
   ```

4. **Cloud Secret Managers** (Recommended)
   - AWS Secrets Manager
   - Google Cloud Secret Manager
   - Azure Key Vault
   - HashiCorp Vault

**Example using AWS Secrets Manager:**

```bash
# Store secret
aws secretsmanager create-secret \
  --name draft-genie/gemini-api-key \
  --secret-string "your-api-key"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id draft-genie/gemini-api-key \
  --query SecretString \
  --output text
```

#### Credential Rotation

**Best Practices:**
1. Rotate database passwords every 90 days
2. Rotate API keys every 180 days
3. Rotate JWT secrets every 365 days
4. Use automated rotation where possible

**Rotation Procedure:**
1. Generate new credentials
2. Update secrets in secret manager
3. Deploy updated configuration
4. Verify services are working
5. Revoke old credentials

#### Network Security

**Production Checklist:**
- [ ] Use HTTPS/TLS for all external communication
- [ ] Restrict database access to application servers only
- [ ] Use VPC/private networks for inter-service communication
- [ ] Enable firewall rules (allow only necessary ports)
- [ ] Use API Gateway for external access (don't expose services directly)
- [ ] Implement rate limiting and DDoS protection
- [ ] Enable audit logging for all access

### 4.4 Database Backup and Restore

#### PostgreSQL Backup

**Manual Backup:**
```bash
# Backup to file
docker exec draft-genie-postgres pg_dump -U draftgenie draftgenie > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec draft-genie-postgres pg_dump -U draftgenie draftgenie | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Automated Backup (Cron):**
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * docker exec draft-genie-postgres pg_dump -U draftgenie draftgenie | gzip > /backups/postgres_$(date +\%Y\%m\%d).sql.gz

# Keep only last 30 days
0 3 * * * find /backups -name "postgres_*.sql.gz" -mtime +30 -delete
```

**Restore:**
```bash
# Restore from uncompressed backup
docker exec -i draft-genie-postgres psql -U draftgenie draftgenie < backup_20251006_120000.sql

# Restore from compressed backup
gunzip -c backup_20251006_120000.sql.gz | docker exec -i draft-genie-postgres psql -U draftgenie draftgenie
```

#### MongoDB Backup

**Manual Backup:**
```bash
# Backup entire database
docker exec draft-genie-mongodb mongodump \
  --username=draftgenie \
  --password=draftgenie123 \
  --authenticationDatabase=admin \
  --db=draftgenie \
  --out=/tmp/backup

# Copy backup from container
docker cp draft-genie-mongodb:/tmp/backup ./mongodb_backup_$(date +%Y%m%d_%H%M%S)
```

**Automated Backup (Cron):**
```bash
# Add to crontab (daily at 2:30 AM)
30 2 * * * docker exec draft-genie-mongodb mongodump --username=draftgenie --password=draftgenie123 --authenticationDatabase=admin --db=draftgenie --out=/tmp/backup && docker cp draft-genie-mongodb:/tmp/backup /backups/mongodb_$(date +\%Y\%m\%d)
```

**Restore:**
```bash
# Copy backup to container
docker cp ./mongodb_backup_20251006 draft-genie-mongodb:/tmp/restore

# Restore database
docker exec draft-genie-mongodb mongorestore \
  --username=draftgenie \
  --password=draftgenie123 \
  --authenticationDatabase=admin \
  --db=draftgenie \
  /tmp/restore/draftgenie
```

#### Qdrant Backup

**Manual Backup:**
```bash
# Create snapshot via API
curl -X POST http://localhost:6333/collections/correction_vectors/snapshots

# Download snapshot
curl http://localhost:6333/collections/correction_vectors/snapshots/{snapshot_name} -o qdrant_backup.snapshot

# Or backup the entire data directory
docker run --rm -v draft-genie_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup_$(date +%Y%m%d).tar.gz /data
```

**Restore:**
```bash
# Restore via API
curl -X PUT http://localhost:6333/collections/correction_vectors/snapshots/upload \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@qdrant_backup.snapshot"

# Or restore data directory
docker run --rm -v draft-genie_qdrant_data:/data -v $(pwd):/backup alpine tar xzf /backup/qdrant_backup_20251006.tar.gz -C /
```

### 4.5 Scaling Considerations

#### Horizontal Scaling

**Stateless Services (Can scale horizontally):**
- API Gateway
- Draft Service
- RAG Service
- Evaluation Service

**Stateful Services (Require special handling):**
- Speaker Service (uses PostgreSQL - can scale with read replicas)

**Scaling with Docker Compose:**
```bash
# Scale a service to 3 replicas
docker compose up -d --scale draft-service=3 --scale rag-service=3
```

**Scaling with Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: draft-service
spec:
  replicas: 3  # Scale to 3 pods
  # ... rest of config
```

#### Database Scaling

**PostgreSQL:**
- **Vertical Scaling:** Increase CPU/RAM
- **Read Replicas:** For read-heavy workloads
- **Connection Pooling:** Use PgBouncer
- **Partitioning:** For large tables

**MongoDB:**
- **Vertical Scaling:** Increase CPU/RAM
- **Sharding:** For horizontal scaling
- **Replica Sets:** For high availability
- **Indexes:** Optimize query performance

**Qdrant:**
- **Vertical Scaling:** Increase RAM (vectors stored in memory)
- **Sharding:** Distribute collections across nodes
- **Replication:** For high availability

**Redis:**
- **Vertical Scaling:** Increase RAM
- **Redis Cluster:** For horizontal scaling
- **Redis Sentinel:** For high availability

#### Load Balancing

**For multiple service instances:**

```nginx
# Nginx configuration example
upstream draft_service {
    server draft-service-1:3002;
    server draft-service-2:3002;
    server draft-service-3:3002;
}

server {
    listen 80;
    location / {
        proxy_pass http://draft_service;
    }
}
```

### 4.6 Health Checks and Monitoring

#### Service Health Endpoints

All services expose health check endpoints:

```bash
# API Gateway
curl http://localhost:3000/health
# Response: {"status":"ok","timestamp":"2025-10-10T12:00:00Z"}

# Speaker Service
curl http://localhost:3001/health
# Response: {"status":"ok","database":"connected"}

# Draft Service
curl http://localhost:3002/health
# Response: {"status":"healthy","mongodb":"connected","qdrant":"connected"}

# RAG Service
curl http://localhost:3003/health
# Response: {"status":"healthy","dependencies":{"mongodb":"ok","qdrant":"ok"}}

# Evaluation Service
curl http://localhost:3004/health
# Response: {"status":"healthy","database":"connected"}
```

#### Monitoring Setup

**Recommended Tools:**

1. **Prometheus + Grafana** (Metrics)
   - Collect metrics from all services
   - Visualize dashboards
   - Set up alerts

2. **ELK Stack** (Logs)
   - Elasticsearch: Store logs
   - Logstash: Process logs
   - Kibana: Visualize logs

3. **Jaeger** (Distributed Tracing)
   - Trace requests across services
   - Identify bottlenecks

**Basic Monitoring with Docker:**

```bash
# Monitor container resource usage
docker stats

# Monitor specific containers
docker stats draft-genie-postgres draft-genie-mongodb

# View container logs
docker logs -f draft-genie-api-gateway

# View logs with timestamps
docker logs -f --timestamps draft-genie-api-gateway
```

#### Alerting

**Key Metrics to Monitor:**

| Metric | Warning Threshold | Critical Threshold |
|--------|------------------|-------------------|
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 80% | > 90% |
| Response Time | > 1s | > 3s |
| Error Rate | > 1% | > 5% |
| Database Connections | > 80% of max | > 95% of max |

**Example Alert Configuration (Prometheus):**

```yaml
groups:
  - name: draft-genie-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 0.05)"
```

### 4.7 CI/CD Pipeline Overview

While DraftGenie doesn't currently have a CI/CD pipeline configured, here's a recommended setup:

#### Recommended Pipeline Stages

1. **Build Stage**
   - Install dependencies
   - Build TypeScript services
   - Build Docker images

2. **Test Stage**
   - Run unit tests
   - Run integration tests
   - Generate coverage reports

3. **Security Stage**
   - Scan dependencies for vulnerabilities
   - Scan Docker images
   - Run SAST (Static Application Security Testing)

4. **Deploy Stage**
   - Push Docker images to registry
   - Deploy to staging environment
   - Run smoke tests
   - Deploy to production (manual approval)

#### Example GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build services
        run: npm run build

      - name: Build Docker images
        run: docker compose build

      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker compose push
```

---

## 5. Configuration Management

### 5.1 Environment Variables Reference

#### Global Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `NODE_ENV` | Node.js environment | `development` | No | `production` |
| `ENVIRONMENT` | Application environment | `development` | No | `production` |
| `LOG_LEVEL` | Logging level | `info` | No | `debug`, `info`, `warn`, `error` |

#### API Gateway Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `PORT` | Server port | `3000` | No | `3000` |
| `JWT_SECRET` | JWT signing secret | `draft-genie-secret-change-in-production` | **Yes** | `your-super-secret-key-min-32-chars` |
| `JWT_EXPIRES_IN` | JWT expiration time | `24h` | No | `1d`, `7d`, `30d` |
| `API_KEYS` | Service API keys (comma-separated) | `service-key-1,service-key-2` | **Yes** | `key1,key2,key3` |
| `CORS_ORIGIN` | Allowed CORS origins | `*` | No | `https://yourdomain.com` |
| `THROTTLE_TTL` | Rate limit window (ms) | `60000` | No | `60000` (1 minute) |
| `THROTTLE_LIMIT` | Max requests per window | `100` | No | `100` |
| `SWAGGER_ENABLED` | Enable Swagger docs | `true` | No | `true`, `false` |
| `SWAGGER_PATH` | Swagger UI path | `api/docs` | No | `api/docs` |
| `SPEAKER_SERVICE_URL` | Speaker service URL | `http://localhost:3001` | **Yes** | `http://speaker-service:3001` |
| `DRAFT_SERVICE_URL` | Draft service URL | `http://localhost:3002` | **Yes** | `http://draft-service:3002` |
| `RAG_SERVICE_URL` | RAG service URL | `http://localhost:3003` | **Yes** | `http://rag-service:3003` |
| `EVALUATION_SERVICE_URL` | Evaluation service URL | `http://localhost:3004` | **Yes** | `http://evaluation-service:3004` |

#### PostgreSQL Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `POSTGRES_USER` | Database username | `draftgenie` | **Yes** | `draftgenie` |
| `POSTGRES_PASSWORD` | Database password | `draftgenie123` | **Yes** | `your-secure-password` |
| `POSTGRES_DB` | Database name | `draftgenie` | **Yes** | `draftgenie` |
| `POSTGRES_PORT` | Database port | `5432` | No | `5432` |
| `DATABASE_URL` | Full connection string | (constructed) | **Yes** | `postgresql://user:pass@host:5432/db` |

#### MongoDB Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `MONGO_USER` | Database username | `draftgenie` | **Yes** | `draftgenie` |
| `MONGO_PASSWORD` | Database password | `draftgenie123` | **Yes** | `your-secure-password` |
| `MONGO_DB` | Database name | `draftgenie` | **Yes** | `draftgenie` |
| `MONGO_PORT` | Database port | `27017` | No | `27017` |
| `MONGODB_URL` | Full connection string | (constructed) | **Yes** | `mongodb://user:pass@host:27017/db?authSource=admin` |

#### Qdrant Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` | **Yes** | `http://qdrant:6333` |
| `QDRANT_PORT` | HTTP API port | `6333` | No | `6333` |
| `QDRANT_GRPC_PORT` | gRPC API port | `6334` | No | `6334` |
| `QDRANT_API_KEY` | API key (if enabled) | (none) | No | `your-api-key` |
| `QDRANT_COLLECTION_NAME` | Collection name | `correction_vectors` | No | `correction_vectors` |
| `QDRANT_VECTOR_SIZE` | Vector dimensions | `768` | No | `768` |

#### Redis Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `REDIS_URL` | Redis connection URL | `redis://:password@localhost:6379` | **Yes** | `redis://:pass@redis:6379` |
| `REDIS_PORT` | Redis port | `6379` | No | `6379` |
| `REDIS_PASSWORD` | Redis password | `draftgenie123` | **Yes** | `your-secure-password` |

#### RabbitMQ Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `RABBITMQ_URL` | RabbitMQ connection URL | `amqp://user:pass@localhost:5672/` | **Yes** | `amqp://user:pass@rabbitmq:5672/` |
| `RABBITMQ_USER` | RabbitMQ username | `draftgenie` | **Yes** | `draftgenie` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `draftgenie123` | **Yes** | `your-secure-password` |
| `RABBITMQ_VHOST` | Virtual host | `/` | No | `/` |
| `RABBITMQ_PORT` | AMQP port | `5672` | No | `5672` |
| `RABBITMQ_MANAGEMENT_PORT` | Management UI port | `15672` | No | `15672` |
| `RABBITMQ_EXCHANGE` | Exchange name | `draft-genie.events` | No | `draft-genie.events` |

#### AI Service Environment Variables

| Variable | Description | Default | Required | Example |
|----------|-------------|---------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | (none) | **Yes** | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini model name | `models/embedding-001` | No | `models/embedding-001` |
| `GEMINI_EMBEDDING_DIMENSION` | Embedding dimensions | `768` | No | `768` |

### 5.2 Configuration File Locations

#### Project Root Configuration

| File | Purpose | Format |
|------|---------|--------|
| `config/ports.json` | **Port configuration (SSOT)** | JSON |
| `docker/.env` | Docker infrastructure environment variables | ENV |
| `package.json` | Node.js dependencies and scripts | JSON |
| `nx.json` | NX monorepo configuration | JSON |
| `tsconfig.json` | TypeScript compiler configuration | JSON |

#### Service-Specific Configuration

**Speaker Service:**
- `apps/speaker-service/.env.example` - Environment template
- `apps/speaker-service/prisma/schema.prisma` - Database schema
- `apps/speaker-service/src/config/` - Application configuration

**Draft Service:**
- `services/draft-service/.env.example` - Environment template
- `services/draft-service/pyproject.toml` - Python dependencies
- `services/draft-service/app/core/config.py` - Application settings

**RAG Service:**
- `services/rag-service/.env.example` - Environment template
- `services/rag-service/pyproject.toml` - Python dependencies
- `services/rag-service/app/core/config.py` - Application settings

**Evaluation Service:**
- `services/evaluation-service/.env.example` - Environment template
- `services/evaluation-service/pyproject.toml` - Python dependencies
- `services/evaluation-service/app/core/config.py` - Application settings

**API Gateway:**
- `services/api-gateway/.env.example` - Environment template
- `services/api-gateway/src/config/` - Application configuration

#### Docker Configuration

| File | Purpose |
|------|---------|
| `docker/docker-compose.yml` | Main Docker Compose configuration |
| `docker/.env` | Docker environment variables |
| `docker/.env.example` | Environment template |
| `docker/Dockerfile.base` | Base Docker image |
| `docker/Dockerfile.api-gateway` | API Gateway image |
| `docker/Dockerfile.speaker-service` | Speaker Service image |
| `docker/Dockerfile.draft-service` | Draft Service image |
| `docker/Dockerfile.rag-service` | RAG Service image |
| `docker/Dockerfile.evaluation-service` | Evaluation Service image |
| `docker/rabbitmq/rabbitmq.conf` | RabbitMQ configuration |
| `docker/rabbitmq/definitions.json` | RabbitMQ queues/exchanges |

### 5.3 Overriding Default Configurations

#### Port Configuration

**To change service ports:**

1. Edit `config/ports.json`:
   ```json
   {
     "services": {
       "api-gateway": {
         "port": 8080,  // Changed from 3000
         "description": "API Gateway - Main entry point"
       }
     }
   }
   ```

2. Restart the service:
   ```bash
   ./scripts/stop.sh
   ./scripts/start.sh
   ```

**Note:** Services read ports from this file at startup. No need to update individual service configs.

#### Environment-Specific Overrides

**Using environment variables (highest priority):**
```bash
# Override port via environment variable
export PORT=8080
npm run dev:gateway
```

**Using .env files (medium priority):**
```bash
# In docker/.env or service-specific .env
PORT=8080
```

**Using config files (lowest priority):**
```json
// In config/ports.json
{"services": {"api-gateway": {"port": 8080}}}
```

**Priority order:** Environment Variables > .env Files > Config Files > Defaults

#### Docker Compose Overrides

**For local development customizations:**

Create `docker/docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  postgres:
    ports:
      - '5433:5432'  # Use different host port
    environment:
      POSTGRES_PASSWORD: my-custom-password

  api-gateway:
    environment:
      LOG_LEVEL: debug  # Override log level
```

**Apply overrides:**
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
```

**Note:** `docker-compose.override.yml` is automatically loaded if present and excluded from Git.

---

## 6. Quick Reference

### 6.1 Common Commands Cheat Sheet

#### Service Management

```bash
# Start all services
./scripts/start.sh

# Stop all services
./scripts/stop.sh

# Start only Docker infrastructure
npm run docker:up

# Stop Docker infrastructure
npm run docker:down

# View all Docker logs
npm run docker:logs

# View specific service logs
docker logs -f draft-genie-api-gateway
docker logs -f draft-genie-postgres

# Restart a specific service
docker restart draft-genie-postgres

# Check service status
docker ps
```

#### Database Operations

```bash
# PostgreSQL - Run migrations
npm run db:migrate

# PostgreSQL - Seed data
npm run db:seed

# PostgreSQL - Access database
docker exec -it draft-genie-postgres psql -U draftgenie -d draftgenie

# PostgreSQL - Backup
docker exec draft-genie-postgres pg_dump -U draftgenie draftgenie > backup.sql

# PostgreSQL - Restore
docker exec -i draft-genie-postgres psql -U draftgenie draftgenie < backup.sql

# MongoDB - Access database
docker exec -it draft-genie-mongodb mongosh -u draftgenie -p draftgenie123

# MongoDB - Backup
docker exec draft-genie-mongodb mongodump -u draftgenie -p draftgenie123 --authenticationDatabase=admin --db=draftgenie --out=/tmp/backup

# MongoDB - Restore
docker exec draft-genie-mongodb mongorestore -u draftgenie -p draftgenie123 --authenticationDatabase=admin --db=draftgenie /tmp/backup/draftgenie

# Redis - Access CLI
docker exec -it draft-genie-redis redis-cli -a draftgenie123

# Redis - Clear cache
docker exec -it draft-genie-redis redis-cli -a draftgenie123 FLUSHALL
```

#### Development

```bash
# Install dependencies
npm install

# Install Python dependencies
cd services/draft-service && poetry install && cd ../..
cd services/rag-service && poetry install && cd ../..
cd services/evaluation-service && poetry install && cd ../..

# Run tests
npm test

# Run tests with coverage
npm run test:cov

# Lint code
npm run lint

# Format code
npm run format

# Build all services
npm run build

# Start individual services
npm run dev:gateway      # API Gateway
npm run dev:speaker      # Speaker Service
npm run dev:draft        # Draft Service (requires Poetry)
npm run dev:rag          # RAG Service (requires Poetry)
```

#### Docker Management

```bash
# Build all images
docker compose -f docker/docker-compose.yml build

# Build specific service
docker compose -f docker/docker-compose.yml build api-gateway

# Pull latest images
docker compose -f docker/docker-compose.yml pull

# Remove all containers and volumes (⚠️ destructive)
docker compose -f docker/docker-compose.yml down -v

# View resource usage
docker stats

# Clean up unused resources
docker system prune -a

# View volumes
docker volume ls

# Remove specific volume
docker volume rm draft-genie_postgres_data
```

#### Troubleshooting

```bash
# Check port availability
lsof -i :3000
lsof -i :5432

# Kill process on port
kill -9 $(lsof -t -i:3000)

# Test port configuration
./scripts/test-ports.sh

# View service health
curl http://localhost:3000/health
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
curl http://localhost:3004/health

# Check Docker network
docker network ls
docker network inspect draft-genie_draft-genie-network

# Check container health
docker inspect --format='{{.State.Health.Status}}' draft-genie-postgres

# View container environment variables
docker exec draft-genie-api-gateway env
```

### 6.2 Service URLs and Ports Reference

#### Application Services

| Service | Port | URL | Health Check | Swagger Docs |
|---------|------|-----|--------------|--------------|
| **API Gateway** | 3000 | http://localhost:3000 | http://localhost:3000/health | http://localhost:3000/api/docs |
| **Speaker Service** | 3001 | http://localhost:3001 | http://localhost:3001/health | http://localhost:3001/api/docs |
| **Draft Service** | 3002 | http://localhost:3002 | http://localhost:3002/health | http://localhost:3002/docs |
| **RAG Service** | 3003 | http://localhost:3003 | http://localhost:3003/health | http://localhost:3003/docs |
| **Evaluation Service** | 3004 | http://localhost:3004 | http://localhost:3004/health | http://localhost:3004/docs |

#### Infrastructure Services

| Service | Port(s) | URL | Credentials | Purpose |
|---------|---------|-----|-------------|---------|
| **PostgreSQL** | 5432 | postgresql://localhost:5432 | User: `draftgenie`<br>Pass: `draftgenie123` | Relational database |
| **MongoDB** | 27017 | mongodb://localhost:27017 | User: `draftgenie`<br>Pass: `draftgenie123` | Document database |
| **Qdrant** | 6333, 6334 | http://localhost:6333 | None (default) | Vector database |
| **Redis** | 6379 | redis://localhost:6379 | Pass: `draftgenie123` | Cache & sessions |
| **RabbitMQ** | 5672, 15672 | http://localhost:15672 | User: `draftgenie`<br>Pass: `draftgenie123` | Message broker |

#### Management UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **RabbitMQ Management** | http://localhost:15672 | User: `draftgenie`<br>Pass: `draftgenie123` |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | None |
| **API Documentation** | http://localhost:3000/api/docs | None (or API key) |

### 6.3 Links to Additional Resources

#### Official Documentation

- **DraftGenie System Architecture:** [docs/system_architecture_and_implementation_plan.md](./system_architecture_and_implementation_plan.md)
- **Getting Started Guide:** [GETTING_STARTED.md](../GETTING_STARTED.md)
- **Service Management Guide:** [docs/SERVICE_MANAGEMENT.md](./SERVICE_MANAGEMENT.md)
- **Manual Testing Guide:** [docs/MANUAL_TESTING_GUIDE.md](./MANUAL_TESTING_GUIDE.md)
- **Event Infrastructure Guide:** [docs/EVENT_INFRASTRUCTURE_GUIDE.md](./EVENT_INFRASTRUCTURE_GUIDE.md)

#### Technology Documentation

- **Node.js:** https://nodejs.org/docs/
- **NestJS:** https://docs.nestjs.com/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Prisma:** https://www.prisma.io/docs/
- **Docker:** https://docs.docker.com/
- **Docker Compose:** https://docs.docker.com/compose/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **MongoDB:** https://www.mongodb.com/docs/
- **Qdrant:** https://qdrant.tech/documentation/
- **Redis:** https://redis.io/documentation
- **RabbitMQ:** https://www.rabbitmq.com/documentation.html
- **Google Gemini AI:** https://ai.google.dev/docs
- **LangChain:** https://python.langchain.com/docs/
- **Poetry:** https://python-poetry.org/docs/

#### Community & Support

- **GitHub Repository:** https://github.com/tan-res-space/draft-genie
- **Issue Tracker:** https://github.com/tan-res-space/draft-genie/issues
- **Discussions:** https://github.com/tan-res-space/draft-genie/discussions

---

## Appendix A: Environment File Templates

### docker/.env (Complete Template)

```bash
# ============================================
# DraftGenie Environment Configuration
# ============================================

# Environment
NODE_ENV=development
ENVIRONMENT=development

# ============================================
# PostgreSQL Configuration
# ============================================
POSTGRES_USER=draftgenie
POSTGRES_PASSWORD=draftgenie123
POSTGRES_DB=draftgenie
POSTGRES_PORT=5432

# ============================================
# MongoDB Configuration
# ============================================
MONGO_USER=draftgenie
MONGO_PASSWORD=draftgenie123
MONGO_DB=draftgenie
MONGO_PORT=27017

# ============================================
# Qdrant Configuration
# ============================================
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334

# ============================================
# Redis Configuration
# ============================================
REDIS_PORT=6379
REDIS_PASSWORD=draftgenie123

# ============================================
# RabbitMQ Configuration
# ============================================
RABBITMQ_USER=draftgenie
RABBITMQ_PASSWORD=draftgenie123
RABBITMQ_VHOST=/
RABBITMQ_PORT=5672
RABBITMQ_MANAGEMENT_PORT=15672

# ============================================
# Gemini API Configuration
# ============================================
# REQUIRED: Get your API key from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# ============================================
# JWT Configuration
# ============================================
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=24h

# ============================================
# API Gateway Configuration
# ============================================
API_KEYS=service-key-1,service-key-2
CORS_ORIGIN=*
THROTTLE_TTL=60000
THROTTLE_LIMIT=100
SWAGGER_ENABLED=true
SWAGGER_PATH=api/docs

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL=info

# ============================================
# Service Ports (Read from config/ports.json)
# ============================================
# These are managed centrally in config/ports.json
# Override here only if needed for specific environments
# API_GATEWAY_PORT=3000
# SPEAKER_SERVICE_PORT=3001
# DRAFT_SERVICE_PORT=3002
# RAG_SERVICE_PORT=3003
# EVALUATION_SERVICE_PORT=3004
```

---

## Appendix B: Troubleshooting Decision Tree

```
Service won't start?
├─ Check prerequisites installed? → Run verification commands (Section 1.4)
├─ Port already in use? → Check with lsof, kill process (Section 2.9)
├─ Docker containers not running? → Run `npm run docker:up`
└─ Environment variables missing? → Check docker/.env file

Database connection error?
├─ PostgreSQL → Check container: `docker logs draft-genie-postgres`
├─ MongoDB → Check container: `docker logs draft-genie-mongodb`
└─ Verify credentials in docker/.env

API returns 401/403?
├─ JWT_SECRET not set? → Check docker/.env
├─ API key invalid? → Check API_KEYS in docker/.env
└─ Token expired? → Generate new token

Gemini API error?
├─ API key missing? → Add GEMINI_API_KEY to docker/.env
├─ API key invalid? → Verify at https://makersuite.google.com/app/apikey
└─ Rate limit exceeded? → Check quota, upgrade plan

Service health check fails?
├─ Check service logs → `docker logs <container-name>`
├─ Check dependencies → Verify all infrastructure containers are healthy
└─ Restart service → `docker restart <container-name>`

Performance issues?
├─ Check resource usage → `docker stats`
├─ Check database connections → See Section 2.9
└─ Check Redis memory → `docker exec draft-genie-redis redis-cli INFO memory`
```

---

## Appendix C: Production Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Secrets stored in secret manager
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] SSL/TLS certificates obtained
- [ ] Domain DNS configured
- [ ] Load balancer configured (if applicable)

### Security

- [ ] Strong passwords generated for all databases
- [ ] JWT_SECRET is strong and unique (32+ characters)
- [ ] API_KEYS are unique and secure
- [ ] CORS_ORIGIN restricted to actual domain(s)
- [ ] Swagger docs disabled or protected
- [ ] Rate limiting configured appropriately
- [ ] Firewall rules configured
- [ ] VPC/private network configured
- [ ] Audit logging enabled

### Deployment

- [ ] Docker images built and pushed to registry
- [ ] Database migrations run
- [ ] Services deployed in correct order
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Rollback plan prepared

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Monitor metrics (CPU, memory, response times)
- [ ] Verify all endpoints working
- [ ] Test critical user flows
- [ ] Update status page
- [ ] Notify stakeholders

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-10 | DraftGenie Team | Initial comprehensive deployment handbook |

---

**End of Deployment Handbook**

For questions or issues, please refer to the [GitHub Issues](https://github.com/tan-res-space/draft-genie/issues) page.


