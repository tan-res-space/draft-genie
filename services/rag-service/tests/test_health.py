"""
Tests for health check endpoints
"""
import pytest
from fastapi import status


def test_health_check(client):
    """Test basic health check"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rag-service"


def test_liveness_check(client):
    """Test liveness check"""
    response = client.get("/health/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "rag-service"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["service"] == "rag-service"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"

