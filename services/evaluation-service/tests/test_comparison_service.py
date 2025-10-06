"""
Tests for Comparison Service
"""
import pytest
from app.services.comparison_service import ComparisonService


@pytest.fixture
def comparison_service():
    """Comparison service fixture"""
    return ComparisonService()


def test_calculate_sentence_edit_rate_identical(comparison_service):
    """Test SER with identical texts"""
    text1 = "Patient has diabetes. Blood pressure is normal."
    text2 = "Patient has diabetes. Blood pressure is normal."
    
    ser = comparison_service.calculate_sentence_edit_rate(text1, text2)
    assert ser == 0.0  # No changes


def test_calculate_sentence_edit_rate_different(comparison_service):
    """Test SER with different texts"""
    text1 = "Pt has diabetis."
    text2 = "Patient has diabetes mellitus."
    
    ser = comparison_service.calculate_sentence_edit_rate(text1, text2)
    assert 0.0 < ser <= 1.0  # Some changes


def test_calculate_word_error_rate_identical(comparison_service):
    """Test WER with identical texts"""
    text1 = "Patient has diabetes"
    text2 = "Patient has diabetes"
    
    wer = comparison_service.calculate_word_error_rate(text1, text2)
    assert wer == 0.0  # No changes


def test_calculate_word_error_rate_different(comparison_service):
    """Test WER with different texts"""
    text1 = "Pt has diabetis"
    text2 = "Patient has diabetes mellitus"
    
    wer = comparison_service.calculate_word_error_rate(text1, text2)
    assert 0.0 < wer <= 1.0  # Some changes


def test_calculate_quality_score(comparison_service):
    """Test quality score calculation"""
    ser = 0.2
    wer = 0.3
    semantic_similarity = 0.9
    
    quality = comparison_service.calculate_quality_score(ser, wer, semantic_similarity)
    assert 0.0 <= quality <= 1.0
    assert quality > 0.5  # Should be good quality


def test_calculate_improvement_score(comparison_service):
    """Test improvement score calculation"""
    ifn_word_count = 10
    dfn_word_count = 20  # 2x expansion (ideal range)
    quality_score = 0.8
    
    improvement = comparison_service.calculate_improvement_score(
        ifn_word_count, dfn_word_count, quality_score
    )
    assert 0.0 <= improvement <= 1.0
    assert improvement > 0.7  # Should be good improvement


def test_get_detailed_metrics(comparison_service):
    """Test detailed metrics"""
    text1 = "Patient has diabetes. Blood pressure is normal."
    text2 = "Patient has diabetes mellitus. Blood pressure is within normal limits."
    
    metrics = comparison_service.get_detailed_metrics(text1, text2, 0.2, 0.3)
    
    assert "ifn_word_count" in metrics
    assert "dfn_word_count" in metrics
    assert "expansion_ratio" in metrics
    assert "text_similarity_ratio" in metrics
    assert metrics["ifn_word_count"] > 0
    assert metrics["dfn_word_count"] > 0


def test_split_sentences(comparison_service):
    """Test sentence splitting"""
    text = "First sentence. Second sentence! Third sentence?"
    sentences = comparison_service._split_sentences(text)
    assert len(sentences) == 3


def test_split_words(comparison_service):
    """Test word splitting"""
    text = "Patient has diabetes, and hypertension."
    words = comparison_service._split_words(text)
    assert len(words) == 5  # patient, has, diabetes, and, hypertension

