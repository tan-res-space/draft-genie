# Integration Tests

This directory contains end-to-end integration tests for the Draft Genie system. These tests validate complete workflows across all microservices.

## Test Structure

```
tests/integration/
├── README.md                          # This file
├── conftest.py                        # Shared pytest fixtures
├── test_complete_workflow.py          # Full speaker → draft → RAG → evaluation flow
├── test_authentication_flow.py        # API Gateway authentication tests
├── test_event_driven_workflows.py     # RabbitMQ message flow tests
├── test_service_communication.py      # Inter-service communication tests
├── test_error_scenarios.py            # Error handling and failure scenarios
├── test_data_consistency.py           # Data consistency across services
└── helpers/
    ├── __init__.py
    ├── api_client.py                  # HTTP client helpers
    ├── database_helpers.py            # Database setup/teardown
    └── test_data.py                   # Test data generators
```

## Prerequisites

### 1. Environment Setup

All services must be running. You can start them with:

```bash
# Start all services via Docker Compose
docker-compose up -d

# Or start services individually for development
npm run dev:speaker      # Terminal 1
npm run dev:gateway      # Terminal 2
cd services/draft-service && poetry run uvicorn app.main:app --port 3002  # Terminal 3
cd services/rag-service && poetry run uvicorn app.main:app --port 3003    # Terminal 4
cd services/evaluation-service && poetry run uvicorn app.main:app --port 3004  # Terminal 5
```

### 2. Environment Variables

Create `.env.test` file:

```env
# API Gateway
API_GATEWAY_URL=http://localhost:3000
JWT_SECRET=test-secret-key

# Services
SPEAKER_SERVICE_URL=http://localhost:3001
DRAFT_SERVICE_URL=http://localhost:3002
RAG_SERVICE_URL=http://localhost:3003
EVALUATION_SERVICE_URL=http://localhost:3004

# Databases
POSTGRES_URL=postgresql://draftgenie:draftgenie123@localhost:5432/draftgenie_test
MONGODB_URL=mongodb://draftgenie:draftgenie123@localhost:27017/draftgenie_test?authSource=admin
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://:draftgenie123@localhost:6379/1
RABBITMQ_URL=amqp://draftgenie:draftgenie123@localhost:5672/

# AI Services
GEMINI_API_KEY=your-test-api-key
```

### 3. Test Database Setup

Integration tests use separate test databases to avoid polluting development data:

```bash
# Create test databases
psql -U draftgenie -c "CREATE DATABASE draftgenie_test;"
mongosh --eval "use draftgenie_test"
```

## Running Tests

### Run All Integration Tests

```bash
# From project root
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=. --cov-report=html

# Run specific test file
pytest tests/integration/test_complete_workflow.py -v

# Run specific test
pytest tests/integration/test_complete_workflow.py::test_speaker_to_evaluation_flow -v
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/integration/ -n 4
```

### Run Tests with Docker

```bash
# Run tests inside Docker container
docker-compose run --rm api-gateway pytest /app/tests/integration/
```

## Test Scenarios

### 1. Complete Workflow Test (`test_complete_workflow.py`)

Tests the full end-to-end flow:
1. Create speaker via API Gateway
2. Upload draft (IFN) for speaker
3. Trigger RAG generation (DFN)
4. Verify evaluation is created
5. Check bucket reassignment if needed

**Expected Duration:** ~30 seconds

### 2. Authentication Flow Test (`test_authentication_flow.py`)

Tests API Gateway authentication:
1. User registration
2. User login (JWT token)
3. Token refresh
4. Protected endpoint access
5. Token expiration handling
6. API key authentication

**Expected Duration:** ~5 seconds

### 3. Event-Driven Workflows Test (`test_event_driven_workflows.py`)

Tests RabbitMQ message flow:
1. Speaker created event → Draft service listens
2. Draft ingested event → RAG service listens
3. DFN generated event → Evaluation service listens
4. Evaluation completed event → Speaker service listens
5. Verify message delivery and processing

**Expected Duration:** ~15 seconds

### 4. Service Communication Test (`test_service_communication.py`)

Tests inter-service HTTP communication:
1. API Gateway → Speaker Service
2. Draft Service → Speaker Service (speaker validation)
3. RAG Service → Draft Service (fetch drafts)
4. Evaluation Service → Draft Service (fetch drafts for comparison)
5. Verify proper error handling for service unavailability

**Expected Duration:** ~10 seconds

### 5. Error Scenarios Test (`test_error_scenarios.py`)

Tests error handling:
1. Invalid speaker ID
2. Missing required fields
3. Database connection failures
4. Service timeout scenarios
5. Duplicate resource creation
6. Invalid authentication tokens

**Expected Duration:** ~10 seconds

### 6. Data Consistency Test (`test_data_consistency.py`)

Tests data consistency across services:
1. Speaker data consistency (PostgreSQL)
2. Draft data consistency (MongoDB)
3. Vector data consistency (Qdrant)
4. Cache consistency (Redis)
5. Event ordering and idempotency

**Expected Duration:** ~15 seconds

## Test Data Management

### Fixtures

Common fixtures are defined in `conftest.py`:

- `api_client`: HTTP client for API Gateway
- `test_speaker`: Creates a test speaker
- `test_draft`: Creates a test draft
- `cleanup_databases`: Cleans up test data after tests

### Test Data Generators

Use helpers in `helpers/test_data.py`:

```python
from tests.integration.helpers.test_data import (
    generate_speaker_data,
    generate_draft_data,
    generate_evaluation_data
)

# Generate test speaker
speaker_data = generate_speaker_data(name="Test Speaker", bucket="A")

# Generate test draft
draft_data = generate_draft_data(speaker_id="123", content="Test content")
```

## Debugging Tests

### Enable Verbose Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=debug
pytest tests/integration/ -v -s
```

### Inspect Test Failures

```bash
# Run with pytest-pdb for interactive debugging
pytest tests/integration/ --pdb

# Generate detailed HTML report
pytest tests/integration/ --html=report.html --self-contained-html
```

### Check Service Health

Before running tests, verify all services are healthy:

```bash
# Check API Gateway
curl http://localhost:3000/api/v1/health

# Check Speaker Service
curl http://localhost:3001/health

# Check Draft Service
curl http://localhost:3002/health

# Check RAG Service
curl http://localhost:3003/health

# Check Evaluation Service
curl http://localhost:3004/health
```

## CI/CD Integration

These tests are automatically run in the CI/CD pipeline:

```yaml
# .github/workflows/ci.yml
- name: Run Integration Tests
  run: |
    docker-compose up -d
    sleep 30  # Wait for services to be ready
    pytest tests/integration/ -v --cov
    docker-compose down
```

## Performance Benchmarks

Expected test execution times:

| Test Suite | Duration | Tests |
|------------|----------|-------|
| Complete Workflow | ~30s | 5 |
| Authentication Flow | ~5s | 8 |
| Event-Driven Workflows | ~15s | 6 |
| Service Communication | ~10s | 10 |
| Error Scenarios | ~10s | 12 |
| Data Consistency | ~15s | 8 |
| **Total** | **~85s** | **49** |

## Troubleshooting

### Tests Failing Due to Service Unavailability

```bash
# Check if all services are running
docker-compose ps

# Restart services
docker-compose restart

# Check service logs
docker-compose logs -f [service-name]
```

### Database Connection Errors

```bash
# Verify database connectivity
psql -U draftgenie -h localhost -p 5432 -d draftgenie_test
mongosh mongodb://draftgenie:draftgenie123@localhost:27017/draftgenie_test

# Reset test databases
npm run db:reset:test
```

### RabbitMQ Message Not Delivered

```bash
# Check RabbitMQ management UI
open http://localhost:15672

# Check queue status
curl -u draftgenie:draftgenie123 http://localhost:15672/api/queues
```

## Contributing

When adding new integration tests:

1. Follow the existing test structure
2. Use fixtures from `conftest.py`
3. Clean up test data in teardown
4. Add test documentation to this README
5. Ensure tests are idempotent
6. Add appropriate timeouts for async operations

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX Testing](https://www.python-httpx.org/advanced/#testing)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

