"""
RAG Pipeline - Orchestrates DFN generation
"""
import uuid
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.context_service import ContextService
from app.services.llm_service import LLMService
from app.services.dfn_service import DFNService
from app.services.rag_session_service import RAGSessionService
from app.agents.rag_agent import RAGAgent, get_rag_agent
from app.models.dfn import DFNCreate
from app.models.rag_session import RAGSessionCreate
from app.prompts.templates import get_system_prompt, get_user_prompt, get_critique_prompt
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """RAG Pipeline for DFN generation"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        context_service: ContextService,
        llm_service: LLMService,
        dfn_service: DFNService,
        session_service: RAGSessionService,
        use_agent: bool = True,
    ):
        self.db = db
        self.context_service = context_service
        self.llm_service = llm_service
        self.dfn_service = dfn_service
        self.session_service = session_service
        self.use_agent = use_agent

        # Create RAG agent
        if use_agent:
            self.agent = get_rag_agent(context_service, llm_service)
        else:
            self.agent = None

    async def generate_dfn_with_agent(
        self,
        speaker_id: str,
        ifn_draft_id: str,
        use_critique: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate DFN using LangGraph agent

        Args:
            speaker_id: Speaker UUID
            ifn_draft_id: IFN draft ID
            use_critique: Whether to use self-critique and refinement

        Returns:
            Dictionary with DFN and session information
        """
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        try:
            logger.info(f"Starting RAG agent for speaker {speaker_id}, draft {ifn_draft_id}")

            # Step 1: Create RAG session
            session = await self._create_session(session_id, speaker_id, ifn_draft_id)

            # Step 2: Run LangGraph agent
            await self.session_service.add_agent_step(
                session_id,
                {"step": "agent_workflow", "status": "started"},
            )

            agent_state = await self.agent.run(
                speaker_id=speaker_id,
                ifn_draft_id=ifn_draft_id,
                use_critique=use_critique,
            )

            # Check for errors
            if agent_state.get("error"):
                raise ValueError(agent_state["error"])

            # Log agent steps
            for step in agent_state.get("steps_completed", []):
                await self.session_service.add_agent_step(
                    session_id,
                    {"step": step, "status": "complete"},
                )

            await self.session_service.add_agent_step(
                session_id,
                {"step": "agent_workflow", "status": "complete"},
            )

            # Step 3: Create DFN
            await self.session_service.add_agent_step(
                session_id,
                {"step": "dfn_storage", "status": "started"},
            )

            dfn_id = f"dfn_{uuid.uuid4().hex[:12]}"
            dfn_create = DFNCreate(
                dfn_id=dfn_id,
                speaker_id=speaker_id,
                session_id=session_id,
                ifn_draft_id=ifn_draft_id,
                generated_text=agent_state["generated_text"],
                word_count=agent_state["word_count"],
                confidence_score=0.85,  # TODO: Calculate actual confidence
                context_used={
                    "correction_patterns": len(agent_state["context"].get("correction_patterns", [])),
                    "historical_drafts": len(agent_state["context"].get("historical_drafts", [])),
                    "speaker_profile": agent_state["context"].get("speaker_profile") is not None,
                },
                metadata={
                    "use_critique": use_critique,
                    "use_agent": True,
                    "steps_completed": agent_state.get("steps_completed", []),
                },
            )

            dfn = await self.dfn_service.create_dfn(dfn_create)

            await self.session_service.add_agent_step(
                session_id,
                {"step": "dfn_storage", "status": "complete", "dfn_id": dfn_id},
            )

            # Step 4: Mark session complete
            await self.session_service.mark_complete(session_id, dfn_id)

            logger.info(f"RAG agent complete - DFN {dfn_id} generated")

            return {
                "dfn_id": dfn_id,
                "session_id": session_id,
                "generated_text": agent_state["generated_text"],
                "word_count": agent_state["word_count"],
                "confidence_score": 0.85,
                "context_used": dfn_create.context_used,
                "steps_completed": agent_state.get("steps_completed", []),
            }

        except Exception as e:
            logger.error(f"Error in RAG agent: {e}")

            # Mark session as failed
            try:
                await self.session_service.mark_failed(session_id, str(e))
            except:
                pass

            raise

    async def generate_dfn(
        self,
        speaker_id: str,
        ifn_draft_id: str,
        use_critique: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate DFN from IFN using RAG pipeline

        Uses LangGraph agent if enabled, otherwise uses direct pipeline

        Args:
            speaker_id: Speaker UUID
            ifn_draft_id: IFN draft ID
            use_critique: Whether to use self-critique and refinement

        Returns:
            Dictionary with DFN and session information
        """
        # Use agent if enabled
        if self.use_agent and self.agent:
            return await self.generate_dfn_with_agent(
                speaker_id, ifn_draft_id, use_critique
            )

        # Otherwise use direct pipeline
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        try:
            logger.info(f"Starting RAG pipeline for speaker {speaker_id}, draft {ifn_draft_id}")

            # Step 1: Create RAG session
            session = await self._create_session(session_id, speaker_id, ifn_draft_id)

            # Step 2: Retrieve context
            await self.session_service.add_agent_step(
                session_id,
                {"step": "context_retrieval", "status": "started"},
            )
            
            context = await self.context_service.retrieve_context(
                speaker_id, ifn_draft_id
            )
            
            await self.session_service.add_agent_step(
                session_id,
                {
                    "step": "context_retrieval",
                    "status": "complete",
                    "context_summary": {
                        "speaker_found": context["speaker_profile"] is not None,
                        "ifn_found": context["ifn_draft"] is not None,
                        "correction_patterns_count": len(context["correction_patterns"]),
                        "historical_drafts_count": len(context["historical_drafts"]),
                    },
                },
            )

            # Validate context
            if not context["ifn_draft"]:
                raise ValueError(f"IFN draft {ifn_draft_id} not found")

            # Step 3: Generate prompts
            await self.session_service.add_agent_step(
                session_id,
                {"step": "prompt_generation", "status": "started"},
            )
            
            formatted_context = self.context_service.format_context_for_prompt(context)
            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(**formatted_context)
            
            await self.session_service.update_session(
                session_id,
                {"prompts_used": ["system_prompt_v1", "user_prompt_v1"]},
            )
            
            await self.session_service.add_agent_step(
                session_id,
                {"step": "prompt_generation", "status": "complete"},
            )

            # Step 4: Generate initial DFN
            await self.session_service.add_agent_step(
                session_id,
                {"step": "dfn_generation", "status": "started"},
            )
            
            generated_text = await self.llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            
            await self.session_service.add_agent_step(
                session_id,
                {
                    "step": "dfn_generation",
                    "status": "complete",
                    "word_count": len(generated_text.split()),
                },
            )

            # Step 5: Self-critique and refinement (optional)
            if use_critique:
                await self.session_service.add_agent_step(
                    session_id,
                    {"step": "self_critique", "status": "started"},
                )
                
                critique_prompt = get_critique_prompt(
                    ifn_text=formatted_context["ifn_text"],
                    dfn_text=generated_text,
                )
                
                critique = await self.llm_service.critique(critique_prompt)
                
                await self.session_service.add_agent_step(
                    session_id,
                    {"step": "self_critique", "status": "complete"},
                )

                # Step 6: Refinement
                await self.session_service.add_agent_step(
                    session_id,
                    {"step": "refinement", "status": "started"},
                )
                
                refined_text = await self.llm_service.refine(
                    system_prompt=system_prompt,
                    original_prompt=user_prompt,
                    generated_text=generated_text,
                    critique=critique,
                )
                
                # Use refined text
                generated_text = refined_text
                
                await self.session_service.add_agent_step(
                    session_id,
                    {
                        "step": "refinement",
                        "status": "complete",
                        "word_count": len(generated_text.split()),
                    },
                )

            # Step 7: Create DFN
            await self.session_service.add_agent_step(
                session_id,
                {"step": "dfn_storage", "status": "started"},
            )
            
            dfn_id = f"dfn_{uuid.uuid4().hex[:12]}"
            dfn_create = DFNCreate(
                dfn_id=dfn_id,
                speaker_id=speaker_id,
                session_id=session_id,
                ifn_draft_id=ifn_draft_id,
                generated_text=generated_text,
                word_count=len(generated_text.split()),
                confidence_score=0.85,  # TODO: Calculate actual confidence
                context_used={
                    "correction_patterns": len(context["correction_patterns"]),
                    "historical_drafts": len(context["historical_drafts"]),
                    "speaker_profile": context["speaker_profile"] is not None,
                },
                metadata={
                    "use_critique": use_critique,
                    "session_id": session_id,
                },
            )
            
            dfn = await self.dfn_service.create_dfn(dfn_create)
            
            await self.session_service.add_agent_step(
                session_id,
                {"step": "dfn_storage", "status": "complete", "dfn_id": dfn_id},
            )

            # Step 8: Mark session complete
            await self.session_service.mark_complete(session_id, dfn_id)

            logger.info(f"RAG pipeline complete - DFN {dfn_id} generated")

            return {
                "dfn_id": dfn_id,
                "session_id": session_id,
                "generated_text": generated_text,
                "word_count": len(generated_text.split()),
                "confidence_score": 0.85,
                "context_used": dfn_create.context_used,
            }

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            
            # Mark session as failed
            try:
                await self.session_service.mark_failed(session_id, str(e))
            except:
                pass
            
            raise

    async def _create_session(
        self, session_id: str, speaker_id: str, ifn_draft_id: str
    ) -> Any:
        """Create RAG session"""
        session_create = RAGSessionCreate(
            session_id=session_id,
            speaker_id=speaker_id,
            ifn_draft_id=ifn_draft_id,
            context_retrieved={},
            metadata={},
        )
        
        return await self.session_service.create_session(session_create)


def get_rag_pipeline(
    db: AsyncIOMotorDatabase,
    context_service: ContextService,
    llm_service: LLMService,
    dfn_service: DFNService,
    session_service: RAGSessionService,
) -> RAGPipeline:
    """Factory function to create RAGPipeline"""
    return RAGPipeline(
        db, context_service, llm_service, dfn_service, session_service
    )

