# Draft Service

FastAPI-based microservice for ingesting and processing speaker drafts from InstaNote.

## Features

- **Draft Ingestion**: Fetch and store drafts from InstaNote API
- **Correction Analysis**: Extract and analyze correction patterns
- **Vector Generation**: Generate embeddings using Gemini API
- **Vector Storage**: Store embeddings in Qdrant for similarity search
- **Event-Driven**: Publish and consume events via RabbitMQ
- **MongoDB Storage**: Store drafts and correction metadata
- **Health Checks**: Kubernetes-ready health endpoints
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Motor** - Async MongoDB driver
- **Qdrant** - Vector database for embeddings
- **RabbitMQ** - Message broker for events
- **Gemini API** - Google's embedding model
- **Pydantic** - Data validation
- **Poetry** - Dependency management

## Prerequisites

- Python 3.11+
- MongoDB 7.0+
- Qdrant 1.7+
- RabbitMQ 3.13+
- Gemini API key

## Installation

### Using Poetry

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

- `MONGODB_URL` - MongoDB connection string
- `QDRANT_URL` - Qdrant server URL
- `RABBITMQ_URL` - RabbitMQ connection string
- `GEMINI_API_KEY` - Google Gemini API key
- `INSTANOTE_API_URL` - InstaNote API endpoint

## Running the Service

### Development

```bash
# Using Poetry
poetry run python -m app.main

# Or with uvicorn directly
poetry run uvicorn app.main:app --reload --port 8001
```

### Production

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## API Documentation

Once running, access the API documentation at:

- **Swagger UI**: http://localhost:8001/api/docs
- **ReDoc**: http://localhost:8001/api/redoc
- **OpenAPI JSON**: http://localhost:8001/api/openapi.json

## Health Checks

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (includes dependencies)
- `GET /health/live` - Liveness check

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_health.py -v
```

## Project Structure

```
services/draft-service/
├── app/
│   ├── api/              # API endpoints
│   │   ├── health.py     # Health check endpoints
│   │   └── ...
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   └── logging.py    # Logging setup
│   ├── db/               # Database clients
│   │   ├── mongodb.py    # MongoDB client
│   │   └── qdrant.py     # Qdrant client
│   ├── models/           # Pydantic models
│   │   ├── draft.py      # Draft model
│   │   └── correction_vector.py
│   ├── services/         # Business logic
│   ├── events/           # Event handlers
│   └── main.py           # FastAPI application
├── tests/                # Test files
├── pyproject.toml        # Poetry configuration
├── .env.example          # Environment template
└── README.md             # This file
```

## API Endpoints

### Drafts

- `POST /api/v1/drafts/ingest` - Manually ingest drafts
- `GET /api/v1/drafts` - List all drafts
- `GET /api/v1/drafts/{id}` - Get draft by ID
- `GET /api/v1/drafts/speaker/{speaker_id}` - Get speaker's drafts

### Vectors

- `POST /api/v1/vectors/generate` - Generate correction vectors
- `GET /api/v1/vectors/speaker/{speaker_id}` - Get speaker's vectors
- `POST /api/v1/vectors/search` - Search similar vectors

## Events

### Consumed Events

- `SpeakerOnboardedEvent` - Triggers draft ingestion for new speaker

### Published Events

- `DraftIngestedEvent` - Published when drafts are ingested
- `CorrectionVectorCreatedEvent` - Published when vectors are generated

## Development

### Code Quality

```bash
# Format code
poetry run black app tests

# Lint code
poetry run ruff check app tests

# Type checking
poetry run mypy app
```

### Adding Dependencies

```bash
# Add production dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name
```

## Docker

```bash
# Build image
docker build -t draft-service:latest .

# Run container
docker run -p 8001:8001 --env-file .env draft-service:latest
```

## Monitoring

The service provides structured JSON logging for easy integration with log aggregation tools like:

- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki
- CloudWatch
- Datadog

## License

Proprietary - Draft Genie Team

