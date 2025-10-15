# DraftGenie Deployment Guide - Microsoft Azure

This comprehensive guide will walk you through deploying the DraftGenie application to Microsoft Azure, step by step. This guide is designed for developers with minimal cloud deployment experience.

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

**Estimated Monthly Cost**: $150-300 USD (depending on usage and tier selection)

**Deployment Time**: 2-3 hours for first-time deployment

---

## Prerequisites

### Required Accounts & Subscriptions

1. **Azure Account**
   - Sign up at: https://azure.microsoft.com/free/
   - Free tier includes $200 credit for 30 days
   - Credit card required (won't be charged during free trial)

2. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: 60 requests per minute
   - Required for AI-powered features

### Required Tools

Install these tools on your local machine:

1. **Azure CLI** (Command Line Interface)
   ```bash
   # macOS
   brew install azure-cli
   
   # Windows (using PowerShell as Administrator)
   Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
   Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'
   
   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```
   
   **What this does**: Allows you to manage Azure resources from your terminal

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
# Check Azure CLI
az --version
# Expected output: azure-cli 2.x.x or higher

# Check Docker
docker --version
# Expected output: Docker version 24.x.x or higher

# Check Git
git --version
# Expected output: git version 2.x.x or higher
```

---

## Architecture Overview

### Azure Services Used

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Azure Container Apps (Compute)                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │   API    │ │ Speaker  │ │  Draft   │             │  │
│  │  │ Gateway  │ │ Service  │ │ Service  │ ...         │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Managed Databases                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │PostgreSQL│ │ MongoDB  │ │  Redis   │             │  │
│  │  │ Flexible │ │  Atlas   │ │  Cache   │             │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Additional Services                           │  │
│  │  • Container Registry (ACR)                           │  │
│  │  • Key Vault (Secrets Management)                     │  │
│  │  • Application Insights (Monitoring)                  │  │
│  │  • Log Analytics (Logging)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Service Mapping

| DraftGenie Component | Azure Service | Purpose |
|---------------------|---------------|---------|
| Application Services | Azure Container Apps | Serverless container hosting |
| PostgreSQL | Azure Database for PostgreSQL Flexible Server | Managed PostgreSQL database |
| MongoDB | MongoDB Atlas on Azure | Managed MongoDB database |
| Redis | Azure Cache for Redis | Managed Redis cache |
| RabbitMQ | Container App | Message broker (containerized) |
| Qdrant | Container App | Vector database (containerized) |
| Container Images | Azure Container Registry | Private Docker registry |
| Secrets | Azure Key Vault | Secure secrets storage |
| Monitoring | Application Insights | Application monitoring |
| Logging | Log Analytics Workspace | Centralized logging |

---

## Step-by-Step Deployment

### Step 1: Login to Azure

Open your terminal and login to Azure:

```bash
az login
```

**What this does**: Opens your browser to authenticate with Azure. After successful login, you'll see a list of your subscriptions.

If you have multiple subscriptions, set the one you want to use:

```bash
# List all subscriptions
az account list --output table

# Set the subscription you want to use
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

### Step 2: Set Up Environment Variables

Create a file to store your configuration (this makes the commands easier):

```bash
# Create a deployment configuration file
cat > azure-config.sh << 'EOF'
# Azure Configuration
export RESOURCE_GROUP="draftgenie-rg"
export LOCATION="eastus"
export ACR_NAME="draftgenieacr"
export CONTAINER_ENV="draftgenie-env"
export KEY_VAULT_NAME="draftgenie-kv"
export LOG_WORKSPACE="draftgenie-logs"
export APP_INSIGHTS="draftgenie-insights"

# Database Configuration
export POSTGRES_SERVER="draftgenie-postgres"
export REDIS_NAME="draftgenie-redis"

# Your Gemini API Key (replace with your actual key)
export GEMINI_API_KEY="your-gemini-api-key-here"
EOF

# Load the configuration
source azure-config.sh
```

**What this does**: Creates reusable variables for all Azure resources. This prevents typos and makes commands easier to read.

**Important**: Replace `your-gemini-api-key-here` with your actual Gemini API key!

### Step 3: Create Resource Group

A resource group is a container that holds related Azure resources.

```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

**What this does**: Creates a logical container for all DraftGenie resources in the East US region.

**Why East US?**: It's one of the most cost-effective regions with all required services available.

### Step 4: Create Azure Container Registry (ACR)

This is where we'll store our Docker images.

```bash
# Create the registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get the login server
export ACR_LOGIN_SERVER=$(az acr show \
  --name $ACR_NAME \
  --query loginServer \
  --output tsv)

echo "ACR Login Server: $ACR_LOGIN_SERVER"
```

**What this does**: Creates a private Docker registry to store your container images securely.

**SKU Explanation**: 
- Basic: $5/month, 10 GB storage, suitable for development
- Standard: $20/month, 100 GB storage, better for production
- Premium: $50/month, 500 GB storage, geo-replication

### Step 5: Create Key Vault for Secrets

Azure Key Vault securely stores secrets, keys, and certificates.

```bash
az keyvault create \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization false
```

**What this does**: Creates a secure vault to store sensitive information like database passwords and API keys.

### Step 6: Set Up Monitoring & Logging

```bash
# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE \
  --location $LOCATION

# Get workspace ID and key
export LOG_WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE \
  --query customerId \
  --output tsv)

export LOG_WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE \
  --query primarySharedKey \
  --output tsv)

# Create Application Insights
az monitor app-insights component create \
  --app $APP_INSIGHTS \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --workspace $LOG_WORKSPACE

# Get instrumentation key
export APP_INSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey \
  --output tsv)
```

**What this does**: Sets up centralized logging and application monitoring so you can track errors and performance.

### Step 7: Create PostgreSQL Database

```bash
# Generate a secure password
export POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --location $LOCATION \
  --admin-user draftgenie \
  --admin-password $POSTGRES_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 16 \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $POSTGRES_SERVER \
  --database-name draftgenie

# Store password in Key Vault
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "postgres-password" \
  --value $POSTGRES_PASSWORD

echo "PostgreSQL Password stored in Key Vault"
```

**What this does**: Creates a managed PostgreSQL database with automatic backups and updates.

**SKU Explanation**:
- Standard_B1ms: 1 vCore, 2 GB RAM, ~$12/month (good for development)
- Standard_B2s: 2 vCores, 4 GB RAM, ~$60/month (better for production)

**Important**: The password is automatically generated and stored securely in Key Vault.

### Step 8: Create Redis Cache

```bash
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false

# Get Redis connection details
export REDIS_HOST=$(az redis show \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query hostName \
  --output tsv)

export REDIS_KEY=$(az redis list-keys \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query primaryKey \
  --output tsv)

# Store in Key Vault
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "redis-key" \
  --value $REDIS_KEY

echo "Redis connection details stored in Key Vault"
```

**What this does**: Creates a managed Redis cache for session storage and caching.

**SKU Explanation**:
- Basic C0: 250 MB, ~$16/month (development)
- Basic C1: 1 GB, ~$55/month (small production)
- Standard C1: 1 GB with replication, ~$110/month (production with HA)

### Step 9: Set Up MongoDB Atlas

MongoDB Atlas is the recommended managed MongoDB service on Azure.

1. **Sign up for MongoDB Atlas**:
   - Go to: https://www.mongodb.com/cloud/atlas/register
   - Choose "Sign up with Google" or create an account
   - Select "Azure" as your cloud provider

2. **Create a Free Cluster**:
   ```
   - Click "Build a Database"
   - Select "Shared" (Free tier)
   - Choose "Azure" as cloud provider
   - Select same region as your Azure resources (e.g., "East US")
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

   **Security Note**: In production, restrict this to your Azure Container Apps IP ranges.

5. **Get Connection String**:
   ```
   - Go to "Database" in left menu
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace <password> with the password you copied earlier
   ```

6. **Store in Key Vault**:
   ```bash
   # Replace with your actual connection string
   export MONGODB_URL="mongodb+srv://draftgenie:<password>@draftgenie-cluster.xxxxx.mongodb.net/draftgenie?retryWrites=true&w=majority"

   az keyvault secret set \
     --vault-name $KEY_VAULT_NAME \
     --name "mongodb-url" \
     --value $MONGODB_URL
   ```

**What this does**: Sets up a fully managed MongoDB database with automatic backups and scaling.

**Cost**: Free tier includes 512 MB storage, perfect for development and small production workloads.

### Step 10: Create Container Apps Environment

The Container Apps Environment is where all your application containers will run.

```bash
az containerapp env create \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id $LOG_WORKSPACE_ID \
  --logs-workspace-key $LOG_WORKSPACE_KEY
```

**What this does**: Creates a managed environment for running containers with built-in logging and networking.

### Step 11: Clone and Prepare the Application

```bash
# Clone the repository
git clone https://github.com/tan-res-space/draft-genie.git
cd draft-genie

# Login to Azure Container Registry
az acr login --name $ACR_NAME
```

**What this does**: Downloads the DraftGenie source code and authenticates with your container registry.

### Step 12: Build and Push Docker Images

We'll build Docker images for each service and push them to Azure Container Registry.

```bash
# Build and push API Gateway
docker build -f docker/Dockerfile.api-gateway -t $ACR_LOGIN_SERVER/api-gateway:latest .
docker push $ACR_LOGIN_SERVER/api-gateway:latest

# Build and push Draft Service
docker build -f docker/Dockerfile.draft-service -t $ACR_LOGIN_SERVER/draft-service:latest .
docker push $ACR_LOGIN_SERVER/draft-service:latest

# Build and push RAG Service
docker build -f docker/Dockerfile.rag-service -t $ACR_LOGIN_SERVER/rag-service:latest .
docker push $ACR_LOGIN_SERVER/rag-service:latest

# Build and push Evaluation Service
docker build -f docker/Dockerfile.evaluation-service -t $ACR_LOGIN_SERVER/evaluation-service:latest .
docker push $ACR_LOGIN_SERVER/evaluation-service:latest

# Build and push Speaker Service
docker build -f docker/Dockerfile.speaker-service -t $ACR_LOGIN_SERVER/speaker-service:latest .
docker push $ACR_LOGIN_SERVER/speaker-service:latest
```

**What this does**: Packages each service into a Docker container and uploads it to your private registry.

**Time estimate**: 10-15 minutes depending on your internet speed.

**Troubleshooting**: If builds fail, ensure Docker Desktop is running and you have enough disk space (need ~5 GB free).

### Step 13: Deploy Infrastructure Services (RabbitMQ & Qdrant)

These services will run as containers in Azure Container Apps.

```bash
# Deploy RabbitMQ
az containerapp create \
  --name rabbitmq \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image rabbitmq:3.13-management-alpine \
  --target-port 5672 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    RABBITMQ_DEFAULT_USER=draftgenie \
    RABBITMQ_DEFAULT_PASS=secretref:rabbitmq-password \
  --secrets rabbitmq-password=$(openssl rand -base64 32)

# Deploy Qdrant
az containerapp create \
  --name qdrant \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image qdrant/qdrant:v1.7.4 \
  --target-port 6333 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi
```

**What this does**: Deploys RabbitMQ (message broker) and Qdrant (vector database) as managed containers.

**Ingress Explanation**:
- `internal`: Only accessible within the Container Apps environment (secure)
- `external`: Accessible from the internet (use for API Gateway only)

### Step 14: Deploy Application Services

Now we'll deploy the main application services.

```bash
# Get ACR credentials
export ACR_USERNAME=$(az acr credential show \
  --name $ACR_NAME \
  --query username \
  --output tsv)

export ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --query passwords[0].value \
  --output tsv)

# Get secrets from Key Vault
export POSTGRES_PASSWORD=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name postgres-password \
  --query value \
  --output tsv)

export REDIS_KEY=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name redis-key \
  --query value \
  --output tsv)

export MONGODB_URL=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name mongodb-url \
  --query value \
  --output tsv)

# Deploy Speaker Service
az containerapp create \
  --name speaker-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_LOGIN_SERVER/speaker-service:latest \
  --target-port 3001 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    NODE_ENV=production \
    PORT=3001 \
    DATABASE_URL="postgresql://draftgenie:$POSTGRES_PASSWORD@$POSTGRES_SERVER.postgres.database.azure.com:5432/draftgenie?sslmode=require" \
    REDIS_URL="rediss://:$REDIS_KEY@$REDIS_HOST:6380" \
    RABBITMQ_URL="amqp://draftgenie:secretref:rabbitmq-password@rabbitmq:5672/" \
    LOG_LEVEL=info \
  --secrets rabbitmq-password=$(az containerapp show --name rabbitmq --resource-group $RESOURCE_GROUP --query 'properties.template.containers[0].env[?name==`RABBITMQ_DEFAULT_PASS`].secretRef' -o tsv)

# Deploy Draft Service
az containerapp create \
  --name draft-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_LOGIN_SERVER/draft-service:latest \
  --target-port 3002 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3002 \
    MONGODB_URL=$MONGODB_URL \
    QDRANT_URL=http://qdrant:6333 \
    REDIS_URL="rediss://:$REDIS_KEY@$REDIS_HOST:6380" \
    RABBITMQ_URL="amqp://draftgenie:secretref:rabbitmq-password@rabbitmq:5672/" \
    GEMINI_API_KEY=$GEMINI_API_KEY \
    LOG_LEVEL=info

# Deploy RAG Service
az containerapp create \
  --name rag-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_LOGIN_SERVER/rag-service:latest \
  --target-port 3003 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3003 \
    MONGODB_URL=$MONGODB_URL \
    QDRANT_URL=http://qdrant:6333 \
    GEMINI_API_KEY=$GEMINI_API_KEY \
    LOG_LEVEL=info

# Deploy Evaluation Service
az containerapp create \
  --name evaluation-service \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_LOGIN_SERVER/evaluation-service:latest \
  --target-port 3004 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    ENVIRONMENT=production \
    PORT=3004 \
    MONGODB_URL=$MONGODB_URL \
    RABBITMQ_URL="amqp://draftgenie:secretref:rabbitmq-password@rabbitmq:5672/" \
    LOG_LEVEL=info

# Deploy API Gateway (with external ingress)
az containerapp create \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_ENV \
  --image $ACR_LOGIN_SERVER/api-gateway:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    NODE_ENV=production \
    PORT=3000 \
    SPEAKER_SERVICE_URL=http://speaker-service:3001 \
    DRAFT_SERVICE_URL=http://draft-service:3002 \
    RAG_SERVICE_URL=http://rag-service:3003 \
    EVALUATION_SERVICE_URL=http://evaluation-service:3004 \
    JWT_SECRET=secretref:jwt-secret \
    CORS_ORIGIN=* \
    SWAGGER_ENABLED=true \
  --secrets jwt-secret=$(openssl rand -base64 32)

# Get the API Gateway URL
export API_GATEWAY_URL=$(az containerapp show \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "API Gateway URL: https://$API_GATEWAY_URL"
```

**What this does**: Deploys all five application services with proper networking, scaling, and environment variables.

**Resource Allocation**:
- CPU: 0.5-1.0 cores per service (RAG service gets more for AI processing)
- Memory: 1.0-2.0 GB per service (RAG service gets more for model loading)
- Replicas: 1-5 instances (auto-scales based on load)

### Step 15: Run Database Migrations

Now that the Speaker Service is deployed, we need to initialize the PostgreSQL database schema.

```bash
# Get the Speaker Service container app name
export SPEAKER_CONTAINER=$(az containerapp show \
  --name speaker-service \
  --resource-group $RESOURCE_GROUP \
  --query 'properties.template.containers[0].name' \
  --output tsv)

# Run Prisma migrations
az containerapp exec \
  --name speaker-service \
  --resource-group $RESOURCE_GROUP \
  --command "npx prisma migrate deploy"
```

**What this does**: Creates the necessary database tables and schema in PostgreSQL.

**Troubleshooting**: If this fails, you can run migrations locally:
```bash
# Set DATABASE_URL locally
export DATABASE_URL="postgresql://draftgenie:$POSTGRES_PASSWORD@$POSTGRES_SERVER.postgres.database.azure.com:5432/draftgenie?sslmode=require"

# Run migrations
cd apps/speaker-service
npx prisma migrate deploy
```

### Step 16: Verify Deployment

Test that all services are running correctly:

```bash
# Check health of all container apps
az containerapp list \
  --resource-group $RESOURCE_GROUP \
  --query '[].{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}' \
  --output table

# Test the API Gateway
curl https://$API_GATEWAY_URL/api/v1/health

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
- All services show "Running" status
- Health check returns 200 OK
- All service statuses are "healthy"

---

## Environment Variables & Secrets

### Managing Secrets with Key Vault

All sensitive information should be stored in Azure Key Vault:

```bash
# Add a new secret
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "my-secret-name" \
  --value "my-secret-value"

# Retrieve a secret
az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name "my-secret-name" \
  --query value \
  --output tsv

# List all secrets
az keyvault secret list \
  --vault-name $KEY_VAULT_NAME \
  --query '[].name' \
  --output table
```

### Updating Environment Variables

To update environment variables for a running service:

```bash
# Update a single environment variable
az containerapp update \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars "NEW_VAR=new_value"

# Update multiple environment variables
az containerapp update \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "VAR1=value1" \
    "VAR2=value2"
```

**What this does**: Updates environment variables and automatically restarts the container with new values.

### Required Environment Variables by Service

**API Gateway**:
- `NODE_ENV`: production
- `PORT`: 3000
- `SPEAKER_SERVICE_URL`: Internal URL
- `DRAFT_SERVICE_URL`: Internal URL
- `RAG_SERVICE_URL`: Internal URL
- `EVALUATION_SERVICE_URL`: Internal URL
- `JWT_SECRET`: Secret from Key Vault
- `CORS_ORIGIN`: Your domain or *

**Speaker Service**:
- `NODE_ENV`: production
- `PORT`: 3001
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

**Draft Service**:
- `ENVIRONMENT`: production
- `PORT`: 3002
- `MONGODB_URL`: MongoDB connection string
- `QDRANT_URL`: http://qdrant:6333
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `GEMINI_API_KEY`: Your Gemini API key

**RAG Service**:
- `ENVIRONMENT`: production
- `PORT`: 3003
- `MONGODB_URL`: MongoDB connection string
- `QDRANT_URL`: http://qdrant:6333
- `GEMINI_API_KEY`: Your Gemini API key

**Evaluation Service**:
- `ENVIRONMENT`: production
- `PORT`: 3004
- `MONGODB_URL`: MongoDB connection string
- `RABBITMQ_URL`: RabbitMQ connection string

---

## Domain & SSL Configuration

### Option 1: Use Azure-Provided Domain (Easiest)

Azure Container Apps automatically provides an HTTPS endpoint:

```
https://api-gateway.{random-string}.{region}.azurecontainerapps.io
```

**Pros**:
- Free SSL certificate
- No configuration needed
- Works immediately

**Cons**:
- Long, non-branded URL
- Can't customize

### Option 2: Add Custom Domain

If you own a domain (e.g., api.yourdomain.com):

1. **Add Custom Domain to Container App**:
   ```bash
   az containerapp hostname add \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --hostname api.yourdomain.com
   ```

2. **Get Validation Details**:
   ```bash
   az containerapp hostname list \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP
   ```

   This will show you the TXT and CNAME records you need to add.

3. **Add DNS Records** (in your domain registrar):
   ```
   Type: CNAME
   Name: api
   Value: api-gateway.{random-string}.{region}.azurecontainerapps.io

   Type: TXT
   Name: asuid.api
   Value: {validation-code-from-step-2}
   ```

4. **Bind SSL Certificate**:
   ```bash
   az containerapp hostname bind \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --hostname api.yourdomain.com \
     --environment $CONTAINER_ENV \
     --validation-method CNAME
   ```

**What this does**: Configures your custom domain with automatic SSL certificate from Azure.

**Time to propagate**: DNS changes can take 5-60 minutes to propagate globally.

### SSL Certificate Management

Azure Container Apps automatically manages SSL certificates:
- **Automatic renewal**: Certificates renew 45 days before expiration
- **Free**: No cost for managed certificates
- **TLS 1.2+**: Modern security standards

---

## Monitoring & Logging

### Viewing Logs

**Real-time logs** (like `tail -f`):
```bash
# View logs for a specific service
az containerapp logs show \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --follow

# View logs from the last hour
az containerapp logs show \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --since 1h
```

**What this does**: Streams live logs from your container to your terminal.

### Application Insights Dashboard

1. **Open Azure Portal**: https://portal.azure.com
2. **Navigate to Application Insights**: Search for "draftgenie-insights"
3. **View Metrics**:
   - **Live Metrics**: Real-time request/response data
   - **Failures**: Error rates and exceptions
   - **Performance**: Response times and dependencies
   - **Availability**: Uptime monitoring

### Setting Up Alerts

Create an alert when error rate exceeds threshold:

```bash
# Create action group (email notification)
az monitor action-group create \
  --name "draftgenie-alerts" \
  --resource-group $RESOURCE_GROUP \
  --short-name "DGAlerts" \
  --email-receiver \
    name="Admin" \
    email="your-email@example.com"

# Create alert rule for high error rate
az monitor metrics alert create \
  --name "high-error-rate" \
  --resource-group $RESOURCE_GROUP \
  --scopes $(az containerapp show --name api-gateway --resource-group $RESOURCE_GROUP --query id -o tsv) \
  --condition "avg requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action "draftgenie-alerts"
```

**What this does**: Sends you an email when the error rate exceeds 10 failed requests in 5 minutes.

### Log Analytics Queries

Access Log Analytics in Azure Portal to run custom queries:

```kusto
// Find all errors in the last 24 hours
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "ERROR"
| project TimeGenerated, ContainerAppName_s, Log_s
| order by TimeGenerated desc

// Count requests by service
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| summarize RequestCount = count() by ContainerAppName_s
| order by RequestCount desc

// Average response time by endpoint
AppRequests
| where TimeGenerated > ago(1h)
| summarize AvgDuration = avg(DurationMs) by Name
| order by AvgDuration desc
```

**What this does**: Provides powerful querying capabilities for troubleshooting and analytics.

---

## Cost Optimization

### Understanding Costs

**Monthly Cost Breakdown** (estimated):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Container Apps (5 services) | 0.5-1 vCPU, 1-2 GB RAM each | $50-100 |
| PostgreSQL Flexible Server | Standard_B1ms | $12 |
| MongoDB Atlas | Free tier (512 MB) | $0 |
| Redis Cache | Basic C0 (250 MB) | $16 |
| Container Registry | Basic (10 GB) | $5 |
| Log Analytics | 5 GB/month | $10 |
| Application Insights | 5 GB/month | $0 (first 5 GB free) |
| **Total** | | **$93-143/month** |

### Cost Optimization Tips

1. **Use Auto-Scaling Wisely**:
   ```bash
   # Set minimum replicas to 0 for non-critical services (scales to zero when idle)
   az containerapp update \
     --name evaluation-service \
     --resource-group $RESOURCE_GROUP \
     --min-replicas 0 \
     --max-replicas 3
   ```

   **Savings**: Up to 50% on compute costs for low-traffic services

2. **Use Spot Instances** (for non-production):
   - Not directly available in Container Apps, but consider Azure Kubernetes Service (AKS) with spot nodes for dev/staging

3. **Optimize Database Tiers**:
   ```bash
   # Scale down PostgreSQL during off-hours
   az postgres flexible-server update \
     --resource-group $RESOURCE_GROUP \
     --name $POSTGRES_SERVER \
     --sku-name Standard_B1ms  # Smallest tier
   ```

4. **Set Up Budget Alerts**:
   ```bash
   az consumption budget create \
     --resource-group $RESOURCE_GROUP \
     --budget-name "draftgenie-monthly-budget" \
     --amount 200 \
     --time-grain Monthly \
     --start-date $(date +%Y-%m-01) \
     --end-date 2025-12-31
   ```

   **What this does**: Alerts you when spending exceeds $200/month

5. **Use Reserved Instances** (for production):
   - Commit to 1 or 3 years for 30-50% discount
   - Only for stable, long-running workloads

### Free Tier Maximization

- **MongoDB Atlas**: Free tier (512 MB) - sufficient for development
- **Application Insights**: First 5 GB/month free
- **Azure Free Account**: $200 credit for first 30 days
- **Container Apps**: First 180,000 vCPU-seconds and 360,000 GiB-seconds free per month

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Container App Won't Start

**Symptoms**: Container app shows "Provisioning" or "Failed" status

**Diagnosis**:
```bash
# Check container app status
az containerapp show \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --query 'properties.{Status:runningStatus, Message:latestRevisionName}' \
  --output table

# View recent logs
az containerapp logs show \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --tail 100
```

**Common Causes & Solutions**:

1. **Image Pull Failure**:
   ```bash
   # Verify ACR credentials are correct
   az containerapp update \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --registry-server $ACR_LOGIN_SERVER \
     --registry-username $ACR_USERNAME \
     --registry-password $ACR_PASSWORD
   ```

2. **Port Mismatch**:
   - Ensure `--target-port` matches the port your app listens on
   - Check Dockerfile EXPOSE directive

3. **Environment Variable Error**:
   ```bash
   # List current environment variables
   az containerapp show \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --query 'properties.template.containers[0].env' \
     --output table
   ```

#### Issue 2: Database Connection Failures

**Symptoms**: Services start but can't connect to databases

**Diagnosis**:
```bash
# Test PostgreSQL connection
az postgres flexible-server connect \
  --name $POSTGRES_SERVER \
  --resource-group $RESOURCE_GROUP \
  --admin-user draftgenie \
  --admin-password $POSTGRES_PASSWORD

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $POSTGRES_SERVER \
  --output table
```

**Solutions**:

1. **PostgreSQL Firewall**:
   ```bash
   # Allow Azure services
   az postgres flexible-server firewall-rule create \
     --resource-group $RESOURCE_GROUP \
     --name $POSTGRES_SERVER \
     --rule-name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

2. **MongoDB Connection String**:
   - Verify connection string format
   - Ensure password is URL-encoded
   - Check MongoDB Atlas network access settings

3. **Redis SSL**:
   - Use `rediss://` (with double 's') for SSL connections
   - Ensure port 6380 (not 6379) for SSL

#### Issue 3: High Memory Usage / OOM Kills

**Symptoms**: Container restarts frequently, logs show "Out of Memory"

**Diagnosis**:
```bash
# Check resource usage
az monitor metrics list \
  --resource $(az containerapp show --name rag-service --resource-group $RESOURCE_GROUP --query id -o tsv) \
  --metric "UsageNanoCores,WorkingSetBytes" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1M \
  --output table
```

**Solutions**:

1. **Increase Memory Allocation**:
   ```bash
   az containerapp update \
     --name rag-service \
     --resource-group $RESOURCE_GROUP \
     --memory 4.0Gi  # Increase from 2.0Gi
   ```

2. **Optimize Application**:
   - Review application logs for memory leaks
   - Implement connection pooling
   - Add memory limits to Node.js: `NODE_OPTIONS=--max-old-space-size=1536`

#### Issue 4: Slow Response Times

**Symptoms**: API requests take longer than expected

**Diagnosis**:
```bash
# Check Application Insights performance
az monitor app-insights metrics show \
  --app $APP_INSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --metric requests/duration \
  --interval PT1H \
  --output table
```

**Solutions**:

1. **Enable Redis Caching**:
   - Verify Redis connection is working
   - Implement caching in application code

2. **Scale Up Resources**:
   ```bash
   # Increase CPU allocation
   az containerapp update \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --cpu 1.0  # Increase from 0.5
   ```

3. **Add More Replicas**:
   ```bash
   az containerapp update \
     --name api-gateway \
     --resource-group $RESOURCE_GROUP \
     --min-replicas 2 \
     --max-replicas 10
   ```

#### Issue 5: Services Can't Communicate

**Symptoms**: API Gateway returns 502/503 errors when calling backend services

**Diagnosis**:
```bash
# Check if services are in the same environment
az containerapp list \
  --resource-group $RESOURCE_GROUP \
  --query '[].{Name:name, Environment:properties.environmentId}' \
  --output table

# Test internal connectivity
az containerapp exec \
  --name api-gateway \
  --resource-group $RESOURCE_GROUP \
  --command "curl http://speaker-service:3001/health"
```

**Solutions**:

1. **Verify Service URLs**:
   - Internal services use format: `http://service-name:port`
   - No need for FQDN within same environment

2. **Check Ingress Configuration**:
   ```bash
   # Ensure backend services have internal ingress
   az containerapp ingress show \
     --name speaker-service \
     --resource-group $RESOURCE_GROUP
   ```

3. **Restart Services**:
   ```bash
   # Restart a specific service
   az containerapp revision restart \
     --name speaker-service \
     --resource-group $RESOURCE_GROUP
   ```

#### Issue 6: Deployment Takes Too Long

**Symptoms**: `az containerapp create` or `update` commands timeout

**Solutions**:

1. **Use Smaller Images**:
   - Optimize Dockerfiles with multi-stage builds
   - Remove unnecessary dependencies

2. **Increase Timeout**:
   ```bash
   # Set longer timeout (default is 5 minutes)
   az config set core.timeout=1200  # 20 minutes
   ```

3. **Deploy in Stages**:
   - Deploy infrastructure services first
   - Then deploy application services one by one

### Getting Help

1. **Azure Support**:
   - Free support: https://azure.microsoft.com/support/community/
   - Paid support: https://azure.microsoft.com/support/plans/

2. **Check Service Health**:
   ```bash
   az monitor service-health list \
     --resource-group $RESOURCE_GROUP
   ```

3. **Azure Status Page**: https://status.azure.com/

4. **DraftGenie Issues**: https://github.com/tan-res-space/draft-genie/issues

### Useful Commands Reference

```bash
# View all resources in resource group
az resource list \
  --resource-group $RESOURCE_GROUP \
  --output table

# Get cost analysis
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query '[].{Service:instanceName, Cost:pretaxCost}' \
  --output table

# Delete everything (cleanup)
az group delete \
  --name $RESOURCE_GROUP \
  --yes \
  --no-wait

# Export configuration
az group export \
  --name $RESOURCE_GROUP \
  --output json > draftgenie-config.json
```

---

## Next Steps

After successful deployment:

1. **Set Up CI/CD Pipeline**:
   - Use GitHub Actions or Azure DevOps
   - Automate builds and deployments
   - See: https://learn.microsoft.com/azure/container-apps/github-actions

2. **Implement Backup Strategy**:
   - PostgreSQL: Automated backups enabled by default (7-day retention)
   - MongoDB: Configure Atlas backup policy
   - Export critical data regularly

3. **Security Hardening**:
   - Enable Azure AD authentication
   - Implement network policies
   - Regular security scans with Azure Security Center

4. **Performance Testing**:
   - Use Azure Load Testing
   - Identify bottlenecks
   - Optimize based on real traffic patterns

5. **Documentation**:
   - Document your specific configuration
   - Create runbooks for common operations
   - Train team members on Azure tools

---

## Additional Resources

- **Azure Container Apps Documentation**: https://learn.microsoft.com/azure/container-apps/
- **Azure CLI Reference**: https://learn.microsoft.com/cli/azure/
- **Azure Pricing Calculator**: https://azure.microsoft.com/pricing/calculator/
- **Azure Architecture Center**: https://learn.microsoft.com/azure/architecture/
- **DraftGenie Documentation**: https://github.com/tan-res-space/draft-genie/tree/main/docs

---

## Conclusion

Congratulations! You've successfully deployed DraftGenie to Microsoft Azure. Your application is now running on enterprise-grade infrastructure with automatic scaling, monitoring, and high availability.

**What you've accomplished**:
- ✅ Deployed 5 microservices to Azure Container Apps
- ✅ Set up managed databases (PostgreSQL, MongoDB, Redis)
- ✅ Configured secure secrets management with Key Vault
- ✅ Enabled monitoring and logging with Application Insights
- ✅ Implemented auto-scaling and high availability
- ✅ Secured your application with HTTPS

**Your deployment is production-ready!** 🎉

For questions or issues, please refer to the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.


