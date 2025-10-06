"""
RAG Agent - LangGraph-based AI agent for DFN generation
"""
from typing import Dict, Any, TypedDict, Annotated, Sequence
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.services.context_service import ContextService
from app.services.llm_service import LLMService
from app.prompts.templates import get_system_prompt, get_user_prompt, get_critique_prompt
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for RAG agent workflow"""
    
    # Input
    speaker_id: str
    ifn_draft_id: str
    use_critique: bool
    
    # Context
    context: Dict[str, Any]
    formatted_context: Dict[str, Any]
    
    # Prompts
    system_prompt: str
    user_prompt: str
    
    # Generation
    generated_text: str
    word_count: int
    
    # Critique
    critique: str
    needs_refinement: bool
    
    # Refinement
    refined_text: str
    
    # Messages
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Workflow
    current_step: str
    steps_completed: list[str]
    error: str | None


class RAGAgent:
    """LangGraph-based RAG agent for DFN generation"""

    def __init__(
        self,
        context_service: ContextService,
        llm_service: LLMService,
    ):
        self.context_service = context_service
        self.llm_service = llm_service
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("context_analysis", self._context_analysis)
        workflow.add_node("pattern_matching", self._pattern_matching)
        workflow.add_node("draft_generation", self._draft_generation)
        workflow.add_node("self_critique", self._self_critique)
        workflow.add_node("refinement", self._refinement)
        
        # Set entry point
        workflow.set_entry_point("context_analysis")
        
        # Add edges
        workflow.add_edge("context_analysis", "pattern_matching")
        workflow.add_edge("pattern_matching", "draft_generation")
        
        # Conditional edge after draft generation
        workflow.add_conditional_edges(
            "draft_generation",
            self._should_critique,
            {
                "critique": "self_critique",
                "end": END,
            },
        )
        
        # Conditional edge after critique
        workflow.add_conditional_edges(
            "self_critique",
            self._should_refine,
            {
                "refine": "refinement",
                "end": END,
            },
        )
        
        # Edge from refinement to end
        workflow.add_edge("refinement", END)
        
        return workflow.compile()

    async def _context_analysis(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 1: Analyze context
        
        Retrieves and analyzes all context needed for DFN generation
        """
        logger.info(f"[Context Analysis] Starting for speaker {state['speaker_id']}")
        
        try:
            # Retrieve context
            context = await self.context_service.retrieve_context(
                state["speaker_id"],
                state["ifn_draft_id"],
            )
            
            # Format context for prompts
            formatted_context = self.context_service.format_context_for_prompt(context)
            
            # Validate context
            if not context["ifn_draft"]:
                raise ValueError(f"IFN draft {state['ifn_draft_id']} not found")
            
            logger.info(
                f"[Context Analysis] Retrieved context: "
                f"speaker={context['speaker_profile'] is not None}, "
                f"patterns={len(context['correction_patterns'])}, "
                f"history={len(context['historical_drafts'])}"
            )
            
            return {
                "context": context,
                "formatted_context": formatted_context,
                "current_step": "context_analysis",
                "steps_completed": state.get("steps_completed", []) + ["context_analysis"],
                "messages": [HumanMessage(content="Context retrieved and analyzed")],
            }
            
        except Exception as e:
            logger.error(f"[Context Analysis] Error: {e}")
            return {
                "error": str(e),
                "current_step": "context_analysis",
            }

    async def _pattern_matching(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 2: Pattern matching

        Analyzes correction patterns and historical examples
        """
        # Skip if there was an error
        if state.get("error"):
            return {"current_step": "pattern_matching"}

        logger.info("[Pattern Matching] Starting pattern analysis")

        try:
            context = state["context"]
            
            # Analyze correction patterns
            patterns = context["correction_patterns"]
            pattern_categories = {}
            for pattern in patterns:
                category = pattern.get("category", "unknown")
                pattern_categories[category] = pattern_categories.get(category, 0) + 1
            
            # Analyze historical drafts
            historical_count = len(context["historical_drafts"])
            
            logger.info(
                f"[Pattern Matching] Found {len(patterns)} patterns "
                f"in {len(pattern_categories)} categories, "
                f"{historical_count} historical examples"
            )
            
            return {
                "current_step": "pattern_matching",
                "steps_completed": state["steps_completed"] + ["pattern_matching"],
                "messages": [
                    AIMessage(
                        content=f"Analyzed {len(patterns)} correction patterns "
                        f"and {historical_count} historical examples"
                    )
                ],
            }
            
        except Exception as e:
            logger.error(f"[Pattern Matching] Error: {e}")
            return {
                "error": str(e),
                "current_step": "pattern_matching",
            }

    async def _draft_generation(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 3: Draft generation

        Generates initial DFN using LLM with context
        """
        # Skip if there was an error
        if state.get("error"):
            return {"current_step": "draft_generation"}

        logger.info("[Draft Generation] Starting DFN generation")

        try:
            # Generate prompts
            system_prompt = get_system_prompt()
            user_prompt = get_user_prompt(**state["formatted_context"])
            
            # Generate DFN
            generated_text = await self.llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            
            word_count = len(generated_text.split())
            
            logger.info(f"[Draft Generation] Generated DFN with {word_count} words")
            
            return {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "generated_text": generated_text,
                "word_count": word_count,
                "current_step": "draft_generation",
                "steps_completed": state["steps_completed"] + ["draft_generation"],
                "messages": [
                    AIMessage(content=f"Generated DFN with {word_count} words")
                ],
            }
            
        except Exception as e:
            logger.error(f"[Draft Generation] Error: {e}")
            return {
                "error": str(e),
                "current_step": "draft_generation",
            }

    async def _self_critique(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 4: Self-critique

        Evaluates generated DFN and identifies improvements
        """
        # Skip if there was an error
        if state.get("error"):
            return {"current_step": "self_critique", "needs_refinement": False}

        logger.info("[Self Critique] Starting self-evaluation")

        try:
            # Generate critique prompt
            critique_prompt = get_critique_prompt(
                ifn_text=state["formatted_context"]["ifn_text"],
                dfn_text=state["generated_text"],
            )
            
            # Get critique
            critique = await self.llm_service.critique(critique_prompt)
            
            # Determine if refinement is needed
            needs_refinement = self._analyze_critique(critique)
            
            logger.info(
                f"[Self Critique] Critique complete, "
                f"needs_refinement={needs_refinement}"
            )
            
            return {
                "critique": critique,
                "needs_refinement": needs_refinement,
                "current_step": "self_critique",
                "steps_completed": state["steps_completed"] + ["self_critique"],
                "messages": [
                    AIMessage(
                        content=f"Self-critique complete. "
                        f"Refinement {'needed' if needs_refinement else 'not needed'}"
                    )
                ],
            }
            
        except Exception as e:
            logger.error(f"[Self Critique] Error: {e}")
            return {
                "error": str(e),
                "current_step": "self_critique",
                "needs_refinement": False,
            }

    async def _refinement(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 5: Refinement

        Refines DFN based on critique
        """
        # Skip if there was an error
        if state.get("error"):
            return {"current_step": "refinement"}

        logger.info("[Refinement] Starting refinement")

        try:
            # Refine text
            refined_text = await self.llm_service.refine(
                system_prompt=state["system_prompt"],
                original_prompt=state["user_prompt"],
                generated_text=state["generated_text"],
                critique=state["critique"],
            )
            
            word_count = len(refined_text.split())
            
            logger.info(f"[Refinement] Refined DFN with {word_count} words")
            
            return {
                "refined_text": refined_text,
                "generated_text": refined_text,  # Update generated_text
                "word_count": word_count,
                "current_step": "refinement",
                "steps_completed": state["steps_completed"] + ["refinement"],
                "messages": [
                    AIMessage(content=f"Refined DFN with {word_count} words")
                ],
            }
            
        except Exception as e:
            logger.error(f"[Refinement] Error: {e}")
            return {
                "error": str(e),
                "current_step": "refinement",
            }

    def _should_critique(self, state: AgentState) -> str:
        """Decide whether to perform critique"""
        if state.get("error"):
            return "end"
        if state.get("use_critique", True):
            return "critique"
        return "end"

    def _should_refine(self, state: AgentState) -> str:
        """Decide whether to perform refinement"""
        if state.get("error"):
            return "end"
        if state.get("needs_refinement", False):
            return "refine"
        return "end"

    def _analyze_critique(self, critique: str) -> bool:
        """
        Analyze critique to determine if refinement is needed
        
        Simple heuristic: if critique mentions issues, refinement is needed
        """
        critique_lower = critique.lower()
        
        # Keywords indicating issues
        issue_keywords = [
            "error", "mistake", "incorrect", "missing", "unclear",
            "improve", "should", "could", "needs", "lacks",
        ]
        
        # Check for issue keywords
        for keyword in issue_keywords:
            if keyword in critique_lower:
                return True
        
        return False

    async def run(
        self,
        speaker_id: str,
        ifn_draft_id: str,
        use_critique: bool = True,
    ) -> Dict[str, Any]:
        """
        Run RAG agent workflow
        
        Args:
            speaker_id: Speaker UUID
            ifn_draft_id: IFN draft ID
            use_critique: Whether to use self-critique
            
        Returns:
            Final state with generated DFN
        """
        logger.info(f"[RAG Agent] Starting workflow for speaker {speaker_id}")
        
        # Initialize state
        initial_state: AgentState = {
            "speaker_id": speaker_id,
            "ifn_draft_id": ifn_draft_id,
            "use_critique": use_critique,
            "context": {},
            "formatted_context": {},
            "system_prompt": "",
            "user_prompt": "",
            "generated_text": "",
            "word_count": 0,
            "critique": "",
            "needs_refinement": False,
            "refined_text": "",
            "messages": [],
            "current_step": "",
            "steps_completed": [],
            "error": None,
        }
        
        # Run workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(
            f"[RAG Agent] Workflow complete. "
            f"Steps: {final_state.get('steps_completed', [])}"
        )
        
        return final_state


def get_rag_agent(
    context_service: ContextService,
    llm_service: LLMService,
) -> RAGAgent:
    """Factory function to create RAGAgent"""
    return RAGAgent(context_service, llm_service)

