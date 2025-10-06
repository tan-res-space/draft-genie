"""Value objects for DraftGenie domain."""

from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator

from common.constants import BucketType


class SER(BaseModel):
    """Sentence Edit Rate value object."""

    value: float = Field(..., description="SER value between 0 and 1")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        """Validate SER is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("SER must be between 0 and 1")
        return v

    def as_percentage(self) -> float:
        """Return SER as percentage."""
        return self.value * 100

    def is_excellent(self) -> bool:
        """Check if SER indicates excellent quality."""
        return self.value < 0.05

    def is_good(self) -> bool:
        """Check if SER indicates good quality."""
        return self.value < 0.10

    def is_average(self) -> bool:
        """Check if SER indicates average quality."""
        return self.value < 0.20

    def __str__(self) -> str:
        """String representation."""
        return f"{self.as_percentage():.2f}%"

    def __float__(self) -> float:
        """Float representation."""
        return self.value


class WER(BaseModel):
    """Word Error Rate value object."""

    value: float = Field(..., description="WER value between 0 and 1")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        """Validate WER is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("WER must be between 0 and 1")
        return v

    def as_percentage(self) -> float:
        """Return WER as percentage."""
        return self.value * 100

    def is_excellent(self) -> bool:
        """Check if WER indicates excellent quality."""
        return self.value < 0.05

    def is_good(self) -> bool:
        """Check if WER indicates good quality."""
        return self.value < 0.10

    def is_average(self) -> bool:
        """Check if WER indicates average quality."""
        return self.value < 0.20

    def __str__(self) -> str:
        """String representation."""
        return f"{self.as_percentage():.2f}%"

    def __float__(self) -> float:
        """Float representation."""
        return self.value


class SimilarityScore(BaseModel):
    """Semantic similarity score value object."""

    value: float = Field(..., description="Similarity score between 0 and 1")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        """Validate similarity is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Similarity score must be between 0 and 1")
        return v

    def as_percentage(self) -> float:
        """Return similarity as percentage."""
        return self.value * 100

    def is_high(self) -> bool:
        """Check if similarity is high (>= 0.9)."""
        return self.value >= 0.9

    def is_moderate(self) -> bool:
        """Check if similarity is moderate (>= 0.7)."""
        return self.value >= 0.7

    def is_low(self) -> bool:
        """Check if similarity is low (< 0.7)."""
        return self.value < 0.7

    def __str__(self) -> str:
        """String representation."""
        return f"{self.as_percentage():.2f}%"

    def __float__(self) -> float:
        """Float representation."""
        return self.value


class QualityScore(BaseModel):
    """Overall quality score value object."""

    ser: SER = Field(..., description="Sentence Edit Rate")
    wer: WER = Field(..., description="Word Error Rate")
    similarity: SimilarityScore = Field(..., description="Similarity score")
    weights: Dict[str, float] = Field(
        default={"ser": 0.3, "wer": 0.3, "similarity": 0.4},
        description="Weights for each metric",
    )

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate weights sum to 1."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError("Weights must sum to 1")
        return v

    def calculate(self) -> float:
        """
        Calculate overall quality score (0-100).
        
        Lower SER/WER and higher similarity = better score.
        """
        # Convert SER and WER to scores (lower is better, so invert)
        ser_score = max(0, 100 - (self.ser.value * 100))
        wer_score = max(0, 100 - (self.wer.value * 100))
        sim_score = self.similarity.value * 100

        # Weighted average
        quality = (
            ser_score * self.weights["ser"]
            + wer_score * self.weights["wer"]
            + sim_score * self.weights["similarity"]
        )

        return round(quality, 2)

    def recommend_bucket(self) -> BucketType:
        """Recommend bucket based on quality score."""
        score = self.calculate()

        if score >= 95:
            return BucketType.EXCELLENT
        elif score >= 85:
            return BucketType.GOOD
        elif score >= 70:
            return BucketType.AVERAGE
        elif score >= 50:
            return BucketType.POOR
        else:
            return BucketType.NEEDS_IMPROVEMENT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ser": self.ser.value,
            "wer": self.wer.value,
            "similarity": self.similarity.value,
            "quality_score": self.calculate(),
            "recommended_bucket": self.recommend_bucket().value,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Quality Score: {self.calculate():.2f} (Bucket: {self.recommend_bucket().value})"

    def __float__(self) -> float:
        """Float representation."""
        return self.calculate()


class ImprovementScore(BaseModel):
    """Improvement score comparing DFN vs IFN."""

    baseline_ser: float = Field(..., description="Baseline SER (before)")
    improved_ser: float = Field(..., description="Improved SER (after)")
    baseline_wer: float = Field(..., description="Baseline WER (before)")
    improved_wer: float = Field(..., description="Improved WER (after)")

    @field_validator("baseline_ser", "improved_ser", "baseline_wer", "improved_wer")
    @classmethod
    def validate_rate(cls, v: float) -> float:
        """Validate rate is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Rate must be between 0 and 1")
        return v

    def ser_improvement(self) -> float:
        """Calculate SER improvement percentage."""
        if self.baseline_ser == 0:
            return 0.0
        return ((self.baseline_ser - self.improved_ser) / self.baseline_ser) * 100

    def wer_improvement(self) -> float:
        """Calculate WER improvement percentage."""
        if self.baseline_wer == 0:
            return 0.0
        return ((self.baseline_wer - self.improved_wer) / self.baseline_wer) * 100

    def overall_improvement(self) -> float:
        """Calculate overall improvement score."""
        return (self.ser_improvement() + self.wer_improvement()) / 2

    def is_improved(self) -> bool:
        """Check if there is improvement."""
        return self.overall_improvement() > 0

    def is_degraded(self) -> bool:
        """Check if quality degraded."""
        return self.overall_improvement() < 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_ser": self.baseline_ser,
            "improved_ser": self.improved_ser,
            "baseline_wer": self.baseline_wer,
            "improved_wer": self.improved_wer,
            "ser_improvement": self.ser_improvement(),
            "wer_improvement": self.wer_improvement(),
            "overall_improvement": self.overall_improvement(),
            "is_improved": self.is_improved(),
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Improvement: {self.overall_improvement():.2f}%"

    def __float__(self) -> float:
        """Float representation."""
        return self.overall_improvement()

