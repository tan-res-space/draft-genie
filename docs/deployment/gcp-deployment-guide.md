# DraftGenie Deployment Guide - Google Cloud Platform (GCP)

This comprehensive guide will walk you through deploying the DraftGenie application to Google Cloud Platform, step by step. This guide is designed for developers with minimal cloud deployment experience.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Environment Variables & Secrets](#environment-variables--secrets)
6. [Domain & SSL Configuration](#domain--ssl-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Cost Optimization](#cost-optimization)
9. [Troubleshooting](#troubleshooting)

---

## Overview

DraftGenie is a microservices-based application that consists of:
- **4 Application Services**: API Gateway (Node.js), Speaker Service (Node.js), Draft Service (Python), RAG Service (Python), Evaluation Service (Python)
- **5 Infrastructure Services**: PostgreSQL, MongoDB, Qdrant (Vector DB), Redis, RabbitMQ

**Estimated Monthly Cost**: $120-250 USD (depending on usage and tier selection)

**Deployment Time**: 2-3 hours for first-time deployment

---

## Prerequisites

### Required Accounts & Subscriptions

1. **Google Cloud Account**
   - Sign up at: https://cloud.google.com/free
   - Free tier includes $300 credit for 90 days
   - Credit card required (won't be charged during free trial)
   - Always Free tier available for many services

2. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: 60 requests per minute
   - Required for AI-powered features
   - **Note**: This is the same API used by the application!

### Required Tools

Install these tools on your local machine:

1. **Google Cloud SDK (gcloud CLI)**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk
   
   # Windows (using PowerShell as Administrator)
   # Download from: https://cloud.google.com/sdk/docs/install
   
   # Linux
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```
   
   **What this does**: Allows you to manage GCP resources from your terminal

2. **Docker** (for building container images)
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   
   **What this does**: Packages your application into containers for deployment

3. **Git** (for cloning the repository)
   ```bash
   # macOS
   brew install git
   
   # Windows
   # Download from: https://git-scm.com/download/win
   
   # Linux
   sudo apt-get install git
   ```

### Verify Installation

Run these commands to verify everything is installed:

```bash
# Check gcloud CLI
gcloud --version
# Expected output: Google Cloud SDK 450.x.x or higher

# Check Docker
docker --version
# Expected output: Docker version 24.x.x or higher

# Check Git
git --version
# Expected output: git version 2.x.x or higher
```

---

## Architecture Overview

### GCP Services Used

```
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Platform (GCP)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Cloud Run (Serverless Containers)             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │   API    │ │ Speaker  │ │  Draft   │             │  │
│  │  │ Gateway  │ │ Service  │ │ Service  │ ...         │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Managed Databases                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │Cloud SQL │ │ MongoDB  │ │Memorystore│            │  │
│  │  │PostgreSQL│ │  Atlas   │ │  Redis   │             │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Additional Services                           │  │
│  │  • Artifact Registry (Container Images)               │  │
│  │  • Secret Manager (Secrets Management)                │  │
│  │  • Cloud Monitoring (Metrics & Alerts)                │  │
│  │  • Cloud Logging (Centralized Logs)                   │  │
│  │  • Cloud Pub/Sub (Message Queue - alternative)        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Service Mapping

| DraftGenie Component | GCP Service | Purpose |
|---------------------|-------------|---------|
| Application Services | Cloud Run | Fully managed serverless containers |
| PostgreSQL | Cloud SQL for PostgreSQL | Managed PostgreSQL database |
| MongoDB | MongoDB Atlas on GCP | Managed MongoDB database |
| Redis | Memorystore for Redis | Managed Redis cache |
| RabbitMQ | Cloud Run (containerized) | Message broker |
| Qdrant | Cloud Run (containerized) | Vector database |
| Container Images | Artifact Registry | Private Docker registry |
| Secrets | Secret Manager | Secure secrets storage |
| Monitoring | Cloud Monitoring | Application monitoring & metrics |
| Logging | Cloud Logging | Centralized logging |

---

## Step-by-Step Deployment

### Step 1: Login to Google Cloud

Open your terminal and login to GCP:

```bash
gcloud auth login
```

**What this does**: Opens your browser to authenticate with Google Cloud. After successful login, you'll see your account information.

### Step 2: Create a New Project

```bash
# Set your project ID (must be globally unique)
export PROJECT_ID="draftgenie-prod-$(date +%s)"

# Create the project
gcloud projects create $PROJECT_ID \
  --name="DraftGenie Production"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account (required for most services)
# First, list your billing accounts
gcloud billing accounts list

# Link billing (replace BILLING_ACCOUNT_ID with your actual ID)
export BILLING_ACCOUNT_ID="YOUR_BILLING_ACCOUNT_ID"
gcloud billing projects link $PROJECT_ID \
  --billing-account=$BILLING_ACCOUNT_ID
```

**What this does**: Creates a new GCP project to organize all DraftGenie resources.

**Project ID**: Must be globally unique across all of GCP. We append a timestamp to ensure uniqueness.

### Step 3: Enable Required APIs

```bash
# Enable all required GCP APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudmonitoring.googleapis.com \
  cloudlogging.googleapis.com \
  compute.googleapis.com \
  vpcaccess.googleapis.com \
  servicenetworking.googleapis.com
```

**What this does**: Activates the GCP services needed for DraftGenie. This may take 2-3 minutes.

**Why needed**: GCP requires explicit API enablement for security and billing purposes.

### Step 4: Set Up Environment Variables

Create a configuration file for easy reference:

```bash
# Create a deployment configuration file
cat > gcp-config.sh << 'EOF'
# GCP Configuration
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export ZONE="us-central1-a"

# Artifact Registry
export REGISTRY_NAME="draftgenie-registry"
export REGISTRY_LOCATION="us-central1"

# Cloud SQL
export SQL_INSTANCE="draftgenie-postgres"
export SQL_DATABASE="draftgenie"
export SQL_USER="draftgenie"

# Redis
export REDIS_INSTANCE="draftgenie-redis"

# VPC
export VPC_CONNECTOR="draftgenie-vpc"

# Your Gemini API Key (replace with your actual key)
export GEMINI_API_KEY="your-gemini-api-key-here"
EOF

# Load the configuration
source gcp-config.sh
```

**What this does**: Creates reusable variables for all GCP resources.

**Important**: Replace `your-gemini-api-key-here` with your actual Gemini API key!

### Step 5: Create Artifact Registry

This is where we'll store our Docker images.

```bash
# Create the registry
gcloud artifacts repositories create $REGISTRY_NAME \
  --repository-format=docker \
  --location=$REGISTRY_LOCATION \
  --description="DraftGenie container images"

# Configure Docker to use gcloud for authentication
gcloud auth configure-docker ${REGISTRY_LOCATION}-docker.pkg.dev

# Set registry URL
export REGISTRY_URL="${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"

echo "Registry URL: $REGISTRY_URL"
```

**What this does**: Creates a private Docker registry to store your container images securely.

**Cost**: $0.10 per GB per month for storage

### Step 6: Set Up Secret Manager

Secret Manager securely stores sensitive information like passwords and API keys.

```bash
# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export RABBITMQ_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 32)

# Create secrets
echo -n "$POSTGRES_PASSWORD" | gcloud secrets create postgres-password \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$RABBITMQ_PASSWORD" | gcloud secrets create rabbitmq-password \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
  --data-file=- \
  --replication-policy="automatic"

echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run access to secrets
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding postgres-password \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding rabbitmq-password \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding jwt-secret \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

echo "Secrets created and permissions granted"
```

**What this does**: Creates secure storage for sensitive data and grants Cloud Run permission to access them.

**Security**: Secrets are encrypted at rest and in transit. Access is logged for audit purposes.

### Step 7: Create VPC Connector

VPC Connector allows Cloud Run to communicate with VPC-based resources like Cloud SQL and Redis.

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create $VPC_CONNECTOR \
  --region=$REGION \
  --range=10.8.0.0/28 \
  --network=default \
  --min-instances=2 \
  --max-instances=3 \
  --machine-type=e2-micro

echo "VPC Connector created: $VPC_CONNECTOR"
```

**What this does**: Creates a bridge between serverless Cloud Run and VPC-based databases.

**Cost**: ~$10/month for 2 e2-micro instances (minimum required)

**IP Range**: 10.8.0.0/28 provides 16 IP addresses (14 usable)

### Step 8: Create Cloud SQL PostgreSQL Instance

```bash
# Create Cloud SQL instance
gcloud sql instances create $SQL_INSTANCE \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=$REGION \
  --network=default \
  --no-assign-ip \
  --database-flags=max_connections=100

# Create database
gcloud sql databases create $SQL_DATABASE \
  --instance=$SQL_INSTANCE

# Create user
gcloud sql users create $SQL_USER \
  --instance=$SQL_INSTANCE \
  --password=$POSTGRES_PASSWORD

# Get connection name
export SQL_CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE \
  --format="value(connectionName)")

echo "Cloud SQL Connection Name: $SQL_CONNECTION_NAME"
```

**What this does**: Creates a managed PostgreSQL database with automatic backups and updates.

**Tier Explanation**:
- db-f1-micro: 0.6 GB RAM, shared CPU, ~$7/month (development)
- db-g1-small: 1.7 GB RAM, shared CPU, ~$25/month (small production)
- db-custom-2-7680: 2 vCPU, 7.5 GB RAM, ~$100/month (production)

**Important**: `--no-assign-ip` means the database is only accessible via private IP (more secure).

### Step 9: Create Memorystore for Redis

```bash
# Create Redis instance
gcloud redis instances create $REDIS_INSTANCE \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0 \
  --tier=basic \
  --network=default

# Get Redis host and port
export REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE \
  --region=$REGION \
  --format="value(host)")

export REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE \
  --region=$REGION \
  --format="value(port)")

echo "Redis Host: $REDIS_HOST"
echo "Redis Port: $REDIS_PORT"
```

**What this does**: Creates a managed Redis cache for session storage and caching.

**Tier Explanation**:
- Basic: 1 GB, no replication, ~$35/month (development)
- Standard: 1 GB with replication, ~$70/month (production with HA)

**Note**: Basic tier doesn't support AUTH, so no password needed.

### Step 10: Set Up MongoDB Atlas

MongoDB Atlas is the recommended managed MongoDB service on GCP.

1. **Sign up for MongoDB Atlas**:
   - Go to: https://www.mongodb.com/cloud/atlas/register
   - Choose "Sign up with Google" or create an account
   - Select "Google Cloud" as your cloud provider

2. **Create a Free Cluster**:
   ```
   - Click "Build a Database"
   - Select "Shared" (Free tier)
   - Choose "Google Cloud" as cloud provider
   - Select same region as your GCP resources (e.g., "Iowa (us-central1)")
   - Cluster Name: "draftgenie-cluster"
   - Click "Create Cluster"
   ```

3. **Configure Database Access**:
   ```
   - Go to "Database Access" in left menu
   - Click "Add New Database User"
   - Username: draftgenie
   - Password: Click "Autogenerate Secure Password" and copy it
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"
   ```

4. **Configure Network Access**:
   ```
   - Go to "Network Access" in left menu
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for now)
   - Click "Confirm"
   ```

   **Security Note**: In production, restrict this to your Cloud Run IP ranges.

5. **Get Connection String**:
   ```
   - Go to "Database" in left menu
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace <password> with the password you copied earlier
   ```

6. **Store in Secret Manager**:
   ```bash
   # Replace with your actual connection string
   export MONGODB_URL="mongodb+srv://draftgenie:<password>@draftgenie-cluster.xxxxx.mongodb.net/draftgenie?retryWrites=true&w=majority"

   echo -n "$MONGODB_URL" | gcloud secrets create mongodb-url \
     --data-file=- \
     --replication-policy="automatic"

   # Grant access to Cloud Run
   gcloud secrets add-iam-policy-binding mongodb-url \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

**What this does**: Sets up a fully managed MongoDB database with automatic backups and scaling.

**Cost**: Free tier includes 512 MB storage, perfect for development and small production workloads.

### Step 11: Clone and Prepare the Application

```bash
# Clone the repository
git clone https://github.com/tan-res-space/draft-genie.git
cd draft-genie
```

**What this does**: Downloads the DraftGenie source code.

### Step 12: Build and Push Docker Images

We'll build Docker images for each service and push them to Artifact Registry.

```bash
# Build and push API Gateway
docker build -f docker/Dockerfile.api-gateway -t $REGISTRY_URL/api-gateway:latest .
docker push $REGISTRY_URL/api-gateway:latest

# Build and push Speaker Service
docker build -f docker/Dockerfile.speaker-service -t $REGISTRY_URL/speaker-service:latest .
docker push $REGISTRY_URL/speaker-service:latest

# Build and push Draft Service
docker build -f docker/Dockerfile.draft-service -t $REGISTRY_URL/draft-service:latest .
docker push $REGISTRY_URL/draft-service:latest

# Build and push RAG Service
docker build -f docker/Dockerfile.rag-service -t $REGISTRY_URL/rag-service:latest .
docker push $REGISTRY_URL/rag-service:latest

# Build and push Evaluation Service
docker build -f docker/Dockerfile.evaluation-service -t $REGISTRY_URL/evaluation-service:latest .
docker push $REGISTRY_URL/evaluation-service:latest

echo "All images built and pushed successfully!"
```

**What this does**: Packages each service into a Docker container and uploads it to your private registry.

**Time estimate**: 10-15 minutes depending on your internet speed.

**Troubleshooting**: If builds fail, ensure Docker Desktop is running and you have enough disk space (need ~5 GB free).

### Step 13: Deploy Infrastructure Services (RabbitMQ & Qdrant)

These services will run as containers in Cloud Run.

```bash
# Deploy RabbitMQ
gcloud run deploy rabbitmq \
  --image=rabbitmq:3.13-management-alpine \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="RABBITMQ_DEFAULT_USER=draftgenie" \
  --set-secrets="RABBITMQ_DEFAULT_PASS=rabbitmq-password:latest" \
  --port=5672 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=1

# Deploy Qdrant
gcloud run deploy qdrant \
  --image=qdrant/qdrant:v1.7.4 \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --port=6333 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=1

# Get service URLs
export RABBITMQ_URL=$(gcloud run services describe rabbitmq \
  --region=$REGION \
  --format="value(status.url)")

export QDRANT_URL=$(gcloud run services describe qdrant \
  --region=$REGION \
  --format="value(status.url)")

echo "RabbitMQ URL: $RABBITMQ_URL"
echo "Qdrant URL: $QDRANT_URL"
```

**What this does**: Deploys RabbitMQ (message broker) and Qdrant (vector database) as managed containers.

**Authentication**: `--no-allow-unauthenticated` means only authenticated requests are allowed (secure).

### Step 14: Deploy Application Services

Now we'll deploy the main application services.

```bash
# Deploy Speaker Service
gcloud run deploy speaker-service \
  --image=$REGISTRY_URL/speaker-service:latest \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --add-cloudsql-instances=$SQL_CONNECTION_NAME \
  --set-env-vars="NODE_ENV=production,PORT=3001,LOG_LEVEL=info" \
  --set-env-vars="DATABASE_URL=postgresql://${SQL_USER}:${POSTGRES_PASSWORD}@/draftgenie?host=/cloudsql/${SQL_CONNECTION_NAME}" \
  --set-env-vars="REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}" \
  --set-secrets="RABBITMQ_PASSWORD=rabbitmq-password:latest" \
  --update-env-vars="RABBITMQ_URL=amqp://draftgenie:RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --port=3001 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

# Deploy Draft Service
gcloud run deploy draft-service \
  --image=$REGISTRY_URL/draft-service:latest \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="ENVIRONMENT=production,PORT=3002,LOG_LEVEL=info" \
  --set-env-vars="QDRANT_URL=${QDRANT_URL}" \
  --set-env-vars="REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}" \
  --set-secrets="MONGODB_URL=mongodb-url:latest,GEMINI_API_KEY=gemini-api-key:latest,RABBITMQ_PASSWORD=rabbitmq-password:latest" \
  --update-env-vars="RABBITMQ_URL=amqp://draftgenie:RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --port=3002 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

# Deploy RAG Service
gcloud run deploy rag-service \
  --image=$REGISTRY_URL/rag-service:latest \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="ENVIRONMENT=production,PORT=3003,LOG_LEVEL=info" \
  --set-env-vars="QDRANT_URL=${QDRANT_URL}" \
  --set-secrets="MONGODB_URL=mongodb-url:latest,GEMINI_API_KEY=gemini-api-key:latest" \
  --port=3003 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=40 \
  --timeout=300

# Deploy Evaluation Service
gcloud run deploy evaluation-service \
  --image=$REGISTRY_URL/evaluation-service:latest \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="ENVIRONMENT=production,PORT=3004,LOG_LEVEL=info" \
  --set-secrets="MONGODB_URL=mongodb-url:latest,RABBITMQ_PASSWORD=rabbitmq-password:latest" \
  --update-env-vars="RABBITMQ_URL=amqp://draftgenie:RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --port=3004 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

# Get service URLs
export SPEAKER_SERVICE_URL=$(gcloud run services describe speaker-service \
  --region=$REGION \
  --format="value(status.url)")

export DRAFT_SERVICE_URL=$(gcloud run services describe draft-service \
  --region=$REGION \
  --format="value(status.url)")

export RAG_SERVICE_URL=$(gcloud run services describe rag-service \
  --region=$REGION \
  --format="value(status.url)")

export EVALUATION_SERVICE_URL=$(gcloud run services describe evaluation-service \
  --region=$REGION \
  --format="value(status.url)")

# Deploy API Gateway (with public access)
gcloud run deploy api-gateway \
  --image=$REGISTRY_URL/api-gateway:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="NODE_ENV=production,PORT=3000" \
  --set-env-vars="SPEAKER_SERVICE_URL=${SPEAKER_SERVICE_URL}" \
  --set-env-vars="DRAFT_SERVICE_URL=${DRAFT_SERVICE_URL}" \
  --set-env-vars="RAG_SERVICE_URL=${RAG_SERVICE_URL}" \
  --set-env-vars="EVALUATION_SERVICE_URL=${EVALUATION_SERVICE_URL}" \
  --set-env-vars="CORS_ORIGIN=*,SWAGGER_ENABLED=true" \
  --set-secrets="JWT_SECRET=jwt-secret:latest" \
  --port=3000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=100

# Get the API Gateway URL
export API_GATEWAY_URL=$(gcloud run services describe api-gateway \
  --region=$REGION \
  --format="value(status.url)")

echo "API Gateway URL: $API_GATEWAY_URL"
```

**What this does**: Deploys all five application services with proper networking, scaling, and environment variables.

**Resource Allocation**:
- CPU: 1-2 cores per service (RAG service gets more for AI processing)
- Memory: 1-2 GB per service (RAG service gets more for model loading)
- Min instances: 0 for most services (scales to zero when idle), 1 for API Gateway
- Max instances: 10-20 (auto-scales based on load)
- Concurrency: 40-100 requests per instance

**Cost Optimization**: Setting `min-instances=0` allows services to scale to zero when not in use, saving costs.

### Step 15: Grant Service-to-Service Permissions

Cloud Run services need permission to call each other.

```bash
# Allow API Gateway to invoke backend services
gcloud run services add-iam-policy-binding speaker-service \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding draft-service \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding rag-service \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding evaluation-service \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding rabbitmq \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding qdrant \
  --region=$REGION \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"

echo "Service-to-service permissions granted"
```

**What this does**: Allows Cloud Run services to authenticate and call each other securely.

**Security**: Each service uses the default compute service account for authentication.

### Step 16: Run Database Migrations

Now that the Speaker Service is deployed, we need to initialize the PostgreSQL database schema.

```bash
# Create a temporary Cloud Run job to run migrations
gcloud run jobs create speaker-migration \
  --image=$REGISTRY_URL/speaker-service:latest \
  --region=$REGION \
  --vpc-connector=$VPC_CONNECTOR \
  --add-cloudsql-instances=$SQL_CONNECTION_NAME \
  --set-env-vars="DATABASE_URL=postgresql://${SQL_USER}:${POSTGRES_PASSWORD}@/draftgenie?host=/cloudsql/${SQL_CONNECTION_NAME}" \
  --command="npx" \
  --args="prisma,migrate,deploy" \
  --max-retries=0 \
  --task-timeout=5m

# Execute the migration job
gcloud run jobs execute speaker-migration \
  --region=$REGION \
  --wait

echo "Database migrations completed"
```

**What this does**: Creates the necessary database tables and schema in Cloud SQL PostgreSQL.

**Alternative Method**: If the job fails, you can run migrations locally:
```bash
# Set DATABASE_URL locally (requires Cloud SQL Proxy)
export DATABASE_URL="postgresql://${SQL_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/draftgenie"

# Start Cloud SQL Proxy
cloud_sql_proxy -instances=${SQL_CONNECTION_NAME}=tcp:5432 &

# Run migrations
cd apps/speaker-service
npx prisma migrate deploy
```

### Step 17: Verify Deployment

Test that all services are running correctly:

```bash
# Check status of all Cloud Run services
gcloud run services list --region=$REGION

# Test the API Gateway health endpoint
curl $API_GATEWAY_URL/api/v1/health

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2024-01-15T10:30:00.000Z",
#   "services": {
#     "speaker": "healthy",
#     "draft": "healthy",
#     "rag": "healthy",
#     "evaluation": "healthy"
#   }
# }
```

**What this does**: Verifies that all services are running and can communicate with each other.

**Success Indicators**:
- All services show "Ready" status
- Health check returns 200 OK
- All service statuses are "healthy"

---

## Environment Variables & Secrets

### Managing Secrets with Secret Manager

All sensitive information should be stored in Secret Manager:

```bash
# Add a new secret
echo -n "my-secret-value" | gcloud secrets create my-secret-name \
  --data-file=- \
  --replication-policy="automatic"

# Update an existing secret
echo -n "new-secret-value" | gcloud secrets versions add my-secret-name \
  --data-file=-

# Retrieve a secret
gcloud secrets versions access latest --secret="my-secret-name"

# List all secrets
gcloud secrets list

# Delete a secret
gcloud secrets delete my-secret-name
```

**What this does**: Manages secrets securely with automatic encryption and access control.

### Updating Environment Variables

To update environment variables for a running service:

```bash
# Update a single environment variable
gcloud run services update api-gateway \
  --region=$REGION \
  --update-env-vars="NEW_VAR=new_value"

# Update multiple environment variables
gcloud run services update api-gateway \
  --region=$REGION \
  --update-env-vars="VAR1=value1,VAR2=value2"

# Remove an environment variable
gcloud run services update api-gateway \
  --region=$REGION \
  --remove-env-vars="VAR_TO_REMOVE"

# Update secrets
gcloud run services update api-gateway \
  --region=$REGION \
  --update-secrets="JWT_SECRET=jwt-secret:latest"
```

**What this does**: Updates environment variables and automatically deploys a new revision with the changes.

### Required Environment Variables by Service

**API Gateway**:
- `NODE_ENV`: production
- `PORT`: 3000
- `SPEAKER_SERVICE_URL`: Cloud Run URL
- `DRAFT_SERVICE_URL`: Cloud Run URL
- `RAG_SERVICE_URL`: Cloud Run URL
- `EVALUATION_SERVICE_URL`: Cloud Run URL
- `JWT_SECRET`: Secret from Secret Manager
- `CORS_ORIGIN`: Your domain or *
- `SWAGGER_ENABLED`: true

**Speaker Service**:
- `NODE_ENV`: production
- `PORT`: 3001
- `DATABASE_URL`: Cloud SQL connection string
- `REDIS_URL`: Memorystore connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `LOG_LEVEL`: info

**Draft Service**:
- `ENVIRONMENT`: production
- `PORT`: 3002
- `MONGODB_URL`: MongoDB Atlas connection string (secret)
- `QDRANT_URL`: Qdrant Cloud Run URL
- `REDIS_URL`: Memorystore connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `GEMINI_API_KEY`: Gemini API key (secret)
- `LOG_LEVEL`: info

**RAG Service**:
- `ENVIRONMENT`: production
- `PORT`: 3003
- `MONGODB_URL`: MongoDB Atlas connection string (secret)
- `QDRANT_URL`: Qdrant Cloud Run URL
- `GEMINI_API_KEY`: Gemini API key (secret)
- `LOG_LEVEL`: info

**Evaluation Service**:
- `ENVIRONMENT`: production
- `PORT`: 3004
- `MONGODB_URL`: MongoDB Atlas connection string (secret)
- `RABBITMQ_URL`: RabbitMQ connection string
- `LOG_LEVEL`: info

---

## Domain & SSL Configuration

### Option 1: Use GCP-Provided Domain (Easiest)

Cloud Run automatically provides an HTTPS endpoint:

```
https://api-gateway-{random-hash}-uc.a.run.app
```

**Pros**:
- Free SSL certificate
- No configuration needed
- Works immediately
- Automatic renewal

**Cons**:
- Long, non-branded URL
- Can't customize

### Option 2: Add Custom Domain

If you own a domain (e.g., api.yourdomain.com):

1. **Map Custom Domain to Cloud Run**:
   ```bash
   gcloud run domain-mappings create \
     --service=api-gateway \
     --domain=api.yourdomain.com \
     --region=$REGION
   ```

2. **Get DNS Configuration**:
   ```bash
   gcloud run domain-mappings describe \
     --domain=api.yourdomain.com \
     --region=$REGION
   ```

   This will show you the DNS records you need to add.

3. **Add DNS Records** (in your domain registrar):

   For root domain (yourdomain.com):
   ```
   Type: A
   Name: @
   Value: 216.239.32.21

   Type: A
   Name: @
   Value: 216.239.34.21

   Type: A
   Name: @
   Value: 216.239.36.21

   Type: A
   Name: @
   Value: 216.239.38.21

   Type: AAAA
   Name: @
   Value: 2001:4860:4802:32::15

   Type: AAAA
   Name: @
   Value: 2001:4860:4802:34::15

   Type: AAAA
   Name: @
   Value: 2001:4860:4802:36::15

   Type: AAAA
   Name: @
   Value: 2001:4860:4802:38::15
   ```

   For subdomain (api.yourdomain.com):
   ```
   Type: CNAME
   Name: api
   Value: ghs.googlehosted.com
   ```

4. **Verify Domain Mapping**:
   ```bash
   gcloud run domain-mappings list --region=$REGION
   ```

**What this does**: Configures your custom domain with automatic SSL certificate from Google.

**Time to propagate**: DNS changes can take 5-60 minutes to propagate globally.

### SSL Certificate Management

Cloud Run automatically manages SSL certificates:
- **Automatic provisioning**: Certificates are created when you map a domain
- **Automatic renewal**: Certificates renew 30 days before expiration
- **Free**: No cost for managed certificates
- **TLS 1.2+**: Modern security standards

### Using Cloud Load Balancer (Advanced)

For more control over SSL and routing:

```bash
# Reserve a static IP
gcloud compute addresses create draftgenie-ip \
  --global

# Get the IP address
gcloud compute addresses describe draftgenie-ip \
  --global \
  --format="value(address)"

# Create a serverless NEG (Network Endpoint Group)
gcloud compute network-endpoint-groups create api-gateway-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=api-gateway

# Create backend service
gcloud compute backend-services create api-gateway-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED

# Add NEG to backend service
gcloud compute backend-services add-backend api-gateway-backend \
  --global \
  --network-endpoint-group=api-gateway-neg \
  --network-endpoint-group-region=$REGION

# Create URL map
gcloud compute url-maps create api-gateway-lb \
  --default-service=api-gateway-backend

# Create SSL certificate
gcloud compute ssl-certificates create api-gateway-cert \
  --domains=api.yourdomain.com \
  --global

# Create HTTPS proxy
gcloud compute target-https-proxies create api-gateway-https-proxy \
  --url-map=api-gateway-lb \
  --ssl-certificates=api-gateway-cert

# Create forwarding rule
gcloud compute forwarding-rules create api-gateway-https-rule \
  --global \
  --target-https-proxy=api-gateway-https-proxy \
  --address=draftgenie-ip \
  --ports=443
```

**What this does**: Creates a global load balancer with custom SSL certificate and static IP.

**Use case**: When you need advanced routing, CDN, or multiple backends.

---

## Monitoring & Logging

### Viewing Logs

**Real-time logs** in Cloud Console:
1. Go to: https://console.cloud.google.com/run
2. Click on a service (e.g., "api-gateway")
3. Click "LOGS" tab
4. Logs stream in real-time

**Using gcloud CLI**:
```bash
# View recent logs for a service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway" \
  --limit=50 \
  --format=json

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway"

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway AND severity>=ERROR" \
  --limit=50

# Filter by time range
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway" \
  --freshness=1h
```

**What this does**: Retrieves and displays logs from Cloud Logging.

### Cloud Monitoring Dashboard

1. **Open Cloud Console**: https://console.cloud.google.com/monitoring
2. **Create Dashboard**:
   ```bash
   # Or use gcloud to create a dashboard
   gcloud monitoring dashboards create --config-from-file=dashboard.json
   ```

3. **Key Metrics to Monitor**:
   - **Request Count**: Number of requests per service
   - **Request Latency**: Response time (p50, p95, p99)
   - **Error Rate**: Percentage of failed requests
   - **Instance Count**: Number of running instances
   - **CPU Utilization**: CPU usage per instance
   - **Memory Utilization**: Memory usage per instance
   - **Billable Time**: Total compute time (for cost tracking)

### Setting Up Alerts

Create an alert when error rate exceeds threshold:

```bash
# Create notification channel (email)
gcloud alpha monitoring channels create \
  --display-name="Admin Email" \
  --type=email \
  --channel-labels=email_address=your-email@example.com

# Get channel ID
export CHANNEL_ID=$(gcloud alpha monitoring channels list \
  --filter="displayName='Admin Email'" \
  --format="value(name)")

# Create alert policy for high error rate
cat > alert-policy.yaml << EOF
displayName: "High Error Rate - API Gateway"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="api-gateway" AND metric.type="run.googleapis.com/request_count"'
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_SUM
          groupByFields:
            - resource.service_name
      comparison: COMPARISON_GT
      thresholdValue: 0.05
      duration: 300s
notificationChannels:
  - $CHANNEL_ID
alertStrategy:
  autoClose: 604800s
EOF

gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml
```

**What this does**: Sends you an email when the error rate exceeds 5% for 5 minutes.

### Log-Based Metrics

Create custom metrics from logs:

```bash
# Create a metric for specific error patterns
gcloud logging metrics create error_count \
  --description="Count of application errors" \
  --log-filter='resource.type="cloud_run_revision" AND severity="ERROR"'

# Create a metric for slow requests
gcloud logging metrics create slow_requests \
  --description="Count of requests taking >5s" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.latency>5000'
```

**What this does**: Creates custom metrics that you can use in dashboards and alerts.

### Cloud Trace (Distributed Tracing)

Cloud Trace is automatically enabled for Cloud Run:

1. **View Traces**: https://console.cloud.google.com/traces
2. **Analyze Latency**: See which services are slow
3. **Debug Issues**: Trace requests across services

**No configuration needed**: Cloud Run automatically sends trace data.

---

## Cost Optimization

### Understanding Costs

**Monthly Cost Breakdown** (estimated for moderate usage):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Cloud Run (5 services) | 1-2 vCPU, 1-2 GB RAM, 100K requests | $20-50 |
| Cloud SQL PostgreSQL | db-f1-micro | $7 |
| MongoDB Atlas | Free tier (512 MB) | $0 |
| Memorystore Redis | Basic 1 GB | $35 |
| VPC Connector | 2 e2-micro instances | $10 |
| Artifact Registry | 5 GB storage | $0.50 |
| Cloud Logging | 10 GB/month | $5 |
| Cloud Monitoring | Included | $0 |
| **Total** | | **$77.50-102.50/month** |

**Note**: Cloud Run pricing is based on actual usage (CPU, memory, requests), so costs can be much lower with minimal traffic.

### Cloud Run Pricing Details

Cloud Run charges for:
1. **CPU allocation**: $0.00002400 per vCPU-second
2. **Memory allocation**: $0.00000250 per GiB-second
3. **Requests**: $0.40 per million requests
4. **Networking**: $0.12 per GB egress (first 1 GB free per month)

**Free Tier** (per month):
- 2 million requests
- 360,000 GiB-seconds of memory
- 180,000 vCPU-seconds
- 1 GB network egress

### Cost Optimization Tips

1. **Scale to Zero for Low-Traffic Services**:
   ```bash
   # Set minimum instances to 0
   gcloud run services update evaluation-service \
     --region=$REGION \
     --min-instances=0
   ```

   **Savings**: Pay only when service is actively processing requests

2. **Right-Size Resources**:
   ```bash
   # Reduce memory for services that don't need much
   gcloud run services update speaker-service \
     --region=$REGION \
     --memory=512Mi \
     --cpu=0.5
   ```

   **Savings**: Up to 50% on compute costs

3. **Use Concurrency Effectively**:
   ```bash
   # Increase concurrency to handle more requests per instance
   gcloud run services update api-gateway \
     --region=$REGION \
     --concurrency=100
   ```

   **Savings**: Fewer instances needed = lower costs

4. **Optimize Database Tiers**:
   ```bash
   # Use smallest tier for development
   gcloud sql instances patch $SQL_INSTANCE \
     --tier=db-f1-micro

   # Scale up for production
   gcloud sql instances patch $SQL_INSTANCE \
     --tier=db-custom-2-7680
   ```

5. **Set Up Budget Alerts**:
   ```bash
   # Create a budget
   gcloud billing budgets create \
     --billing-account=$BILLING_ACCOUNT_ID \
     --display-name="DraftGenie Monthly Budget" \
     --budget-amount=200 \
     --threshold-rule=percent=50 \
     --threshold-rule=percent=90 \
     --threshold-rule=percent=100
   ```

   **What this does**: Alerts you at 50%, 90%, and 100% of your $200 budget

6. **Use Committed Use Discounts** (for production):
   - Commit to 1 or 3 years for Cloud SQL
   - Save up to 57% on database costs
   - Only for stable, long-running workloads

7. **Optimize Container Images**:
   - Use multi-stage builds to reduce image size
   - Smaller images = faster cold starts = lower costs
   - Remove unnecessary dependencies

8. **Monitor and Optimize**:
   ```bash
   # View cost breakdown
   gcloud billing accounts get-iam-policy $BILLING_ACCOUNT_ID

   # Export billing data to BigQuery for analysis
   gcloud billing accounts export create \
     --billing-account=$BILLING_ACCOUNT_ID \
     --dataset=billing_export \
     --project=$PROJECT_ID
   ```

### Free Tier Maximization

- **Cloud Run**: 2M requests/month free
- **Cloud SQL**: No free tier, but db-f1-micro is cheapest at ~$7/month
- **MongoDB Atlas**: Free tier (512 MB) - sufficient for development
- **Cloud Logging**: First 50 GB/month free
- **Cloud Monitoring**: Included with GCP services
- **Artifact Registry**: First 0.5 GB free

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Cloud Run Service Won't Start

**Symptoms**: Service shows "Deploying" or "Failed" status

**Diagnosis**:
```bash
# Check service status
gcloud run services describe api-gateway \
  --region=$REGION \
  --format="value(status.conditions)"

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway" \
  --limit=50 \
  --format=json
```

**Common Causes & Solutions**:

1. **Image Pull Failure**:
   ```bash
   # Verify image exists
   gcloud artifacts docker images list $REGISTRY_URL

   # Check permissions
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/artifactregistry.reader"
   ```

2. **Port Mismatch**:
   - Ensure `--port` matches the port your app listens on
   - Check Dockerfile EXPOSE directive
   - Verify application logs for "listening on port X"

3. **Container Crash**:
   ```bash
   # Check container logs for errors
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway AND severity>=ERROR" \
     --limit=20
   ```

4. **Timeout During Startup**:
   ```bash
   # Increase startup timeout
   gcloud run services update api-gateway \
     --region=$REGION \
     --timeout=300
   ```

#### Issue 2: Database Connection Failures

**Symptoms**: Services start but can't connect to databases

**Diagnosis**:
```bash
# Test Cloud SQL connection
gcloud sql connect $SQL_INSTANCE --user=$SQL_USER

# Check VPC connector status
gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR \
  --region=$REGION

# Verify Cloud SQL instance is running
gcloud sql instances describe $SQL_INSTANCE
```

**Solutions**:

1. **Cloud SQL Connection Issues**:
   ```bash
   # Verify Cloud SQL instance is added to service
   gcloud run services describe speaker-service \
     --region=$REGION \
     --format="value(spec.template.metadata.annotations)"

   # Update service with Cloud SQL connection
   gcloud run services update speaker-service \
     --region=$REGION \
     --add-cloudsql-instances=$SQL_CONNECTION_NAME
   ```

2. **VPC Connector Issues**:
   ```bash
   # Check connector status
   gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR \
     --region=$REGION

   # If failed, delete and recreate
   gcloud compute networks vpc-access connectors delete $VPC_CONNECTOR \
     --region=$REGION

   # Then recreate (see Step 7)
   ```

3. **MongoDB Connection String**:
   - Verify connection string format in Secret Manager
   - Ensure password is URL-encoded
   - Check MongoDB Atlas network access settings (allow all IPs or specific ranges)

4. **Redis Connection**:
   ```bash
   # Verify Redis instance is running
   gcloud redis instances describe $REDIS_INSTANCE \
     --region=$REGION

   # Check host and port
   echo "Host: $REDIS_HOST"
   echo "Port: $REDIS_PORT"
   ```

#### Issue 3: High Memory Usage / OOM Kills

**Symptoms**: Container restarts frequently, logs show "Out of Memory"

**Diagnosis**:
```bash
# Check memory usage metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations" AND resource.labels.service_name="rag-service"' \
  --format=json

# View OOM events in logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="rag-service" AND textPayload=~"out of memory"' \
  --limit=10
```

**Solutions**:

1. **Increase Memory Allocation**:
   ```bash
   gcloud run services update rag-service \
     --region=$REGION \
     --memory=4Gi  # Increase from 2Gi
   ```

2. **Optimize Application**:
   - Review application logs for memory leaks
   - Implement connection pooling
   - Add memory limits to Node.js: `NODE_OPTIONS=--max-old-space-size=3072`

3. **Reduce Concurrency**:
   ```bash
   # Lower concurrency to use less memory per instance
   gcloud run services update rag-service \
     --region=$REGION \
     --concurrency=20  # Reduce from 40
   ```

#### Issue 4: Slow Response Times / Cold Starts

**Symptoms**: First request after idle period is very slow

**Diagnosis**:
```bash
# Check request latency
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies" AND resource.labels.service_name="api-gateway"' \
  --format=json

# View slow requests in logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="api-gateway" AND httpRequest.latency>"5s"' \
  --limit=10
```

**Solutions**:

1. **Keep Minimum Instances Warm**:
   ```bash
   # Set minimum instances to avoid cold starts
   gcloud run services update api-gateway \
     --region=$REGION \
     --min-instances=1
   ```

   **Trade-off**: Costs more but eliminates cold starts

2. **Optimize Container Image**:
   - Use smaller base images (alpine, distroless)
   - Reduce dependencies
   - Use multi-stage builds

3. **Increase CPU During Startup**:
   ```bash
   # Allocate more CPU
   gcloud run services update api-gateway \
     --region=$REGION \
     --cpu=2
   ```

4. **Use Startup CPU Boost** (automatically enabled):
   - Cloud Run temporarily allocates extra CPU during startup
   - No configuration needed

#### Issue 5: Services Can't Communicate

**Symptoms**: API Gateway returns 403/502 errors when calling backend services

**Diagnosis**:
```bash
# Check IAM permissions
gcloud run services get-iam-policy speaker-service \
  --region=$REGION

# Test service URL
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $SPEAKER_SERVICE_URL/health
```

**Solutions**:

1. **Grant Invoker Permissions**:
   ```bash
   # Allow default compute service account to invoke service
   gcloud run services add-iam-policy-binding speaker-service \
     --region=$REGION \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

2. **Use Service Account for Authentication**:
   ```bash
   # In your application code, use Google Auth Library
   # to get identity tokens for service-to-service calls
   ```

3. **Check Service URLs**:
   ```bash
   # Verify all service URLs are correct
   gcloud run services list --region=$REGION
   ```

#### Issue 6: Deployment Takes Too Long

**Symptoms**: `gcloud run deploy` commands timeout or take >5 minutes

**Solutions**:

1. **Optimize Docker Build**:
   - Use layer caching
   - Build images locally and push to registry
   - Use Cloud Build for faster builds

2. **Use Cloud Build** (recommended):
   ```bash
   # Build in the cloud (faster)
   gcloud builds submit \
     --tag=$REGISTRY_URL/api-gateway:latest \
     --dockerfile=docker/Dockerfile.api-gateway

   # Then deploy
   gcloud run deploy api-gateway \
     --image=$REGISTRY_URL/api-gateway:latest \
     --region=$REGION
   ```

3. **Increase Timeout**:
   ```bash
   # Set longer deployment timeout
   gcloud config set run/deployment_timeout 1200  # 20 minutes
   ```

#### Issue 7: High Costs

**Symptoms**: Monthly bill is higher than expected

**Diagnosis**:
```bash
# View cost breakdown
gcloud billing accounts get-iam-policy $BILLING_ACCOUNT_ID

# Check which services are using the most resources
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/billable_instance_time"' \
  --format=json
```

**Solutions**:

1. **Identify Cost Drivers**:
   - Check Cloud Console Billing page
   - Look for services with high instance counts
   - Review services that don't scale to zero

2. **Optimize Resource Allocation**:
   ```bash
   # Reduce memory and CPU for over-provisioned services
   gcloud run services update speaker-service \
     --region=$REGION \
     --memory=512Mi \
     --cpu=0.5
   ```

3. **Scale to Zero**:
   ```bash
   # Allow services to scale to zero when idle
   gcloud run services update evaluation-service \
     --region=$REGION \
     --min-instances=0
   ```

4. **Review Database Tiers**:
   - Downgrade Cloud SQL to smaller tier if over-provisioned
   - Consider MongoDB Atlas free tier for development

### Getting Help

1. **GCP Support**:
   - Free support: https://cloud.google.com/support/docs
   - Community: https://stackoverflow.com/questions/tagged/google-cloud-platform
   - Paid support: https://cloud.google.com/support

2. **Check Service Health**:
   - GCP Status: https://status.cloud.google.com/

3. **Cloud Run Documentation**:
   - https://cloud.google.com/run/docs

4. **DraftGenie Issues**:
   - https://github.com/tan-res-space/draft-genie/issues

### Useful Commands Reference

```bash
# View all Cloud Run services
gcloud run services list --region=$REGION

# View all Cloud SQL instances
gcloud sql instances list

# View all secrets
gcloud secrets list

# Get project info
gcloud projects describe $PROJECT_ID

# View current costs
gcloud billing accounts list

# Delete everything (cleanup)
gcloud projects delete $PROJECT_ID

# Export configuration
gcloud projects describe $PROJECT_ID --format=json > project-config.json
```

---

## Next Steps

After successful deployment:

1. **Set Up CI/CD Pipeline**:
   - Use Cloud Build with GitHub integration
   - Automate builds and deployments
   - Example: https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build

2. **Implement Backup Strategy**:
   - Cloud SQL: Automated backups enabled by default (7-day retention)
   - MongoDB: Configure Atlas backup policy
   - Export critical data regularly

3. **Security Hardening**:
   - Enable Binary Authorization
   - Implement VPC Service Controls
   - Use Workload Identity for service accounts
   - Regular security scans with Container Analysis

4. **Performance Testing**:
   - Use Cloud Load Testing
   - Identify bottlenecks
   - Optimize based on real traffic patterns

5. **Documentation**:
   - Document your specific configuration
   - Create runbooks for common operations
   - Train team members on GCP tools

---

## Additional Resources

- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **gcloud CLI Reference**: https://cloud.google.com/sdk/gcloud/reference
- **GCP Pricing Calculator**: https://cloud.google.com/products/calculator
- **GCP Architecture Center**: https://cloud.google.com/architecture
- **Cloud Run Best Practices**: https://cloud.google.com/run/docs/best-practices
- **DraftGenie Documentation**: https://github.com/tan-res-space/draft-genie/tree/main/docs

---

## Conclusion

Congratulations! You've successfully deployed DraftGenie to Google Cloud Platform. Your application is now running on Google's world-class infrastructure with automatic scaling, monitoring, and high availability.

**What you've accomplished**:
- ✅ Deployed 5 microservices to Cloud Run
- ✅ Set up managed databases (Cloud SQL, MongoDB Atlas, Memorystore)
- ✅ Configured secure secrets management with Secret Manager
- ✅ Enabled monitoring and logging with Cloud Monitoring
- ✅ Implemented auto-scaling with scale-to-zero capability
- ✅ Secured your application with HTTPS and IAM

**Your deployment is production-ready!** 🎉

**Key Advantages of GCP Deployment**:
- **Cost-effective**: Pay only for what you use, scale to zero when idle
- **Fully managed**: No servers to manage, automatic updates
- **Global scale**: Deploy to multiple regions easily
- **Integrated**: Seamless integration with other Google services

For questions or issues, please refer to the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.


