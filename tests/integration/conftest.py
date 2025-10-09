"""
Shared pytest fixtures for integration tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, Any
import pytest
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import psycopg2
from redis import Redis
from qdrant_client import QdrantClient
import aio_pika

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env.test")

# Service URLs
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:3000")
SPEAKER_SERVICE_URL = os.getenv("SPEAKER_SERVICE_URL", "http://localhost:3001")
DRAFT_SERVICE_URL = os.getenv("DRAFT_SERVICE_URL", "http://localhost:3002")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:3003")
EVALUATION_SERVICE_URL = os.getenv("EVALUATION_SERVICE_URL", "http://localhost:3004")

# Database URLs
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://draftgenie:draftgenie123@localhost:5432/draftgenie_test")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://draftgenie:draftgenie123@localhost:27017/draftgenie_test?authSource=admin")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
REDIS_URL = os.getenv("REDIS_URL", "redis://:draftgenie123@localhost:6379/1")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://draftgenie:draftgenie123@localhost:5672/")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API Gateway."""
    async with httpx.AsyncClient(base_url=API_GATEWAY_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def speaker_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for Speaker Service."""
    async with httpx.AsyncClient(base_url=SPEAKER_SERVICE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def draft_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for Draft Service."""
    async with httpx.AsyncClient(base_url=DRAFT_SERVICE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def rag_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for RAG Service."""
    async with httpx.AsyncClient(base_url=RAG_SERVICE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def evaluation_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for Evaluation Service."""
    async with httpx.AsyncClient(base_url=EVALUATION_SERVICE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def postgres_connection():
    """PostgreSQL connection for test data management."""
    conn = psycopg2.connect(POSTGRES_URL)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
async def mongodb_client():
    """MongoDB client for test data management."""
    client = AsyncIOMotorClient(MONGODB_URL)
    yield client
    client.close()


@pytest.fixture(scope="session")
def redis_client():
    """Redis client for test data management."""
    client = Redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    client.close()


@pytest.fixture(scope="session")
def qdrant_client():
    """Qdrant client for test data management."""
    client = QdrantClient(url=QDRANT_URL)
    yield client


@pytest.fixture(scope="session")
async def rabbitmq_connection():
    """RabbitMQ connection for event testing."""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    yield connection
    await connection.close()


@pytest.fixture
async def auth_token(api_client: httpx.AsyncClient) -> str:
    """Get authentication token from API Gateway."""
    # Login with default admin user
    response = await api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@draftgenie.com",
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    return data["accessToken"]


@pytest.fixture
async def auth_headers(auth_token: str) -> Dict[str, str]:
    """Get authentication headers for API requests."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
async def test_speaker(api_client: httpx.AsyncClient, auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Create a test speaker and return its data."""
    speaker_data = {
        "name": "Test Speaker Integration",
        "email": f"test-{os.urandom(4).hex()}@example.com",
        "bucket": "A",
        "metadata": {
            "test": True,
            "created_by": "integration_test"
        }
    }
    
    response = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def test_draft(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a test draft for the test speaker."""
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": "This is a test draft content for integration testing. It contains some sample text.",
        "type": "IFN",
        "metadata": {
            "test": True,
            "created_by": "integration_test"
        }
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture(autouse=True)
async def cleanup_test_data(
    postgres_connection,
    mongodb_client,
    redis_client,
    qdrant_client
):
    """Clean up test data after each test."""
    yield
    
    # Clean up PostgreSQL test data
    with postgres_connection.cursor() as cursor:
        cursor.execute("DELETE FROM speakers WHERE metadata->>'test' = 'true'")
        postgres_connection.commit()
    
    # Clean up MongoDB test data
    db = mongodb_client.get_database("draftgenie_test")
    await db.drafts.delete_many({"metadata.test": True})
    await db.evaluations.delete_many({"metadata.test": True})
    
    # Clean up Redis test data
    for key in redis_client.scan_iter("test:*"):
        redis_client.delete(key)
    
    # Clean up Qdrant test collections
    try:
        collections = qdrant_client.get_collections().collections
        for collection in collections:
            if "test" in collection.name.lower():
                qdrant_client.delete_collection(collection.name)
    except Exception:
        pass  # Collection might not exist


@pytest.fixture
async def wait_for_event(rabbitmq_connection):
    """Helper to wait for RabbitMQ events."""
    async def _wait(queue_name: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for a message on the specified queue."""
        channel = await rabbitmq_connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        
        try:
            message = await asyncio.wait_for(
                queue.get(timeout=timeout),
                timeout=timeout
            )
            await message.ack()
            return message.body.decode()
        except asyncio.TimeoutError:
            raise TimeoutError(f"No message received on queue '{queue_name}' within {timeout}s")
        finally:
            await channel.close()
    
    return _wait


@pytest.fixture
def assert_service_healthy():
    """Helper to assert service health."""
    async def _check(client: httpx.AsyncClient, service_name: str):
        """Check if service is healthy."""
        try:
            response = await client.get("/health")
            assert response.status_code == 200, f"{service_name} is not healthy"
            data = response.json()
            assert data.get("status") in ["ok", "healthy"], f"{service_name} status: {data.get('status')}"
        except Exception as e:
            pytest.fail(f"{service_name} health check failed: {str(e)}")
    
    return _check


@pytest.fixture
async def verify_all_services_healthy(
    api_client,
    speaker_client,
    draft_client,
    rag_client,
    evaluation_client,
    assert_service_healthy
):
    """Verify all services are healthy before running tests."""
    await assert_service_healthy(api_client, "API Gateway")
    await assert_service_healthy(speaker_client, "Speaker Service")
    await assert_service_healthy(draft_client, "Draft Service")
    await assert_service_healthy(rag_client, "RAG Service")
    await assert_service_healthy(evaluation_client, "Evaluation Service")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "requires_ai: marks tests that require AI services (Gemini)")

