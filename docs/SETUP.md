# DraftGenie Setup Guide

This guide will help you set up the DraftGenie microservice system on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 20.x or higher ([Download](https://nodejs.org/))
- **npm** 10.x or higher (comes with Node.js)
- **Docker** 24.x or higher ([Download](https://www.docker.com/products/docker-desktop))
- **Docker Compose** 2.x or higher (comes with Docker Desktop)
- **Git** ([Download](https://git-scm.com/downloads))

### Verify Installation

```bash
node --version    # Should be v20.x.x or higher
npm --version     # Should be 10.x.x or higher
docker --version  # Should be 24.x.x or higher
docker-compose --version  # Should be 2.x.x or higher
```

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd draft-genie
```

## Step 2: Install Dependencies

```bash
npm install
```

This will install all dependencies for the monorepo, including all microservices and shared libraries.

## Step 3: Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key

## Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp docker/.env.example docker/.env

# Edit the .env file
nano docker/.env  # or use your preferred editor
```

Update the following variables in `docker/.env`:

```env
# Required: Add your Gemini API key
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Optional: Change default passwords (recommended for production)
POSTGRES_PASSWORD=your-secure-password
MONGO_PASSWORD=your-secure-password
REDIS_PASSWORD=your-secure-password
JWT_SECRET=your-super-secret-jwt-key-change-in-production
```

## Step 5: Start Infrastructure Services

Start all database and infrastructure services using Docker Compose:

```bash
npm run docker:up
```

This will start:
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Qdrant (port 6333)
- Redis (port 6379)

Wait for all services to be healthy (about 30 seconds). You can check the logs:

```bash
npm run docker:logs
```

## Step 6: Initialize Databases

### Run Prisma Migrations

```bash
npm run db:migrate
```

This will create all necessary tables in PostgreSQL.

### Seed Mock Data (Optional)

```bash
npm run db:seed
```

This will populate the database with sample speakers and drafts for testing.

## Step 7: Start Microservices

You have two options:

### Option A: Start All Services at Once

```bash
npm run dev:all
```

This will start all 4 microservices in parallel.

### Option B: Start Services Individually

Open 4 separate terminal windows and run:

```bash
# Terminal 1: Speaker Service
npm run dev:speaker

# Terminal 2: Draft Service
npm run dev:draft

# Terminal 3: RAG Service
npm run dev:rag

# Terminal 4: API Gateway
npm run dev:gateway
```

## Step 8: Verify Installation

### Check Service Health

Open your browser and visit:

- **API Gateway**: http://localhost:3000/health
- **Speaker Service**: http://localhost:3001/health
- **Draft Service**: http://localhost:3002/health
- **RAG Service**: http://localhost:3003/health

All should return `{"status": "ok"}`.

### Access API Documentation

Visit http://localhost:3000/api/docs to see the Swagger API documentation.

## Step 9: Test the System

### Create a Test Speaker

```bash
curl -X POST http://localhost:3000/api/v1/speakers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. John Smith",
    "email": "john.smith@example.com",
    "bucket": "GOOD",
    "metadata": {
      "ser": 0.08,
      "wer": 0.10
    }
  }'
```

### List Speakers

```bash
curl http://localhost:3000/api/v1/speakers
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors, you can change the ports in `docker/.env`:

```env
POSTGRES_PORT=5433
MONGO_PORT=27018
QDRANT_PORT=6334
REDIS_PORT=6380
```

### Docker Services Not Starting

```bash
# Stop all services
npm run docker:down

# Remove volumes (WARNING: This will delete all data)
docker-compose -f docker/docker-compose.yml down -v

# Start again
npm run docker:up
```

### Database Connection Errors

Make sure all Docker services are running and healthy:

```bash
docker ps
```

You should see 4 containers running (postgres, mongodb, qdrant, redis).

### Prisma Migration Errors

If migrations fail, try:

```bash
# Reset the database (WARNING: This will delete all data)
npx prisma migrate reset

# Run migrations again
npm run db:migrate
```

### Module Not Found Errors

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Making Changes

1. Make changes to the code
2. The services will automatically reload (hot reload enabled)
3. Test your changes using the API

### Running Tests

```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:cov

# Run tests for specific service
npm run test -- apps/speaker-service
```

### Linting and Formatting

```bash
# Check code style
npm run lint

# Fix linting issues
npm run lint -- --fix

# Format code
npm run format

# Check formatting
npm run format:check
```

## Stopping Services

### Stop Microservices

Press `Ctrl+C` in the terminal where services are running.

### Stop Infrastructure Services

```bash
npm run docker:down
```

### Stop Everything and Remove Data

```bash
# WARNING: This will delete all data in databases
docker-compose -f docker/docker-compose.yml down -v
```

## Next Steps

- Read the [API Documentation](http://localhost:3000/api/docs)
- Review the [System Architecture](draft-genie-system-documentation.md)
- Explore the codebase
- Start building features!

## Common Commands Reference

```bash
# Development
npm run dev:all              # Start all services
npm run dev:speaker          # Start speaker service
npm run dev:draft            # Start draft service
npm run dev:rag              # Start RAG service
npm run dev:gateway          # Start API gateway

# Docker
npm run docker:up            # Start infrastructure
npm run docker:down          # Stop infrastructure
npm run docker:logs          # View logs

# Database
npm run db:migrate           # Run migrations
npm run db:seed              # Seed data

# Testing
npm run test                 # Run tests
npm run test:cov             # Test coverage

# Code Quality
npm run lint                 # Lint code
npm run format               # Format code
npm run build                # Build all services
```

## Support

If you encounter any issues:

1. Check the logs: `npm run docker:logs`
2. Verify all services are running: `docker ps`
3. Check the troubleshooting section above
4. Create an issue in the repository

## Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md) (coming soon).

