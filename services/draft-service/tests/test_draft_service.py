"""
Tests for draft service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.draft_service import DraftService
from app.models.draft import DraftCreate, DraftModel
from app.repositories.draft_repository import DraftRepository
from app.clients.instanote_client import InstaNoteMockClient


@pytest.fixture
def mock_draft_repository():
    """Mock draft repository"""
    repo = AsyncMock(spec=DraftRepository)
    return repo


@pytest.fixture
def mock_instanote_client():
    """Mock InstaNote client"""
    client = AsyncMock(spec=InstaNoteMockClient)
    return client


@pytest.fixture
def draft_service(mock_draft_repository, mock_instanote_client):
    """Create draft service with mocked dependencies"""
    return DraftService(mock_draft_repository, mock_instanote_client)


@pytest.mark.asyncio
async def test_ingest_drafts_for_speaker(
    draft_service, mock_instanote_client, mock_draft_repository, mock_draft_data
):
    """Test ingesting drafts for a speaker"""
    speaker_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Mock InstaNote response
    mock_instanote_client.fetch_speaker_drafts.return_value = [mock_draft_data]
    
    # Mock repository responses
    mock_draft_repository.find_by_id.return_value = None  # Draft doesn't exist
    mock_draft_repository.create.return_value = DraftModel(
        **mock_draft_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_processed=False,
        vector_generated=False,
    )
    
    # Mock event publisher
    with patch("app.services.draft_service.event_publisher") as mock_publisher:
        mock_publisher.publish_draft_ingested_event = AsyncMock()
        
        # Execute
        drafts = await draft_service.ingest_drafts_for_speaker(speaker_id, limit=10)
        
        # Verify
        assert len(drafts) == 1
        assert drafts[0].speaker_id == speaker_id
        mock_instanote_client.fetch_speaker_drafts.assert_called_once_with(speaker_id, 10)
        mock_draft_repository.create.assert_called_once()
        mock_publisher.publish_draft_ingested_event.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_drafts_skip_existing(
    draft_service, mock_instanote_client, mock_draft_repository, mock_draft_data
):
    """Test that existing drafts are skipped during ingestion"""
    speaker_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Mock InstaNote response
    mock_instanote_client.fetch_speaker_drafts.return_value = [mock_draft_data]
    
    # Mock repository - draft already exists
    mock_draft_repository.find_by_id.return_value = DraftModel(
        **mock_draft_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_processed=False,
        vector_generated=False,
    )
    
    # Execute
    drafts = await draft_service.ingest_drafts_for_speaker(speaker_id, limit=10)
    
    # Verify - no drafts created
    assert len(drafts) == 0
    mock_draft_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_draft(draft_service, mock_draft_repository, mock_draft_data):
    """Test creating a single draft"""
    draft_create = DraftCreate(**mock_draft_data)
    
    # Mock repository responses
    mock_draft_repository.find_by_id.return_value = None
    mock_draft_repository.create.return_value = DraftModel(
        **mock_draft_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_processed=False,
        vector_generated=False,
    )
    
    # Mock event publisher
    with patch("app.services.draft_service.event_publisher") as mock_publisher:
        mock_publisher.publish_draft_ingested_event = AsyncMock()
        
        # Execute
        draft = await draft_service.create_draft(draft_create)
        
        # Verify
        assert draft.draft_id == mock_draft_data["draft_id"]
        assert draft.speaker_id == mock_draft_data["speaker_id"]
        mock_draft_repository.create.assert_called_once()
        mock_publisher.publish_draft_ingested_event.assert_called_once()


@pytest.mark.asyncio
async def test_create_draft_already_exists(
    draft_service, mock_draft_repository, mock_draft_data
):
    """Test creating a draft that already exists raises error"""
    draft_create = DraftCreate(**mock_draft_data)
    
    # Mock repository - draft already exists
    mock_draft_repository.find_by_id.return_value = DraftModel(
        **mock_draft_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_processed=False,
        vector_generated=False,
    )
    
    # Execute and verify error
    with pytest.raises(ValueError, match="already exists"):
        await draft_service.create_draft(draft_create)


@pytest.mark.asyncio
async def test_get_draft_by_id(draft_service, mock_draft_repository, mock_draft_data):
    """Test getting draft by ID"""
    draft_id = mock_draft_data["draft_id"]
    
    # Mock repository response
    mock_draft_repository.find_by_id.return_value = DraftModel(
        **mock_draft_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_processed=False,
        vector_generated=False,
    )
    
    # Execute
    draft = await draft_service.get_draft_by_id(draft_id)
    
    # Verify
    assert draft is not None
    assert draft.draft_id == draft_id
    mock_draft_repository.find_by_id.assert_called_once_with(draft_id)


@pytest.mark.asyncio
async def test_get_drafts_by_speaker(
    draft_service, mock_draft_repository, mock_draft_data
):
    """Test getting drafts by speaker ID"""
    speaker_id = mock_draft_data["speaker_id"]
    
    # Mock repository response
    mock_draft_repository.find_by_speaker_id.return_value = [
        DraftModel(
            **mock_draft_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_processed=False,
            vector_generated=False,
        )
    ]
    
    # Execute
    drafts = await draft_service.get_drafts_by_speaker(speaker_id)
    
    # Verify
    assert len(drafts) == 1
    assert drafts[0].speaker_id == speaker_id
    mock_draft_repository.find_by_speaker_id.assert_called_once()


@pytest.mark.asyncio
async def test_mark_draft_as_processed(draft_service, mock_draft_repository):
    """Test marking draft as processed"""
    draft_id = "draft_test_123"
    
    # Mock repository response
    mock_draft_repository.mark_as_processed.return_value = True
    
    # Execute
    result = await draft_service.mark_draft_as_processed(draft_id)
    
    # Verify
    assert result is True
    mock_draft_repository.mark_as_processed.assert_called_once_with(draft_id)


@pytest.mark.asyncio
async def test_get_unprocessed_drafts(
    draft_service, mock_draft_repository, mock_draft_data
):
    """Test getting unprocessed drafts"""
    # Mock repository response
    mock_draft_repository.get_unprocessed_drafts.return_value = [
        DraftModel(
            **mock_draft_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_processed=False,
            vector_generated=False,
        )
    ]
    
    # Execute
    drafts = await draft_service.get_unprocessed_drafts(limit=100)
    
    # Verify
    assert len(drafts) == 1
    assert drafts[0].is_processed is False
    mock_draft_repository.get_unprocessed_drafts.assert_called_once_with(100)

