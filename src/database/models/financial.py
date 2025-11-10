"""
Financial data models: Revenues, Expenditures, Fund Balances.

These models store the core financial data extracted from CAFRs and budgets.
Designed for year-over-year comparison and trend analysis.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
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


class RevenueCategory(Base, AuditMixin):
    """
    Standardized revenue categories for cross-year comparison.

    Hierarchical structure (3 levels) allows for both detailed and
    aggregate analysis.
    """

    __tablename__ = "revenue_categories"

    id = Column(Integer, primary_key=True)

    # Category Hierarchy (3 levels)
    category_level1 = Column(String(100), nullable=False)  # e.g., "Taxes"
    category_level2 = Column(String(100), nullable=True)  # e.g., "Property Taxes"
    category_level3 = Column(
        String(100), nullable=True
    )  # e.g., "Secured Property Taxes"

    # Standardized name for reporting
    standard_name = Column(String(255), nullable=False, unique=True)

    # Classification
    is_recurring = Column(Boolean, nullable=False, default=True)
    is_discretionary = Column(Boolean, nullable=True)

    # Description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    revenues = relationship("Revenue", back_populates="category")

    def __repr__(self) -> str:
        """String representation of RevenueCategory."""
        return f"<RevenueCategory(id={self.id}, name='{self.standard_name}')>"


class Revenue(Base, AuditMixin):
    """
    Revenue data for a fiscal year.

    Tracks both budgeted and actual revenues by category and fund type.
    Critical for analyzing revenue volatility and concentration.
    """

    __tablename__ = "revenues"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id",
            "category_id",
            "fund_type",
            name="uq_revenue_year_category_fund",
        ),
        CheckConstraint("actual_amount >= 0", name="ck_revenue_actual_non_negative"),
        Index("ix_revenue_fiscal_year", "fiscal_year_id"),
        Index("ix_revenue_category", "category_id"),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=False)

    # Fund Classification
    fund_type = Column(
        String(50), nullable=False, default="General"
    )  # General, Special, Enterprise
    fund_name = Column(String(255), nullable=True)

    # Amounts (in dollars)
    budget_amount = Column(Numeric(15, 2), nullable=True)
    actual_amount = Column(Numeric(15, 2), nullable=False)

    # Variance Analysis
    variance_amount = Column(Numeric(15, 2), nullable=True)  # Actual - Budget
    variance_percent = Column(
        Numeric(6, 2), nullable=True
    )  # (Actual - Budget) / Budget * 100

    # Source Information
    source_document_type = Column(String(50), nullable=False)  # CAFR, Budget, etc.
    source_page = Column(Integer, nullable=True)
    source_line_item = Column(String(255), nullable=True)

    # Data Quality
    is_estimated = Column(Boolean, nullable=False, default=False)
    estimation_method = Column(String(255), nullable=True)
    confidence_level = Column(String(20), nullable=True)  # High, Medium, Low

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="revenues")
    category = relationship("RevenueCategory", back_populates="revenues")

    def __repr__(self) -> str:
        """String representation of Revenue."""
        return f"<Revenue(id={self.id}, fy_id={self.fiscal_year_id}, amount=${self.actual_amount})>"


class ExpenditureCategory(Base, AuditMixin):
    """
    Standardized expenditure categories.

    Includes flags to identify special types of expenditures like
    personnel costs, pension costs, debt service, and capital expenses.
    """

    __tablename__ = "expenditure_categories"

    id = Column(Integer, primary_key=True)

    # Category Hierarchy
    category_level1 = Column(String(100), nullable=False)  # e.g., "Public Safety"
    category_level2 = Column(String(100), nullable=True)  # e.g., "Police"
    category_level3 = Column(String(100), nullable=True)  # e.g., "Police Salaries"

    standard_name = Column(String(255), nullable=False, unique=True)

    # Classification - Important for risk analysis
    is_personnel_cost = Column(Boolean, nullable=False, default=False)
    is_pension_cost = Column(Boolean, nullable=False, default=False)
    is_debt_service = Column(Boolean, nullable=False, default=False)
    is_capital = Column(Boolean, nullable=False, default=False)

    description = Column(Text, nullable=True)

    # Relationships
    expenditures = relationship("Expenditure", back_populates="category")

    def __repr__(self) -> str:
        """String representation of ExpenditureCategory."""
        return f"<ExpenditureCategory(id={self.id}, name='{self.standard_name}')>"


class Expenditure(Base, AuditMixin):
    """
    Expenditure data for a fiscal year.

    Tracks spending by category, department, and fund.
    Includes budget vs. actual variance analysis.
    """

    __tablename__ = "expenditures"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id",
            "category_id",
            "fund_type",
            name="uq_expenditure_year_category_fund",
        ),
        CheckConstraint(
            "actual_amount >= 0", name="ck_expenditure_actual_non_negative"
        ),
        Index("ix_expenditure_fiscal_year", "fiscal_year_id"),
        Index("ix_expenditure_category", "category_id"),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    category_id = Column(
        Integer, ForeignKey("expenditure_categories.id"), nullable=False
    )

    # Fund Classification
    fund_type = Column(String(50), nullable=False, default="General")
    fund_name = Column(String(255), nullable=True)

    # Department (if available)
    department = Column(String(255), nullable=True)

    # Amounts
    budget_amount = Column(Numeric(15, 2), nullable=True)
    actual_amount = Column(Numeric(15, 2), nullable=False)

    # Variance
    variance_amount = Column(Numeric(15, 2), nullable=True)
    variance_percent = Column(Numeric(6, 2), nullable=True)

    # Source
    source_document_type = Column(String(50), nullable=False)
    source_page = Column(Integer, nullable=True)
    source_line_item = Column(String(255), nullable=True)

    # Data Quality
    is_estimated = Column(Boolean, nullable=False, default=False)
    estimation_method = Column(String(255), nullable=True)
    confidence_level = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="expenditures")
    category = relationship("ExpenditureCategory", back_populates="expenditures")

    def __repr__(self) -> str:
        """String representation of Expenditure."""
        return f"<Expenditure(id={self.id}, fy_id={self.fiscal_year_id}, amount=${self.actual_amount})>"


class FundBalance(Base, AuditMixin):
    """
    Fund balance data (city's reserves/savings).

    Critical indicator of fiscal health. Tracks fund balance components
    per GASB 54 classification and calculates key financial ratios.
    """

    __tablename__ = "fund_balances"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id", "fund_type", name="uq_fund_balance_year_fund"
        ),
        Index("ix_fund_balance_fiscal_year", "fiscal_year_id"),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Fund Classification
    fund_type = Column(String(50), nullable=False, default="General")
    fund_name = Column(String(255), nullable=True)

    # Fund Balance Components (per GASB 54)
    nonspendable = Column(Numeric(15, 2), nullable=True, default=0)
    restricted = Column(Numeric(15, 2), nullable=True, default=0)
    committed = Column(Numeric(15, 2), nullable=True, default=0)
    assigned = Column(Numeric(15, 2), nullable=True, default=0)
    unassigned = Column(Numeric(15, 2), nullable=True, default=0)

    # Total
    total_fund_balance = Column(Numeric(15, 2), nullable=False)

    # Key Ratios
    fund_balance_ratio = Column(
        Numeric(6, 4), nullable=True
    )  # Fund Balance / Expenditures
    days_of_cash = Column(Numeric(8, 2), nullable=True)  # Days city can operate

    # Year-over-year Change
    yoy_change_amount = Column(Numeric(15, 2), nullable=True)
    yoy_change_percent = Column(Numeric(6, 2), nullable=True)

    # Source
    source_document_type = Column(String(50), nullable=False)
    source_page = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="fund_balances")

    def __repr__(self) -> str:
        """String representation of FundBalance."""
        return f"<FundBalance(id={self.id}, fy_id={self.fiscal_year_id}, balance=${self.total_fund_balance})>"
