"""
Pydantic schemas for risk scoring API.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RiskIndicatorDetailResponse(BaseModel):
    """Individual risk indicator details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    indicator_code: str
    indicator_value: Decimal
    indicator_score: Decimal
    threshold_category: str = Field(..., description="healthy, adequate, warning, or critical")
    weight: Decimal = Field(..., description="Indicator weight in overall score")
    contribution_to_overall: Decimal = Field(..., description="Contribution to overall score")


class RiskScoreResponse(BaseModel):
    """Risk score for a fiscal year."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    calculation_date: datetime
    model_version: str

    # Overall Score
    overall_score: Decimal = Field(..., description="Composite risk score (0-100)")
    risk_level: str = Field(..., description="low, moderate, high, or severe")

    # Category Scores
    liquidity_score: Decimal
    structural_balance_score: Decimal
    pension_stress_score: Decimal
    revenue_sustainability_score: Decimal
    debt_burden_score: Decimal

    # Data Quality
    data_completeness_percent: Decimal
    indicators_available: int
    indicators_missing: int
    data_as_of_date: datetime

    # Analysis
    top_risk_factors: List[Dict[str, Any]] = Field(
        ...,
        description="Top 5 risk factors driving the score"
    )
    summary: str = Field(..., description="Human-readable summary")

    validated: bool
    validator_notes: Optional[str] = None
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None

    # Relationships
    indicator_scores: List[RiskIndicatorDetailResponse] = Field(
        default_factory=list,
        description="Individual indicator scores"
    )


class RiskScoreSummaryResponse(BaseModel):
    """Simplified risk score for listings."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    overall_score: Decimal
    risk_level: str
    calculation_date: datetime
    data_completeness_percent: Decimal


class RiskTrendResponse(BaseModel):
    """Risk score trend over time."""

    year: int
    overall_score: float
    risk_level: str
    liquidity_score: float
    structural_balance_score: float
    pension_stress_score: float


class RiskComparisonResponse(BaseModel):
    """Compare risk scores across cities."""

    city_id: int
    city_name: str
    fiscal_year: int
    overall_score: float
    risk_level: str
    pension_stress_score: float
    data_completeness_percent: float
