"""
Tests for RAG agent
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.rag_agent import RAGAgent
from app.services.context_service import ContextService
from app.services.llm_service import LLMService


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
    service.critique = AsyncMock(return_value="The correction is good. No issues found.")
    service.refine = AsyncMock(return_value="Patient has diabetes and is stable.")
    return service


@pytest.fixture
def rag_agent(mock_context_service, mock_llm_service):
    """Create RAG agent with mocked dependencies"""
    return RAGAgent(mock_context_service, mock_llm_service)


@pytest.mark.asyncio
async def test_agent_workflow_without_critique(rag_agent, mock_context_service, mock_llm_service):
    """Test agent workflow without critique"""
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=False,
    )
    
    # Verify result
    assert result["generated_text"] == "Patient has diabetes."
    assert result["word_count"] == 3
    assert "context_analysis" in result["steps_completed"]
    assert "pattern_matching" in result["steps_completed"]
    assert "draft_generation" in result["steps_completed"]
    assert "self_critique" not in result["steps_completed"]
    assert "refinement" not in result["steps_completed"]
    
    # Verify context was retrieved
    mock_context_service.retrieve_context.assert_called_once()
    
    # Verify LLM was called
    mock_llm_service.generate.assert_called_once()
    
    # Verify critique was NOT called
    mock_llm_service.critique.assert_not_called()
    mock_llm_service.refine.assert_not_called()


@pytest.mark.asyncio
async def test_agent_workflow_with_critique_no_refinement(rag_agent, mock_llm_service):
    """Test agent workflow with critique but no refinement needed"""
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=True,
    )
    
    # Verify result
    assert result["generated_text"] == "Patient has diabetes."
    assert "context_analysis" in result["steps_completed"]
    assert "pattern_matching" in result["steps_completed"]
    assert "draft_generation" in result["steps_completed"]
    assert "self_critique" in result["steps_completed"]
    assert "refinement" not in result["steps_completed"]  # No refinement needed
    
    # Verify LLM methods were called
    mock_llm_service.generate.assert_called_once()
    mock_llm_service.critique.assert_called_once()
    mock_llm_service.refine.assert_not_called()  # No refinement needed


@pytest.mark.asyncio
async def test_agent_workflow_with_critique_and_refinement(rag_agent, mock_llm_service):
    """Test agent workflow with critique and refinement"""
    # Mock critique that triggers refinement
    mock_llm_service.critique = AsyncMock(
        return_value="The text needs improvement. It should include more details."
    )
    
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=True,
    )
    
    # Verify result
    assert result["generated_text"] == "Patient has diabetes and is stable."
    assert result["refined_text"] == "Patient has diabetes and is stable."
    assert "context_analysis" in result["steps_completed"]
    assert "pattern_matching" in result["steps_completed"]
    assert "draft_generation" in result["steps_completed"]
    assert "self_critique" in result["steps_completed"]
    assert "refinement" in result["steps_completed"]
    
    # Verify LLM methods were called
    mock_llm_service.generate.assert_called_once()
    mock_llm_service.critique.assert_called_once()
    mock_llm_service.refine.assert_called_once()


@pytest.mark.asyncio
async def test_agent_workflow_missing_ifn(rag_agent, mock_context_service):
    """Test agent workflow with missing IFN"""
    # Mock missing IFN
    mock_context_service.retrieve_context = AsyncMock(return_value={
        "speaker_profile": {},
        "ifn_draft": None,
        "correction_patterns": [],
        "historical_drafts": [],
        "similar_patterns": [],
    })
    
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="nonexistent",
        use_critique=False,
    )
    
    # Should have error
    assert result["error"] is not None
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_agent_state_tracking(rag_agent):
    """Test that agent tracks state correctly"""
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=False,
    )
    
    # Verify state tracking
    assert result["speaker_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert result["ifn_draft_id"] == "draft_test_123"
    assert result["use_critique"] is False
    assert len(result["steps_completed"]) >= 3
    assert result["context"] is not None
    assert result["formatted_context"] is not None
    assert result["system_prompt"] != ""
    assert result["user_prompt"] != ""


@pytest.mark.asyncio
async def test_agent_messages(rag_agent):
    """Test that agent generates messages"""
    result = await rag_agent.run(
        speaker_id="550e8400-e29b-41d4-a716-446655440000",
        ifn_draft_id="draft_test_123",
        use_critique=False,
    )
    
    # Verify messages
    assert len(result["messages"]) >= 3
    assert any("Context retrieved" in str(msg.content) for msg in result["messages"])
    assert any("patterns" in str(msg.content) for msg in result["messages"])
    assert any("Generated DFN" in str(msg.content) for msg in result["messages"])

