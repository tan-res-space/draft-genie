# Evaluation Service

Evaluation Service for Draft Genie - Compares IFN and DFN drafts, calculates quality metrics, and manages speaker bucket reassignment.

## Overview

The Evaluation Service is responsible for:
- **Draft Comparison**: Comparing IFN (Informal Notes) and DFN (Draft Final Notes)
- **Metrics Calculation**: SER, WER, semantic similarity, quality scores
- **Bucket Reassignment**: Automatically reassigning speakers to appropriate buckets based on performance
- **Event Processing**: Listening to DFNGeneratedEvent and publishing evaluation events

## Features

- 📊 **Comprehensive Metrics**: SER, WER, semantic similarity, quality scores
- 🔄 **Automatic Bucket Reassignment**: Based on quality thresholds
- 📈 **Aggregated Analytics**: Speaker-level metrics and trends
- 🎯 **Event-Driven**: Listens to DFNGeneratedEvent, publishes evaluation events
- 💾 **PostgreSQL Storage**: Persistent storage of evaluations and metrics

## Installation

```bash
cd services/evaluation-service
poetry install
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key configurations:
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_DB`: Database name
- `RABBITMQ_HOST`: RabbitMQ host
- `SPEAKER_SERVICE_URL`: Speaker Service URL
- `DRAFT_SERVICE_URL`: Draft Service URL
- `RAG_SERVICE_URL`: RAG Service URL

## Running the Service

### Development
```bash
poetry run uvicorn app.main:app --reload --port 8004
```

### Production
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8004
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with dependencies
- `GET /health/live` - Liveness check

### Evaluation Operations (Coming in Days 20-21)
- `POST /api/v1/evaluations/trigger` - Manual evaluation trigger
- `GET /api/v1/evaluations` - List evaluations
- `GET /api/v1/evaluations/:id` - Get evaluation details
- `GET /api/v1/metrics` - Aggregated metrics
- `GET /api/v1/metrics/speaker/:id` - Speaker metrics

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

1. **Comparison Service**: Calculates text differences and metrics
2. **Metrics Service**: Aggregates and stores metrics
3. **Bucket Service**: Determines bucket reassignment
4. **Event Consumer**: Listens to DFNGeneratedEvent
5. **Event Publisher**: Publishes evaluation events

### Workflow

1. Listen to DFNGeneratedEvent from RAG Service
2. Retrieve IFN and DFN texts
3. Calculate metrics:
   - Sentence Edit Rate (SER)
   - Word Error Rate (WER)
   - Semantic Similarity (sentence transformers)
   - Quality Score
   - Improvement Score
4. Store evaluation in PostgreSQL
5. Determine recommended bucket
6. Update speaker bucket if needed
7. Publish EvaluationCompletedEvent
8. Publish BucketReassignedEvent (if changed)

## Metrics

### Sentence Edit Rate (SER)
- Measures sentence-level changes
- Lower is better (fewer changes needed)

### Word Error Rate (WER)
- Measures word-level changes
- Lower is better (fewer word corrections)

### Semantic Similarity
- Measures meaning preservation
- Higher is better (0-1 scale)

### Quality Score
- Overall quality assessment
- Combines multiple metrics
- Higher is better (0-1 scale)

### Improvement Score
- Measures improvement from IFN to DFN
- Higher is better (0-1 scale)

## Bucket Reassignment

### Bucket Thresholds
- **Bucket A**: Quality Score >= 0.9 (High quality)
- **Bucket B**: Quality Score >= 0.7 (Medium quality)
- **Bucket C**: Quality Score < 0.7 (Low quality)

### Reassignment Logic
- Analyzes recent evaluations
- Calculates average quality score
- Recommends bucket based on thresholds
- Calls Speaker Service to update bucket
- Publishes BucketReassignedEvent

## Database Schema

### Evaluations Table
- Stores individual evaluation results
- Links to speaker, IFN, DFN
- Contains all calculated metrics
- Tracks bucket changes

### Metrics Table
- Stores aggregated speaker metrics
- Average scores across evaluations
- Trend data
- Bucket change history

## Events

### Consumed Events
- **DFNGeneratedEvent**: Triggers evaluation

### Published Events
- **EvaluationCompletedEvent**: Evaluation finished
- **BucketReassignedEvent**: Speaker bucket changed

## Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM for PostgreSQL
- **asyncpg**: Async PostgreSQL driver
- **sentence-transformers**: Semantic similarity
- **aio-pika**: RabbitMQ client
- **httpx**: HTTP client

## Development

### Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Code Quality

```bash
# Format code
poetry run black app tests

# Lint code
poetry run ruff check app tests

# Type check
poetry run mypy app
```

## License

MIT

