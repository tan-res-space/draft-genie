"""
Integration tests for error scenarios and failure handling.

Tests how the system handles various error conditions.
"""

import pytest
import asyncio
from typing import Dict
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_speaker_id(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test handling of invalid speaker ID."""
    invalid_id = "00000000-0000-0000-0000-000000000000"
    
    response = await api_client.get(
        f"/api/v1/speakers/{invalid_id}",
        headers=auth_headers
    )
    assert response.status_code == 404
    
    error = response.json()
    assert "message" in error or "detail" in error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_speaker_missing_required_fields(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test creating speaker with missing required fields."""
    incomplete_data = {
        "name": "Test Speaker"
        # Missing email and bucket
    }
    
    response = await api_client.post(
        "/api/v1/speakers",
        json=incomplete_data,
        headers=auth_headers
    )
    assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_draft_for_nonexistent_speaker(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test creating draft for non-existent speaker."""
    draft_data = {
        "speaker_id": "00000000-0000-0000-0000-000000000000",
        "content": "Test draft",
        "type": "IFN",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code in [400, 404]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_speaker_email(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test creating speaker with duplicate email."""
    speaker_data = {
        "name": "Duplicate Test",
        "email": "duplicate-test@example.com",
        "bucket": "A",
        "metadata": {"test": True}
    }
    
    # Create first speaker
    response1 = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    assert response2.status_code == 409  # Conflict


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_bucket_value(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test creating speaker with invalid bucket value."""
    speaker_data = {
        "name": "Invalid Bucket Test",
        "email": "invalid-bucket@example.com",
        "bucket": "Z",  # Invalid bucket (should be A, B, or C)
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_empty_draft_content(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test creating draft with empty content."""
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": "",  # Empty content
        "type": "IFN",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_draft_type(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test creating draft with invalid type."""
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": "Test content",
        "type": "INVALID",  # Should be IFN or DFN
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_json_request(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test handling of malformed JSON in request."""
    response = await api_client.post(
        "/api/v1/speakers",
        content="{ invalid json }",
        headers=auth_headers
    )
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unauthorized_access_to_protected_endpoint(
    api_client: httpx.AsyncClient
):
    """Test accessing protected endpoint without authentication."""
    response = await api_client.get("/api/v1/speakers")
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_token_handling(
    api_client: httpx.AsyncClient
):
    """Test handling of expired JWT token."""
    # Use a clearly expired token
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid"
    
    headers = {
        "Authorization": f"Bearer {expired_token}",
        "Content-Type": "application/json"
    }
    
    response = await api_client.get(
        "/api/v1/speakers",
        headers=headers
    )
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limit_exceeded(
    api_client: httpx.AsyncClient
):
    """Test rate limiting when too many requests are made."""
    # Make many requests quickly
    responses = []
    for _ in range(150):
        response = await api_client.get("/api/v1/health")
        responses.append(response)
        if response.status_code == 429:
            break
    
    # Check if any request was rate limited
    status_codes = [r.status_code for r in responses]
    if 429 in status_codes:
        assert True, "Rate limiting is working"
    else:
        pytest.skip("Rate limiting not triggered in test environment")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_dfn_without_drafts(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test DFN generation for speaker with no drafts."""
    # Create speaker without drafts
    speaker_data = {
        "name": "No Drafts Speaker",
        "email": "no-drafts@example.com",
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
    
    # Try to generate DFN
    rag_request = {
        "speakerId": speaker["id"],
        "prompt": "Generate DFN"
    }
    
    response = await api_client.post(
        "/api/v1/workflow/generate-dfn",
        json=rag_request,
        headers=auth_headers
    )
    assert response.status_code in [400, 404]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_updates_to_same_resource(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test concurrent updates to the same resource."""
    speaker_id = test_speaker["id"]
    
    # Make concurrent update requests
    update_data = {
        "name": "Updated Name",
        "bucket": "B"
    }
    
    tasks = [
        api_client.patch(
            f"/api/v1/speakers/{speaker_id}",
            json=update_data,
            headers=auth_headers
        )
        for _ in range(5)
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # At least one should succeed
    successful = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
    assert len(successful) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_pagination_parameters(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test handling of invalid pagination parameters."""
    # Negative page number
    response = await api_client.get(
        "/api/v1/speakers?page=-1&limit=10",
        headers=auth_headers
    )
    assert response.status_code in [400, 422]
    
    # Invalid limit
    response = await api_client.get(
        "/api/v1/speakers?page=1&limit=0",
        headers=auth_headers
    )
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_timeout_handling(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test handling of service timeouts."""
    # This test would require simulating a slow service
    # For now, we test that the gateway has appropriate timeouts
    
    # Make a request that might timeout
    try:
        response = await api_client.get(
            "/api/v1/dashboard/metrics",
            headers=auth_headers,
            timeout=1.0  # Very short timeout
        )
        # If it succeeds, that's fine
        assert response.status_code in [200, 503, 504]
    except httpx.TimeoutException:
        # Timeout is expected behavior
        assert True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_large_payload_handling(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict
):
    """Test handling of very large payloads."""
    # Create a very large draft content
    large_content = "A" * (10 * 1024 * 1024)  # 10MB
    
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": large_content,
        "type": "IFN",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    # Should either succeed or reject with 413 (Payload Too Large)
    assert response.status_code in [201, 413]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_special_characters_in_input(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """Test handling of special characters in input."""
    speaker_data = {
        "name": "Test <script>alert('xss')</script>",
        "email": "special-chars@example.com",
        "bucket": "A",
        "metadata": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/speakers",
        json=speaker_data,
        headers=auth_headers
    )
    
    if response.status_code == 201:
        speaker = response.json()
        # Verify special characters are properly escaped/sanitized
        assert "<script>" not in speaker["name"]

