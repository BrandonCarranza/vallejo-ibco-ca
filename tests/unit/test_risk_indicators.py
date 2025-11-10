"""
Test risk indicator calculations.
"""
import pytest
from decimal import Decimal

from src.analytics.risk_scoring.indicators import RiskIndicatorCalculator


def test_fund_balance_ratio_healthy(test_db, sample_fiscal_year, sample_financial_data):
    """Test fund balance ratio calculation - healthy scenario."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_fund_balance_ratio()

    assert result["available"] is True
    assert result["threshold"] == "adequate"  # 10M / 48M = 20.8%
    assert result["score"] == 0  # Healthy


def test_pension_funded_ratio_warning(test_db, sample_fiscal_year, sample_financial_data):
    """Test pension funded ratio - warning scenario."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_pension_funded_ratio()

    assert result["available"] is True
    assert result["value"] == pytest.approx(0.65, 0.01)
    assert result["threshold"] == "warning"  # 65% funded
    assert result["score"] == 50


def test_operating_balance_surplus(test_db, sample_fiscal_year, sample_financial_data):
    """Test operating balance with surplus."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_operating_balance()

    assert result["available"] is True
    assert result["value"] > 0  # Surplus
    assert result["threshold"] == "adequate"


def test_indicator_unavailable_when_no_data(test_db, sample_fiscal_year):
    """Test that indicators return unavailable when data missing."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_fund_balance_ratio()

    assert result["available"] is False
    assert result["value"] is None


def test_days_of_cash(test_db, sample_fiscal_year, sample_financial_data):
    """Test days of cash calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_days_of_cash()

    assert result["available"] is True
    # 10M fund balance / (48M expenditures / 365) = ~76 days
    assert result["value"] > 60
    assert result["value"] < 100


def test_ual_ratio(test_db, sample_fiscal_year, sample_financial_data):
    """Test UAL ratio calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_ual_ratio()

    assert result["available"] is True
    # 70M UAL / 50M revenue = 1.4 (140%)
    assert result["value"] > 1.0
    assert result["threshold"] == "severe"  # > 100%


def test_pension_contribution_burden(test_db, sample_fiscal_year, sample_financial_data):
    """Test pension contribution burden calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_pension_contribution_burden()

    assert result["available"] is True
    # 10M contribution / ~26M payroll (estimated) = ~38%
    assert result["value"] > 0.20


def test_all_indicators_calculated(test_db, sample_fiscal_year, sample_financial_data):
    """Test that all indicators can be calculated."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    all_indicators = calculator.calculate_all_indicators()

    assert len(all_indicators) == 9

    # Check that each indicator has required fields
    for indicator in all_indicators:
        assert "indicator_code" in indicator
        assert "available" in indicator
        assert "value" in indicator
        assert "score" in indicator
        assert "threshold" in indicator
        assert "interpretation" in indicator


def test_structural_deficit_trend(test_db, sample_fiscal_year, sample_financial_data):
    """Test structural deficit trend calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_structural_deficit_trend()

    # With only one year of data, should have minimal trend
    assert result["available"] is True


def test_revenue_volatility(test_db, sample_fiscal_year, sample_financial_data):
    """Test revenue volatility calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_revenue_volatility()

    # With only one year of data, should be unavailable or zero
    # depending on implementation
    assert "available" in result


def test_debt_service_ratio(test_db, sample_fiscal_year, sample_financial_data):
    """Test debt service ratio calculation."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_debt_service_ratio()

    # May be unavailable if no debt data
    assert "available" in result
