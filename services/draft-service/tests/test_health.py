"""
Tests for health check endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "draft-service"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint"""
    response = await client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["service"] == "draft-service"
    assert "dependencies" in data
    assert "mongodb" in data["dependencies"]
    assert "qdrant" in data["dependencies"]


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness check endpoint"""
    response = await client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"
    assert data["service"] == "draft-service"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["service"] == "draft-service"
    assert data["status"] == "running"
    assert "version" in data
    assert "docs" in data

