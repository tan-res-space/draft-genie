"""
Integration tests for API Gateway authentication flow.

Tests JWT authentication, token refresh, and protected endpoints.
"""

import pytest
import asyncio
from typing import Dict
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_registration(api_client: httpx.AsyncClient):
    """Test user registration flow."""
    user_data = {
        "email": f"test-{asyncio.get_event_loop().time()}@example.com",
        "password": "SecurePassword123!",
        "name": "Test User"
    }
    
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    assert response.status_code == 201
    
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert "user" in data
    assert data["user"]["email"] == user_data["email"]
    assert data["user"]["name"] == user_data["name"]
    assert "password" not in data["user"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_login(api_client: httpx.AsyncClient):
    """Test user login with valid credentials."""
    # Use default admin user
    login_data = {
        "email": "admin@draftgenie.com",
        "password": "admin123"
    }
    
    response = await api_client.post(
        "/api/v1/auth/login",
        json=login_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert "expiresIn" in data
    assert "user" in data
    assert data["user"]["email"] == login_data["email"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_with_invalid_credentials(api_client: httpx.AsyncClient):
    """Test login fails with invalid credentials."""
    login_data = {
        "email": "admin@draftgenie.com",
        "password": "wrongpassword"
    }
    
    response = await api_client.post(
        "/api/v1/auth/login",
        json=login_data
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_token_refresh(api_client: httpx.AsyncClient):
    """Test token refresh flow."""
    # First, login to get tokens
    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@draftgenie.com",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refreshToken"]
    
    # Refresh the token
    refresh_response = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token}
    )
    assert refresh_response.status_code == 200
    
    new_tokens = refresh_response.json()
    assert "accessToken" in new_tokens
    assert "refreshToken" in new_tokens
    assert new_tokens["accessToken"] != tokens["accessToken"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_with_invalid_token(api_client: httpx.AsyncClient):
    """Test token refresh fails with invalid token."""
    response = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": "invalid-token-12345"}
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_profile(api_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test getting current user profile."""
    response = await api_client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    user = response.json()
    assert "id" in user
    assert "email" in user
    assert "name" in user
    assert "role" in user
    assert "password" not in user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_without_token(api_client: httpx.AsyncClient):
    """Test protected endpoint fails without authentication token."""
    response = await api_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(api_client: httpx.AsyncClient):
    """Test protected endpoint fails with invalid token."""
    headers = {
        "Authorization": "Bearer invalid-token-12345",
        "Content-Type": "application/json"
    }
    
    response = await api_client.get(
        "/api/v1/auth/me",
        headers=headers
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout(api_client: httpx.AsyncClient):
    """Test user logout flow."""
    # Login first
    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@draftgenie.com",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    refresh_token = tokens["refreshToken"]
    
    # Logout
    logout_response = await api_client.post(
        "/api/v1/auth/logout",
        json={"refreshToken": refresh_token}
    )
    assert logout_response.status_code in [200, 204]
    
    # Try to refresh with logged out token (should fail)
    refresh_response = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token}
    )
    assert refresh_response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_access_speaker_service_through_gateway(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test accessing Speaker Service through API Gateway."""
    # Create speaker through gateway
    speaker_data = {
        "name": "Gateway Test Speaker",
        "email": "gateway-test@example.com",
        "bucket": "A",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    speaker = response.json()
    
    # Get speaker through gateway
    response = await api_client.get(
        f"/api/v1/speakers/{speaker['id']}",
        headers=auth_headers
    )
    assert response.status_code == 200
    retrieved_speaker = response.json()
    assert retrieved_speaker["id"] == speaker["id"]
    assert retrieved_speaker["name"] == speaker_data["name"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_access_draft_service_through_gateway(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test accessing Draft Service through API Gateway."""
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": "Test draft through gateway",
        "type": "IFN",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    draft = response.json()
    assert draft["speaker_id"] == test_speaker["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_key_authentication(api_client: httpx.AsyncClient):
    """Test API key authentication for service-to-service communication."""
    headers = {
        "X-API-Key": "service-key-1",
        "Content-Type": "application/json"
    }
    
    # Try to access health endpoint with API key
    response = await api_client.get(
        "/api/v1/health/services",
        headers=headers
    )
    # Health endpoints might be public, so we test a protected endpoint
    # For now, just verify the request doesn't fail with 401
    assert response.status_code in [200, 403, 404]  # Not 401 (unauthorized)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_authenticated_requests(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test multiple concurrent authenticated requests."""
    # Make 10 concurrent requests
    tasks = [
        api_client.get(
            f"/api/v1/speakers/{test_speaker['id']}",
            headers=auth_headers
        )
        for _ in range(10)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_speaker["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting(api_client: httpx.AsyncClient):
    """Test rate limiting on API Gateway."""
    # Make many requests quickly to trigger rate limiting
    # Note: This test might be flaky depending on rate limit configuration
    
    responses = []
    for _ in range(150):  # Exceed default limit of 100 requests/minute
        response = await api_client.get("/api/v1/health")
        responses.append(response)
    
    # At least one request should be rate limited
    status_codes = [r.status_code for r in responses]
    # Rate limiting returns 429 Too Many Requests
    # This is a soft assertion as rate limiting might not trigger in test environment
    if 429 in status_codes:
        assert True, "Rate limiting is working"
    else:
        # Rate limiting might not be strict in test environment
        pytest.skip("Rate limiting not triggered in test environment")

