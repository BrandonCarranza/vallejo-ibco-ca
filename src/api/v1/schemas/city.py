"""
City-related Pydantic schemas.
"""
from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, ConfigDict


class CityResponse(BaseModel):
    """Basic city information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    county: str
    population: Optional[int] = None
    government_type: Optional[str] = None
    is_active: bool
    has_bankruptcy_history: bool


class CityDetailResponse(BaseModel):
    """Detailed city information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    county: str

    # Demographics
    population: Optional[int] = None
    population_year: Optional[int] = None
    incorporation_date: Optional[date] = None

    # Geographic
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Government
    government_type: Optional[str] = None
    fiscal_year_end_month: int
    fiscal_year_end_day: int
    is_charter_city: Optional[bool] = None

    # Status
    is_active: bool

    # Bankruptcy history
    has_bankruptcy_history: bool
    bankruptcy_filing_date: Optional[date] = None
    bankruptcy_exit_date: Optional[date] = None
    bankruptcy_chapter: Optional[str] = None
    bankruptcy_notes: Optional[str] = None

    # Contact
    website_url: Optional[str] = None
    finance_department_url: Optional[str] = None


class FiscalYearSummaryResponse(BaseModel):
    """Summary of a fiscal year's data availability."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    start_date: date
    end_date: date

    # Data availability
    cafr_available: bool
    cafr_url: Optional[str] = None
    cafr_publish_date: Optional[date] = None

    budget_available: bool

    calpers_valuation_available: bool

    # Completeness
    revenues_complete: bool
    expenditures_complete: bool
    pension_data_complete: bool

    data_quality_score: Optional[int] = None
