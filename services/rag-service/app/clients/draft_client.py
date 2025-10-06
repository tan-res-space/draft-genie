"""
Draft Service HTTP client
"""
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DraftClient:
    """Client for Draft Service API"""

    def __init__(self):
        self.base_url = settings.draft_service_url
        self.timeout = 30.0

    async def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        Get draft by ID
        
        Args:
            draft_id: Draft ID
            
        Returns:
            Draft data or None
        """
        try:
            logger.info(f"Fetching draft {draft_id} from Draft Service")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/drafts/{draft_id}"
                )
                
                if response.status_code == 200:
                    draft_data = response.json()
                    logger.info(f"Retrieved draft {draft_id}")
                    return draft_data
                elif response.status_code == 404:
                    logger.warning(f"Draft {draft_id} not found")
                    return None
                else:
                    logger.error(f"Error fetching draft: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching draft {draft_id}: {e}")
            return None

    async def get_speaker_drafts(
        self, speaker_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get drafts for a speaker
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of drafts
            
        Returns:
            List of drafts
        """
        try:
            logger.info(f"Fetching drafts for speaker {speaker_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/drafts/speaker/{speaker_id}",
                    params={"limit": limit},
                )
                
                if response.status_code == 200:
                    drafts = response.json()
                    logger.info(f"Retrieved {len(drafts)} drafts for speaker {speaker_id}")
                    return drafts
                else:
                    logger.error(f"Error fetching speaker drafts: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching speaker drafts: {e}")
            return []

    async def get_speaker_vectors(
        self, speaker_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get correction vectors for a speaker
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of vectors
            
        Returns:
            List of correction vectors
        """
        try:
            logger.info(f"Fetching vectors for speaker {speaker_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/vectors/speaker/{speaker_id}",
                    params={"limit": limit},
                )
                
                if response.status_code == 200:
                    vectors = response.json()
                    logger.info(f"Retrieved {len(vectors)} vectors for speaker {speaker_id}")
                    return vectors
                else:
                    logger.error(f"Error fetching speaker vectors: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching speaker vectors: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if Draft Service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Draft Service health check failed: {e}")
            return False


# Global draft client instance
draft_client = DraftClient()

