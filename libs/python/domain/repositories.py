"""Repository protocols for DraftGenie domain."""

from abc import abstractmethod
from typing import List, Optional, Protocol

from .models import (
    CorrectionVector,
    Draft,
    DraftGenieNote,
    Evaluation,
    Speaker,
)


class SpeakerRepository(Protocol):
    """Protocol for Speaker repository."""

    @abstractmethod
    async def create(self, speaker: Speaker) -> Speaker:
        """Create a new speaker."""
        ...

    @abstractmethod
    async def get_by_id(self, speaker_id: str) -> Optional[Speaker]:
        """Get speaker by ID."""
        ...

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[Speaker]:
        """Get speaker by external ID."""
        ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        bucket: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Speaker]:
        """List speakers with pagination and filters."""
        ...

    @abstractmethod
    async def update(self, speaker_id: str, updates: dict) -> Optional[Speaker]:
        """Update speaker."""
        ...

    @abstractmethod
    async def delete(self, speaker_id: str) -> bool:
        """Soft delete speaker."""
        ...

    @abstractmethod
    async def count(self, bucket: Optional[str] = None, status: Optional[str] = None) -> int:
        """Count speakers with filters."""
        ...


class DraftRepository(Protocol):
    """Protocol for Draft repository."""

    @abstractmethod
    async def create(self, draft: Draft) -> Draft:
        """Create a new draft."""
        ...

    @abstractmethod
    async def create_many(self, drafts: List[Draft]) -> List[Draft]:
        """Create multiple drafts."""
        ...

    @abstractmethod
    async def get_by_id(self, draft_id: str) -> Optional[Draft]:
        """Get draft by ID."""
        ...

    @abstractmethod
    async def get_by_speaker_id(
        self,
        speaker_id: str,
        draft_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Draft]:
        """Get drafts by speaker ID."""
        ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        draft_type: Optional[str] = None,
    ) -> List[Draft]:
        """List drafts with pagination and filters."""
        ...

    @abstractmethod
    async def update(self, draft_id: str, updates: dict) -> Optional[Draft]:
        """Update draft."""
        ...

    @abstractmethod
    async def delete(self, draft_id: str) -> bool:
        """Delete draft."""
        ...

    @abstractmethod
    async def count(
        self,
        speaker_id: Optional[str] = None,
        draft_type: Optional[str] = None,
    ) -> int:
        """Count drafts with filters."""
        ...


class CorrectionVectorRepository(Protocol):
    """Protocol for CorrectionVector repository."""

    @abstractmethod
    async def create(self, vector: CorrectionVector) -> CorrectionVector:
        """Create a new correction vector."""
        ...

    @abstractmethod
    async def get_by_id(self, vector_id: str) -> Optional[CorrectionVector]:
        """Get correction vector by ID."""
        ...

    @abstractmethod
    async def get_by_speaker_id(
        self,
        speaker_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[CorrectionVector]:
        """Get correction vectors by speaker ID."""
        ...

    @abstractmethod
    async def update(self, vector_id: str, updates: dict) -> Optional[CorrectionVector]:
        """Update correction vector."""
        ...

    @abstractmethod
    async def delete(self, vector_id: str) -> bool:
        """Delete correction vector."""
        ...

    @abstractmethod
    async def search_similar(
        self,
        speaker_id: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> List[tuple[CorrectionVector, float]]:
        """Search for similar correction vectors."""
        ...


class DraftGenieNoteRepository(Protocol):
    """Protocol for DraftGenieNote repository."""

    @abstractmethod
    async def create(self, dfn: DraftGenieNote) -> DraftGenieNote:
        """Create a new DFN."""
        ...

    @abstractmethod
    async def get_by_id(self, dfn_id: str) -> Optional[DraftGenieNote]:
        """Get DFN by ID."""
        ...

    @abstractmethod
    async def get_by_speaker_id(
        self,
        speaker_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DraftGenieNote]:
        """Get DFNs by speaker ID."""
        ...

    @abstractmethod
    async def get_by_source_draft_id(self, source_draft_id: str) -> Optional[DraftGenieNote]:
        """Get DFN by source draft ID."""
        ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DraftGenieNote]:
        """List DFNs with pagination."""
        ...

    @abstractmethod
    async def delete(self, dfn_id: str) -> bool:
        """Delete DFN."""
        ...

    @abstractmethod
    async def count(self, speaker_id: Optional[str] = None) -> int:
        """Count DFNs with filters."""
        ...


class EvaluationRepository(Protocol):
    """Protocol for Evaluation repository."""

    @abstractmethod
    async def create(self, evaluation: Evaluation) -> Evaluation:
        """Create a new evaluation."""
        ...

    @abstractmethod
    async def get_by_id(self, evaluation_id: str) -> Optional[Evaluation]:
        """Get evaluation by ID."""
        ...

    @abstractmethod
    async def get_by_speaker_id(
        self,
        speaker_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Evaluation]:
        """Get evaluations by speaker ID."""
        ...

    @abstractmethod
    async def get_by_dfn_id(self, dfn_id: str) -> Optional[Evaluation]:
        """Get evaluation by DFN ID."""
        ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Evaluation]:
        """List evaluations with pagination and filters."""
        ...

    @abstractmethod
    async def update(self, evaluation_id: str, updates: dict) -> Optional[Evaluation]:
        """Update evaluation."""
        ...

    @abstractmethod
    async def delete(self, evaluation_id: str) -> bool:
        """Delete evaluation."""
        ...

    @abstractmethod
    async def count(
        self,
        speaker_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count evaluations with filters."""
        ...

    @abstractmethod
    async def get_latest_by_speaker_id(self, speaker_id: str) -> Optional[Evaluation]:
        """Get latest evaluation for a speaker."""
        ...

