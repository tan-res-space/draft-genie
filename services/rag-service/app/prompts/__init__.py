"""
Prompts module - Prompt templates for RAG
"""
from app.prompts.templates import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    CRITIQUE_PROMPT_TEMPLATE,
    get_system_prompt,
    get_user_prompt,
    get_critique_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
    "CRITIQUE_PROMPT_TEMPLATE",
    "get_system_prompt",
    "get_user_prompt",
    "get_critique_prompt",
]

