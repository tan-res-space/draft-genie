"""
Tests for health check endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "evaluation-service"
        assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check():
    """Test basic health check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_liveness_check():
    """Test liveness check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_check():
    """Test readiness check"""
    with patch("app.api.health.database") as mock_db:
        mock_db.health_check = AsyncMock(return_value=True)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "dependencies" in data

