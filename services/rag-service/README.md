# RAG Service

RAG (Retrieval-Augmented Generation) Service for Draft Genie using LangChain, LangGraph, and Gemini.

## Overview

The RAG Service is responsible for generating Draft Final Notes (DFN) from Informal Notes (IFN) using:
- **LangChain**: For LLM orchestration
- **LangGraph**: For AI agent workflows
- **Gemini**: For text generation and embeddings
- **Qdrant**: For vector similarity search
- **MongoDB**: For DFN and session storage

## Features

- 🤖 **AI Agent Workflow**: Multi-step reasoning with LangGraph
- 🔍 **Context Retrieval**: Retrieves speaker profiles, correction patterns, and historical drafts
- 📝 **Prompt Engineering**: Sophisticated prompts with speaker-specific context
- 🎯 **Self-Critique**: Agent critiques and refines its own output
- 📊 **Session Tracking**: Tracks RAG sessions and agent steps
- 🔄 **Event-Driven**: Publishes DFNGeneratedEvent

## Installation

```bash
cd services/rag-service
poetry install
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key configurations:
- `GEMINI_API_KEY`: Your Gemini API key
- `MONGODB_URI`: MongoDB connection string
- `QDRANT_HOST`: Qdrant host
- `SPEAKER_SERVICE_URL`: Speaker Service URL
- `DRAFT_SERVICE_URL`: Draft Service URL

## Running the Service

### Development
```bash
poetry run uvicorn app.main:app --reload --port 8003
```

### Production
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with dependencies
- `GET /health/live` - Liveness check

### RAG Operations (Coming in Days 16-18)
- `POST /api/v1/rag/generate` - Generate DFN from IFN
- `GET /api/v1/dfn` - List DFNs
- `GET /api/v1/dfn/:id` - Get DFN details
- `GET /api/v1/dfn/speaker/:id` - Get speaker DFNs
- `POST /api/v1/rag/sessions` - Create RAG session
- `GET /api/v1/rag/sessions/:id` - Get session details

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_health.py -v
```

## Architecture

### Components

1. **LLM Service**: Gemini integration with LangChain
2. **Context Service**: Retrieves context from external services
3. **Agent Service**: LangGraph workflow for DFN generation
4. **DFN Service**: Manages DFN storage and retrieval
5. **Session Service**: Tracks RAG sessions

### Workflow

1. Receive IFN draft ID and speaker ID
2. Retrieve context (speaker profile, correction patterns, historical drafts)
3. Generate prompts with context
4. Run LangGraph agent workflow:
   - Context analysis
   - Pattern matching
   - Draft generation
   - Self-critique
   - Refinement
5. Store DFN in MongoDB
6. Publish DFNGeneratedEvent

## Dependencies

- **FastAPI**: Web framework
- **LangChain**: LLM orchestration
- **LangGraph**: AI agent workflows
- **Gemini**: Google's LLM
- **Motor**: Async MongoDB driver
- **Qdrant Client**: Vector database
- **aio-pika**: RabbitMQ client

## Development Status

- ✅ Day 15: Service Setup (COMPLETE)
  - FastAPI application
  - LangChain + Gemini integration
  - MongoDB and Qdrant clients
  - Prompt templates
  - Context retrieval
  - Health checks

- ⏳ Day 16: RAG Pipeline (IN PROGRESS)
- ⏳ Day 17: LangGraph AI Agent (PLANNED)
- ⏳ Day 18: RAG Management APIs (PLANNED)

## License

Copyright © 2025 Draft Genie Team

