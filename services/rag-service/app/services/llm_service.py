"""
LLM Service - Gemini integration with LangChain
"""
from typing import Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for LLM operations using Gemini"""

    def __init__(self):
        """Initialize LLM service"""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.gemini_temperature,
            max_tokens=settings.gemini_max_tokens,
            top_p=settings.gemini_top_p,
            top_k=settings.gemini_top_k,
        )
        logger.info(f"Initialized LLM service with model {settings.gemini_model}")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using Gemini
        
        Args:
            system_prompt: System prompt defining behavior
            user_prompt: User prompt with task
            temperature: Optional temperature override
            
        Returns:
            Generated text
        """
        try:
            logger.info("Generating text with Gemini")
            
            # Override temperature if provided
            if temperature is not None:
                self.llm.temperature = temperature

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Generate
            response = await self.llm.ainvoke(messages)
            generated_text = response.content

            logger.info(f"Generated {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    async def generate_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate text with context tracking
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            context: Context dictionary
            temperature: Optional temperature
            
        Returns:
            Dictionary with generated text and metadata
        """
        try:
            generated_text = await self.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )

            return {
                "generated_text": generated_text,
                "word_count": len(generated_text.split()),
                "model": settings.gemini_model,
                "temperature": temperature or settings.gemini_temperature,
                "context_used": context,
            }

        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            raise

    async def critique(
        self,
        critique_prompt: str,
    ) -> str:
        """
        Generate critique of generated text
        
        Args:
            critique_prompt: Prompt for critique
            
        Returns:
            Critique text
        """
        try:
            logger.info("Generating critique")

            # Use lower temperature for critique (more focused)
            messages = [HumanMessage(content=critique_prompt)]
            
            # Temporarily set lower temperature
            original_temp = self.llm.temperature
            self.llm.temperature = 0.3

            response = await self.llm.ainvoke(messages)
            critique_text = response.content

            # Restore temperature
            self.llm.temperature = original_temp

            logger.info("Generated critique")
            return critique_text

        except Exception as e:
            logger.error(f"Error generating critique: {e}")
            raise

    async def refine(
        self,
        system_prompt: str,
        original_prompt: str,
        generated_text: str,
        critique: str,
    ) -> str:
        """
        Refine generated text based on critique
        
        Args:
            system_prompt: System prompt
            original_prompt: Original user prompt
            generated_text: Previously generated text
            critique: Critique of generated text
            
        Returns:
            Refined text
        """
        try:
            logger.info("Refining generated text")

            refinement_prompt = f"""Based on the following critique, please refine the Draft Final Note.

**Original Task:**
{original_prompt}

**Previous Draft:**
{generated_text}

**Critique:**
{critique}

**Generate an improved Draft Final Note:**
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=refinement_prompt),
            ]

            response = await self.llm.ainvoke(messages)
            refined_text = response.content

            logger.info("Generated refined text")
            return refined_text

        except Exception as e:
            logger.error(f"Error refining text: {e}")
            raise


def get_llm_service() -> LLMService:
    """Factory function to create LLMService"""
    return LLMService()

