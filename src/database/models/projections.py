"""
Financial projection models.

Store forward-looking projections and scenario analysis.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean,
    ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class ProjectionScenario(Base, AuditMixin):
    """
    A projection scenario with assumptions.

    Multiple scenarios can be compared: base, optimistic, pessimistic.
    """
    __tablename__ = "projection_scenarios"

    id = Column(Integer, primary_key=True)

    # Scenario Identity
    scenario_name = Column(String(100), nullable=False)  # "Base Case", "Pension Reform", etc.
    scenario_code = Column(String(50), nullable=False)   # "base", "optimistic", "pessimistic"

    # Description
    description = Column(Text, nullable=False)

    # Is this the default/baseline scenario?
    is_baseline = Column(Boolean, nullable=False, default=False)

    # Display order
    display_order = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    projections = relationship("FinancialProjection", back_populates="scenario")

    def __repr__(self) -> str:
        return f"<ProjectionScenario(name='{self.scenario_name}', code='{self.scenario_code}')>"


class FinancialProjection(Base, AuditMixin):
    """
    Projected financial data for a future year.

    Based on current trends + assumptions.
    """
    __tablename__ = "financial_projections"
    __table_args__ = (
        UniqueConstraint('city_id', 'base_fiscal_year_id', 'projection_year', 'scenario_id',
                        name='uq_financial_projection'),
        Index('ix_financial_projection_city', 'city_id'),
        Index('ix_financial_projection_base_year', 'base_fiscal_year_id'),
        Index('ix_financial_projection_year', 'projection_year'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Which fiscal year is this projection based on?
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Which scenario?
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Which future year is being projected?
    projection_year = Column(Integer, nullable=False)
    years_ahead = Column(Integer, nullable=False)  # 1, 2, 3, ... 10

    # When was this projection created?
    projection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    projection_model_version = Column(String(20), nullable=False)

    # REVENUE PROJECTIONS
    total_revenues_projected = Column(Numeric(15, 2), nullable=False)
    recurring_revenues_projected = Column(Numeric(15, 2), nullable=True)

    # Revenue growth assumptions
    revenue_growth_rate = Column(Numeric(6, 4), nullable=True)  # As decimal

    # EXPENDITURE PROJECTIONS
    total_expenditures_projected = Column(Numeric(15, 2), nullable=False)

    # Expenditure components
    personnel_costs_projected = Column(Numeric(15, 2), nullable=True)
    pension_costs_projected = Column(Numeric(15, 2), nullable=True)  # THE BIG ONE
    opeb_costs_projected = Column(Numeric(15, 2), nullable=True)
    other_costs_projected = Column(Numeric(15, 2), nullable=True)

    # Expenditure growth assumptions
    base_expenditure_growth_rate = Column(Numeric(6, 4), nullable=True)
    pension_growth_rate = Column(Numeric(6, 4), nullable=True)

    # STRUCTURAL BALANCE
    operating_surplus_deficit = Column(Numeric(15, 2), nullable=False)  # Revenues - Expenditures
    operating_margin_percent = Column(Numeric(6, 2), nullable=True)  # As percent

    # FUND BALANCE PROJECTION
    beginning_fund_balance = Column(Numeric(15, 2), nullable=False)
    ending_fund_balance = Column(Numeric(15, 2), nullable=False)
    fund_balance_ratio = Column(Numeric(6, 4), nullable=True)  # Fund Balance / Expenditures

    # FISCAL HEALTH FLAGS
    is_deficit = Column(Boolean, nullable=False)
    is_depleting_reserves = Column(Boolean, nullable=False)
    reserves_below_minimum = Column(Boolean, nullable=False)  # Below 10%

    # Is this the "fiscal cliff" year? (when reserves run out)
    is_fiscal_cliff = Column(Boolean, nullable=False, default=False)

    # PENSION SPECIFIC PROJECTIONS
    pension_funded_ratio_projected = Column(Numeric(6, 4), nullable=True)
    pension_ual_projected = Column(Numeric(15, 2), nullable=True)

    # ASSUMPTIONS (stored as JSON for flexibility)
    # Format: {"discount_rate": 0.068, "inflation": 0.025, "payroll_growth": 0.03, ...}
    assumptions = Column(JSON, nullable=True)

    # CONFIDENCE
    confidence_level = Column(String(20), nullable=True)  # "high", "medium", "low"

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    base_fiscal_year = relationship("FiscalYear")
    scenario = relationship("ProjectionScenario", back_populates="projections")

    def __repr__(self) -> str:
        return (f"<FinancialProjection(city_id={self.city_id}, year={self.projection_year}, "
                f"deficit={self.operating_surplus_deficit})>")


class ScenarioAssumption(Base, AuditMixin):
    """
    Detailed assumptions for a projection scenario.

    Documents what-if assumptions clearly.
    """
    __tablename__ = "scenario_assumptions"
    __table_args__ = (
        UniqueConstraint('scenario_id', 'assumption_category', 'assumption_name',
                        name='uq_scenario_assumption'),
    )

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Assumption Identity
    assumption_category = Column(String(50), nullable=False)  # "revenue", "expenditure", "pension"
    assumption_name = Column(String(100), nullable=False)  # "property_tax_growth_rate"

    # Value
    assumption_value = Column(String(100), nullable=False)
    assumption_numeric_value = Column(Numeric(10, 6), nullable=True)  # If numeric

    # Description
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)  # Why this assumption?

    # Source
    source = Column(String(255), nullable=True)  # Where did this assumption come from?

    is_custom = Column(Boolean, nullable=False, default=False)  # User-modified assumption?

    # Relationships
    scenario = relationship("ProjectionScenario")

    def __repr__(self) -> str:
        return (f"<ScenarioAssumption(scenario_id={self.scenario_id}, "
                f"name='{self.assumption_name}', value='{self.assumption_value}')>")


class FiscalCliffAnalysis(Base, AuditMixin):
    """
    Analysis of when/if a city hits fiscal crisis.

    "Fiscal Cliff" = year when revenues < expenditures AND reserves exhausted.
    """
    __tablename__ = "fiscal_cliff_analyses"
    __table_args__ = (
        UniqueConstraint('city_id', 'base_fiscal_year_id', 'scenario_id',
                        name='uq_fiscal_cliff_analysis'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Analysis date
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Results
    has_fiscal_cliff = Column(Boolean, nullable=False)
    fiscal_cliff_year = Column(Integer, nullable=True)  # Which year does crisis hit?
    years_until_cliff = Column(Integer, nullable=True)  # How many years away?

    # Details
    reserves_exhausted_year = Column(Integer, nullable=True)
    cumulative_deficit_at_cliff = Column(Numeric(15, 2), nullable=True)

    # Severity
    severity = Column(String(20), nullable=True)  # "immediate", "near_term", "long_term", "none"

    # Narrative
    summary = Column(Text, nullable=True)

    # Sensitivity analysis
    # How much would revenues need to increase to avoid cliff?
    revenue_increase_needed_percent = Column(Numeric(6, 2), nullable=True)

    # How much would expenditures need to decrease?
    expenditure_decrease_needed_percent = Column(Numeric(6, 2), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    base_fiscal_year = relationship("FiscalYear")
    scenario = relationship("ProjectionScenario")

    def __repr__(self) -> str:
        return (f"<FiscalCliffAnalysis(city_id={self.city_id}, "
                f"has_cliff={self.has_fiscal_cliff}, year={self.fiscal_cliff_year})>")
