"""
Pension data models.

Tracks pension plans, liabilities, contributions, and actuarial assumptions.
This is the CORE of California municipal fiscal crisis analysis.

Pension underfunding is THE primary driver of municipal fiscal stress in California.
These models support:
- Detailed actuarial analysis
- Scenario modeling (what-if discount rate changes)
- Multi-year projections
- Assumption change tracking
"""

from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base


class PensionPlan(Base, AuditMixin):
    """
    A pension plan for a fiscal year.

    Most cities have multiple plans (Safety, Miscellaneous, PEPRA).
    Tracks complete actuarial valuation data from CalPERS reports.

    This is the foundation for pension stress analysis.
    """

    __tablename__ = "pension_plans"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id", "plan_name", name="uq_pension_plan_year_name"
        ),
        Index("ix_pension_plan_fiscal_year", "fiscal_year_id"),
        CheckConstraint(
            "funded_ratio >= 0 AND funded_ratio <= 2.0",
            name="ck_pension_funded_ratio_reasonable",
        ),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Plan Identification
    plan_name = Column(String(100), nullable=False)  # "Miscellaneous", "Safety", etc.
    plan_id = Column(String(50), nullable=True)  # CalPERS plan ID if available

    # Member Information
    active_members = Column(Integer, nullable=True)
    retired_members = Column(Integer, nullable=True)
    total_members = Column(Integer, nullable=True)

    # Actuarial Valuation Date
    valuation_date = Column(Date, nullable=False)

    # ========================================================================
    # LIABILITY SIDE (What the city owes)
    # ========================================================================

    # Total Pension Liability (TPL) - the BIG number
    total_pension_liability = Column(Numeric(15, 2), nullable=False)

    # Service Cost (new benefits earned this year)
    service_cost = Column(Numeric(15, 2), nullable=True)

    # Interest on TPL
    interest_cost = Column(Numeric(15, 2), nullable=True)

    # ========================================================================
    # ASSET SIDE (What the city has saved)
    # ========================================================================

    # Fiduciary Net Position (plan assets)
    fiduciary_net_position = Column(Numeric(15, 2), nullable=False)

    # Investment Return (actual)
    actual_investment_return = Column(Numeric(15, 2), nullable=True)
    actual_investment_return_percent = Column(
        Numeric(6, 4), nullable=True
    )  # As decimal

    # ========================================================================
    # UNFUNDED LIABILITY (The crisis)
    # ========================================================================

    # Net Pension Liability = TPL - Assets
    net_pension_liability = Column(Numeric(15, 2), nullable=False)

    # Unfunded Actuarial Liability (UAL) - same as NPL in most contexts
    unfunded_actuarial_liability = Column(Numeric(15, 2), nullable=False)

    # KEY RATIO
    funded_ratio = Column(Numeric(6, 4), nullable=False)  # Assets / TPL (as decimal)

    # ========================================================================
    # CONTRIBUTIONS (What the city pays annually)
    # ========================================================================

    # Employer Normal Cost (cost of benefits earned this year)
    employer_normal_cost = Column(Numeric(15, 2), nullable=True)
    employer_normal_cost_percent = Column(
        Numeric(6, 4), nullable=True
    )  # % of payroll

    # UAL Payment (paying down the unfunded liability)
    ual_payment = Column(Numeric(15, 2), nullable=True)

    # Total Employer Contribution
    total_employer_contribution = Column(Numeric(15, 2), nullable=True)
    total_employer_contribution_percent = Column(
        Numeric(6, 4), nullable=True
    )  # % of payroll

    # Employee Contributions
    employee_contribution = Column(Numeric(15, 2), nullable=True)

    # Payroll
    covered_payroll = Column(Numeric(15, 2), nullable=True)

    # ========================================================================
    # ACTUARIAL ASSUMPTIONS (Critical - small changes = huge impact)
    # ========================================================================

    # Discount Rate (assumed investment return)
    discount_rate = Column(Numeric(5, 4), nullable=True)  # e.g., 0.0680 for 6.8%

    # Inflation assumption
    inflation_rate = Column(Numeric(5, 4), nullable=True)

    # Payroll growth assumption
    payroll_growth_rate = Column(Numeric(5, 4), nullable=True)

    # Mortality table
    mortality_table = Column(String(100), nullable=True)

    # Amortization period (years to pay off UAL)
    amortization_period_years = Column(Integer, nullable=True)

    # Amortization method
    amortization_method = Column(
        String(50), nullable=True
    )  # "Level Percent", "Level Dollar"

    # ========================================================================
    # PROJECTIONS (From CalPERS)
    # ========================================================================

    # Projected contribution next year
    projected_contribution_next_year = Column(Numeric(15, 2), nullable=True)
    projected_contribution_rate_next_year = Column(Numeric(6, 4), nullable=True)

    # ========================================================================
    # SOURCE INFORMATION
    # ========================================================================
    source_document = Column(
        String(255), nullable=False
    )  # "CalPERS Valuation Report"
    source_url = Column(String(500), nullable=True)
    source_page = Column(Integer, nullable=True)

    # DATA QUALITY
    is_preliminary = Column(Boolean, nullable=False, default=False)
    confidence_level = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="pension_plans")

    def __repr__(self) -> str:
        """String representation of PensionPlan."""
        funded_pct = float(self.funded_ratio) * 100 if self.funded_ratio else 0
        return (
            f"<PensionPlan(id={self.id}, fy_id={self.fiscal_year_id}, "
            f"plan='{self.plan_name}', funded={funded_pct:.1f}%)>"
        )


class PensionContribution(Base, AuditMixin):
    """
    Historical pension contributions (what city actually paid).

    Separate from projections - this is cash out the door.
    Used to track budget vs. actual and contribution growth over time.
    """

    __tablename__ = "pension_contributions"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id", "plan_name", name="uq_pension_contribution"
        ),
        Index("ix_pension_contribution_fiscal_year", "fiscal_year_id"),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    plan_name = Column(String(100), nullable=False)

    # Budgeted amounts
    budgeted_contribution = Column(Numeric(15, 2), nullable=True)

    # Actual amounts paid
    actual_contribution = Column(Numeric(15, 2), nullable=False)

    # Variance
    variance = Column(Numeric(15, 2), nullable=True)

    # Breakdown (if available)
    normal_cost_paid = Column(Numeric(15, 2), nullable=True)
    ual_payment_paid = Column(Numeric(15, 2), nullable=True)

    # Source
    source_document = Column(String(255), nullable=False)
    source_page = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        """String representation of PensionContribution."""
        return (
            f"<PensionContribution(fy_id={self.fiscal_year_id}, "
            f"plan='{self.plan_name}', paid=${self.actual_contribution:,.0f})>"
        )


class PensionProjection(Base, AuditMixin):
    """
    CalPERS-published contribution projections.

    CalPERS publishes 20-year amortization schedules showing required contributions.
    This is THE most predictable (and alarming) trend in municipal finance.

    Used for:
    - Multi-year fiscal projections
    - Scenario analysis
    - "Fiscal cliff" identification
    """

    __tablename__ = "pension_projections"
    __table_args__ = (
        UniqueConstraint(
            "base_fiscal_year_id",
            "plan_name",
            "projection_year",
            "scenario",
            name="uq_pension_projection",
        ),
        Index("ix_pension_projection_base_year", "base_fiscal_year_id"),
        Index("ix_pension_projection_year", "projection_year"),
    )

    id = Column(Integer, primary_key=True)

    # Which valuation is this projection from?
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    plan_name = Column(String(100), nullable=False)

    # Which future year is being projected?
    projection_year = Column(Integer, nullable=False)

    # Projected contribution
    projected_contribution = Column(Numeric(15, 2), nullable=False)
    projected_contribution_rate = Column(
        Numeric(6, 4), nullable=True
    )  # % of payroll

    # Projected payroll (assumption)
    projected_payroll = Column(Numeric(15, 2), nullable=True)

    # Components
    projected_normal_cost = Column(Numeric(15, 2), nullable=True)
    projected_ual_payment = Column(Numeric(15, 2), nullable=True)

    # Scenario label (for what-if analysis)
    scenario = Column(
        String(50), nullable=False, default="Base"
    )  # Base, Optimistic, Pessimistic

    # Assumptions for this scenario
    assumed_discount_rate = Column(Numeric(5, 4), nullable=True)
    assumed_investment_return = Column(Numeric(5, 4), nullable=True)
    assumed_payroll_growth = Column(Numeric(5, 4), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    base_fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        """String representation of PensionProjection."""
        return (
            f"<PensionProjection(base_fy={self.base_fiscal_year_id}, "
            f"proj_year={self.projection_year}, amount=${self.projected_contribution:,.0f})>"
        )


class OPEBLiability(Base, AuditMixin):
    """
    Other Post-Employment Benefits (retiree healthcare).

    Often overlooked but can be massive. Typically NOT pre-funded like pensions,
    meaning cities pay as bills come in (pay-as-you-go).

    For Vallejo and many CA cities, OPEB is another significant unfunded liability.
    """

    __tablename__ = "opeb_liabilities"
    __table_args__ = (
        UniqueConstraint("fiscal_year_id", name="uq_opeb_fiscal_year"),
        Index("ix_opeb_fiscal_year", "fiscal_year_id"),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Actuarial valuation date
    valuation_date = Column(Date, nullable=False)

    # Total OPEB Liability
    total_opeb_liability = Column(Numeric(15, 2), nullable=False)

    # Plan assets (if any - most cities have $0)
    plan_fiduciary_net_position = Column(Numeric(15, 2), nullable=False, default=0)

    # Net OPEB Liability
    net_opeb_liability = Column(Numeric(15, 2), nullable=False)

    # Funded ratio (usually 0% for unfunded plans)
    funded_ratio = Column(Numeric(6, 4), nullable=False, default=0)

    # Annual cost
    opeb_expense = Column(Numeric(15, 2), nullable=True)
    actual_contributions = Column(
        Numeric(15, 2), nullable=True
    )  # Usually pay-as-you-go

    # Actuarial assumptions
    discount_rate = Column(Numeric(5, 4), nullable=True)
    healthcare_cost_trend = Column(Numeric(5, 4), nullable=True)

    # Source
    source_document = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        """String representation of OPEBLiability."""
        return f"<OPEBLiability(fy_id={self.fiscal_year_id}, liability=${self.net_opeb_liability:,.0f})>"


class PensionAssumptionChange(Base, AuditMixin):
    """
    Track changes in actuarial assumptions over time.

    When CalPERS lowers the discount rate, UAL explodes overnight.
    Track these changes for transparency and to explain liability spikes.

    Example: CalPERS lowered discount rate from 7.5% to 7.0% to 6.8%
    Each drop added billions in unfunded liabilities statewide.
    """

    __tablename__ = "pension_assumption_changes"

    id = Column(Integer, primary_key=True)

    # Which fiscal year did the change take effect?
    effective_fiscal_year_id = Column(
        Integer, ForeignKey("fiscal_years.id"), nullable=False
    )

    # Which plan?
    plan_name = Column(String(100), nullable=False)

    # What changed?
    assumption_type = Column(
        String(50), nullable=False
    )  # "discount_rate", "mortality", etc.

    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=False)

    # Impact on liability
    impact_on_liability = Column(Numeric(15, 2), nullable=True)
    impact_on_funded_ratio = Column(Numeric(6, 4), nullable=True)

    # Why did it change?
    reason = Column(Text, nullable=True)

    # Source
    source_document = Column(String(255), nullable=True)
    announced_date = Column(Date, nullable=True)

    # Relationships
    effective_fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        """String representation of PensionAssumptionChange."""
        return (
            f"<PensionAssumptionChange(type='{self.assumption_type}', "
            f"old={self.old_value}, new={self.new_value})>"
        )
