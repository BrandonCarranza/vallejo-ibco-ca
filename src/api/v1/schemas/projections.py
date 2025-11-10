"""
Pydantic schemas for financial projections API.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProjectionScenarioResponse(BaseModel):
    """Projection scenario metadata."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_name: str
    scenario_code: str
    description: str
    is_baseline: bool
    display_order: int
    is_active: bool


class FinancialProjectionResponse(BaseModel):
    """Financial projection for a future year."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    base_fiscal_year_id: int
    scenario_id: int

    # Projection Identity
    projection_year: int
    years_ahead: int
    projection_date: datetime
    projection_model_version: str

    # Revenue Projections
    total_revenues_projected: Decimal
    recurring_revenues_projected: Optional[Decimal] = None
    revenue_growth_rate: Optional[Decimal] = None

    # Expenditure Projections
    total_expenditures_projected: Decimal
    personnel_costs_projected: Optional[Decimal] = None
    pension_costs_projected: Optional[Decimal] = None
    opeb_costs_projected: Optional[Decimal] = None
    other_costs_projected: Optional[Decimal] = None
    base_expenditure_growth_rate: Optional[Decimal] = None
    pension_growth_rate: Optional[Decimal] = None

    # Structural Balance
    operating_surplus_deficit: Decimal
    operating_margin_percent: Optional[Decimal] = None

    # Fund Balance
    beginning_fund_balance: Decimal
    ending_fund_balance: Decimal
    fund_balance_ratio: Optional[Decimal] = None

    # Health Flags
    is_deficit: bool
    is_depleting_reserves: bool
    reserves_below_minimum: bool
    is_fiscal_cliff: bool

    # Pension Projections
    pension_funded_ratio_projected: Optional[Decimal] = None
    pension_ual_projected: Optional[Decimal] = None

    # Assumptions
    assumptions: Optional[Dict[str, Any]] = None
    confidence_level: Optional[str] = None
    notes: Optional[str] = None


class FinancialProjectionSummaryResponse(BaseModel):
    """Simplified projection for charts/listings."""

    projection_year: int
    years_ahead: int
    total_revenues: float
    total_expenditures: float
    surplus_deficit: float
    ending_fund_balance: float
    is_deficit: bool
    is_fiscal_cliff: bool


class FiscalCliffAnalysisResponse(BaseModel):
    """Fiscal cliff analysis results."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    base_fiscal_year_id: int
    scenario_id: int
    analysis_date: datetime

    # Results
    has_fiscal_cliff: bool
    fiscal_cliff_year: Optional[int] = None
    years_until_cliff: Optional[int] = None

    # Details
    reserves_exhausted_year: Optional[int] = None
    cumulative_deficit_at_cliff: Optional[Decimal] = None

    # Severity
    severity: Optional[str] = Field(
        None,
        description="immediate, near_term, long_term, or none"
    )

    # Narrative
    summary: Optional[str] = Field(
        None,
        description="Human-readable summary of fiscal cliff analysis"
    )

    # Sensitivity Analysis
    revenue_increase_needed_percent: Optional[Decimal] = Field(
        None,
        description="How much revenues need to increase to avoid cliff"
    )
    expenditure_decrease_needed_percent: Optional[Decimal] = Field(
        None,
        description="How much expenditures need to decrease to avoid cliff"
    )

    notes: Optional[str] = None


class ScenarioComparisonResponse(BaseModel):
    """Compare outcomes across scenarios."""

    base_year: int
    scenarios: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Scenario outcomes keyed by scenario code"
    )
    scenario_spread: Dict[str, Any] = Field(
        ...,
        description="Difference between best/worst cases"
    )


class ProjectionCalculationRequest(BaseModel):
    """Request to calculate projections."""

    base_year: int = Field(..., description="Base fiscal year")
    years_ahead: int = Field(10, ge=1, le=20, description="Years to project")
    scenarios: Optional[list[str]] = Field(
        None,
        description="Scenarios to run (default: all)"
    )
