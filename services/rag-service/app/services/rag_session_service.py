"""
RAG Session Service - Manage RAG sessions
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.rag_session import (
    RAGSessionModel,
    RAGSessionCreate,
    RAGSessionUpdate,
    RAGSessionResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGSessionService:
    """Service for managing RAG sessions"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.rag_sessions

    async def create_session(
        self, session_create: RAGSessionCreate
    ) -> RAGSessionModel:
        """
        Create a new RAG session
        
        Args:
            session_create: Session creation data
            
        Returns:
            Created session model
        """
        try:
            logger.info(f"Creating RAG session {session_create.session_id}")

            # Check if session already exists
            existing = await self.collection.find_one(
                {"session_id": session_create.session_id}
            )
            if existing:
                raise ValueError(f"Session {session_create.session_id} already exists")

            # Create session document
            session_dict = session_create.model_dump()
            session_dict["prompts_used"] = []
            session_dict["agent_steps"] = []
            session_dict["dfn_generated"] = False
            session_dict["dfn_id"] = None
            session_dict["status"] = "pending"
            session_dict["error_message"] = None
            session_dict["created_at"] = datetime.utcnow()
            session_dict["updated_at"] = datetime.utcnow()

            # Insert into database
            result = await self.collection.insert_one(session_dict)
            session_dict["_id"] = result.inserted_id

            session_model = RAGSessionModel(**session_dict)
            logger.info(f"Created RAG session {session_create.session_id}")
            return session_model

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    async def get_session_by_id(self, session_id: str) -> Optional[RAGSessionModel]:
        """Get session by ID"""
        try:
            session = await self.collection.find_one({"session_id": session_id})
            if session:
                return RAGSessionModel(**session)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def get_sessions_by_speaker(
        self, speaker_id: str, skip: int = 0, limit: int = 100
    ) -> List[RAGSessionModel]:
        """Get all sessions for a speaker"""
        try:
            cursor = (
                self.collection.find({"speaker_id": speaker_id})
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )

            sessions = []
            async for session in cursor:
                sessions.append(RAGSessionModel(**session))

            return sessions

        except Exception as e:
            logger.error(f"Error getting sessions for speaker {speaker_id}: {e}")
            return []

    async def update_session(
        self, session_id: str, session_update: RAGSessionUpdate
    ) -> Optional[RAGSessionModel]:
        """Update a session"""
        try:
            logger.info(f"Updating session {session_id}")

            # Get update data
            update_data = session_update.model_dump(exclude_unset=True)
            if not update_data:
                return await self.get_session_by_id(session_id)

            update_data["updated_at"] = datetime.utcnow()

            # Update in database
            result = await self.collection.update_one(
                {"session_id": session_id},
                {"$set": update_data},
            )

            if result.modified_count == 0:
                logger.warning(f"Session {session_id} not found or not modified")
                return None

            return await self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            raise

    async def add_agent_step(
        self, session_id: str, step: Dict[str, Any]
    ) -> Optional[RAGSessionModel]:
        """Add an agent step to session"""
        try:
            logger.info(f"Adding agent step to session {session_id}")

            # Add timestamp to step
            step["timestamp"] = datetime.utcnow().isoformat()

            # Update in database
            result = await self.collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"agent_steps": step},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            if result.modified_count == 0:
                logger.warning(f"Session {session_id} not found")
                return None

            return await self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"Error adding agent step: {e}")
            raise

    async def mark_complete(
        self, session_id: str, dfn_id: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as complete"""
        try:
            logger.info(f"Marking session {session_id} as complete")

            result = await self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "dfn_generated": True,
                        "dfn_id": dfn_id,
                        "status": "complete",
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(f"Session {session_id} not found")
                return None

            return await self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"Error marking session complete: {e}")
            raise

    async def mark_failed(
        self, session_id: str, error_message: str
    ) -> Optional[RAGSessionModel]:
        """Mark session as failed"""
        try:
            logger.info(f"Marking session {session_id} as failed")

            result = await self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count == 0:
                logger.warning(f"Session {session_id} not found")
                return None

            return await self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"Error marking session failed: {e}")
            raise


def get_rag_session_service(db: AsyncIOMotorDatabase) -> RAGSessionService:
    """Factory function to create RAGSessionService"""
    return RAGSessionService(db)

