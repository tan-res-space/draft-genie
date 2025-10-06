"""
Comparison Service - Calculates text differences and metrics
"""
import difflib
from typing import Dict, Any, List, Tuple
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class ComparisonService:
    """Service for comparing IFN and DFN texts"""

    def __init__(self):
        pass

    def calculate_sentence_edit_rate(self, ifn_text: str, dfn_text: str) -> float:
        """
        Calculate Sentence Edit Rate (SER)
        
        SER = (insertions + deletions + substitutions) / total_sentences
        Lower is better (fewer changes needed)
        
        Args:
            ifn_text: Original informal note text
            dfn_text: Draft final note text
            
        Returns:
            SER score (0.0 to 1.0+)
        """
        try:
            # Split into sentences
            ifn_sentences = self._split_sentences(ifn_text)
            dfn_sentences = self._split_sentences(dfn_text)
            
            if not ifn_sentences:
                return 0.0
            
            # Use SequenceMatcher to find differences
            matcher = difflib.SequenceMatcher(None, ifn_sentences, dfn_sentences)
            opcodes = matcher.get_opcodes()
            
            # Count operations
            insertions = 0
            deletions = 0
            substitutions = 0
            
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'insert':
                    insertions += (j2 - j1)
                elif tag == 'delete':
                    deletions += (i2 - i1)
                elif tag == 'replace':
                    substitutions += max(i2 - i1, j2 - j1)
            
            # Calculate SER
            total_operations = insertions + deletions + substitutions
            ser = total_operations / len(ifn_sentences) if ifn_sentences else 0.0
            
            # Normalize to 0-1 range (cap at 1.0)
            ser = min(ser, 1.0)
            
            logger.debug(f"SER: {ser:.3f} (ins={insertions}, del={deletions}, sub={substitutions})")
            return ser
            
        except Exception as e:
            logger.error(f"Error calculating SER: {e}")
            return 0.0

    def calculate_word_error_rate(self, ifn_text: str, dfn_text: str) -> float:
        """
        Calculate Word Error Rate (WER)
        
        WER = (insertions + deletions + substitutions) / total_words
        Lower is better (fewer word corrections)
        
        Args:
            ifn_text: Original informal note text
            dfn_text: Draft final note text
            
        Returns:
            WER score (0.0 to 1.0+)
        """
        try:
            # Split into words
            ifn_words = self._split_words(ifn_text)
            dfn_words = self._split_words(dfn_text)
            
            if not ifn_words:
                return 0.0
            
            # Use SequenceMatcher to find differences
            matcher = difflib.SequenceMatcher(None, ifn_words, dfn_words)
            opcodes = matcher.get_opcodes()
            
            # Count operations
            insertions = 0
            deletions = 0
            substitutions = 0
            
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'insert':
                    insertions += (j2 - j1)
                elif tag == 'delete':
                    deletions += (i2 - i1)
                elif tag == 'replace':
                    substitutions += max(i2 - i1, j2 - j1)
            
            # Calculate WER
            total_operations = insertions + deletions + substitutions
            wer = total_operations / len(ifn_words) if ifn_words else 0.0
            
            # Normalize to 0-1 range (cap at 1.0)
            wer = min(wer, 1.0)
            
            logger.debug(f"WER: {wer:.3f} (ins={insertions}, del={deletions}, sub={substitutions})")
            return wer
            
        except Exception as e:
            logger.error(f"Error calculating WER: {e}")
            return 0.0

    def calculate_quality_score(
        self,
        ser: float,
        wer: float,
        semantic_similarity: float,
    ) -> float:
        """
        Calculate overall quality score
        
        Quality = (1 - SER) * 0.3 + (1 - WER) * 0.3 + semantic_similarity * 0.4
        Higher is better (0-1 scale)
        
        Args:
            ser: Sentence Edit Rate
            wer: Word Error Rate
            semantic_similarity: Semantic similarity score
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        try:
            # Invert SER and WER (lower is better -> higher is better)
            ser_score = 1.0 - min(ser, 1.0)
            wer_score = 1.0 - min(wer, 1.0)
            
            # Weighted average
            quality = (
                ser_score * 0.3 +
                wer_score * 0.3 +
                semantic_similarity * 0.4
            )
            
            # Ensure 0-1 range
            quality = max(0.0, min(1.0, quality))
            
            logger.debug(f"Quality Score: {quality:.3f}")
            return quality
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0

    def calculate_improvement_score(
        self,
        ifn_word_count: int,
        dfn_word_count: int,
        quality_score: float,
    ) -> float:
        """
        Calculate improvement score
        
        Considers both quality and text expansion
        Higher is better (0-1 scale)
        
        Args:
            ifn_word_count: Word count of IFN
            dfn_word_count: Word count of DFN
            quality_score: Overall quality score
            
        Returns:
            Improvement score (0.0 to 1.0)
        """
        try:
            # Calculate expansion ratio
            if ifn_word_count == 0:
                expansion_ratio = 0.0
            else:
                expansion_ratio = dfn_word_count / ifn_word_count
            
            # Ideal expansion is 1.5x to 2.5x
            # Score expansion ratio
            if expansion_ratio < 1.0:
                expansion_score = expansion_ratio  # Penalize contraction
            elif 1.5 <= expansion_ratio <= 2.5:
                expansion_score = 1.0  # Ideal range
            elif expansion_ratio < 1.5:
                expansion_score = 0.5 + (expansion_ratio - 1.0) / 1.0  # 1.0-1.5
            else:
                expansion_score = max(0.5, 1.0 - (expansion_ratio - 2.5) / 2.0)  # >2.5
            
            # Combine quality and expansion
            improvement = quality_score * 0.7 + expansion_score * 0.3
            
            # Ensure 0-1 range
            improvement = max(0.0, min(1.0, improvement))
            
            logger.debug(f"Improvement Score: {improvement:.3f} (expansion={expansion_ratio:.2f}x)")
            return improvement
            
        except Exception as e:
            logger.error(f"Error calculating improvement score: {e}")
            return 0.0

    def get_detailed_metrics(
        self,
        ifn_text: str,
        dfn_text: str,
        ser: float,
        wer: float,
    ) -> Dict[str, Any]:
        """
        Get detailed metrics for analysis
        
        Args:
            ifn_text: Original informal note text
            dfn_text: Draft final note text
            ser: Sentence Edit Rate
            wer: Word Error Rate
            
        Returns:
            Dictionary with detailed metrics
        """
        try:
            ifn_words = self._split_words(ifn_text)
            dfn_words = self._split_words(dfn_text)
            ifn_sentences = self._split_sentences(ifn_text)
            dfn_sentences = self._split_sentences(dfn_text)
            
            # Calculate similarity ratio
            similarity_ratio = difflib.SequenceMatcher(
                None, ifn_text.lower(), dfn_text.lower()
            ).ratio()
            
            return {
                "ifn_word_count": len(ifn_words),
                "dfn_word_count": len(dfn_words),
                "ifn_sentence_count": len(ifn_sentences),
                "dfn_sentence_count": len(dfn_sentences),
                "expansion_ratio": len(dfn_words) / len(ifn_words) if ifn_words else 0.0,
                "text_similarity_ratio": similarity_ratio,
                "ser": ser,
                "wer": wer,
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed metrics: {e}")
            return {}

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _split_words(self, text: str) -> List[str]:
        """Split text into words"""
        # Split on whitespace and punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        return words


# Factory function
def get_comparison_service() -> ComparisonService:
    """Get comparison service instance"""
    return ComparisonService()

