"""
Context Service - Retrieve and aggregate context for RAG
"""
from typing import Dict, Any, List, Optional
from app.clients.speaker_client import speaker_client
from app.clients.draft_client import draft_client
from app.db.qdrant import qdrant
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextService:
    """Service for retrieving and aggregating RAG context"""

    def __init__(self):
        self.speaker_client = speaker_client
        self.draft_client = draft_client
        self.qdrant = qdrant

    async def retrieve_context(
        self,
        speaker_id: str,
        ifn_draft_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve all context needed for RAG
        
        Args:
            speaker_id: Speaker UUID
            ifn_draft_id: IFN draft ID
            
        Returns:
            Dictionary with all context
        """
        logger.info(f"Retrieving context for speaker {speaker_id}, draft {ifn_draft_id}")

        context = {
            "speaker_profile": None,
            "ifn_draft": None,
            "correction_patterns": [],
            "historical_drafts": [],
            "similar_patterns": [],
        }

        try:
            # Retrieve speaker profile
            context["speaker_profile"] = await self._get_speaker_profile(speaker_id)

            # Retrieve IFN draft
            context["ifn_draft"] = await self._get_ifn_draft(ifn_draft_id)

            # Retrieve correction patterns
            context["correction_patterns"] = await self._get_correction_patterns(speaker_id)

            # Retrieve historical drafts
            context["historical_drafts"] = await self._get_historical_drafts(speaker_id)

            # Retrieve similar patterns from Qdrant
            context["similar_patterns"] = await self._get_similar_patterns(speaker_id)

            logger.info("Successfully retrieved all context")
            return context

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise

    async def _get_speaker_profile(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """Get speaker profile from Speaker Service"""
        try:
            speaker = await self.speaker_client.get_speaker(speaker_id)
            if speaker:
                return {
                    "name": speaker.get("name", "Unknown"),
                    "specialty": speaker.get("specialty", "General"),
                    "experience_level": speaker.get("experience_level", "Intermediate"),
                    "bucket": speaker.get("bucket", "B"),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting speaker profile: {e}")
            return None

    async def _get_ifn_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get IFN draft from Draft Service"""
        try:
            draft = await self.draft_client.get_draft(draft_id)
            if draft:
                return {
                    "draft_id": draft.get("draft_id"),
                    "original_text": draft.get("original_text", ""),
                    "draft_type": draft.get("draft_type", "IFN"),
                    "word_count": draft.get("word_count", 0),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting IFN draft: {e}")
            return None

    async def _get_correction_patterns(
        self, speaker_id: str
    ) -> List[Dict[str, Any]]:
        """Get correction patterns from Draft Service"""
        try:
            vectors = await self.draft_client.get_speaker_vectors(speaker_id, limit=5)
            
            # Extract patterns from vectors
            all_patterns = []
            for vector in vectors:
                patterns = vector.get("patterns", [])
                all_patterns.extend(patterns)

            # Sort by frequency and return top patterns
            sorted_patterns = sorted(
                all_patterns,
                key=lambda p: p.get("frequency", 0),
                reverse=True,
            )

            return sorted_patterns[:20]  # Top 20 patterns

        except Exception as e:
            logger.error(f"Error getting correction patterns: {e}")
            return []

    async def _get_historical_drafts(
        self, speaker_id: str
    ) -> List[Dict[str, Any]]:
        """Get historical drafts from Draft Service"""
        try:
            drafts = await self.draft_client.get_speaker_drafts(speaker_id, limit=5)
            
            # Format drafts for context
            formatted_drafts = []
            for draft in drafts:
                formatted_drafts.append({
                    "original": draft.get("original_text", ""),
                    "corrected": draft.get("corrected_text", ""),
                    "draft_type": draft.get("draft_type", ""),
                })

            return formatted_drafts

        except Exception as e:
            logger.error(f"Error getting historical drafts: {e}")
            return []

    async def _get_similar_patterns(
        self, speaker_id: str
    ) -> List[Dict[str, Any]]:
        """Get similar patterns from Qdrant"""
        try:
            # Get speaker's vectors from Qdrant
            vectors = await self.qdrant.get_speaker_vectors(speaker_id, limit=10)
            
            # Format for context
            formatted_vectors = []
            for vector in vectors:
                payload = vector.get("payload", {})
                formatted_vectors.append({
                    "total_corrections": payload.get("total_corrections", 0),
                    "unique_patterns": payload.get("unique_patterns", 0),
                    "category_counts": payload.get("category_counts", {}),
                })

            return formatted_vectors

        except Exception as e:
            logger.error(f"Error getting similar patterns: {e}")
            return []

    def format_context_for_prompt(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format context for prompt generation
        
        Args:
            context: Raw context dictionary
            
        Returns:
            Formatted context for prompts
        """
        speaker_profile = context.get("speaker_profile", {}) or {}
        ifn_draft = context.get("ifn_draft", {}) or {}
        correction_patterns = context.get("correction_patterns", [])
        historical_drafts = context.get("historical_drafts", [])

        return {
            "speaker_name": speaker_profile.get("name", "Unknown"),
            "speaker_specialty": speaker_profile.get("specialty", "General"),
            "speaker_experience": speaker_profile.get("experience_level", "Intermediate"),
            "ifn_text": ifn_draft.get("original_text", ""),
            "correction_patterns": correction_patterns,
            "historical_examples": historical_drafts,
        }

