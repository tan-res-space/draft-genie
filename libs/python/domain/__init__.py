"""Domain models and events for DraftGenie."""

from .models import (
    Speaker,
    Draft,
    CorrectionVector,
    DraftGenieNote,
    Evaluation,
    SpeakerMetadata,
    DraftMetadata,
    EvaluationMetrics,
)
from .events import (
    DomainEvent,
    SpeakerOnboardedEvent,
    SpeakerUpdatedEvent,
    BucketReassignedEvent,
    DraftIngestedEvent,
    CorrectionVectorCreatedEvent,
    CorrectionVectorUpdatedEvent,
    DFNGeneratedEvent,
    EvaluationStartedEvent,
    EvaluationCompletedEvent,
    EvaluationFailedEvent,
)
from .value_objects import (
    SER,
    WER,
    QualityScore,
    SimilarityScore,
    ImprovementScore,
)
from .repositories import (
    SpeakerRepository,
    DraftRepository,
    CorrectionVectorRepository,
    DraftGenieNoteRepository,
    EvaluationRepository,
)

__all__ = [
    # Models
    "Speaker",
    "Draft",
    "CorrectionVector",
    "DraftGenieNote",
    "Evaluation",
    "SpeakerMetadata",
    "DraftMetadata",
    "EvaluationMetrics",
    # Events
    "DomainEvent",
    "SpeakerOnboardedEvent",
    "SpeakerUpdatedEvent",
    "BucketReassignedEvent",
    "DraftIngestedEvent",
    "CorrectionVectorCreatedEvent",
    "CorrectionVectorUpdatedEvent",
    "DFNGeneratedEvent",
    "EvaluationStartedEvent",
    "EvaluationCompletedEvent",
    "EvaluationFailedEvent",
    # Value Objects
    "SER",
    "WER",
    "QualityScore",
    "SimilarityScore",
    "ImprovementScore",
    # Repositories
    "SpeakerRepository",
    "DraftRepository",
    "CorrectionVectorRepository",
    "DraftGenieNoteRepository",
    "EvaluationRepository",
]

