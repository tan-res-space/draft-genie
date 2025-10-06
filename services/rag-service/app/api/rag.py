"""
RAG API endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.services.context_service import ContextService
from app.services.llm_service import LLMService, get_llm_service
from app.services.dfn_service import DFNService, get_dfn_service
from app.services.rag_session_service import RAGSessionService, get_rag_session_service
from app.services.rag_pipeline import RAGPipeline, get_rag_pipeline
from app.events.publisher import event_publisher
from app.db.mongodb import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


async def get_rag_pipeline_dependency() -> RAGPipeline:
    """Dependency to get RAGPipeline instance"""
    db = await get_database()
    context_service = ContextService()
    llm_service = get_llm_service()
    dfn_service = get_dfn_service(db)
    session_service = get_rag_session_service(db)
    return get_rag_pipeline(db, context_service, llm_service, dfn_service, session_service)


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_dfn(
    speaker_id: str = Query(..., description="Speaker UUID"),
    ifn_draft_id: str = Query(..., description="IFN draft ID"),
    use_critique: bool = Query(True, description="Use self-critique and refinement"),
    pipeline: RAGPipeline = Depends(get_rag_pipeline_dependency),
) -> Dict[str, Any]:
    """
    Generate DFN from IFN using RAG pipeline
    
    This endpoint:
    1. Retrieves context (speaker profile, correction patterns, historical drafts)
    2. Generates prompts with context
    3. Uses LLM to generate DFN
    4. Optionally critiques and refines the output
    5. Stores DFN in MongoDB
    6. Publishes DFNGeneratedEvent
    """
    try:
        logger.info(f"POST /api/v1/rag/generate - speaker_id={speaker_id}, ifn_draft_id={ifn_draft_id}")
        
        # Run RAG pipeline
        result = await pipeline.generate_dfn(
            speaker_id=speaker_id,
            ifn_draft_id=ifn_draft_id,
            use_critique=use_critique,
        )
        
        # Publish event
        await event_publisher.publish_dfn_generated_event(
            dfn_id=result["dfn_id"],
            speaker_id=speaker_id,
            session_id=result["session_id"],
            ifn_draft_id=ifn_draft_id,
            word_count=result["word_count"],
            confidence_score=result["confidence_score"],
        )
        
        return {
            "message": "Successfully generated DFN",
            "dfn_id": result["dfn_id"],
            "session_id": result["session_id"],
            "speaker_id": speaker_id,
            "ifn_draft_id": ifn_draft_id,
            "word_count": result["word_count"],
            "confidence_score": result["confidence_score"],
            "generated_text": result["generated_text"],
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating DFN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DFN: {str(e)}",
        )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    pipeline: RAGPipeline = Depends(get_rag_pipeline_dependency),
) -> Dict[str, Any]:
    """
    Get RAG session details
    
    Returns session information including:
    - Context retrieved
    - Prompts used
    - Agent workflow steps
    - DFN generated
    - Status
    """
    try:
        logger.info(f"GET /api/v1/rag/sessions/{session_id}")
        
        session = await pipeline.session_service.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )
        
        return {
            "session_id": session.session_id,
            "speaker_id": session.speaker_id,
            "ifn_draft_id": session.ifn_draft_id,
            "context_retrieved": session.context_retrieved,
            "prompts_used": session.prompts_used,
            "agent_steps": session.agent_steps,
            "dfn_generated": session.dfn_generated,
            "dfn_id": session.dfn_id,
            "status": session.status,
            "error_message": session.error_message,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}",
        )


@router.get("/sessions/speaker/{speaker_id}")
async def get_speaker_sessions(
    speaker_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    pipeline: RAGPipeline = Depends(get_rag_pipeline_dependency),
) -> Dict[str, Any]:
    """
    Get all RAG sessions for a speaker
    """
    try:
        logger.info(f"GET /api/v1/rag/sessions/speaker/{speaker_id}")
        
        sessions = await pipeline.session_service.get_sessions_by_speaker(
            speaker_id, skip, limit
        )
        
        return {
            "speaker_id": speaker_id,
            "count": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "ifn_draft_id": s.ifn_draft_id,
                    "dfn_generated": s.dfn_generated,
                    "dfn_id": s.dfn_id,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                }
                for s in sessions
            ],
        }
        
    except Exception as e:
        logger.error(f"Error getting speaker sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get speaker sessions: {str(e)}",
        )

