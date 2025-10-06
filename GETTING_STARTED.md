# Getting Started with DraftGenie

Welcome to DraftGenie! This guide will help you get up and running quickly.

## 🎯 What is DraftGenie?

DraftGenie is a Speaker-centric AI-powered system that improves draft quality by:
1. Learning from speaker-specific patterns
2. Using Retrieval-Augmented Generation (RAG) with Google Gemini
3. Applying personalized corrections based on historical data
4. Continuously evaluating and improving draft quality

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Node.js 20+
- Docker Desktop
- Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Automated Setup

```bash
# Run the setup script
./scripts/setup.sh
```

This script will:
1. ✅ Check prerequisites
2. ✅ Install dependencies
3. ✅ Setup environment variables
4. ✅ Start Docker services
5. ✅ Run database migrations
6. ✅ Optionally seed mock data

### Manual Setup

If you prefer manual setup, follow these steps:

```bash
# 1. Install dependencies
npm install

# 2. Setup environment
cp docker/.env.example docker/.env
# Edit docker/.env and add your GEMINI_API_KEY

# 3. Start infrastructure
npm run docker:up

# 4. Wait 30 seconds for services to be healthy

# 5. Run migrations
npm run db:migrate

# 6. (Optional) Seed data
npm run db:seed
```

## 🎮 Running the Application

### Start All Services

```bash
npm run dev:all
```

This starts all 4 microservices:
- API Gateway (port 3000)
- Speaker Service (port 3001)
- Draft Service (port 3002)
- RAG Service (port 3003)

### Start Individual Services

```bash
# In separate terminals
npm run dev:speaker
npm run dev:draft
npm run dev:rag
npm run dev:gateway
```

## 🧪 Testing the System

### 1. Check Health

```bash
curl http://localhost:3000/health
```

Expected response: `{"status": "ok"}`

### 2. View API Documentation

Open http://localhost:3000/api/docs in your browser

### 3. Create a Speaker

```bash
curl -X POST http://localhost:3000/api/v1/speakers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "email": "jane.smith@example.com",
    "bucket": "GOOD",
    "metadata": {
      "ser": 0.08,
      "wer": 0.10
    }
  }'
```

### 4. List Speakers

```bash
curl http://localhost:3000/api/v1/speakers
```

## 📚 Key Concepts

### Speaker-Centric Approach
Everything starts with a Speaker. Each speaker has:
- **Bucket**: Quality category (EXCELLENT, GOOD, AVERAGE, POOR, NEEDS_IMPROVEMENT)
- **Metadata**: SER (Sentence Edit Rate), WER (Word Error Rate)
- **Historical Drafts**: Past ASR drafts and final notes
- **Correction Vectors**: Personalized correction patterns

### Draft Types
- **AD (ASR Draft)**: Raw automatic speech recognition output
- **LD (LLM Draft)**: LLM-generated draft
- **IFN (InstaNote Final)**: Final note from InstaNote system
- **DFN (DraftGenie Final)**: Improved final note from DraftGenie

### Processing Flow
1. **Onboard Speaker** → Add speaker to system
2. **Ingest Drafts** → Pull historical drafts from InstaNote
3. **Build Vectors** → Create correction patterns
4. **Generate DFN** → Use RAG with Gemini to create improved draft
5. **Evaluate** → Compare DFN vs IFN, calculate metrics
6. **Reassign Bucket** → Update speaker bucket based on quality

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 3000)                  │
│              (Authentication, Routing, Aggregation)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   Speaker      │  │   Draft         │  │   RAG           │
│   Service      │  │   Service       │  │   Service       │
│   (Port 3001)  │  │   (Port 3002)   │  │   (Port 3003)   │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   PostgreSQL   │  │   MongoDB       │  │   Qdrant        │
│   (Port 5432)  │  │   (Port 27017)  │  │   (Port 6333)   │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📖 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed setup instructions
- **[System Architecture](docs/draft-genie-system-documentation.md)** - Complete system design
- **[Phase 1 Completion](docs/PHASE1_COMPLETION.md)** - What's been implemented
- **[API Documentation](http://localhost:3000/api/docs)** - Interactive API docs (when running)

## 🛠️ Development Workflow

### Making Changes

1. Edit code in `apps/` or `libs/`
2. Services auto-reload (hot reload enabled)
3. Test changes via API or tests

### Running Tests

```bash
# All tests
npm run test

# With coverage
npm run test:cov

# Specific service
npm run test -- apps/speaker-service
```

### Code Quality

```bash
# Lint
npm run lint

# Format
npm run format

# Type check
npx tsc --noEmit
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker services
docker ps

# View logs
npm run docker:logs

# Restart infrastructure
npm run docker:down
npm run docker:up
```

### Port Conflicts

Edit `docker/.env` and change ports:
```env
POSTGRES_PORT=5433
MONGO_PORT=27018
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
npx prisma migrate reset
npm run db:migrate
```

### Module Not Found

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## 📊 Current Status

### ✅ Completed (Phase 1)
- Project structure and monorepo setup
- Shared libraries (common, domain, database)
- Docker infrastructure
- Database schemas
- Documentation

### 🚧 In Progress (Phase 2)
- Speaker Service implementation
- REST API endpoints
- Authentication
- Testing

### ⏳ Upcoming
- Draft Service
- RAG Service with Gemini
- API Gateway
- Web Dashboard

## 🎯 Next Steps

1. **Explore the codebase**
   - Check out `libs/` for shared code
   - Review `docs/` for architecture details

2. **Start developing**
   - Implement Speaker Service (Phase 2)
   - Add new features
   - Write tests

3. **Contribute**
   - Follow the coding standards
   - Write tests for new features
   - Update documentation

## 💡 Tips

- Use `npm run dev:all` for full system development
- Check logs with `npm run docker:logs`
- API docs are your friend: http://localhost:3000/api/docs
- All services have hot reload enabled
- Use correlation IDs in logs for debugging

## 🆘 Need Help?

- Check [SETUP.md](docs/SETUP.md) for detailed instructions
- Review [troubleshooting section](#-troubleshooting)
- Check Docker logs: `npm run docker:logs`
- Verify services: `docker ps`

## 🎉 You're Ready!

You now have a fully functional DraftGenie development environment. Start building! 🚀

---

**Happy Coding!** 💻

