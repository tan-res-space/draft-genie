# DraftGenie - AI-Powered Draft Improvement System

DraftGenie is a Speaker-centric microservice system that uses AI and Retrieval-Augmented Generation (RAG) to improve draft quality by learning from speaker-specific patterns and historical data.

## 📖 Documentation

**📘 [Complete System Architecture & Implementation Plan](docs/system_architecture_and_implementation_plan.md)** - **Single Source of Truth (SSOT)**

This comprehensive document contains everything you need to know about DraftGenie:
- Complete architecture overview with diagrams
- Detailed service specifications
- Technology stack and dependencies
- Phase-by-phase implementation plan (5-6 weeks)
- Development guidelines and best practices
- Logging and debugging strategies
- Testing strategy and examples
- Setup and deployment instructions
- API reference and event schemas
- Troubleshooting guide

**Additional Documentation:**
- [Original Requirements](docs/draft-genie-system-documentation.md) - Original system requirements
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [Getting Started](docs/GETTING_STARTED.md) - Quick start guide for developers
- [Phase 1 Completion](docs/PHASE1_COMPLETION.md) - Historical record of Phase 1

## 🏗️ Architecture

DraftGenie uses a **hybrid polyglot microservices architecture**:

**Node.js Services (2):**
- **API Gateway** - Authentication, routing, aggregation (NestJS)
- **Speaker Service** - Speaker CRUD, metadata management (NestJS + Prisma)

**Python Services (3):**
- **Draft Service** - Draft ingestion, NLP, correction vectors (FastAPI + spaCy)
- **RAG Service** - AI-powered draft generation (FastAPI + LangChain + LangGraph + Gemini)
- **Evaluation Service** - Metrics calculation, bucket reassignment (FastAPI + scikit-learn)

## 🚀 Quick Start

### Prerequisites

- Node.js 20+ and npm 10+
- Docker and Docker Compose
- Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd draft-genie
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Setup environment variables**
   ```bash
   cp docker/.env.example docker/.env
   # Edit docker/.env and add your GEMINI_API_KEY
   ```

4. **Start infrastructure services**
   ```bash
   npm run docker:up
   ```

5. **Run database migrations**
   ```bash
   npm run db:migrate
   ```

6. **Seed mock data (optional)**
   ```bash
   npm run db:seed
   ```

7. **Start all services**
   ```bash
   npm run dev:all
   ```

### Access the Services

- **API Gateway**: http://localhost:3000
- **API Documentation**: http://localhost:3000/api/docs
- **Speaker Service**: http://localhost:3001
- **Draft Service**: http://localhost:3002
- **RAG Service**: http://localhost:3003

## 📚 Additional Resources

- **[API Documentation](http://localhost:3000/api/docs)** - Interactive API docs (when services are running)
- **[RabbitMQ Management](http://localhost:15672)** - Message queue dashboard (guest/guest)
- **[Qdrant Dashboard](http://localhost:6333/dashboard)** - Vector database UI

## 🛠️ Development

### Project Structure

```
draft-genie/
├── apps/                    # Microservices
│   ├── speaker-service/     # Speaker management
│   ├── draft-service/       # Draft ingestion & vectors
│   ├── rag-service/         # RAG & DFN generation
│   └── api-gateway/         # API Gateway
├── libs/                    # Shared libraries
│   ├── common/              # Common utilities
│   ├── domain/              # Domain models & events
│   └── database/            # Database clients
├── docker/                  # Docker configuration
└── docs/                    # Documentation
```

### Available Scripts

```bash
# Development
npm run dev:all              # Start all services
npm run dev:speaker          # Start speaker service only
npm run dev:draft            # Start draft service only
npm run dev:rag              # Start RAG service only
npm run dev:gateway          # Start API gateway only

# Build
npm run build                # Build all services

# Testing
npm run test                 # Run all tests
npm run test:cov             # Run tests with coverage

# Linting & Formatting
npm run lint                 # Lint all code
npm run format               # Format all code
npm run format:check         # Check formatting

# Docker
npm run docker:up            # Start Docker services
npm run docker:down          # Stop Docker services
npm run docker:logs          # View Docker logs

# Database
npm run db:migrate           # Run Prisma migrations
npm run db:seed              # Seed database with mock data
```

## 🧪 Testing

```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:cov

# Run tests for specific service
npm run test -- apps/speaker-service
```

## 🏭 Technology Stack

### Node.js Services
- **Runtime**: Node.js 20 LTS
- **Language**: TypeScript 5
- **Framework**: NestJS 10
- **ORM**: Prisma 5
- **Testing**: Jest

### Python Services
- **Runtime**: Python 3.11+
- **Framework**: FastAPI 0.109+
- **AI/ML**: LangChain 0.1+, LangGraph 0.0.20+, Google Generative AI SDK
- **NLP**: spaCy 3.7+, NLTK 3.8+
- **Data Science**: scikit-learn, numpy, pandas
- **ORM**: SQLAlchemy 2.0 (async)
- **ODM**: Motor (async MongoDB)
- **Testing**: pytest

### Databases
- **PostgreSQL 16** - Relational data (Speaker, Evaluation services)
- **MongoDB 7** - Document storage (Draft, RAG services)
- **Qdrant 1.7** - Vector database for correction vectors
- **Redis 7** - Caching and session management

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **RabbitMQ 3.12** - Message queue for event-driven architecture
- **NX** - Monorepo management

## 🔐 Security

- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Input validation
- Secure password hashing
- Environment-based configuration

## 📊 Monitoring & Logging

- Structured logging with Winston
- Correlation IDs for request tracking
- Health check endpoints
- Error tracking and reporting

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run linting and formatting
5. Submit a pull request

## 📝 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the [documentation](docs/)
- Review the [API documentation](http://localhost:3000/api/docs)

## 🗺️ Implementation Status

### Phase 1: Foundation ✅ COMPLETE
- [x] Monorepo structure with NX
- [x] TypeScript shared libraries (common, domain, database)
- [x] Docker infrastructure (PostgreSQL, MongoDB, Qdrant, Redis)
- [x] Prisma schema for Speaker Service
- [x] Documentation and setup scripts

### Phase 2: Python Foundation 🚧 IN PROGRESS
- [x] Poetry configuration
- [x] Python shared libraries - common (logger, errors, constants, utils)
- [ ] Python shared libraries - domain (models, events, value objects)
- [ ] Python shared libraries - database (PostgreSQL, MongoDB, Qdrant, Redis)
- [ ] RabbitMQ setup and event bus
- [ ] Shared schemas (OpenAPI, JSON Schema)

### Phase 3-8: Service Implementation ⏳ PLANNED
- [ ] Speaker Service (Node.js + NestJS + Prisma)
- [ ] Draft Service (Python + FastAPI + NLP)
- [ ] RAG Service (Python + FastAPI + LangChain + LangGraph)
- [ ] Evaluation Service (Python + FastAPI)
- [ ] API Gateway (Node.js + NestJS)
- [ ] Integration & Testing

**Timeline:** 5-6 weeks total
**Current Status:** Week 1-2, Phase 2 in progress

For detailed implementation plan, see [System Architecture & Implementation Plan](docs/system_architecture_and_implementation_plan.md)

### Post-MVP Features
- [ ] Batch Speaker Addition (BSA)
- [ ] Background job scheduler
- [ ] Web dashboard UI
- [ ] Real-time updates (WebSockets)
- [ ] Advanced observability (Prometheus, Grafana)
- [ ] Kubernetes deployment

## 📞 Contact

[Add contact information]

