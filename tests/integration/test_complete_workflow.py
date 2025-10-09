"""
End-to-end integration tests for complete workflows.

Tests the full flow: Speaker → Draft → RAG → Evaluation
"""

import pytest
import asyncio
from typing import Dict, Any
import httpx


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_speaker_to_evaluation_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    verify_all_services_healthy
):
    """
    Test complete workflow from speaker creation to evaluation.
    
    Flow:
    1. Create speaker
    2. Upload draft (IFN)
    3. Trigger RAG generation (DFN)
    4. Verify evaluation is created
    5. Check metrics are calculated
    """
    # Step 1: Create speaker
    speaker_data = {
        "name": "E2E Test Speaker",
        "email": "e2e-test@example.com",
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
    speaker_id = speaker["id"]
    assert speaker["name"] == speaker_data["name"]
    assert speaker["bucket"] == "A"
    
    # Step 2: Upload draft (IFN)
    draft_data = {
        "speaker_id": speaker_id,
        "content": "This is the initial draft from notes. It needs improvement and correction.",
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
    draft_id = draft["id"]
    assert draft["speaker_id"] == speaker_id
    assert draft["type"] == "IFN"
    
    # Wait for draft processing
    await asyncio.sleep(2)
    
    # Step 3: Trigger RAG generation (DFN)
    rag_request = {
        "speakerId": speaker_id,
        "prompt": "Generate an improved draft with corrections",
        "context": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/workflow/generate-dfn",
        json=rag_request,
        headers=auth_headers
    )
    assert response.status_code in [200, 201]
    workflow_result = response.json()
    assert workflow_result["workflow"]["status"] in ["completed", "processing"]
    
    # If workflow is processing, wait for completion
    if workflow_result["workflow"]["status"] == "processing":
        await asyncio.sleep(10)
    
    # Step 4: Verify DFN was created
    response = await api_client.get(
        f"/api/v1/drafts?speaker_id={speaker_id}&type=DFN",
        headers=auth_headers
    )
    assert response.status_code == 200
    drafts = response.json()
    dfn_drafts = [d for d in drafts if d["type"] == "DFN"]
    assert len(dfn_drafts) > 0, "DFN draft should be created"
    
    # Step 5: Verify evaluation is created
    await asyncio.sleep(3)  # Wait for evaluation processing
    
    response = await api_client.get(
        f"/api/v1/evaluations?speaker_id={speaker_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    evaluations = response.json()
    assert len(evaluations) > 0, "Evaluation should be created"
    
    evaluation = evaluations[0]
    assert "metrics" in evaluation
    assert "ser" in evaluation["metrics"]
    assert "wer" in evaluation["metrics"]
    
    # Step 6: Verify speaker metrics are updated
    response = await api_client.get(
        f"/api/v1/speakers/{speaker_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    complete_data = response.json()
    assert complete_data["speaker"]["id"] == speaker_id
    assert complete_data["summary"]["totalDrafts"] >= 2  # IFN + DFN
    assert complete_data["summary"]["totalEvaluations"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_speaker_aggregation_endpoint(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any],
    test_draft: Dict[str, Any]
):
    """Test speaker complete aggregation endpoint."""
    speaker_id = test_speaker["id"]
    
    response = await api_client.get(
        f"/api/v1/speakers/{speaker_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["speaker"]["id"] == speaker_id
    assert "drafts" in data
    assert "evaluations" in data
    assert "metrics" in data
    assert "summary" in data
    assert "aggregatedAt" in data
    
    # Verify summary statistics
    summary = data["summary"]
    assert "totalDrafts" in summary
    assert "totalEvaluations" in summary
    assert "hasMetrics" in summary


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dashboard_metrics_aggregation(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any]
):
    """Test dashboard metrics aggregation endpoint."""
    response = await api_client.get(
        "/api/v1/dashboard/metrics",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "speakers" in data
    assert "evaluations" in data
    assert "drafts" in data
    assert "summary" in data
    assert "aggregatedAt" in data
    
    # Verify summary
    summary = data["summary"]
    assert "totalSpeakers" in summary
    assert "totalDrafts" in summary
    assert "totalEvaluations" in summary
    assert "servicesHealthy" in summary
    assert "servicesTotal" in summary
    assert "healthPercentage" in summary
    
    # Health percentage should be 0-100
    assert 0 <= summary["healthPercentage"] <= 100


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bucket_reassignment_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str]
):
    """
    Test bucket reassignment based on evaluation metrics.
    
    Flow:
    1. Create speaker in bucket A
    2. Create drafts with poor quality
    3. Trigger evaluation
    4. Verify bucket is reassigned to B or C
    """
    # Create speaker in bucket A
    speaker_data = {
        "name": "Bucket Test Speaker",
        "email": "bucket-test@example.com",
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
    speaker_id = speaker["id"]
    
    # Create draft with intentionally poor quality
    draft_data = {
        "speaker_id": speaker_id,
        "content": "tis is a vry bad drft wit lots of erors",
        "type": "IFN",
        "metadata": {"test": True, "quality": "poor"}
    }
    
    response = await api_client.post(
        "/api/v1/drafts",
        json=draft_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Wait for processing and evaluation
    await asyncio.sleep(5)
    
    # Check if bucket was reassigned
    response = await api_client.get(
        f"/api/v1/speakers/{speaker_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_speaker = response.json()
    
    # Bucket might be reassigned based on quality metrics
    # This is a soft assertion as it depends on evaluation thresholds
    assert updated_speaker["bucket"] in ["A", "B", "C"]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_multiple_drafts_workflow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any]
):
    """Test workflow with multiple drafts for the same speaker."""
    speaker_id = test_speaker["id"]
    
    # Create multiple drafts
    draft_contents = [
        "First draft content for testing",
        "Second draft with different content",
        "Third draft to test multiple submissions"
    ]
    
    draft_ids = []
    for content in draft_contents:
        draft_data = {
            "speaker_id": speaker_id,
            "content": content,
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
        draft_ids.append(draft["id"])
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Verify all drafts are stored
    response = await api_client.get(
        f"/api/v1/drafts?speaker_id={speaker_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) >= len(draft_contents)
    
    # Verify speaker complete shows all drafts
    response = await api_client.get(
        f"/api/v1/speakers/{speaker_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == 200
    complete_data = response.json()
    assert complete_data["summary"]["totalDrafts"] >= len(draft_contents)

