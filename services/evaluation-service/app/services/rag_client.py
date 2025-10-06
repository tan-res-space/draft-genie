"""
RAG Service HTTP Client
"""
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGClient:
    """HTTP client for RAG Service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.rag_service_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_dfn_by_id(self, dfn_id: str) -> Optional[Dict[str, Any]]:
        """
        Get DFN by ID from RAG Service
        
        Args:
            dfn_id: DFN ID
            
        Returns:
            DFN data or None
        """
        try:
            logger.debug(f"Fetching DFN {dfn_id} from RAG Service")
            response = await self.client.get(f"/api/v1/dfn/{dfn_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"DFN {dfn_id} not found")
                return None
            else:
                logger.error(f"Error fetching DFN: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching DFN from RAG Service: {e}")
            return None

    async def health_check(self) -> bool:
        """Check RAG Service health"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RAG Service health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
_rag_client: Optional[RAGClient] = None


def get_rag_client() -> RAGClient:
    """Get RAG client instance (singleton)"""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client

