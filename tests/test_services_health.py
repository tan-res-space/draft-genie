"""
Simple health check tests for all running services.

This test suite verifies that all services are running and responding to health checks.
"""

import pytest
import httpx
import asyncio


# Service URLs
SPEAKER_SERVICE_URL = "http://localhost:3001"
DRAFT_SERVICE_URL = "http://localhost:3002"
RAG_SERVICE_URL = "http://localhost:3003"
EVALUATION_SERVICE_URL = "http://localhost:3004"


@pytest.mark.asyncio
async def test_speaker_service_health():
    """Test Speaker Service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SPEAKER_SERVICE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "dependencies" in data
        print(f"✅ Speaker Service: {data}")


@pytest.mark.asyncio
async def test_draft_service_health():
    """Test Draft Service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DRAFT_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "draft-service"
        assert "version" in data
        print(f"✅ Draft Service: {data}")


@pytest.mark.asyncio
async def test_rag_service_health():
    """Test RAG Service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RAG_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rag-service"
        print(f"✅ RAG Service: {data}")


@pytest.mark.asyncio
async def test_evaluation_service_health():
    """Test Evaluation Service health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{EVALUATION_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Evaluation Service: {data}")


@pytest.mark.asyncio
async def test_all_services_healthy():
    """Test that all services are healthy simultaneously."""
    async with httpx.AsyncClient() as client:
        # Make all requests concurrently
        speaker_task = client.get(f"{SPEAKER_SERVICE_URL}/api/v1/health")
        draft_task = client.get(f"{DRAFT_SERVICE_URL}/health")
        rag_task = client.get(f"{RAG_SERVICE_URL}/health")
        evaluation_task = client.get(f"{EVALUATION_SERVICE_URL}/health")
        
        responses = await asyncio.gather(
            speaker_task,
            draft_task,
            rag_task,
            evaluation_task,
            return_exceptions=True
        )
        
        # Check all responses
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                pytest.fail(f"Service {i} failed with exception: {response}")
            assert response.status_code == 200, f"Service {i} returned {response.status_code}"
        
        print("\n✅ All services are healthy!")
        print(f"  - Speaker Service: {responses[0].json()['status']}")
        print(f"  - Draft Service: {responses[1].json()['status']}")
        print(f"  - RAG Service: {responses[2].json()['status']}")
        print(f"  - Evaluation Service: {responses[3].json()['status']}")


@pytest.mark.asyncio
async def test_speaker_service_api_docs():
    """Test that Speaker Service API documentation is accessible."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SPEAKER_SERVICE_URL}/api/docs")
        assert response.status_code == 200
        print("✅ Speaker Service API docs accessible")


@pytest.mark.asyncio
async def test_speaker_service_database_connection():
    """Test that Speaker Service database connection is healthy."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SPEAKER_SERVICE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert data["dependencies"]["database"]["status"] == "healthy"
        print("✅ Speaker Service database connection healthy")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

