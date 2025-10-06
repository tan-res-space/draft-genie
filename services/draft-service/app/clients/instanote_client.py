"""
Mock InstaNote API client for fetching speaker drafts
"""
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.logging import get_logger

logger = get_logger(__name__)


class InstaNoteMockClient:
    """Mock InstaNote API client that generates realistic draft data"""

    # Medical terminology for realistic drafts
    MEDICAL_TERMS = {
        "AD": [
            "patient presents with chest pain",
            "history of hypertension and diabetes",
            "physical examination reveals",
            "laboratory results show elevated",
            "diagnosis of acute myocardial infarction",
            "treatment plan includes medication",
            "follow-up appointment scheduled",
        ],
        "LD": [
            "discharge summary for patient",
            "admitted with complaints of",
            "hospital course was significant for",
            "medications on discharge include",
            "patient advised to follow up with",
            "prognosis is good with compliance",
            "discharge instructions provided",
        ],
        "IFN": [
            "patient called regarding test results",
            "discussed medication side effects",
            "advised to increase fluid intake",
            "scheduled for follow-up visit",
            "no immediate concerns noted",
            "continue current treatment plan",
            "call back if symptoms worsen",
        ],
    }

    # Common medical spelling errors
    COMMON_ERRORS = [
        ("diabetis", "diabetes"),
        ("hypertention", "hypertension"),
        ("pnemonia", "pneumonia"),
        ("asthama", "asthma"),
        ("perscription", "prescription"),
        ("symtoms", "symptoms"),
        ("recieve", "receive"),
        ("occured", "occurred"),
        ("seperate", "separate"),
        ("definately", "definitely"),
    ]

    # Grammar errors
    GRAMMAR_ERRORS = [
        ("was went", "went"),
        ("have went", "have gone"),
        ("more better", "better"),
        ("most best", "best"),
        ("between you and I", "between you and me"),
    ]

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        logger.info(f"Initialized InstaNote mock client for {api_url}")

    async def fetch_speaker_drafts(
        self, speaker_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch drafts for a speaker (mock implementation)
        
        Args:
            speaker_id: Speaker UUID
            limit: Maximum number of drafts to return
            
        Returns:
            List of draft dictionaries
        """
        logger.info(f"Fetching drafts for speaker {speaker_id} (limit: {limit})")

        drafts = []
        draft_types = ["AD", "LD", "IFN"]

        for i in range(limit):
            draft_type = random.choice(draft_types)
            draft = self._generate_mock_draft(speaker_id, draft_type, i)
            drafts.append(draft)

        logger.info(f"Generated {len(drafts)} mock drafts for speaker {speaker_id}")
        return drafts

    def _generate_mock_draft(
        self, speaker_id: str, draft_type: str, index: int
    ) -> Dict[str, Any]:
        """Generate a single mock draft with realistic errors"""
        
        # Generate base text
        base_sentences = random.sample(self.MEDICAL_TERMS[draft_type], k=3)
        original_text = ". ".join(base_sentences) + "."

        # Introduce spelling errors
        corrected_text = original_text
        num_errors = random.randint(1, 3)
        
        for _ in range(num_errors):
            if random.random() < 0.7:  # 70% spelling errors
                error, correction = random.choice(self.COMMON_ERRORS)
                if error in corrected_text.lower():
                    # Replace with error in original
                    original_text = original_text.replace(correction, error)
            else:  # 30% grammar errors
                error, correction = random.choice(self.GRAMMAR_ERRORS)
                if random.random() < 0.3:
                    original_text = original_text.replace(correction, error)

        # Calculate metrics
        word_count = len(original_text.split())
        correction_count = sum(
            1 for word in original_text.split() if word.lower() != corrected_text.lower()
        )

        # Generate draft
        draft_id = f"draft_{uuid.uuid4().hex[:12]}"
        dictated_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        return {
            "draft_id": draft_id,
            "speaker_id": speaker_id,
            "draft_type": draft_type,
            "original_text": original_text,
            "corrected_text": corrected_text,
            "word_count": word_count,
            "correction_count": correction_count,
            "metadata": {
                "source": "instanote_mock",
                "version": "1.0",
                "confidence_score": random.uniform(0.85, 0.99),
            },
            "dictated_at": dictated_at.isoformat(),
        }

    async def fetch_draft_by_id(self, draft_id: str) -> Dict[str, Any]:
        """
        Fetch a specific draft by ID (mock implementation)
        
        Args:
            draft_id: Draft ID
            
        Returns:
            Draft dictionary
        """
        logger.info(f"Fetching draft {draft_id}")
        
        # Generate a mock draft
        speaker_id = str(uuid.uuid4())
        draft_type = random.choice(["AD", "LD", "IFN"])
        draft = self._generate_mock_draft(speaker_id, draft_type, 0)
        draft["draft_id"] = draft_id
        
        return draft

    async def health_check(self) -> bool:
        """Check if InstaNote API is available"""
        # Mock always returns True
        return True

