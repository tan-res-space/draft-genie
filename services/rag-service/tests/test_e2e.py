"""
End-to-end tests for RAG Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.rag_pipeline import RAGPipeline
from app.services.context_service import ContextService
from app.services.llm_service import LLMService
from app.services.dfn_service import DFNService
from app.services.rag_session_service import RAGSessionService
from app.agents.rag_agent import RAGAgent


@pytest.fixture
def mock_db():
    """Mock database"""
    return MagicMock()


@pytest.fixture
def mock_context_service():
    """Mock context service with realistic data"""
    service = AsyncMock(spec=ContextService)
    service.retrieve_context = AsyncMock(return_value={
        "speaker_profile": {
            "speaker_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Dr. Sarah Johnson",
            "specialty": "Cardiology",
            "experience_level": "Senior",
            "years_of_experience": 15,
        },
        "ifn_draft": {
            "draft_id": "draft_ifn_001",
            "original_text": "Pt c/o chest pain. Hx of HTN and diabetis. EKG shows ST elevation. Started on asprin and heparin.",
            "draft_type": "IFN",
            "word_count": 20,
        },
        "correction_patterns": [
            {"original": "diabetis", "corrected": "diabetes", "category": "spelling", "frequency": 8},
            {"original": "asprin", "corrected": "aspirin", "category": "spelling", "frequency": 5},
            {"original": "c/o", "corrected": "complains of", "category": "abbreviation", "frequency": 12},
            {"original": "Pt", "corrected": "Patient", "category": "abbreviation", "frequency": 15},
            {"original": "Hx", "corrected": "History", "category": "abbreviation", "frequency": 10},
        ],
        "historical_drafts": [
            {
                "ifn": "Pt with diabetis",
                "dfn": "Patient with diabetes",
            },
            {
                "ifn": "Started on asprin",
                "dfn": "Started on aspirin",
            },
        ],
        "similar_patterns": [],
    })
    service.format_context_for_prompt = MagicMock(return_value={
        "speaker_name": "Dr. Sarah Johnson",
        "speaker_specialty": "Cardiology",
        "speaker_experience": "Senior (15 years)",
        "ifn_text": "Pt c/o chest pain. Hx of HTN and diabetis. EKG shows ST elevation. Started on asprin and heparin.",
        "correction_patterns": [
            {"original": "diabetis", "corrected": "diabetes", "category": "spelling"},
            {"original": "asprin", "corrected": "aspirin", "category": "spelling"},
            {"original": "c/o", "corrected": "complains of", "category": "abbreviation"},
        ],
        "historical_examples": [
            {"ifn": "Pt with diabetis", "dfn": "Patient with diabetes"},
        ],
    })
    return service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service with realistic responses"""
    service = AsyncMock(spec=LLMService)
    service.generate = AsyncMock(return_value=(
        "Patient complains of chest pain. History of hypertension and diabetes. "
        "EKG shows ST elevation. Started on aspirin and heparin."
    ))
    service.critique = AsyncMock(return_value=(
        "The text is well-formatted and professional. All abbreviations have been expanded correctly. "
        "Spelling errors have been corrected. The clinical information is clear and accurate."
    ))
    service.refine = AsyncMock(return_value=(
        "Patient complains of chest pain. History of hypertension and diabetes mellitus. "
        "Electrocardiogram shows ST segment elevation. Initiated treatment with aspirin and heparin."
    ))
    return service


@pytest.fixture
def mock_dfn_service():
    """Mock DFN service"""
    service = AsyncMock(spec=DFNService)
    
    def create_dfn_side_effect(dfn_create):
        mock_dfn = MagicMock()
        mock_dfn.id = "507f1f77bcf86cd799439011"
        mock_dfn.dfn_id = dfn_create.dfn_id
        mock_dfn.speaker_id = dfn_create.speaker_id
        mock_dfn.session_id = dfn_create.session_id
        mock_dfn.ifn_draft_id = dfn_create.ifn_draft_id
        mock_dfn.generated_text = dfn_create.generated_text
        mock_dfn.word_count = dfn_create.word_count
        mock_dfn.confidence_score = dfn_create.confidence_score
        mock_dfn.context_used = dfn_create.context_used
        mock_dfn.metadata = dfn_create.metadata
        mock_dfn.created_at = datetime.utcnow()
        mock_dfn.updated_at = datetime.utcnow()
        return mock_dfn
    
    service.create_dfn = AsyncMock(side_effect=create_dfn_side_effect)
    service.get_dfn_by_id = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_session_service():
    """Mock session service"""
    service = AsyncMock(spec=RAGSessionService)
    
    def create_session_side_effect(session_create):
        mock_session = MagicMock()
        mock_session.session_id = session_create.session_id
        mock_session.speaker_id = session_create.speaker_id
        mock_session.ifn_draft_id = session_create.ifn_draft_id
        return mock_session
    
    service.create_session = AsyncMock(side_effect=create_session_side_effect)
    service.add_agent_step = AsyncMock()
    service.update_session = AsyncMock()
    service.mark_complete = AsyncMock()
    service.mark_failed = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_e2e_dfn_generation_without_critique(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Test end-to-end DFN generation without critique"""
    # Create pipeline
    pipeline = RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=False,
    )
    
    # Generate DFN
    result = await pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_ifn_001",
        use_critique=False,
    )
    
    # Verify result
    assert "dfn_id" in result
    assert "session_id" in result
    assert "generated_text" in result
    assert result["word_count"] > 0
    assert result["confidence_score"] > 0
    
    # Verify services were called
    mock_context_service.retrieve_context.assert_called_once()
    mock_llm_service.generate.assert_called_once()
    mock_llm_service.critique.assert_not_called()
    mock_llm_service.refine.assert_not_called()
    mock_dfn_service.create_dfn.assert_called_once()
    mock_session_service.mark_complete.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_dfn_generation_with_critique(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Test end-to-end DFN generation with critique and refinement"""
    # Create pipeline
    pipeline = RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=False,
    )
    
    # Generate DFN
    result = await pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_ifn_001",
        use_critique=True,
    )
    
    # Verify result
    assert "dfn_id" in result
    assert "session_id" in result
    assert "generated_text" in result
    
    # Verify all services were called
    mock_context_service.retrieve_context.assert_called_once()
    mock_llm_service.generate.assert_called_once()
    mock_llm_service.critique.assert_called_once()
    mock_llm_service.refine.assert_called_once()
    mock_dfn_service.create_dfn.assert_called_once()
    mock_session_service.mark_complete.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_agent_workflow(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Test end-to-end agent workflow"""
    # Create pipeline with agent
    pipeline = RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=True,
    )
    
    # Generate DFN using agent
    result = await pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_ifn_001",
        use_critique=True,
    )
    
    # Verify result
    assert "dfn_id" in result
    assert "session_id" in result
    assert "generated_text" in result
    assert "steps_completed" in result
    
    # Verify agent steps were completed
    steps = result["steps_completed"]
    assert "context_analysis" in steps
    assert "pattern_matching" in steps
    assert "draft_generation" in steps
    
    # Verify services were called
    mock_context_service.retrieve_context.assert_called_once()
    mock_dfn_service.create_dfn.assert_called_once()
    mock_session_service.mark_complete.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_error_handling(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Test end-to-end error handling"""
    # Mock missing IFN
    mock_context_service.retrieve_context = AsyncMock(return_value={
        "speaker_profile": {},
        "ifn_draft": None,
        "correction_patterns": [],
        "historical_drafts": [],
        "similar_patterns": [],
    })
    
    # Create pipeline
    pipeline = RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=False,
    )
    
    # Should raise error
    with pytest.raises(ValueError, match="not found"):
        await pipeline.generate_dfn(
            speaker_id="550e8400-e29b-41d4-a716-446655440000",
            ifn_draft_id="nonexistent",
            use_critique=False,
        )
    
    # Verify session was marked as failed
    mock_session_service.mark_failed.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_context_usage(
    mock_db,
    mock_context_service,
    mock_llm_service,
    mock_dfn_service,
    mock_session_service,
):
    """Test that context is properly used in DFN generation"""
    # Create pipeline
    pipeline = RAGPipeline(
        mock_db,
        mock_context_service,
        mock_llm_service,
        mock_dfn_service,
        mock_session_service,
        use_agent=False,
    )
    
    # Generate DFN
    result = await pipeline.generate_dfn(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_ifn_001",
        use_critique=False,
    )
    
    # Verify context was used
    assert result["context_used"]["correction_patterns"] == 5
    assert result["context_used"]["historical_drafts"] == 2
    assert result["context_used"]["speaker_profile"] is True

