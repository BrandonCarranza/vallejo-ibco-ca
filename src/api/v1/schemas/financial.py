"""
Financial data Pydantic schemas.
"""
from typing import Optional
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class FinancialSummaryResponse(BaseModel):
    """High-level financial summary."""
    city_id: int
    city_name: str
    fiscal_year: int
    total_revenues: float
    total_expenditures: float
    operating_balance: float
    fund_balance: Optional[float] = None
    fund_balance_ratio: Optional[float] = None
    total_pension_ual: float
    data_quality_score: Optional[int] = None


class RevenueResponse(BaseModel):
    """Revenue data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    budget_amount: Optional[Decimal] = None
    actual_amount: Decimal
    variance_amount: Optional[Decimal] = None
    variance_percent: Optional[Decimal] = None
    is_estimated: bool
    confidence_level: Optional[str] = None


class ExpenditureResponse(BaseModel):
    """Expenditure data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    department: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    actual_amount: Decimal
    variance_amount: Optional[Decimal] = None
    is_estimated: bool


class FundBalanceResponse(BaseModel):
    """Fund balance data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    total_fund_balance: Decimal
    fund_balance_ratio: Optional[Decimal] = None
    days_of_cash: Optional[Decimal] = None
    yoy_change_amount: Optional[Decimal] = None
    yoy_change_percent: Optional[Decimal] = None


class PensionPlanResponse(BaseModel):
    """Pension plan data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    plan_name: str
    valuation_date: date

    # Liabilities
    total_pension_liability: Decimal
    fiduciary_net_position: Decimal
    unfunded_actuarial_liability: Decimal
    funded_ratio: Decimal

    # Contributions
    total_employer_contribution: Optional[Decimal] = None
    total_employer_contribution_percent: Optional[Decimal] = None

    # Assumptions
    discount_rate: Optional[Decimal] = None

    is_preliminary: bool
