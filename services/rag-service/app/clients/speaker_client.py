"""
Speaker Service HTTP client
"""
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpeakerClient:
    """Client for Speaker Service API"""

    def __init__(self):
        self.base_url = settings.speaker_service_url
        self.timeout = 30.0

    async def get_speaker(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get speaker by ID
        
        Args:
            speaker_id: Speaker UUID
            
        Returns:
            Speaker data or None
        """
        try:
            logger.info(f"Fetching speaker {speaker_id} from Speaker Service")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/speakers/{speaker_id}"
                )
                
                if response.status_code == 200:
                    speaker_data = response.json()
                    logger.info(f"Retrieved speaker {speaker_id}")
                    return speaker_data
                elif response.status_code == 404:
                    logger.warning(f"Speaker {speaker_id} not found")
                    return None
                else:
                    logger.error(f"Error fetching speaker: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching speaker {speaker_id}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Speaker Service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Speaker Service health check failed: {e}")
            return False


# Global speaker client instance
speaker_client = SpeakerClient()

