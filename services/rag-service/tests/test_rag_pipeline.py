"""
Tests for RAG pipeline
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag_pipeline import RAGPipeline
from app.services.context_service import ContextService
from app.services.llm_service import LLMService
from app.services.dfn_service import DFNService
from app.services.rag_session_service import RAGSessionService


@pytest.fixture
def mock_db():
    """Mock database"""
    return MagicMock()


@pytest.fixture
def mock_context_service():
    """Mock context service"""
    service = AsyncMock(spec=ContextService)
    service.retrieve_context = AsyncMock(return_value={
        "speaker_profile": {
            "name": "Dr. John Smith",
            "specialty": "Cardiology",
            "experience_level": "Senior",
        },
        "ifn_draft": {
            "draft_id": "draft_test_123",
            "original_text": "Patient has diabetis.",
            "draft_type": "IFN",
        },
        "correction_patterns": [
            {"original": "diabetis", "corrected": "diabetes", "category": "spelling", "frequency": 5}
        ],
        "historical_drafts": [],
        "similar_patterns": [],
    })
    service.format_context_for_prompt = MagicMock(return_value={
        "speaker_name": "Dr. John Smith",
        "speaker_specialty": "Cardiology",
        "speaker_experience": "Senior",
        "ifn_text": "Patient has diabetis.",
        "correction_patterns": [],
        "historical_examples": [],
    })
    return service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    service = AsyncMock(spec=LLMService)
    service.generate = AsyncMock(return_value="Patient has diabetes.")
    service.critique = AsyncMock(return_value="Good correction.")
    service.refine = AsyncMock(return_value="Patient has diabetes and is stable.")
    return service


@pytest.fixture
def mock_dfn_service():
    """Mock DFN service"""
    service = AsyncMock(spec=DFNService)
    service.create_dfn = AsyncMock(return_value=MagicMock(
        dfn_id="dfn_test_123",
        generated_text="Patient has diabetes.",
    ))
    return service


@pytest.fixture
def mock_session_service():
    """Mock session service"""
    service = AsyncMock(spec=RAGSessionService)
    service.create_session = AsyncMock(return_value=MagicMock(session_id="session_test_123"))
    service.add_agent_step = AsyncMock()
    service.update_session = AsyncMock()
    service.mark_complete = AsyncMock()
    service.mark_failed = AsyncMock()
    return service


@pytest.fixture
def rag_pipeline(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Create RAG pipeline with mocked dependencies (without agent)"""
    return RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=False,  # Disable agent for these tests
    )


@pytest.mark.asyncio
async def test_generate_dfn_without_critique(rag_pipeline, mock_context_service, mock_llm_service):
    """Test DFN generation without critique"""
    result = await rag_pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=False,
    )
    
    # Verify result
    assert "dfn_id" in result
    assert "session_id" in result
    assert "generated_text" in result
    assert result["generated_text"] == "Patient has diabetes."
    
    # Verify context was retrieved
    mock_context_service.retrieve_context.assert_called_once()
    
    # Verify LLM was called
    mock_llm_service.generate.assert_called_once()
    
    # Verify critique was NOT called
    mock_llm_service.critique.assert_not_called()
    mock_llm_service.refine.assert_not_called()


@pytest.mark.asyncio
async def test_generate_dfn_with_critique(rag_pipeline, mock_llm_service):
    """Test DFN generation with critique and refinement"""
    result = await rag_pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=True,
    )
    
    # Verify result
    assert "dfn_id" in result
    assert "generated_text" in result
    assert result["generated_text"] == "Patient has diabetes and is stable."
    
    # Verify LLM methods were called
    mock_llm_service.generate.assert_called_once()
    mock_llm_service.critique.assert_called_once()
    mock_llm_service.refine.assert_called_once()


@pytest.mark.asyncio
async def test_generate_dfn_missing_ifn(rag_pipeline, mock_context_service):
    """Test DFN generation with missing IFN"""
    # Mock missing IFN
    mock_context_service.retrieve_context = AsyncMock(return_value={
        "speaker_profile": {},
        "ifn_draft": None,
        "correction_patterns": [],
        "historical_drafts": [],
        "similar_patterns": [],
    })
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="not found"):
        await rag_pipeline.generate_dfn(
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            ifn_draft_id="nonexistent",
            use_critique=False,
        )

