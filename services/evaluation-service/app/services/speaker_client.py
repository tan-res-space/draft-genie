"""
Speaker Service HTTP Client
"""
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpeakerClient:
    """HTTP client for Speaker Service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.speaker_service_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_speaker_by_id(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get speaker by ID from Speaker Service
        
        Args:
            speaker_id: Speaker UUID
            
        Returns:
            Speaker data or None
        """
        try:
            logger.debug(f"Fetching speaker {speaker_id} from Speaker Service")
            response = await self.client.get(f"/api/v1/speakers/{speaker_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Speaker {speaker_id} not found")
                return None
            else:
                logger.error(f"Error fetching speaker: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching speaker from Speaker Service: {e}")
            return None

    async def health_check(self) -> bool:
        """Check Speaker Service health"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Speaker Service health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
_speaker_client: Optional[SpeakerClient] = None


def get_speaker_client() -> SpeakerClient:
    """Get speaker client instance (singleton)"""
    global _speaker_client
    if _speaker_client is None:
        _speaker_client = SpeakerClient()
    return _speaker_client

