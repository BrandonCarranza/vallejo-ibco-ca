"""
Test risk scoring engine.
"""
import pytest

from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine


def test_calculate_risk_score(test_db, sample_fiscal_year, sample_financial_data):
    """Test complete risk score calculation."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score is not None
    assert risk_score.overall_score >= 0
    assert risk_score.overall_score <= 100
    assert risk_score.risk_level in ["low", "moderate", "high", "severe"]
    assert risk_score.data_completeness_percent > 0


def test_risk_level_classification(test_db):
    """Test risk level classification."""
    engine = RiskScoringEngine(test_db)

    assert engine._determine_risk_level(10) == "low"
    assert engine._determine_risk_level(35) == "moderate"
    assert engine._determine_risk_level(60) == "high"
    assert engine._determine_risk_level(85) == "severe"


def test_top_risk_factors_identified(test_db, sample_fiscal_year, sample_financial_data):
    """Test that top risk factors are identified."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score.top_risk_factors is not None
    assert len(risk_score.top_risk_factors) <= 5

    # Should be sorted by score (highest first)
    if len(risk_score.top_risk_factors) > 1:
        assert risk_score.top_risk_factors[0]["score"] >= risk_score.top_risk_factors[1]["score"]


def test_category_scores(test_db, sample_fiscal_year, sample_financial_data):
    """Test that category scores are calculated."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    # All category scores should be present
    assert risk_score.liquidity_score is not None
    assert risk_score.structural_balance_score is not None
    assert risk_score.pension_stress_score is not None
    assert risk_score.revenue_sustainability_score is not None
    assert risk_score.debt_burden_score is not None

    # Should be in valid range
    assert 0 <= risk_score.liquidity_score <= 100
    assert 0 <= risk_score.structural_balance_score <= 100
    assert 0 <= risk_score.pension_stress_score <= 100
    assert 0 <= risk_score.revenue_sustainability_score <= 100
    assert 0 <= risk_score.debt_burden_score <= 100


def test_indicator_scores_created(test_db, sample_fiscal_year, sample_financial_data):
    """Test that individual indicator scores are created."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert len(risk_score.indicator_scores) > 0

    # Check indicator structure
    for indicator in risk_score.indicator_scores:
        assert indicator.indicator_code is not None
        assert indicator.indicator_value is not None
        assert indicator.indicator_score is not None
        assert indicator.threshold_category in ["healthy", "adequate", "warning", "critical", "severe"]
        assert indicator.weight is not None


def test_data_completeness_calculation(test_db, sample_fiscal_year, sample_financial_data):
    """Test data completeness calculation."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    # With complete test data, should have high completeness
    assert risk_score.data_completeness_percent >= 50
    assert risk_score.indicators_available >= 5
    assert risk_score.indicators_available + risk_score.indicators_missing == 9


def test_summary_generated(test_db, sample_fiscal_year, sample_financial_data):
    """Test that a summary is generated."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score.summary is not None
    assert len(risk_score.summary) > 0
    # Summary should mention risk level
    assert risk_score.risk_level in risk_score.summary.lower()


def test_model_version_recorded(test_db, sample_fiscal_year, sample_financial_data):
    """Test that model version is recorded."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score.model_version is not None
    # Should be in format like "1.0"
    assert "." in risk_score.model_version


def test_weighted_category_calculation(test_db):
    """Test weighted category score calculation."""
    engine = RiskScoringEngine(test_db)

    # Test category weights
    assert engine.CATEGORY_WEIGHTS["Liquidity"] == 0.25
    assert engine.CATEGORY_WEIGHTS["Structural"] == 0.25
    assert engine.CATEGORY_WEIGHTS["Pension"] == 0.30  # Highest weight
    assert engine.CATEGORY_WEIGHTS["Revenue"] == 0.10
    assert engine.CATEGORY_WEIGHTS["Debt"] == 0.10

    # Weights should sum to 1.0
    total_weight = sum(engine.CATEGORY_WEIGHTS.values())
    assert abs(total_weight - 1.0) < 0.01


def test_missing_data_handling(test_db, sample_fiscal_year):
    """Test that missing data is handled gracefully."""
    # No financial data loaded
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    # Should still create a risk score with missing indicators
    assert risk_score is not None
    assert risk_score.indicators_missing > 0
    assert risk_score.data_completeness_percent < 100
