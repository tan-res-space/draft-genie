"""
Pytest configuration and fixtures
"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings
from app.db.mongodb import mongodb


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create MongoDB test client"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    yield client
    client.close()


@pytest.fixture
async def test_db(mongodb_client: AsyncIOMotorClient):
    """Create test database"""
    db = mongodb_client[f"{settings.mongodb_database}_test"]
    yield db
    # Cleanup
    await mongodb_client.drop_database(f"{settings.mongodb_database}_test")


@pytest.fixture
def mock_draft_data():
    """Mock draft data for testing"""
    return {
        "draft_id": "draft_test_123",
        "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
        "draft_type": "AD",
        "original_text": "The patient has a history of diabetis and hypertension.",
        "corrected_text": "The patient has a history of diabetes and hypertension.",
        "word_count": 10,
        "correction_count": 1,
        "metadata": {"source": "test"},
    }


@pytest.fixture
def mock_correction_pattern():
    """Mock correction pattern for testing"""
    return {
        "original": "diabetis",
        "corrected": "diabetes",
        "category": "spelling",
        "frequency": 1,
        "context": "history of diabetis and",
    }

