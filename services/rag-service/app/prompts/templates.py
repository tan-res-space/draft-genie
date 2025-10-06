"""
Prompt templates for RAG-based DFN generation
"""
from typing import Dict, Any, List


# System prompt - defines the AI's role and behavior
SYSTEM_PROMPT = """You are an expert medical documentation assistant specializing in transforming informal medical notes (IFN) into formal, professional Draft Final Notes (DFN).

Your role is to:
1. Analyze the speaker's writing patterns and common errors
2. Apply corrections based on historical patterns
3. Maintain the medical accuracy and clinical intent
4. Follow professional medical documentation standards
5. Preserve all critical medical information
6. Use appropriate medical terminology
7. Ensure proper grammar, spelling, and punctuation

You have access to:
- The speaker's profile and specialty
- Historical correction patterns specific to this speaker
- Examples of previous drafts and corrections
- Medical terminology standards

Guidelines:
- Maintain the original clinical meaning
- Apply speaker-specific correction patterns
- Use formal medical language
- Ensure clarity and precision
- Follow standard medical documentation format
- Do not add information not present in the original
- Do not remove critical medical details
"""


# User prompt template - provides context and the task
USER_PROMPT_TEMPLATE = """Please transform the following Informal Note (IFN) into a professional Draft Final Note (DFN).

**Speaker Information:**
- Name: {speaker_name}
- Specialty: {speaker_specialty}
- Experience Level: {speaker_experience}

**Common Correction Patterns for this Speaker:**
{correction_patterns}

**Historical Examples:**
{historical_examples}

**Informal Note (IFN) to Transform:**
```
{ifn_text}
```

**Instructions:**
1. Apply the speaker's common correction patterns
2. Fix spelling, grammar, and punctuation errors
3. Use formal medical terminology
4. Maintain all clinical information
5. Follow standard medical documentation format
6. Ensure professional tone and clarity

**Generate the Draft Final Note (DFN):**
"""


# Critique prompt template - for self-critique step
CRITIQUE_PROMPT_TEMPLATE = """Review the following Draft Final Note (DFN) and provide a critique.

**Original Informal Note (IFN):**
```
{ifn_text}
```

**Generated Draft Final Note (DFN):**
```
{dfn_text}
```

**Evaluation Criteria:**
1. **Accuracy**: Does the DFN preserve all clinical information from the IFN?
2. **Corrections**: Are spelling, grammar, and terminology corrections appropriate?
3. **Completeness**: Is any critical information missing?
4. **Clarity**: Is the DFN clear and professionally written?
5. **Format**: Does it follow standard medical documentation format?

**Provide your critique:**
- What was done well?
- What could be improved?
- Are there any errors or omissions?
- Should any corrections be revised?

**Critique:**
"""


def get_system_prompt() -> str:
    """Get the system prompt"""
    return SYSTEM_PROMPT


def get_user_prompt(
    speaker_name: str,
    speaker_specialty: str,
    speaker_experience: str,
    correction_patterns: List[Dict[str, Any]],
    historical_examples: List[Dict[str, str]],
    ifn_text: str,
) -> str:
    """
    Generate user prompt with context
    
    Args:
        speaker_name: Speaker's name
        speaker_specialty: Speaker's medical specialty
        speaker_experience: Speaker's experience level
        correction_patterns: List of correction patterns
        historical_examples: List of historical draft examples
        ifn_text: The informal note text to transform
        
    Returns:
        Formatted user prompt
    """
    # Format correction patterns
    if correction_patterns:
        patterns_text = "\n".join([
            f"- {p['original']} → {p['corrected']} ({p['category']}, frequency: {p['frequency']})"
            for p in correction_patterns[:10]  # Top 10 patterns
        ])
    else:
        patterns_text = "No specific patterns available for this speaker yet."

    # Format historical examples
    if historical_examples:
        examples_text = "\n\n".join([
            f"Example {i+1}:\nOriginal: {ex['original']}\nCorrected: {ex['corrected']}"
            for i, ex in enumerate(historical_examples[:3])  # Top 3 examples
        ])
    else:
        examples_text = "No historical examples available yet."

    return USER_PROMPT_TEMPLATE.format(
        speaker_name=speaker_name,
        speaker_specialty=speaker_specialty,
        speaker_experience=speaker_experience,
        correction_patterns=patterns_text,
        historical_examples=examples_text,
        ifn_text=ifn_text,
    )


def get_critique_prompt(ifn_text: str, dfn_text: str) -> str:
    """
    Generate critique prompt
    
    Args:
        ifn_text: Original informal note
        dfn_text: Generated draft final note
        
    Returns:
        Formatted critique prompt
    """
    return CRITIQUE_PROMPT_TEMPLATE.format(
        ifn_text=ifn_text,
        dfn_text=dfn_text,
    )

