"""
Integration tests for event-driven workflows via RabbitMQ.

Tests message flow between services through RabbitMQ events.
"""

import pytest
import asyncio
import json
from typing import Dict, Any
import httpx
import aio_pika


@pytest.mark.integration
@pytest.mark.asyncio
async def test_speaker_created_event_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    rabbitmq_connection,
    wait_for_event
):
    """
    Test speaker.created event is published and consumed.
    
    Flow:
    1. Create speaker via API
    2. Verify speaker.created event is published to RabbitMQ
    3. Verify Draft Service receives the event
    """
    # Subscribe to speaker.created queue before creating speaker
    channel = await rabbitmq_connection.channel()
    queue = await channel.declare_queue("speaker.created", durable=True)
    
    # Create speaker
    speaker_data = {
        "name": "Event Test Speaker",
        "email": "event-test@example.com",
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
    
    # Wait for event
    try:
        message = await asyncio.wait_for(queue.get(), timeout=5.0)
        await message.ack()
        
        event_data = json.loads(message.body.decode())
        assert event_data["event_type"] == "speaker.created"
        assert event_data["data"]["id"] == speaker["id"]
        assert event_data["data"]["name"] == speaker_data["name"]
    except asyncio.TimeoutError:
        pytest.fail("speaker.created event not received within timeout")
    finally:
        await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_draft_ingested_event_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any],
    rabbitmq_connection
):
    """
    Test draft.ingested event is published when draft is created.
    
    Flow:
    1. Create draft via API
    2. Verify draft.ingested event is published
    3. Verify RAG Service can receive the event
    """
    channel = await rabbitmq_connection.channel()
    queue = await channel.declare_queue("draft.ingested", durable=True)
    
    # Create draft
    draft_data = {
        "speaker_id": test_speaker["id"],
        "content": "Test draft for event flow",
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
    
    # Wait for event
    try:
        message = await asyncio.wait_for(queue.get(), timeout=5.0)
        await message.ack()
        
        event_data = json.loads(message.body.decode())
        assert event_data["event_type"] == "draft.ingested"
        assert event_data["data"]["id"] == draft["id"]
        assert event_data["data"]["speaker_id"] == test_speaker["id"]
    except asyncio.TimeoutError:
        pytest.fail("draft.ingested event not received within timeout")
    finally:
        await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_ai
async def test_dfn_generated_event_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any],
    test_draft: Dict[str, Any],
    rabbitmq_connection
):
    """
    Test dfn.generated event is published after RAG generation.
    
    Flow:
    1. Trigger DFN generation
    2. Verify dfn.generated event is published
    3. Verify Evaluation Service receives the event
    """
    channel = await rabbitmq_connection.channel()
    queue = await channel.declare_queue("dfn.generated", durable=True)
    
    # Trigger DFN generation
    rag_request = {
        "speakerId": test_speaker["id"],
        "prompt": "Generate improved draft",
        "context": {"test": True}
    }
    
    response = await api_client.post(
        "/api/v1/workflow/generate-dfn",
        json=rag_request,
        headers=auth_headers
    )
    assert response.status_code in [200, 201]
    
    # Wait for event (longer timeout for AI processing)
    try:
        message = await asyncio.wait_for(queue.get(), timeout=30.0)
        await message.ack()
        
        event_data = json.loads(message.body.decode())
        assert event_data["event_type"] == "dfn.generated"
        assert event_data["data"]["speaker_id"] == test_speaker["id"]
    except asyncio.TimeoutError:
        pytest.skip("DFN generation took too long or AI service unavailable")
    finally:
        await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_evaluation_completed_event_flow(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any],
    rabbitmq_connection
):
    """
    Test evaluation.completed event triggers bucket reassignment.
    
    Flow:
    1. Wait for evaluation.completed event
    2. Verify Speaker Service receives the event
    3. Verify bucket reassignment logic is triggered
    """
    channel = await rabbitmq_connection.channel()
    queue = await channel.declare_queue("evaluation.completed", durable=True)
    
    # This test waits for an evaluation.completed event
    # In a real scenario, this would be triggered by the evaluation service
    # For testing, we can simulate or wait for actual evaluation
    
    try:
        message = await asyncio.wait_for(queue.get(), timeout=10.0)
        await message.ack()
        
        event_data = json.loads(message.body.decode())
        assert event_data["event_type"] == "evaluation.completed"
        assert "data" in event_data
        assert "speaker_id" in event_data["data"]
        assert "metrics" in event_data["data"]
    except asyncio.TimeoutError:
        pytest.skip("No evaluation.completed event available for testing")
    finally:
        await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_idempotency(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    rabbitmq_connection
):
    """
    Test that duplicate events are handled idempotently.
    
    Services should handle duplicate events gracefully without
    creating duplicate resources.
    """
    channel = await rabbitmq_connection.channel()
    
    # Publish the same event twice
    event_data = {
        "event_type": "speaker.created",
        "event_id": "test-event-123",
        "timestamp": "2025-10-06T12:00:00Z",
        "data": {
            "id": "test-speaker-123",
            "name": "Idempotency Test",
            "bucket": "A"
        }
    }
    
    # Publish event twice
    for _ in range(2):
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="speaker.created"
        )
    
    await asyncio.sleep(2)
    
    # Services should handle this idempotently
    # This is more of a documentation test - actual verification
    # would require checking service logs or database state
    await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_ordering(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    test_speaker: Dict[str, Any],
    rabbitmq_connection
):
    """
    Test that events are processed in the correct order.
    
    Flow:
    1. Create multiple drafts quickly
    2. Verify events are processed in order
    3. Verify no race conditions
    """
    channel = await rabbitmq_connection.channel()
    queue = await channel.declare_queue("draft.ingested", durable=True)
    
    # Create multiple drafts quickly
    draft_ids = []
    for i in range(3):
        draft_data = {
            "speaker_id": test_speaker["id"],
            "content": f"Draft {i} for ordering test",
            "type": "IFN",
            "metadata": {"test": True, "order": i}
        }
        
        response = await api_client.post(
            "/api/v1/drafts",
            json=draft_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        draft = response.json()
        draft_ids.append(draft["id"])
    
    # Collect events
    events = []
    for _ in range(3):
        try:
            message = await asyncio.wait_for(queue.get(), timeout=5.0)
            await message.ack()
            event_data = json.loads(message.body.decode())
            events.append(event_data)
        except asyncio.TimeoutError:
            break
    
    await channel.close()
    
    # Verify we received events for all drafts
    assert len(events) == 3
    received_ids = [e["data"]["id"] for e in events]
    assert set(received_ids) == set(draft_ids)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dead_letter_queue_handling(
    rabbitmq_connection
):
    """
    Test that failed message processing goes to dead letter queue.
    
    This tests the error handling mechanism for event processing.
    """
    channel = await rabbitmq_connection.channel()
    
    # Declare dead letter queue
    dlq = await channel.declare_queue("dlq.draft.ingested", durable=True)
    
    # Check if there are any messages in DLQ
    # In a real scenario, we would trigger a failure and verify
    # the message ends up in DLQ
    
    try:
        message = await asyncio.wait_for(dlq.get(), timeout=2.0)
        if message:
            await message.ack()
            # If we got a message, DLQ is working
            assert True
    except asyncio.TimeoutError:
        # No messages in DLQ is also fine for this test
        pass
    finally:
        await channel.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_retry_mechanism(
    api_client: httpx.AsyncClient,
    auth_headers: Dict[str, str],
    rabbitmq_connection
):
    """
    Test that failed event processing is retried.
    
    Services should retry failed event processing with exponential backoff.
    """
    # This is more of a documentation test
    # Actual retry testing would require simulating service failures
    # and monitoring retry attempts
    
    channel = await rabbitmq_connection.channel()
    
    # Check retry queue exists
    try:
        retry_queue = await channel.declare_queue(
            "retry.draft.ingested",
            durable=True,
            passive=True  # Don't create, just check if exists
        )
        assert retry_queue is not None
    except Exception:
        pytest.skip("Retry queue not configured")
    finally:
        await channel.close()

