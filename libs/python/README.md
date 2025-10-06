# DraftGenie Python Shared Libraries

Shared Python libraries for DraftGenie microservices.

## Structure

```
libs/python/
├── common/          # Common utilities, logging, errors
├── domain/          # Domain models, events, value objects
├── database/        # Database clients and utilities
├── tests/           # Shared tests
├── pyproject.toml   # Poetry configuration
└── README.md        # This file
```

## Installation

### Using Poetry (Recommended)

```bash
cd libs/python
poetry install
```

### Using pip

```bash
cd libs/python
pip install -e .
```

## Usage

### In Python Services

```python
# Import from shared libraries
from common.logger import get_logger
from common.errors import NotFoundError
from domain.models import Speaker, Draft
from database.postgres import get_postgres_client
```

## Development

### Setup Development Environment

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Code Quality

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8 .
poetry run mypy .
poetry run pylint common domain database

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov
```

### Pre-commit Checks

```bash
# Run all checks
poetry run black . && poetry run isort . && poetry run flake8 . && poetry run mypy . && poetry run pytest
```

## Libraries

### common
- Logger (structlog)
- Error classes
- Constants and enums
- Utility functions
- Validators

### domain
- Pydantic models (Speaker, Draft, Evaluation)
- Domain events
- Value objects
- Repository interfaces

### database
- PostgreSQL client (SQLAlchemy async)
- MongoDB client (Motor)
- Qdrant client
- Redis client

## Testing

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_logger.py

# Run with coverage
poetry run pytest --cov --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Type Checking

```bash
# Check types
poetry run mypy common domain database

# Check specific module
poetry run mypy common/logger.py
```

