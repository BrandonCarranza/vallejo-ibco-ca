"""
Risk scoring models.

Stores fiscal stress indicators and composite risk scores.
This is the PRIMARY OUTPUT of the IBCo platform.

Risk scores are NOT predictions of bankruptcy (insufficient data for that).
They are composite indicators of fiscal stress based on transparent methodology.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base


class RiskIndicator(Base, AuditMixin):
    """
    Definition of a risk indicator.

    Each indicator has thresholds, weights, and scoring logic.
    Used to configure the risk scoring system.

    Example indicators:
    - Fund Balance Ratio
    - Pension Funded Ratio
    - Debt Service Ratio
    - Revenue Volatility
    """

    __tablename__ = "risk_indicators"

    id = Column(Integer, primary_key=True)

    # Indicator Identity
    indicator_code = Column(
        String(50), nullable=False, unique=True
    )  # e.g., "FB_RATIO"
    indicator_name = Column(String(255), nullable=False)  # "Fund Balance Ratio"

    # Category
    category = Column(
        String(50), nullable=False
    )  # Liquidity, Structural, Pension, Revenue, Debt

    # Description
    description = Column(Text, nullable=False)
    calculation_formula = Column(Text, nullable=True)

    # Weight in composite score (0-1, should sum to 1.0 within category)
    weight = Column(Numeric(5, 4), nullable=False)

    # Thresholds (for scoring)
    threshold_healthy = Column(Numeric(15, 4), nullable=True)  # Score 0
    threshold_adequate = Column(Numeric(15, 4), nullable=True)  # Score 25
    threshold_warning = Column(Numeric(15, 4), nullable=True)  # Score 50
    threshold_critical = Column(Numeric(15, 4), nullable=True)  # Score 100

    # Direction (is higher better or worse?)
    higher_is_better = Column(Boolean, nullable=False, default=True)

    # Metadata
    data_source = Column(String(255), nullable=True)
    unit_of_measure = Column(
        String(50), nullable=True
    )  # "ratio", "percent", "dollars"

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)

    notes = Column(Text, nullable=True)

    # Relationships
    indicator_scores = relationship("RiskIndicatorScore", back_populates="indicator")

    def __repr__(self) -> str:
        """String representation of RiskIndicator."""
        return f"<RiskIndicator(code='{self.indicator_code}', name='{self.indicator_name}')>"


class RiskScore(Base, AuditMixin):
    """
    Complete risk assessment for a fiscal year.

    This is THE KEY OUTPUT of the platform.

    Composite score calculated from 12 indicators across 5 categories:
    - Liquidity & Reserves (25% weight)
    - Structural Balance (25% weight)
    - Pension Stress (30% weight)
    - Revenue Sustainability (10% weight)
    - Debt Burden (10% weight)

    Score interpretation:
    - 0-25: Low risk (healthy finances)
    - 26-50: Moderate risk (watch carefully)
    - 51-75: High risk (corrective action needed)
    - 76-100: Severe risk (fiscal crisis)

    IMPORTANT: These are fiscal stress indicators, NOT bankruptcy predictions.
    """

    __tablename__ = "risk_scores"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id", "calculation_date", name="uq_risk_score_fy_date"
        ),
        Index("ix_risk_score_fiscal_year", "fiscal_year_id"),
        Index("ix_risk_score_date", "calculation_date"),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_risk_overall_score_valid",
        ),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # When was this calculated?
    calculation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    model_version = Column(String(20), nullable=False)  # e.g., "1.0", "1.1"

    # OVERALL COMPOSITE SCORE (0-100)
    overall_score = Column(Numeric(5, 2), nullable=False)

    # Risk Level Classification
    risk_level = Column(
        String(20), nullable=False
    )  # "low", "moderate", "high", "severe"

    # CATEGORY SCORES (0-100 each)
    liquidity_score = Column(Numeric(5, 2), nullable=False)
    structural_balance_score = Column(Numeric(5, 2), nullable=False)
    pension_stress_score = Column(Numeric(5, 2), nullable=False)
    revenue_sustainability_score = Column(Numeric(5, 2), nullable=False)
    debt_burden_score = Column(Numeric(5, 2), nullable=False)

    # DATA QUALITY & CONFIDENCE
    data_completeness_percent = Column(
        Numeric(5, 2), nullable=False
    )  # 0-100
    indicators_available = Column(
        Integer, nullable=False
    )  # How many of 12 indicators had data
    indicators_missing = Column(Integer, nullable=False)

    # DATA FRESHNESS
    data_as_of_date = Column(
        DateTime, nullable=False
    )  # When the underlying data was current
    data_age_months = Column(Integer, nullable=True)  # How old is the data?

    # TOP RISK FACTORS (JSON array of top 5)
    # Format: [{"indicator": "pension_funded_ratio", "score": 85, "contribution": 15.3}, ...]
    top_risk_factors = Column(JSON, nullable=True)

    # NARRATIVE SUMMARY
    summary = Column(Text, nullable=True)  # Auto-generated summary

    # VALIDATION
    validated = Column(Boolean, nullable=False, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="risk_scores")
    indicator_scores = relationship(
        "RiskIndicatorScore", back_populates="risk_score", lazy="dynamic"
    )

    def __repr__(self) -> str:
        """String representation of RiskScore."""
        return (
            f"<RiskScore(fy_id={self.fiscal_year_id}, score={self.overall_score:.1f}, "
            f"level='{self.risk_level}')>"
        )


class RiskIndicatorScore(Base, AuditMixin):
    """
    Individual indicator scores that roll up to composite risk score.

    Stores the value and score for each of the 12 indicators.
    Links back to source data for transparency.

    Example:
    - Fund Balance Ratio = 0.15 (15%)
    - Threshold: Warning (10-15%)
    - Score: 50 (out of 100)
    - Weight: 0.083 (1/12 of total)
    - Contribution: 4.15 points to overall score
    """

    __tablename__ = "risk_indicator_scores"
    __table_args__ = (
        UniqueConstraint(
            "risk_score_id", "indicator_id", name="uq_risk_indicator_score"
        ),
        Index("ix_risk_indicator_score_risk_score", "risk_score_id"),
        Index("ix_risk_indicator_score_indicator", "indicator_id"),
    )

    id = Column(Integer, primary_key=True)
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("risk_indicators.id"), nullable=False)

    # The actual measured value
    indicator_value = Column(Numeric(15, 4), nullable=False)

    # The scored value (0-100)
    indicator_score = Column(Numeric(5, 2), nullable=False)

    # Which threshold bucket?
    threshold_category = Column(
        String(20), nullable=False
    )  # healthy, adequate, warning, critical

    # How much does this contribute to overall score?
    weight = Column(Numeric(5, 4), nullable=False)
    contribution_to_overall = Column(
        Numeric(5, 2), nullable=False
    )  # score * weight

    # Data source for this indicator value
    data_source_table = Column(String(100), nullable=True)
    data_source_record_id = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    risk_score = relationship("RiskScore", back_populates="indicator_scores")
    indicator = relationship("RiskIndicator", back_populates="indicator_scores")

    def __repr__(self) -> str:
        """String representation of RiskIndicatorScore."""
        return (
            f"<RiskIndicatorScore(risk_score_id={self.risk_score_id}, "
            f"value={self.indicator_value}, score={self.indicator_score:.1f})>"
        )


class RiskTrend(Base, AuditMixin):
    """
    Risk trend analysis over time.

    Tracks how risk is changing: improving, stable, or deteriorating.

    Critical question: Is Vallejo's fiscal health getting better or worse?

    Analysis includes:
    - Trend direction (improving/stable/deteriorating)
    - Trend slope (rate of change per year)
    - Statistical significance
    - Volatility (stability of the trend)
    """

    __tablename__ = "risk_trends"
    __table_args__ = (
        UniqueConstraint(
            "city_id", "indicator_code", "analysis_date", name="uq_risk_trend"
        ),
        Index("ix_risk_trend_city", "city_id"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Which indicator or overall?
    indicator_code = Column(
        String(50), nullable=False
    )  # "OVERALL" or specific indicator

    # Analysis date
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Time period analyzed
    years_analyzed = Column(Integer, nullable=False)  # e.g., 5 years
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)

    # Trend analysis
    trend_direction = Column(
        String(20), nullable=False
    )  # "improving", "stable", "deteriorating"
    trend_slope = Column(Numeric(8, 4), nullable=True)  # Change per year
    trend_significance = Column(
        String(20), nullable=True
    )  # "significant", "moderate", "minor"

    # Statistics
    average_score = Column(Numeric(5, 2), nullable=True)
    min_score = Column(Numeric(5, 2), nullable=True)
    max_score = Column(Numeric(5, 2), nullable=True)
    volatility = Column(Numeric(5, 2), nullable=True)  # Standard deviation

    # Narrative
    narrative = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")

    def __repr__(self) -> str:
        """String representation of RiskTrend."""
        return (
            f"<RiskTrend(city_id={self.city_id}, indicator='{self.indicator_code}', "
            f"direction='{self.trend_direction}')>"
        )


class BenchmarkComparison(Base, AuditMixin):
    """
    Compare city's indicators to peer cities or benchmarks.

    Context is critical: Is Vallejo worse than similar cities?

    Peer group: California cities with:
    - Population 50,000-250,000
    - Similar pension funded status (±10%)
    - Available CAFR data

    Comparison shows:
    - Where Vallejo ranks vs. peers (percentile)
    - How far from average/median
    - Best and worst performers for context
    """

    __tablename__ = "benchmark_comparisons"
    __table_args__ = (
        Index("ix_benchmark_comparison_city", "city_id"),
        Index("ix_benchmark_comparison_fiscal_year", "fiscal_year_id"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Which indicator?
    indicator_code = Column(String(50), nullable=False)

    # This city's value
    city_value = Column(Numeric(15, 4), nullable=False)

    # Benchmark statistics
    peer_group_name = Column(
        String(100), nullable=False
    )  # e.g., "CA Cities 50K-250K pop"
    peer_group_size = Column(Integer, nullable=True)  # How many cities in peer group

    peer_average = Column(Numeric(15, 4), nullable=True)
    peer_median = Column(Numeric(15, 4), nullable=True)
    peer_25th_percentile = Column(Numeric(15, 4), nullable=True)
    peer_75th_percentile = Column(Numeric(15, 4), nullable=True)
    peer_best = Column(Numeric(15, 4), nullable=True)
    peer_worst = Column(Numeric(15, 4), nullable=True)

    # This city's percentile rank (0-100)
    city_percentile = Column(Numeric(5, 2), nullable=True)

    # Interpretation
    comparison_category = Column(
        String(20), nullable=True
    )  # "much_worse", "worse", "similar", "better", "much_better"

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        """String representation of BenchmarkComparison."""
        return (
            f"<BenchmarkComparison(city_id={self.city_id}, indicator='{self.indicator_code}', "
            f"percentile={self.city_percentile:.1f})>"
        )
