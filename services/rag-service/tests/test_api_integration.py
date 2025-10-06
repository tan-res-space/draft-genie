"""
Integration tests for RAG Service APIs
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB"""
    with patch("app.db.mongodb.mongodb") as mock:
        mock.health_check = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant"""
    with patch("app.db.qdrant.qdrant") as mock:
        mock.health_check = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_speaker_client():
    """Mock Speaker Client"""
    with patch("app.clients.speaker_client.speaker_client") as mock:
        mock.health_check = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_draft_client():
    """Mock Draft Client"""
    with patch("app.clients.draft_client.draft_client") as mock:
        mock.health_check = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_event_publisher():
    """Mock Event Publisher"""
    with patch("app.events.publisher.event_publisher") as mock:
        mock.health_check = AsyncMock(return_value=True)
        mock.publish_dfn_generated_event = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test basic health endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_liveness_endpoint():
    """Test liveness endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_endpoint(
    mock_mongodb, mock_qdrant, mock_speaker_client, mock_draft_client
):
    """Test readiness endpoint with all dependencies"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "dependencies" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "RAG Service" in data["message"]


@pytest.mark.asyncio
async def test_generate_dfn_missing_params():
    """Test generate DFN endpoint with missing parameters"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/rag/generate")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_dfn_with_mocked_pipeline():
    """Test generate DFN endpoint with mocked pipeline"""
    mock_result = {
        "dfn_id": "dfn_test_123",
        "session_id": "session_test_123",
        "generated_text": "Patient has diabetes.",
        "word_count": 3,
        "confidence_score": 0.85,
        "context_used": {},
        "steps_completed": ["context_analysis", "draft_generation"],
    }
    
    with patch("app.api.rag.get_rag_pipeline_dependency") as mock_dep:
        mock_pipeline = AsyncMock()
        mock_pipeline.generate_dfn = AsyncMock(return_value=mock_result)
        mock_dep.return_value = mock_pipeline
        
        with patch("app.events.publisher.event_publisher") as mock_pub:
            mock_pub.publish_dfn_generated_event = AsyncMock()
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/rag/generate",
                    params={
                        "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
                        "ifn_draft_id": "draft_test_123",
                        "use_critique": True,
                    },
                )
                assert response.status_code == 201
                data = response.json()
                assert data["dfn_id"] == "dfn_test_123"
                assert data["session_id"] == "session_test_123"
                assert "generated_text" in data


@pytest.mark.asyncio
async def test_get_session_not_found():
    """Test get session endpoint with non-existent session"""
    with patch("app.api.rag.get_rag_pipeline_dependency") as mock_dep:
        mock_pipeline = AsyncMock()
        mock_pipeline.session_service.get_session_by_id = AsyncMock(return_value=None)
        mock_dep.return_value = mock_pipeline
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/rag/sessions/nonexistent")
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_success():
    """Test get session endpoint with existing session"""
    mock_session = MagicMock()
    mock_session.session_id = "session_test_123"
    mock_session.speaker_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_session.ifn_draft_id = "draft_test_123"
    mock_session.context_retrieved = {}
    mock_session.prompts_used = []
    mock_session.agent_steps = []
    mock_session.dfn_generated = True
    mock_session.dfn_id = "dfn_test_123"
    mock_session.status = "complete"
    mock_session.error_message = None
    mock_session.created_at.isoformat = MagicMock(return_value="2025-10-06T00:00:00")
    mock_session.updated_at.isoformat = MagicMock(return_value="2025-10-06T00:00:00")
    
    with patch("app.api.rag.get_rag_pipeline_dependency") as mock_dep:
        mock_pipeline = AsyncMock()
        mock_pipeline.session_service.get_session_by_id = AsyncMock(return_value=mock_session)
        mock_dep.return_value = mock_pipeline
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/rag/sessions/session_test_123")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_test_123"
            assert data["status"] == "complete"


@pytest.mark.asyncio
async def test_get_speaker_sessions():
    """Test get speaker sessions endpoint"""
    with patch("app.api.rag.get_rag_pipeline_dependency") as mock_dep:
        mock_pipeline = AsyncMock()
        mock_pipeline.session_service.get_sessions_by_speaker = AsyncMock(return_value=[])
        mock_dep.return_value = mock_pipeline
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/rag/sessions/speaker/550e8400-e29b-41d4-a716-446655440000"
            )
            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_get_dfn_not_found():
    """Test get DFN endpoint with non-existent DFN"""
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.get_dfn_by_id = AsyncMock(return_value=None)
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/dfn/nonexistent")
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_dfn_success():
    """Test get DFN endpoint with existing DFN"""
    from datetime import datetime
    
    mock_dfn = MagicMock()
    mock_dfn.id = "507f1f77bcf86cd799439011"
    mock_dfn.dfn_id = "dfn_test_123"
    mock_dfn.speaker_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_dfn.session_id = "session_test_123"
    mock_dfn.ifn_draft_id = "draft_test_123"
    mock_dfn.generated_text = "Patient has diabetes."
    mock_dfn.word_count = 3
    mock_dfn.confidence_score = 0.85
    mock_dfn.context_used = {}
    mock_dfn.metadata = {}
    mock_dfn.created_at = datetime.utcnow()
    mock_dfn.updated_at = datetime.utcnow()
    
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.get_dfn_by_id = AsyncMock(return_value=mock_dfn)
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/dfn/dfn_test_123")
            assert response.status_code == 200
            data = response.json()
            assert data["dfn_id"] == "dfn_test_123"
            assert data["generated_text"] == "Patient has diabetes."


@pytest.mark.asyncio
async def test_list_dfns():
    """Test list DFNs endpoint"""
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.get_all_dfns = AsyncMock(return_value=[])
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/dfn")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_speaker_dfns():
    """Test get speaker DFNs endpoint"""
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.get_dfns_by_speaker = AsyncMock(return_value=[])
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/dfn/speaker/550e8400-e29b-41d4-a716-446655440000"
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_dfn_not_found():
    """Test delete DFN endpoint with non-existent DFN"""
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.delete_dfn = AsyncMock(return_value=False)
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/dfn/nonexistent")
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_dfn_success():
    """Test delete DFN endpoint with existing DFN"""
    with patch("app.api.dfn.get_dfn_service_dependency") as mock_dep:
        mock_service = AsyncMock()
        mock_service.delete_dfn = AsyncMock(return_value=True)
        mock_dep.return_value = mock_service
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/v1/dfn/dfn_test_123")
            assert response.status_code == 204

