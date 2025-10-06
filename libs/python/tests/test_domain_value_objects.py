"""Tests for domain value objects."""

import pytest

from common.constants import BucketType
from domain.value_objects import (
    SER,
    WER,
    SimilarityScore,
    QualityScore,
    ImprovementScore,
)


class TestSER:
    """Tests for SER value object."""

    def test_create_ser(self):
        """Test creating SER."""
        ser = SER(value=0.15)
        assert ser.value == 0.15
        assert float(ser) == 0.15

    def test_ser_as_percentage(self):
        """Test SER as percentage."""
        ser = SER(value=0.15)
        assert ser.as_percentage() == 15.0

    def test_ser_quality_checks(self):
        """Test SER quality checks."""
        excellent = SER(value=0.03)
        assert excellent.is_excellent()
        assert excellent.is_good()
        assert excellent.is_average()

        good = SER(value=0.08)
        assert not good.is_excellent()
        assert good.is_good()
        assert good.is_average()

        average = SER(value=0.15)
        assert not average.is_excellent()
        assert not average.is_good()
        assert average.is_average()

    def test_invalid_ser(self):
        """Test invalid SER value."""
        with pytest.raises(ValueError):
            SER(value=1.5)

        with pytest.raises(ValueError):
            SER(value=-0.1)

    def test_ser_string_representation(self):
        """Test SER string representation."""
        ser = SER(value=0.15)
        assert str(ser) == "15.00%"


class TestWER:
    """Tests for WER value object."""

    def test_create_wer(self):
        """Test creating WER."""
        wer = WER(value=0.12)
        assert wer.value == 0.12
        assert float(wer) == 0.12

    def test_wer_as_percentage(self):
        """Test WER as percentage."""
        wer = WER(value=0.12)
        assert wer.as_percentage() == 12.0

    def test_wer_quality_checks(self):
        """Test WER quality checks."""
        excellent = WER(value=0.03)
        assert excellent.is_excellent()

        good = WER(value=0.08)
        assert good.is_good()

        average = WER(value=0.15)
        assert average.is_average()

    def test_invalid_wer(self):
        """Test invalid WER value."""
        with pytest.raises(ValueError):
            WER(value=2.0)


class TestSimilarityScore:
    """Tests for SimilarityScore value object."""

    def test_create_similarity_score(self):
        """Test creating similarity score."""
        score = SimilarityScore(value=0.95)
        assert score.value == 0.95
        assert float(score) == 0.95

    def test_similarity_as_percentage(self):
        """Test similarity as percentage."""
        score = SimilarityScore(value=0.95)
        assert score.as_percentage() == 95.0

    def test_similarity_levels(self):
        """Test similarity level checks."""
        high = SimilarityScore(value=0.95)
        assert high.is_high()
        assert high.is_moderate()
        assert not high.is_low()

        moderate = SimilarityScore(value=0.80)
        assert not moderate.is_high()
        assert moderate.is_moderate()
        assert not moderate.is_low()

        low = SimilarityScore(value=0.60)
        assert not low.is_high()
        assert not low.is_moderate()
        assert low.is_low()

    def test_invalid_similarity(self):
        """Test invalid similarity value."""
        with pytest.raises(ValueError):
            SimilarityScore(value=1.5)


class TestQualityScore:
    """Tests for QualityScore value object."""

    def test_create_quality_score(self):
        """Test creating quality score."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        quality = QualityScore(ser=ser, wer=wer, similarity=similarity)
        assert quality.ser.value == 0.10
        assert quality.wer.value == 0.08
        assert quality.similarity.value == 0.95

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        quality = QualityScore(ser=ser, wer=wer, similarity=similarity)
        score = quality.calculate()

        # Expected: (90 * 0.3) + (92 * 0.3) + (95 * 0.4) = 92.6
        assert 92.0 <= score <= 93.0

    def test_recommend_bucket(self):
        """Test bucket recommendation."""
        # Excellent quality
        excellent = QualityScore(
            ser=SER(value=0.02),
            wer=WER(value=0.02),
            similarity=SimilarityScore(value=0.98),
        )
        assert excellent.recommend_bucket() == BucketType.EXCELLENT

        # Good quality
        good = QualityScore(
            ser=SER(value=0.08),
            wer=WER(value=0.08),
            similarity=SimilarityScore(value=0.92),
        )
        assert good.recommend_bucket() == BucketType.GOOD

        # Average quality
        average = QualityScore(
            ser=SER(value=0.15),
            wer=WER(value=0.15),
            similarity=SimilarityScore(value=0.80),
        )
        assert average.recommend_bucket() == BucketType.AVERAGE

        # Poor quality (needs lower similarity to get POOR bucket)
        poor = QualityScore(
            ser=SER(value=0.35),
            wer=WER(value=0.35),
            similarity=SimilarityScore(value=0.60),
        )
        assert poor.recommend_bucket() == BucketType.POOR

    def test_custom_weights(self):
        """Test quality score with custom weights."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        quality = QualityScore(
            ser=ser,
            wer=wer,
            similarity=similarity,
            weights={"ser": 0.2, "wer": 0.2, "similarity": 0.6},
        )
        score = quality.calculate()
        assert score > 0

    def test_invalid_weights(self):
        """Test invalid weights."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        with pytest.raises(ValueError):
            QualityScore(
                ser=ser,
                wer=wer,
                similarity=similarity,
                weights={"ser": 0.5, "wer": 0.3, "similarity": 0.1},  # Sum = 0.9
            )

    def test_quality_score_to_dict(self):
        """Test quality score to dict."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        quality = QualityScore(ser=ser, wer=wer, similarity=similarity)
        result = quality.to_dict()

        assert "ser" in result
        assert "wer" in result
        assert "similarity" in result
        assert "quality_score" in result
        assert "recommended_bucket" in result

    def test_quality_score_string_representation(self):
        """Test quality score string representation."""
        ser = SER(value=0.10)
        wer = WER(value=0.08)
        similarity = SimilarityScore(value=0.95)

        quality = QualityScore(ser=ser, wer=wer, similarity=similarity)
        str_repr = str(quality)
        assert "Quality Score" in str_repr
        assert "Bucket" in str_repr


class TestImprovementScore:
    """Tests for ImprovementScore value object."""

    def test_create_improvement_score(self):
        """Test creating improvement score."""
        improvement = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        assert improvement.baseline_ser == 0.20
        assert improvement.improved_ser == 0.10

    def test_ser_improvement(self):
        """Test SER improvement calculation."""
        improvement = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        # (0.20 - 0.10) / 0.20 * 100 = 50%
        assert improvement.ser_improvement() == 50.0

    def test_wer_improvement(self):
        """Test WER improvement calculation."""
        improvement = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        # (0.18 - 0.08) / 0.18 * 100 ≈ 55.56%
        assert 55.0 <= improvement.wer_improvement() <= 56.0

    def test_overall_improvement(self):
        """Test overall improvement calculation."""
        improvement = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        overall = improvement.overall_improvement()
        # Average of 50% and ~55.56% ≈ 52.78%
        assert 52.0 <= overall <= 53.0

    def test_is_improved(self):
        """Test improvement check."""
        improved = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        assert improved.is_improved()
        assert not improved.is_degraded()

    def test_is_degraded(self):
        """Test degradation check."""
        degraded = ImprovementScore(
            baseline_ser=0.10,
            improved_ser=0.20,
            baseline_wer=0.08,
            improved_wer=0.18,
        )
        assert not degraded.is_improved()
        assert degraded.is_degraded()

    def test_zero_baseline(self):
        """Test with zero baseline."""
        improvement = ImprovementScore(
            baseline_ser=0.0,
            improved_ser=0.10,
            baseline_wer=0.0,
            improved_wer=0.08,
        )
        assert improvement.ser_improvement() == 0.0
        assert improvement.wer_improvement() == 0.0

    def test_improvement_to_dict(self):
        """Test improvement score to dict."""
        improvement = ImprovementScore(
            baseline_ser=0.20,
            improved_ser=0.10,
            baseline_wer=0.18,
            improved_wer=0.08,
        )
        result = improvement.to_dict()

        assert "baseline_ser" in result
        assert "improved_ser" in result
        assert "ser_improvement" in result
        assert "wer_improvement" in result
        assert "overall_improvement" in result
        assert "is_improved" in result

