"""
Draft Service HTTP Client
"""
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DraftClient:
    """HTTP client for Draft Service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.draft_service_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_draft_by_id(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """
        Get draft by ID from Draft Service
        
        Args:
            draft_id: Draft ID
            
        Returns:
            Draft data or None
        """
        try:
            logger.debug(f"Fetching draft {draft_id} from Draft Service")
            response = await self.client.get(f"/api/v1/drafts/{draft_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Draft {draft_id} not found")
                return None
            else:
                logger.error(f"Error fetching draft: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching draft from Draft Service: {e}")
            return None

    async def health_check(self) -> bool:
        """Check Draft Service health"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Draft Service health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
_draft_client: Optional[DraftClient] = None


def get_draft_client() -> DraftClient:
    """Get draft client instance (singleton)"""
    global _draft_client
    if _draft_client is None:
        _draft_client = DraftClient()
    return _draft_client

