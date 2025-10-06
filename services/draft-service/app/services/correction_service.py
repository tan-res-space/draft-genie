"""
Correction service - Extract and analyze correction patterns
"""
import difflib
from typing import List, Dict, Any, Tuple
from collections import Counter
import re
import uuid

from app.models.correction_vector import (
    CorrectionPattern,
    CorrectionVectorModel,
    CorrectionVectorCreate,
)
from app.models.draft import DraftModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class CorrectionService:
    """Service for extracting and analyzing correction patterns"""

    # Correction categories
    SPELLING_PATTERNS = [
        r"[a-z]+is$",  # diabetis -> diabetes
        r"[a-z]+tion$",  # perscription -> prescription
    ]

    GRAMMAR_PATTERNS = [
        r"\b(was|have)\s+(went|gone)\b",
        r"\bmore\s+better\b",
        r"\bmost\s+best\b",
    ]

    def extract_corrections(self, draft: DraftModel) -> List[CorrectionPattern]:
        """
        Extract correction patterns from a draft
        
        Args:
            draft: Draft model with original and corrected text
            
        Returns:
            List of correction patterns
        """
        logger.info(f"Extracting corrections from draft {draft.draft_id}")

        original_words = draft.original_text.split()
        corrected_words = draft.corrected_text.split()

        # Use difflib to find differences
        matcher = difflib.SequenceMatcher(None, original_words, corrected_words)
        
        corrections = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                # Words were replaced (correction made)
                original = " ".join(original_words[i1:i2])
                corrected = " ".join(corrected_words[j1:j2])
                
                # Get context (surrounding words)
                context_start = max(0, i1 - 2)
                context_end = min(len(original_words), i2 + 2)
                context = " ".join(original_words[context_start:context_end])
                
                # Categorize correction
                category = self._categorize_correction(original, corrected)
                
                corrections.append(
                    CorrectionPattern(
                        original=original,
                        corrected=corrected,
                        category=category,
                        frequency=1,
                        context=context,
                    )
                )

        logger.info(f"Extracted {len(corrections)} corrections from draft {draft.draft_id}")
        return corrections

    def _categorize_correction(self, original: str, corrected: str) -> str:
        """
        Categorize a correction
        
        Args:
            original: Original text
            corrected: Corrected text
            
        Returns:
            Category string
        """
        # Check if it's a spelling correction (single word)
        if len(original.split()) == 1 and len(corrected.split()) == 1:
            # Check Levenshtein distance
            distance = self._levenshtein_distance(original.lower(), corrected.lower())
            if distance <= 2:
                return "spelling"

        # Check for grammar patterns
        for pattern in self.GRAMMAR_PATTERNS:
            if re.search(pattern, original, re.IGNORECASE):
                return "grammar"

        # Check for punctuation
        if original.replace(" ", "") == corrected.replace(" ", ""):
            return "punctuation"

        # Check for capitalization
        if original.lower() == corrected.lower():
            return "capitalization"

        # Check for word order
        if sorted(original.split()) == sorted(corrected.split()):
            return "word_order"

        # Default to general
        return "general"

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def aggregate_patterns(
        self, patterns: List[CorrectionPattern]
    ) -> Tuple[List[CorrectionPattern], Dict[str, int]]:
        """
        Aggregate correction patterns by frequency
        
        Args:
            patterns: List of correction patterns
            
        Returns:
            Tuple of (aggregated patterns, category counts)
        """
        # Group by (original, corrected) pair
        pattern_map: Dict[Tuple[str, str], CorrectionPattern] = {}
        
        for pattern in patterns:
            key = (pattern.original.lower(), pattern.corrected.lower())
            if key in pattern_map:
                pattern_map[key].frequency += 1
            else:
                pattern_map[key] = pattern

        # Count by category
        category_counts = Counter(p.category for p in pattern_map.values())

        aggregated = list(pattern_map.values())
        logger.info(f"Aggregated {len(patterns)} patterns into {len(aggregated)} unique patterns")

        return aggregated, dict(category_counts)

    def create_correction_vector(
        self, draft: DraftModel, patterns: List[CorrectionPattern]
    ) -> CorrectionVectorCreate:
        """
        Create a correction vector from patterns
        
        Args:
            draft: Draft model
            patterns: List of correction patterns
            
        Returns:
            CorrectionVectorCreate model
        """
        # Aggregate patterns
        aggregated_patterns, category_counts = self.aggregate_patterns(patterns)

        # Create vector
        vector_id = f"vec_{uuid.uuid4().hex[:12]}"

        vector_create = CorrectionVectorCreate(
            vector_id=vector_id,
            speaker_id=draft.speaker_id,
            draft_id=draft.draft_id,
            patterns=aggregated_patterns,
            total_corrections=len(patterns),
            unique_patterns=len(aggregated_patterns),
            category_counts=category_counts,
            metadata={
                "draft_type": draft.draft_type,
                "word_count": draft.word_count,
            },
        )

        logger.info(
            f"Created correction vector {vector_id} with {len(aggregated_patterns)} patterns"
        )
        return vector_create

    def analyze_correction_trends(
        self, patterns: List[CorrectionPattern]
    ) -> Dict[str, Any]:
        """
        Analyze trends in correction patterns
        
        Args:
            patterns: List of correction patterns
            
        Returns:
            Dictionary with trend analysis
        """
        if not patterns:
            return {
                "total_corrections": 0,
                "unique_patterns": 0,
                "most_common": [],
                "category_distribution": {},
            }

        # Aggregate patterns
        aggregated, category_counts = self.aggregate_patterns(patterns)

        # Find most common patterns
        most_common = sorted(aggregated, key=lambda p: p.frequency, reverse=True)[:10]

        return {
            "total_corrections": len(patterns),
            "unique_patterns": len(aggregated),
            "most_common": [
                {
                    "original": p.original,
                    "corrected": p.corrected,
                    "frequency": p.frequency,
                    "category": p.category,
                }
                for p in most_common
            ],
            "category_distribution": category_counts,
        }

