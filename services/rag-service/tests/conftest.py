"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
async def mongodb_client():
    """MongoDB test client fixture"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    client.close()


@pytest.fixture
async def test_db(mongodb_client):
    """Test database fixture"""
    db = mongodb_client.test_draft_genie
    yield db
    # Cleanup
    await mongodb_client.drop_database("test_draft_genie")


@pytest.fixture
def mock_speaker_data():
    """Mock speaker data"""
    return {
        "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dr. John Smith",
        "specialty": "Cardiology",
        "experience_level": "Senior",
        "bucket": "A",
    }


@pytest.fixture
def mock_draft_data():
    """Mock draft data"""
    return {
        "draft_id": "draft_test_123",
        "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
        "draft_type": "IFN",
        "original_text": "Patient has diabetis and hypertention.",
        "corrected_text": "Patient has diabetes and hypertension.",
        "word_count": 5,
        "correction_count": 2,
    }

