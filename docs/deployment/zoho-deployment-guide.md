# DraftGenie Deployment Guide - Zoho Cloud

This comprehensive guide will walk you through deploying the DraftGenie application to Zoho Cloud, step by step. This guide is designed for developers with minimal cloud deployment experience.

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

**Important Note**: Zoho Cloud is primarily focused on business applications and doesn't offer a comprehensive IaaS/PaaS platform like AWS, Azure, or GCP. This guide provides a hybrid approach using Zoho's available services combined with third-party managed services.

**Estimated Monthly Cost**: $100-200 USD (depending on usage and tier selection)

**Deployment Time**: 3-4 hours for first-time deployment

---

## Prerequisites

### Required Accounts & Subscriptions

1. **Zoho Cloud Account**
   - Sign up at: https://www.zoho.com/cloud/
   - Free trial available for 15 days
   - Credit card required for paid services

2. **Zoho Catalyst Account** (Serverless Platform)
   - Sign up at: https://catalyst.zoho.com/
   - Free tier: 10 GB bandwidth, 100K requests/month
   - Required for hosting application services

3. **Third-Party Services** (Due to Zoho's limited infrastructure offerings):
   - **MongoDB Atlas**: For MongoDB database
   - **Render.com or Railway.app**: For PostgreSQL (or use Zoho Creator with custom DB)
   - **Upstash**: For Redis (serverless Redis)
   - **CloudAMQP**: For RabbitMQ (managed message queue)

4. **Google Gemini API Key**
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: 60 requests per minute
   - Required for AI-powered features

### Required Tools

Install these tools on your local machine:

1. **Zoho Catalyst CLI (zcatalyst)**
   ```bash
   # Install via npm
   npm install -g zcatalyst-cli
   
   # Verify installation
   zcatalyst --version
   ```
   
   **What this does**: Allows you to manage Zoho Catalyst resources from your terminal

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

4. **Node.js 18+** (required for Catalyst CLI)
   ```bash
   # macOS
   brew install node@18
   
   # Windows/Linux
   # Download from: https://nodejs.org/
   ```

### Verify Installation

Run these commands to verify everything is installed:

```bash
# Check Catalyst CLI
zcatalyst --version
# Expected output: 2.x.x or higher

# Check Docker
docker --version
# Expected output: Docker version 24.x.x or higher

# Check Git
git --version
# Expected output: git version 2.x.x or higher

# Check Node.js
node --version
# Expected output: v18.x.x or higher
```

---

## Architecture Overview

### Zoho Cloud + Third-Party Services Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Hybrid Cloud Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Zoho Catalyst (Serverless Functions)          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │   API    │ │ Speaker  │ │  Draft   │             │  │
│  │  │ Gateway  │ │ Service  │ │ Service  │ ...         │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Third-Party Managed Services                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │  │
│  │  │PostgreSQL│ │ MongoDB  │ │  Redis   │             │  │
│  │  │ (Render) │ │  Atlas   │ │ (Upstash)│             │  │
│  │  └──────────┘ └──────────┘ └──────────┘             │  │
│  │  ┌──────────┐ ┌──────────┐                          │  │
│  │  │ RabbitMQ │ │  Qdrant  │                          │  │
│  │  │(CloudAMQP│ │ (Docker) │                          │  │
│  │  └──────────┘ └──────────┘                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Zoho Services                                 │  │
│  │  • Catalyst Data Store (NoSQL - optional)             │  │
│  │  • Catalyst Cache (Redis alternative - optional)      │  │
│  │  • Catalyst File Store (Object storage)               │  │
│  │  • Zoho Analytics (Monitoring & Dashboards)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Service Mapping

| DraftGenie Component | Service Provider | Purpose |
|---------------------|------------------|---------|
| Application Services | Zoho Catalyst Functions | Serverless Node.js/Python functions |
| PostgreSQL | Render.com (Free tier) | Managed PostgreSQL database |
| MongoDB | MongoDB Atlas | Managed MongoDB database |
| Redis | Upstash (Free tier) | Serverless Redis cache |
| RabbitMQ | CloudAMQP (Free tier) | Managed message broker |
| Qdrant | Railway.app or Render | Vector database (containerized) |
| Secrets | Catalyst Environment Variables | Secure configuration storage |
| Monitoring | Zoho Analytics | Application monitoring & dashboards |
| Logging | Catalyst Logs | Centralized logging |

**Why Hybrid Approach?**
- Zoho Cloud doesn't offer comprehensive IaaS/PaaS services like AWS/Azure/GCP
- Zoho Catalyst is excellent for serverless functions but lacks managed databases
- Using best-in-class managed services ensures reliability and reduces operational overhead

---

## Step-by-Step Deployment

### Step 1: Login to Zoho Catalyst

Open your terminal and login to Zoho Catalyst:

```bash
# Login to Catalyst
zcatalyst login

# This will open your browser for authentication
# After successful login, you'll see a confirmation message
```

**What this does**: Authenticates your CLI with Zoho Catalyst.

### Step 2: Create a New Catalyst Project

```bash
# Create a new project
zcatalyst init

# Follow the prompts:
# - Project Name: draftgenie
# - Project Type: Advanced I/O Functions
# - Runtime: Node.js 18 (for API Gateway and Speaker Service)
```

**What this does**: Creates a new Catalyst project structure.

**Note**: We'll create separate projects for each service since Catalyst organizes by project.

### Step 3: Set Up Environment Variables

Create a configuration file for easy reference:

```bash
# Create a deployment configuration file
cat > zoho-config.sh << 'EOF'
# Zoho Configuration
export CATALYST_PROJECT_ID="your-project-id"
export CATALYST_ORG_ID="your-org-id"

# Your Gemini API Key (replace with your actual key)
export GEMINI_API_KEY="your-gemini-api-key-here"

# Third-party service URLs (will be filled in later steps)
export POSTGRES_URL=""
export MONGODB_URL=""
export REDIS_URL=""
export RABBITMQ_URL=""
export QDRANT_URL=""
EOF

# Load the configuration
source zoho-config.sh
```

**What this does**: Creates reusable variables for all service configurations.

**Important**: Replace `your-gemini-api-key-here` with your actual Gemini API key!

### Step 4: Set Up PostgreSQL (Using Render.com)

Since Zoho doesn't offer managed PostgreSQL, we'll use Render.com's free tier:

1. **Sign up for Render**:
   - Go to: https://render.com/
   - Click "Get Started for Free"
   - Sign up with GitHub or email

2. **Create PostgreSQL Database**:
   ```
   - Click "New +" → "PostgreSQL"
   - Name: draftgenie-postgres
   - Database: draftgenie
   - User: draftgenie
   - Region: Choose closest to your users (e.g., Oregon, USA)
   - Plan: Free (1 GB storage, expires after 90 days)
   - Click "Create Database"
   ```

3. **Get Connection Details**:
   ```
   - Wait for database to be created (~2 minutes)
   - Copy "External Database URL"
   - Format: postgresql://user:password@host:port/database
   ```

4. **Store Connection String**:
   ```bash
   # Update your config file
   export POSTGRES_URL="postgresql://draftgenie:xxxxx@dpg-xxxxx.oregon-postgres.render.com/draftgenie"
   
   # Save to config
   echo "export POSTGRES_URL=\"$POSTGRES_URL\"" >> zoho-config.sh
   ```

**What this does**: Sets up a free managed PostgreSQL database.

**Free Tier Limits**: 1 GB storage, 90-day expiration (can be extended or upgraded)

**Alternative**: Use Railway.app, Supabase, or Neon for PostgreSQL (all offer free tiers)

### Step 5: Set Up MongoDB Atlas

1. **Sign up for MongoDB Atlas**:
   - Go to: https://www.mongodb.com/cloud/atlas/register
   - Choose "Sign up with Google" or create an account

2. **Create a Free Cluster**:
   ```
   - Click "Build a Database"
   - Select "Shared" (Free tier)
   - Choose cloud provider: AWS, GCP, or Azure
   - Select region closest to your users
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
   - Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Click "Confirm"
   ```

5. **Get Connection String**:
   ```
   - Go to "Database" in left menu
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace <password> with the password you copied earlier
   ```

6. **Store Connection String**:
   ```bash
   export MONGODB_URL="mongodb+srv://draftgenie:<password>@draftgenie-cluster.xxxxx.mongodb.net/draftgenie?retryWrites=true&w=majority"
   
   echo "export MONGODB_URL=\"$MONGODB_URL\"" >> zoho-config.sh
   ```

**What this does**: Sets up a fully managed MongoDB database with automatic backups.

**Cost**: Free tier includes 512 MB storage, perfect for development.

### Step 6: Set Up Redis (Using Upstash)

Upstash provides serverless Redis with a generous free tier:

1. **Sign up for Upstash**:
   - Go to: https://upstash.com/
   - Click "Get Started"
   - Sign up with GitHub or email

2. **Create Redis Database**:
   ```
   - Click "Create Database"
   - Name: draftgenie-redis
   - Type: Regional
   - Region: Choose closest to your users
   - TLS: Enabled (recommended)
   - Eviction: No eviction
   - Click "Create"
   ```

3. **Get Connection Details**:
   ```
   - Click on your database
   - Copy "UPSTASH_REDIS_REST_URL" and "UPSTASH_REDIS_REST_TOKEN"
   - Or use the Redis URL format
   ```

4. **Store Connection String**:
   ```bash
   export REDIS_URL="rediss://default:xxxxx@us1-xxxxx.upstash.io:6379"

   echo "export REDIS_URL=\"$REDIS_URL\"" >> zoho-config.sh
   ```

**What this does**: Sets up a serverless Redis cache with automatic scaling.

**Free Tier**: 10,000 commands/day, 256 MB storage

### Step 7: Set Up RabbitMQ (Using CloudAMQP)

CloudAMQP provides managed RabbitMQ with a free tier:

1. **Sign up for CloudAMQP**:
   - Go to: https://www.cloudamqp.com/
   - Click "Sign Up"
   - Sign up with GitHub or email

2. **Create RabbitMQ Instance**:
   ```
   - Click "Create New Instance"
   - Name: draftgenie-rabbitmq
   - Plan: Little Lemur (Free)
   - Region: Choose closest to your users
   - Click "Create Instance"
   ```

3. **Get Connection Details**:
   ```
   - Click on your instance
   - Copy "AMQP URL"
   - Format: amqps://user:password@host/vhost
   ```

4. **Store Connection String**:
   ```bash
   export RABBITMQ_URL="amqps://xxxxx:xxxxx@xxx.cloudamqp.com/xxxxx"

   echo "export RABBITMQ_URL=\"$RABBITMQ_URL\"" >> zoho-config.sh
   ```

**What this does**: Sets up a managed RabbitMQ message broker.

**Free Tier**: 1 million messages/month, 20 connections

### Step 8: Set Up Qdrant (Using Render.com)

Deploy Qdrant as a containerized service:

1. **Create Qdrant Service on Render**:
   ```
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Choose "Deploy an existing image from a registry"
   - Image URL: qdrant/qdrant:v1.7.4
   - Name: draftgenie-qdrant
   - Region: Same as PostgreSQL
   - Plan: Free (512 MB RAM)
   - Click "Create Web Service"
   ```

2. **Configure Qdrant**:
   ```
   - Environment Variables:
     * QDRANT__SERVICE__HTTP_PORT: 6333
   - Health Check Path: /healthz
   ```

3. **Get Qdrant URL**:
   ```
   - Copy the service URL (e.g., https://draftgenie-qdrant.onrender.com)
   ```

4. **Store Qdrant URL**:
   ```bash
   export QDRANT_URL="https://draftgenie-qdrant.onrender.com"

   echo "export QDRANT_URL=\"$QDRANT_URL\"" >> zoho-config.sh
   ```

**What this does**: Deploys Qdrant vector database as a containerized service.

**Free Tier**: 512 MB RAM, spins down after 15 minutes of inactivity

### Step 9: Clone and Prepare the Application

```bash
# Clone the repository
git clone https://github.com/tan-res-space/draft-genie.git
cd draft-genie

# Load configuration
source zoho-config.sh
```

**What this does**: Downloads the DraftGenie source code.

### Step 10: Adapt Services for Catalyst

Zoho Catalyst uses a specific project structure. We need to adapt our services:

**Important Note**: Catalyst functions have limitations:
- Maximum execution time: 60 seconds
- Maximum memory: 512 MB per function
- No persistent storage (use Catalyst Data Store or external databases)

Due to these limitations, we'll deploy services as follows:
- **API Gateway**: Catalyst Advanced I/O Function
- **Speaker Service**: Catalyst Advanced I/O Function
- **Draft/RAG/Evaluation Services**: Deploy to Render.com or Railway.app as containers (Catalyst can't handle Python ML workloads efficiently)

### Step 11: Deploy API Gateway to Catalyst

1. **Create Catalyst Function for API Gateway**:
   ```bash
   # Create a new Catalyst project
   mkdir catalyst-api-gateway
   cd catalyst-api-gateway

   zcatalyst init
   # Choose: Advanced I/O Functions
   # Runtime: Node.js 18
   ```

2. **Adapt API Gateway Code**:
   ```bash
   # Copy API Gateway source
   cp -r ../services/api-gateway/src/* functions/api-gateway/

   # Install dependencies
   cd functions/api-gateway
   npm install
   ```

3. **Configure Environment Variables**:
   ```bash
   # Set environment variables in Catalyst
   zcatalyst env:set SPEAKER_SERVICE_URL="https://draftgenie-speaker.onrender.com"
   zcatalyst env:set DRAFT_SERVICE_URL="https://draftgenie-draft.onrender.com"
   zcatalyst env:set RAG_SERVICE_URL="https://draftgenie-rag.onrender.com"
   zcatalyst env:set EVALUATION_SERVICE_URL="https://draftgenie-evaluation.onrender.com"
   zcatalyst env:set JWT_SECRET="$(openssl rand -base64 32)"
   zcatalyst env:set NODE_ENV="production"
   ```

4. **Deploy to Catalyst**:
   ```bash
   # Deploy the function
   zcatalyst deploy

   # Get the function URL
   zcatalyst functions:list
   ```

**What this does**: Deploys the API Gateway as a serverless function on Catalyst.

**Limitations**:
- 60-second timeout (should be sufficient for API gateway)
- Cold starts may add 1-2 seconds latency

### Step 12: Deploy Speaker Service to Catalyst

Similar to API Gateway:

```bash
# Create Catalyst project
mkdir catalyst-speaker-service
cd catalyst-speaker-service

zcatalyst init
# Choose: Advanced I/O Functions
# Runtime: Node.js 18

# Copy source code
cp -r ../apps/speaker-service/src/* functions/speaker-service/

# Install dependencies
cd functions/speaker-service
npm install

# Set environment variables
zcatalyst env:set DATABASE_URL="$POSTGRES_URL"
zcatalyst env:set REDIS_URL="$REDIS_URL"
zcatalyst env:set RABBITMQ_URL="$RABBITMQ_URL"
zcatalyst env:set NODE_ENV="production"

# Deploy
zcatalyst deploy
```

**What this does**: Deploys the Speaker Service as a serverless function.

### Step 13: Deploy Python Services to Render.com

Since Catalyst doesn't support Python well for ML workloads, we'll deploy Python services to Render:

1. **Create render.yaml** in project root:
   ```yaml
   services:
     - type: web
       name: draftgenie-draft
       runtime: python
       buildCommand: "cd services/draft-service && pip install -r requirements.txt"
       startCommand: "cd services/draft-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
       envVars:
         - key: ENVIRONMENT
           value: production
         - key: MONGODB_URL
           sync: false
         - key: QDRANT_URL
           sync: false
         - key: REDIS_URL
           sync: false
         - key: RABBITMQ_URL
           sync: false
         - key: GEMINI_API_KEY
           sync: false
       plan: free

     - type: web
       name: draftgenie-rag
       runtime: python
       buildCommand: "cd services/rag-service && pip install -r requirements.txt"
       startCommand: "cd services/rag-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
       envVars:
         - key: ENVIRONMENT
           value: production
         - key: MONGODB_URL
           sync: false
         - key: QDRANT_URL
           sync: false
         - key: GEMINI_API_KEY
           sync: false
       plan: free

     - type: web
       name: draftgenie-evaluation
       runtime: python
       buildCommand: "cd services/evaluation-service && pip install -r requirements.txt"
       startCommand: "cd services/evaluation-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
       envVars:
         - key: ENVIRONMENT
           value: production
         - key: MONGODB_URL
           sync: false
         - key: RABBITMQ_URL
           sync: false
       plan: free
   ```

2. **Create requirements.txt** for each Python service:
   ```bash
   # For each Python service
   cd services/draft-service
   poetry export -f requirements.txt --output requirements.txt --without-hashes

   cd ../rag-service
   poetry export -f requirements.txt --output requirements.txt --without-hashes

   cd ../evaluation-service
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

3. **Deploy to Render**:
   ```
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository
   - Render will detect render.yaml and create all services
   - Set environment variables for each service in Render dashboard
   ```

4. **Set Environment Variables** in Render dashboard for each service:
   - MONGODB_URL: Your MongoDB Atlas connection string
   - QDRANT_URL: Your Qdrant URL
   - REDIS_URL: Your Upstash Redis URL
   - RABBITMQ_URL: Your CloudAMQP URL
   - GEMINI_API_KEY: Your Gemini API key

**What this does**: Deploys all Python services as containerized web services on Render.

**Free Tier**: 512 MB RAM per service, spins down after 15 minutes of inactivity

### Step 14: Run Database Migrations

Now that services are deployed, initialize the PostgreSQL database:

```bash
# Install Prisma CLI
npm install -g prisma

# Set DATABASE_URL
export DATABASE_URL="$POSTGRES_URL"

# Run migrations
cd apps/speaker-service
npx prisma migrate deploy

# Verify
npx prisma db pull
```

**What this does**: Creates the necessary database tables and schema in PostgreSQL.

### Step 15: Verify Deployment

Test that all services are running correctly:

```bash
# Get Catalyst function URLs
zcatalyst functions:list

# Test API Gateway
export API_GATEWAY_URL="https://your-catalyst-function-url.catalyst.zoho.com"
curl $API_GATEWAY_URL/api/v1/health

# Test Speaker Service
export SPEAKER_SERVICE_URL="https://your-speaker-function-url.catalyst.zoho.com"
curl $SPEAKER_SERVICE_URL/health

# Test Python services on Render
curl https://draftgenie-draft.onrender.com/health
curl https://draftgenie-rag.onrender.com/health
curl https://draftgenie-evaluation.onrender.com/health

# Expected response from health endpoint:
# {
#   "status": "ok",
#   "timestamp": "2024-01-15T10:30:00.000Z"
# }
```

**What this does**: Verifies that all services are running and accessible.

**Success Indicators**:
- All services return 200 OK
- Health checks show "ok" status
- No connection errors in logs

---

## Environment Variables & Secrets

### Managing Secrets in Catalyst

Catalyst stores environment variables securely:

```bash
# Set a new environment variable
zcatalyst env:set SECRET_NAME="secret-value"

# List all environment variables
zcatalyst env:list

# Remove an environment variable
zcatalyst env:unset SECRET_NAME

# Update an environment variable
zcatalyst env:set SECRET_NAME="new-value"
```

**What this does**: Manages environment variables for Catalyst functions.

**Security**: Environment variables are encrypted at rest and only accessible to your functions.

### Managing Secrets in Render

For services deployed on Render:

1. **Via Dashboard**:
   ```
   - Go to your service in Render Dashboard
   - Click "Environment" tab
   - Click "Add Environment Variable"
   - Enter key and value
   - Click "Save Changes"
   ```

2. **Via render.yaml**:
   ```yaml
   envVars:
     - key: SECRET_NAME
       sync: false  # Don't sync from repo, set manually
   ```

**What this does**: Stores secrets securely in Render's environment.

### Required Environment Variables by Service

**API Gateway (Catalyst)**:
- `NODE_ENV`: production
- `SPEAKER_SERVICE_URL`: Catalyst or Render URL
- `DRAFT_SERVICE_URL`: Render URL
- `RAG_SERVICE_URL`: Render URL
- `EVALUATION_SERVICE_URL`: Render URL
- `JWT_SECRET`: Random secure string
- `CORS_ORIGIN`: * or your domain
- `SWAGGER_ENABLED`: true

**Speaker Service (Catalyst)**:
- `NODE_ENV`: production
- `DATABASE_URL`: PostgreSQL connection string (Render)
- `REDIS_URL`: Upstash Redis URL
- `RABBITMQ_URL`: CloudAMQP URL
- `LOG_LEVEL`: info

**Draft Service (Render)**:
- `ENVIRONMENT`: production
- `PORT`: 10000 (Render default)
- `MONGODB_URL`: MongoDB Atlas connection string
- `QDRANT_URL`: Qdrant Render URL
- `REDIS_URL`: Upstash Redis URL
- `RABBITMQ_URL`: CloudAMQP URL
- `GEMINI_API_KEY`: Your Gemini API key
- `LOG_LEVEL`: info

**RAG Service (Render)**:
- `ENVIRONMENT`: production
- `PORT`: 10000
- `MONGODB_URL`: MongoDB Atlas connection string
- `QDRANT_URL`: Qdrant Render URL
- `GEMINI_API_KEY`: Your Gemini API key
- `LOG_LEVEL`: info

**Evaluation Service (Render)**:
- `ENVIRONMENT`: production
- `PORT`: 10000
- `MONGODB_URL`: MongoDB Atlas connection string
- `RABBITMQ_URL`: CloudAMQP URL
- `LOG_LEVEL`: info

---

## Domain & SSL Configuration

### Option 1: Use Provided Domains (Easiest)

Both Catalyst and Render provide HTTPS endpoints automatically:

**Catalyst Functions**:
```
https://your-function-name-{project-id}.catalyst.zoho.com
```

**Render Services**:
```
https://your-service-name.onrender.com
```

**Pros**:
- Free SSL certificates
- No configuration needed
- Works immediately
- Automatic renewal

**Cons**:
- Long, non-branded URLs
- Can't customize

### Option 2: Add Custom Domain to Catalyst

If you own a domain (e.g., api.yourdomain.com):

1. **Add Custom Domain in Catalyst Console**:
   ```
   - Go to Catalyst Console: https://console.catalyst.zoho.com
   - Select your project
   - Go to "Settings" → "Custom Domains"
   - Click "Add Domain"
   - Enter your domain: api.yourdomain.com
   - Click "Add"
   ```

2. **Get DNS Configuration**:
   ```
   - Catalyst will show you the CNAME record to add
   - Example: CNAME api → catalyst-proxy.zoho.com
   ```

3. **Add DNS Records** (in your domain registrar):
   ```
   Type: CNAME
   Name: api
   Value: catalyst-proxy.zoho.com
   TTL: 3600
   ```

4. **Verify Domain**:
   ```
   - Wait for DNS propagation (5-60 minutes)
   - Catalyst will automatically verify and provision SSL
   ```

**What this does**: Configures your custom domain with automatic SSL certificate from Zoho.

### Option 3: Add Custom Domain to Render

For Render services:

1. **Add Custom Domain**:
   ```
   - Go to your service in Render Dashboard
   - Click "Settings" tab
   - Scroll to "Custom Domains"
   - Click "Add Custom Domain"
   - Enter your domain: draft.yourdomain.com
   ```

2. **Add DNS Records**:
   ```
   Type: CNAME
   Name: draft
   Value: your-service-name.onrender.com
   ```

3. **SSL Certificate**:
   - Render automatically provisions Let's Encrypt SSL
   - No additional configuration needed

**What this does**: Configures custom domain with free SSL certificate.

### SSL Certificate Management

Both Catalyst and Render automatically manage SSL certificates:
- **Automatic provisioning**: Certificates are created when you add a domain
- **Automatic renewal**: Certificates renew before expiration
- **Free**: No cost for managed certificates
- **TLS 1.2+**: Modern security standards

---

## Monitoring & Logging

### Viewing Logs in Catalyst

**Via Catalyst Console**:
1. Go to: https://console.catalyst.zoho.com
2. Select your project
3. Click "Functions" in left menu
4. Click on a function
5. Click "Logs" tab
6. Logs stream in real-time

**Via CLI**:
```bash
# View recent logs
zcatalyst logs --function-name api-gateway

# Stream logs in real-time
zcatalyst logs --function-name api-gateway --tail

# Filter by severity
zcatalyst logs --function-name api-gateway --level error
```

**What this does**: Retrieves and displays logs from Catalyst functions.

### Viewing Logs in Render

**Via Dashboard**:
1. Go to your service in Render Dashboard
2. Click "Logs" tab
3. Logs stream in real-time
4. Use search to filter logs

**Via CLI** (if using Render CLI):
```bash
# Install Render CLI
npm install -g @render/cli

# Login
render login

# View logs
render logs draftgenie-draft

# Stream logs
render logs draftgenie-draft --tail
```

**What this does**: Displays logs from Render services.

### Setting Up Zoho Analytics for Monitoring

Zoho Analytics can be used to create dashboards and monitor your application:

1. **Sign up for Zoho Analytics**:
   - Go to: https://www.zoho.com/analytics/
   - Sign up (free tier available)

2. **Create a Workspace**:
   ```
   - Click "Create Workspace"
   - Name: DraftGenie Monitoring
   - Click "Create"
   ```

3. **Import Logs** (via API or CSV):
   ```
   - Use Catalyst's logging API to export logs
   - Import into Zoho Analytics
   - Create custom reports and dashboards
   ```

4. **Create Dashboard**:
   ```
   - Add widgets for:
     * Request count by service
     * Error rate over time
     * Response time percentiles
     * Active users
   ```

**What this does**: Provides visual monitoring and analytics for your application.

**Alternative**: Use Render's built-in metrics or integrate with external monitoring tools like Datadog, New Relic, or Sentry.

### Setting Up Alerts

**Catalyst Alerts** (via Zoho Analytics):
```
- Create a report with your alert condition
- Click "Alert" → "Create Alert"
- Set threshold (e.g., error rate > 5%)
- Add email recipients
- Set frequency (e.g., check every 5 minutes)
```

**Render Alerts**:
```
- Render sends email alerts for:
  * Service crashes
  * Deployment failures
  * Health check failures
- Configure in service settings
```

**Third-Party Monitoring** (Recommended for Production):

1. **Sentry** (Error Tracking):
   ```bash
   # Install Sentry SDK
   npm install @sentry/node

   # Initialize in your code
   import * as Sentry from "@sentry/node";

   Sentry.init({
     dsn: "your-sentry-dsn",
     environment: "production",
   });
   ```

2. **Uptime Robot** (Uptime Monitoring):
   ```
   - Sign up at: https://uptimerobot.com/
   - Add monitors for each service URL
   - Get alerts via email/SMS when services are down
   - Free tier: 50 monitors, 5-minute checks
   ```

### Log Aggregation

Since logs are spread across Catalyst and Render, consider using a log aggregation service:

**Option 1: Logtail** (formerly Timber.io)
```bash
# Install Logtail
npm install @logtail/node

# Send logs to Logtail
import { Logtail } from "@logtail/node";
const logtail = new Logtail("your-source-token");

logtail.info("Application started");
```

**Option 2: Better Stack** (Logs + Uptime)
- Sign up at: https://betterstack.com/
- Free tier: 1 GB logs/month
- Unified dashboard for all services

---

## Cost Optimization

### Understanding Costs

**Monthly Cost Breakdown** (using free tiers):

| Service | Provider | Configuration | Monthly Cost |
|---------|----------|---------------|--------------|
| API Gateway | Zoho Catalyst | 100K requests | $0 (free tier) |
| Speaker Service | Zoho Catalyst | 50K requests | $0 (free tier) |
| Draft Service | Render | 512 MB RAM | $0 (free tier) |
| RAG Service | Render | 512 MB RAM | $0 (free tier) |
| Evaluation Service | Render | 512 MB RAM | $0 (free tier) |
| PostgreSQL | Render | 1 GB storage | $0 (free tier, 90 days) |
| MongoDB | Atlas | 512 MB storage | $0 (free tier) |
| Redis | Upstash | 10K commands/day | $0 (free tier) |
| RabbitMQ | CloudAMQP | 1M messages/month | $0 (free tier) |
| Qdrant | Render | 512 MB RAM | $0 (free tier) |
| **Total** | | | **$0/month** |

**After Free Tier Limits**:

| Service | Paid Tier | Monthly Cost |
|---------|-----------|--------------|
| Catalyst Functions | 1M requests | $2 |
| Render Services (3x) | 512 MB RAM each | $21 ($7 each) |
| PostgreSQL (Render) | 1 GB storage | $7 |
| Redis (Upstash) | 100K commands/day | $10 |
| RabbitMQ (CloudAMQP) | 10M messages/month | $19 |
| **Total** | | **$59/month** |

**Production Tier** (recommended for production):

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| Catalyst Functions | 5M requests | $10 |
| Render Services (3x) | 2 GB RAM each | $75 ($25 each) |
| PostgreSQL (Render) | 10 GB storage | $20 |
| MongoDB Atlas | 2 GB storage | $9 |
| Redis (Upstash) | 1M commands/day | $40 |
| RabbitMQ (CloudAMQP) | 100M messages/month | $99 |
| **Total** | | **$253/month** |

### Cost Optimization Tips

1. **Maximize Free Tiers**:
   ```
   - Catalyst: 100K requests/month free
   - Render: 750 hours/month free (enough for 1 service running 24/7)
   - MongoDB Atlas: 512 MB free forever
   - Upstash: 10K commands/day free
   - CloudAMQP: 1M messages/month free
   ```

2. **Optimize Catalyst Functions**:
   ```bash
   # Reduce function memory to minimum needed
   # Edit catalyst-config.json
   {
     "memory": 256,  // MB (default is 512)
     "timeout": 30   // seconds (reduce if possible)
   }
   ```

   **Savings**: Lower memory = lower costs

3. **Use Render's Free Tier Wisely**:
   - Free services spin down after 15 minutes of inactivity
   - First request after spin-down takes 30-60 seconds (cold start)
   - Keep critical services (API Gateway) on paid tier for instant response
   - Use free tier for background services (Evaluation Service)

4. **Optimize Database Usage**:
   ```
   - Use connection pooling to reduce connections
   - Implement caching with Redis to reduce database queries
   - Archive old data to reduce storage costs
   ```

5. **Monitor Usage**:
   ```bash
   # Check Catalyst usage
   zcatalyst usage

   # Check Render usage in dashboard
   # Go to Account → Usage
   ```

6. **Set Up Budget Alerts**:
   - Catalyst: Set up alerts in Zoho Analytics
   - Render: Monitor usage in dashboard
   - Third-party services: Set up billing alerts in each platform

7. **Optimize Cold Starts**:
   ```
   - Keep container images small
   - Minimize dependencies
   - Use health check pings to keep services warm (if needed)
   ```

8. **Use Caching Aggressively**:
   ```
   - Cache API responses in Redis
   - Use CDN for static assets
   - Implement application-level caching
   ```

### Free Tier Limitations

**Catalyst**:
- 100K requests/month
- 10 GB bandwidth/month
- 60-second timeout
- 512 MB memory per function

**Render**:
- 750 hours/month (1 service 24/7)
- 512 MB RAM
- Services spin down after 15 minutes
- 100 GB bandwidth/month

**MongoDB Atlas**:
- 512 MB storage
- Shared CPU
- No backups (manual only)

**Upstash Redis**:
- 10K commands/day
- 256 MB storage
- Single region

**CloudAMQP**:
- 1M messages/month
- 20 connections
- Shared instance

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Catalyst Function Won't Deploy

**Symptoms**: `zcatalyst deploy` fails or function shows error status

**Diagnosis**:
```bash
# Check deployment logs
zcatalyst logs --function-name api-gateway

# Verify project structure
zcatalyst project:info

# Check function configuration
cat catalyst-config.json
```

**Common Causes & Solutions**:

1. **Invalid Project Structure**:
   ```bash
   # Ensure correct structure
   # project-root/
   #   functions/
   #     function-name/
   #       index.js
   #       package.json
   ```

2. **Missing Dependencies**:
   ```bash
   # Install all dependencies
   cd functions/api-gateway
   npm install

   # Verify package.json is correct
   cat package.json
   ```

3. **Syntax Errors**:
   ```bash
   # Test function locally
   node index.js

   # Check for errors
   npm run lint
   ```

4. **Timeout During Deployment**:
   ```bash
   # Reduce dependencies
   # Remove unused packages from package.json
   npm prune
   ```

#### Issue 2: Render Service Won't Start

**Symptoms**: Service shows "Deploy failed" or "Build failed"

**Diagnosis**:
```
- Check build logs in Render Dashboard
- Look for error messages during build or start
```

**Common Causes & Solutions**:

1. **Build Command Failure**:
   ```yaml
   # Verify build command in render.yaml
   buildCommand: "cd services/draft-service && pip install -r requirements.txt"

   # Check requirements.txt exists and is valid
   ```

2. **Start Command Failure**:
   ```yaml
   # Verify start command
   startCommand: "cd services/draft-service && uvicorn app.main:app --host 0.0.0.0 --port $PORT"

   # Ensure PORT environment variable is used
   ```

3. **Missing Environment Variables**:
   ```
   - Go to service settings
   - Check all required env vars are set
   - Verify values are correct (no typos)
   ```

4. **Port Mismatch**:
   ```python
   # Ensure your app uses PORT from environment
   import os
   port = int(os.environ.get("PORT", 10000))
   uvicorn.run(app, host="0.0.0.0", port=port)
   ```

#### Issue 3: Database Connection Failures

**Symptoms**: Services start but can't connect to databases

**Diagnosis**:
```bash
# Test PostgreSQL connection
psql "$POSTGRES_URL"

# Test MongoDB connection
mongosh "$MONGODB_URL"

# Test Redis connection
redis-cli -u "$REDIS_URL" ping
```

**Solutions**:

1. **PostgreSQL Connection Issues**:
   ```bash
   # Verify connection string format
   # postgresql://user:password@host:port/database

   # Check if database is running (Render dashboard)
   # Verify firewall rules allow connections
   ```

2. **MongoDB Connection String**:
   ```bash
   # Ensure password is URL-encoded
   # Replace special characters:
   # @ → %40
   # : → %3A
   # / → %2F

   # Verify MongoDB Atlas network access
   # Should allow 0.0.0.0/0 or specific IPs
   ```

3. **Redis Connection**:
   ```bash
   # Verify Upstash URL format
   # rediss://default:password@host:port

   # Check if using TLS (rediss:// not redis://)
   ```

4. **RabbitMQ Connection**:
   ```bash
   # Verify CloudAMQP URL format
   # amqps://user:password@host/vhost

   # Check connection limits (20 for free tier)
   # Close unused connections
   ```

#### Issue 4: Cold Start Latency

**Symptoms**: First request after idle period is very slow (30-60 seconds)

**Explanation**: Render's free tier spins down services after 15 minutes of inactivity.

**Solutions**:

1. **Upgrade to Paid Tier** (recommended for production):
   ```
   - Go to service settings in Render
   - Upgrade to Starter plan ($7/month)
   - Service stays running 24/7
   ```

2. **Keep Services Warm** (free tier workaround):
   ```bash
   # Use a cron job or external service to ping every 10 minutes
   # Example using cron-job.org:
   # - Sign up at https://cron-job.org/
   # - Create job to ping https://your-service.onrender.com/health
   # - Set interval: Every 10 minutes
   ```

3. **Optimize Cold Start Time**:
   ```
   - Reduce dependencies
   - Use smaller base images
   - Minimize initialization code
   ```

#### Issue 5: Catalyst Function Timeout

**Symptoms**: Function returns 504 Gateway Timeout

**Diagnosis**:
```bash
# Check function logs
zcatalyst logs --function-name api-gateway

# Look for long-running operations
```

**Solutions**:

1. **Increase Timeout** (max 60 seconds):
   ```json
   // catalyst-config.json
   {
     "timeout": 60
   }
   ```

2. **Optimize Function Code**:
   ```javascript
   // Use async/await properly
   // Avoid blocking operations
   // Implement timeouts for external calls

   const response = await fetch(url, {
     timeout: 5000  // 5 second timeout
   });
   ```

3. **Move Long Operations to Background**:
   ```
   - Use Catalyst Cron for scheduled tasks
   - Use message queues for async processing
   - Don't wait for non-critical operations
   ```

#### Issue 6: High Memory Usage

**Symptoms**: Catalyst function or Render service crashes with OOM error

**Diagnosis**:
```bash
# Check Catalyst logs for memory errors
zcatalyst logs --function-name api-gateway | grep -i memory

# Check Render metrics in dashboard
```

**Solutions**:

1. **Increase Memory Allocation**:

   **Catalyst**:
   ```json
   // catalyst-config.json
   {
     "memory": 512  // Increase from 256
   }
   ```

   **Render**:
   ```
   - Upgrade to plan with more RAM
   - Starter: 512 MB → $7/month
   - Standard: 2 GB → $25/month
   ```

2. **Optimize Memory Usage**:
   ```javascript
   // Implement streaming for large data
   // Use pagination instead of loading all data
   // Clear unused variables
   // Avoid memory leaks
   ```

3. **Use External Storage**:
   ```
   - Store large files in Catalyst File Store
   - Use object storage (S3, Cloudinary)
   - Don't load large datasets into memory
   ```

#### Issue 7: Service-to-Service Communication Fails

**Symptoms**: API Gateway can't reach backend services

**Diagnosis**:
```bash
# Test service URLs
curl https://draftgenie-draft.onrender.com/health
curl https://draftgenie-rag.onrender.com/health

# Check if services are running
# Render Dashboard → Services → Status
```

**Solutions**:

1. **Verify Service URLs**:
   ```bash
   # Ensure URLs are correct in environment variables
   zcatalyst env:list

   # Update if needed
   zcatalyst env:set DRAFT_SERVICE_URL="https://draftgenie-draft.onrender.com"
   ```

2. **Handle Cold Starts**:
   ```javascript
   // Implement retry logic for cold starts
   async function callService(url, retries = 3) {
     for (let i = 0; i < retries; i++) {
       try {
         const response = await fetch(url, { timeout: 60000 });
         return response;
       } catch (error) {
         if (i === retries - 1) throw error;
         await new Promise(resolve => setTimeout(resolve, 2000));
       }
     }
   }
   ```

3. **Check CORS Settings**:
   ```javascript
   // Ensure CORS is configured correctly
   app.use(cors({
     origin: '*',  // Or specific domains
     credentials: true
   }));
   ```

#### Issue 8: High Costs

**Symptoms**: Monthly bill is higher than expected

**Diagnosis**:
```bash
# Check Catalyst usage
zcatalyst usage

# Check Render usage
# Dashboard → Account → Usage

# Review third-party service usage
# MongoDB Atlas, Upstash, CloudAMQP dashboards
```

**Solutions**:

1. **Identify Cost Drivers**:
   ```
   - Check which services exceed free tier
   - Look for unexpected traffic spikes
   - Review function invocation counts
   ```

2. **Optimize Function Calls**:
   ```javascript
   // Implement caching
   const cache = new Map();

   async function getCachedData(key) {
     if (cache.has(key)) {
       return cache.get(key);
     }
     const data = await fetchData(key);
     cache.set(key, data);
     return data;
   }
   ```

3. **Reduce Database Queries**:
   ```
   - Use Redis caching
   - Implement query batching
   - Use database indexes
   - Optimize queries
   ```

4. **Monitor and Alert**:
   ```
   - Set up usage alerts in each platform
   - Monitor daily/weekly usage trends
   - Investigate unusual spikes immediately
   ```

### Getting Help

1. **Zoho Catalyst Support**:
   - Documentation: https://catalyst.zoho.com/help/
   - Community: https://help.zoho.com/portal/en/community/catalyst
   - Support: https://catalyst.zoho.com/support

2. **Render Support**:
   - Documentation: https://render.com/docs
   - Community: https://community.render.com/
   - Support: support@render.com

3. **Third-Party Services**:
   - MongoDB Atlas: https://www.mongodb.com/support
   - Upstash: https://upstash.com/docs
   - CloudAMQP: https://www.cloudamqp.com/support.html

4. **DraftGenie Issues**:
   - https://github.com/tan-res-space/draft-genie/issues

### Useful Commands Reference

```bash
# Catalyst Commands
zcatalyst login                          # Login to Catalyst
zcatalyst init                           # Initialize new project
zcatalyst deploy                         # Deploy project
zcatalyst functions:list                 # List all functions
zcatalyst logs --function-name NAME      # View function logs
zcatalyst env:set KEY=VALUE             # Set environment variable
zcatalyst env:list                       # List environment variables
zcatalyst usage                          # View usage statistics

# Database Commands
psql "$POSTGRES_URL"                     # Connect to PostgreSQL
mongosh "$MONGODB_URL"                   # Connect to MongoDB
redis-cli -u "$REDIS_URL" ping          # Test Redis connection

# Testing Commands
curl https://your-service.com/health     # Test service health
curl -X POST https://your-service.com/api/endpoint  # Test API endpoint
```

---

## Next Steps

After successful deployment:

1. **Set Up CI/CD Pipeline**:
   - Use GitHub Actions for automated deployments
   - Integrate with Render's GitHub integration
   - Automate testing before deployment
   - Example workflow:
     ```yaml
     # .github/workflows/deploy.yml
     name: Deploy to Render
     on:
       push:
         branches: [main]
     jobs:
       deploy:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v2
           - name: Trigger Render Deploy
             run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
     ```

2. **Implement Backup Strategy**:
   - **PostgreSQL (Render)**:
     * Automated daily backups (7-day retention on paid plans)
     * Manual backups: `pg_dump $POSTGRES_URL > backup.sql`
   - **MongoDB Atlas**:
     * Configure automated backups in Atlas dashboard
     * Free tier: manual backups only
   - **Export Critical Data**:
     ```bash
     # Schedule weekly exports
     # Use cron or Catalyst Cron
     ```

3. **Security Hardening**:
   - **Enable HTTPS Only**: Already enabled by default
   - **Implement Rate Limiting**:
     ```javascript
     const rateLimit = require('express-rate-limit');

     const limiter = rateLimit({
       windowMs: 15 * 60 * 1000, // 15 minutes
       max: 100 // limit each IP to 100 requests per windowMs
     });

     app.use('/api/', limiter);
     ```
   - **Add API Authentication**:
     ```javascript
     // Use JWT tokens
     // Implement API key validation
     // Add request signing
     ```
   - **Regular Security Audits**:
     ```bash
     npm audit
     pip-audit
     ```

4. **Performance Testing**:
   - Use tools like Apache JMeter or k6
   - Test under load to identify bottlenecks
   - Example k6 test:
     ```javascript
     import http from 'k6/http';
     import { check } from 'k6';

     export let options = {
       vus: 10,
       duration: '30s',
     };

     export default function() {
       let res = http.get('https://your-api.com/health');
       check(res, { 'status is 200': (r) => r.status === 200 });
     }
     ```

5. **Documentation**:
   - Document your specific configuration
   - Create runbooks for common operations
   - Maintain deployment checklist
   - Train team members on the hybrid architecture

6. **Monitoring & Alerting**:
   - Set up comprehensive monitoring
   - Configure alerts for critical issues
   - Create dashboards for key metrics
   - Implement error tracking (Sentry)

---

## Additional Resources

- **Zoho Catalyst Documentation**: https://catalyst.zoho.com/help/
- **Render Documentation**: https://render.com/docs
- **MongoDB Atlas Documentation**: https://docs.atlas.mongodb.com/
- **Upstash Documentation**: https://docs.upstash.com/
- **CloudAMQP Documentation**: https://www.cloudamqp.com/docs/
- **DraftGenie Documentation**: https://github.com/tan-res-space/draft-genie/tree/main/docs

### Comparison with Other Cloud Platforms

| Feature | Zoho Cloud (Hybrid) | Azure | GCP |
|---------|---------------------|-------|-----|
| **Ease of Setup** | Medium (multiple platforms) | Medium | Medium |
| **Cost (Free Tier)** | $0-10/month | $0-50/month | $0-30/month |
| **Cost (Production)** | $100-200/month | $150-300/month | $120-250/month |
| **Scalability** | Limited (free tiers) | Excellent | Excellent |
| **Managed Services** | Limited (hybrid approach) | Comprehensive | Comprehensive |
| **Cold Starts** | Yes (Render free tier) | Minimal | Minimal |
| **Best For** | Small projects, Zoho ecosystem | Enterprise, Microsoft stack | Startups, Google services |

---

## Conclusion

Congratulations! You've successfully deployed DraftGenie using a hybrid cloud approach with Zoho Catalyst and complementary managed services. While this approach requires coordinating multiple platforms, it provides a cost-effective solution for running DraftGenie.

**What you've accomplished**:
- ✅ Deployed API Gateway and Speaker Service to Zoho Catalyst
- ✅ Deployed Python services to Render.com
- ✅ Set up managed databases (PostgreSQL, MongoDB, Redis, RabbitMQ)
- ✅ Configured secure secrets management
- ✅ Enabled logging and monitoring
- ✅ Secured your application with HTTPS
- ✅ Optimized for cost using free tiers

**Your deployment is ready for development and testing!** 🎉

**Key Considerations**:
- **Hybrid Architecture**: Services are distributed across multiple platforms
- **Cost-Effective**: Can run entirely on free tiers for development
- **Scalability**: May need to migrate to Azure/GCP for large-scale production
- **Maintenance**: Requires managing multiple platform accounts

**When to Consider Migration**:
- Traffic exceeds free tier limits consistently
- Need for better performance (no cold starts)
- Require advanced features (auto-scaling, load balancing)
- Want unified platform management

For questions or issues, please refer to the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.

**Note**: For production deployments with high traffic, consider using Azure or GCP for a more integrated and scalable solution. This Zoho-based deployment is ideal for development, testing, and small-scale production workloads.


