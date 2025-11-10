"""
Core database models: Cities, Fiscal Years, and foundational entities.

These models form the backbone of the system and are referenced by all other models.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
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

if TYPE_CHECKING:
    from src.database.models.financial import Expenditure, FundBalance, Revenue


class City(Base, AuditMixin):
    """
    Cities being tracked by the IBCo system.

    Initially focused on Vallejo, but designed for multi-city support.
    Stores demographic, geographic, and governmental structure information.
    """

    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)

    # Basic Information
    name = Column(String(100), nullable=False, unique=True)
    state = Column(String(2), nullable=False)  # CA
    county = Column(String(100), nullable=False)

    # Demographics
    population = Column(Integer, nullable=True)  # Latest estimate
    population_year = Column(Integer, nullable=True)
    incorporation_date = Column(Date, nullable=True)

    # Geographic
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Government Structure
    government_type = Column(String(50), nullable=True)  # e.g., "City Council-Manager"
    fiscal_year_end_month = Column(Integer, nullable=False, default=6)  # Most CA cities: June
    fiscal_year_end_day = Column(Integer, nullable=False, default=30)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_charter_city = Column(Boolean, nullable=True)

    # Bankruptcy History (if applicable)
    has_bankruptcy_history = Column(Boolean, nullable=False, default=False)
    bankruptcy_filing_date = Column(Date, nullable=True)
    bankruptcy_exit_date = Column(Date, nullable=True)
    bankruptcy_chapter = Column(String(20), nullable=True)  # "Chapter 9"
    bankruptcy_notes = Column(Text, nullable=True)

    # Official Website & Contact
    website_url = Column(String(255), nullable=True)
    finance_department_url = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Relationships
    fiscal_years = relationship("FiscalYear", back_populates="city", lazy="dynamic")

    def __repr__(self) -> str:
        """String representation of City."""
        return f"<City(id={self.id}, name='{self.name}', state='{self.state}')>"


class FiscalYear(Base, AuditMixin):
    """
    A single fiscal year for a city.

    Each row represents one year of financial activity.
    Tracks data availability, completeness, and quality for that year.
    """

    __tablename__ = "fiscal_years"
    __table_args__ = (
        UniqueConstraint("city_id", "year", name="uq_fiscal_year_city_year"),
        Index("ix_fiscal_year_city_year", "city_id", "year"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Fiscal Year Identification
    year = Column(Integer, nullable=False)  # Ending year (e.g., 2024 for FY 2023-24)
    start_date = Column(Date, nullable=False)  # Usually July 1
    end_date = Column(Date, nullable=False)  # Usually June 30

    # Data Availability - CAFR
    cafr_available = Column(Boolean, nullable=False, default=False)
    cafr_url = Column(String(500), nullable=True)
    cafr_publish_date = Column(Date, nullable=True)
    cafr_audit_firm = Column(String(255), nullable=True)
    cafr_audit_opinion = Column(String(50), nullable=True)  # Unqualified, Qualified, etc.

    # Data Availability - Budget
    budget_available = Column(Boolean, nullable=False, default=False)
    budget_url = Column(String(500), nullable=True)
    budget_adopted_date = Column(Date, nullable=True)

    # Data Availability - CalPERS
    calpers_valuation_available = Column(Boolean, nullable=False, default=False)
    calpers_valuation_url = Column(String(500), nullable=True)
    calpers_valuation_date = Column(Date, nullable=True)

    # Data Completeness Flags
    revenues_complete = Column(Boolean, nullable=False, default=False)
    expenditures_complete = Column(Boolean, nullable=False, default=False)
    pension_data_complete = Column(Boolean, nullable=False, default=False)

    # Data Quality Score (0-100)
    data_quality_score = Column(Integer, nullable=True)
    data_quality_notes = Column(Text, nullable=True)

    # Validation
    validated_by = Column(String(255), nullable=True)  # Person or system
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    city = relationship("City", back_populates="fiscal_years")
    revenues = relationship("Revenue", back_populates="fiscal_year", lazy="dynamic")
    expenditures = relationship("Expenditure", back_populates="fiscal_year", lazy="dynamic")
    fund_balances = relationship("FundBalance", back_populates="fiscal_year", lazy="dynamic")
    pension_plans = relationship("PensionPlan", back_populates="fiscal_year", lazy="dynamic")
    risk_scores = relationship("RiskScore", back_populates="fiscal_year", lazy="dynamic")

    def __repr__(self) -> str:
        """String representation of FiscalYear."""
        return f"<FiscalYear(id={self.id}, city_id={self.city_id}, year={self.year})>"


class DataSource(Base, AuditMixin):
    """
    Catalog of all data sources.

    Tracks where our data comes from for lineage and citation purposes.
    Every piece of data should be traceable to a source.
    """

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)

    # Source Identification
    name = Column(String(255), nullable=False)
    source_type = Column(
        String(50), nullable=False
    )  # CAFR, CalPERS, StateController, Manual
    url = Column(String(500), nullable=True)

    # Source Details
    organization = Column(String(255), nullable=False)  # e.g., "City of Vallejo"
    description = Column(Text, nullable=True)

    # Reliability Assessment
    reliability_rating = Column(String(20), nullable=True)  # High, Medium, Low
    reliability_notes = Column(Text, nullable=True)

    # Access Information
    access_method = Column(
        String(50), nullable=False
    )  # Download, API, Scrape, Manual
    requires_authentication = Column(Boolean, nullable=False, default=False)

    # Update Frequency
    expected_update_frequency = Column(
        String(50), nullable=True
    )  # Annual, Quarterly, etc.
    last_checked_date = Column(Date, nullable=True)
    last_available_date = Column(Date, nullable=True)

    # Relationships
    data_lineage_records = relationship("DataLineage", foreign_keys="DataLineage.source_id")

    def __repr__(self) -> str:
        """String representation of DataSource."""
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class DataLineage(Base, AuditMixin):
    """
    Tracks the provenance of every data point.

    Links data back to original source documents with complete lineage trail.
    Critical for transparency and verification.
    """

    __tablename__ = "data_lineage"
    __table_args__ = (Index("ix_data_lineage_record", "table_name", "record_id"),)

    id = Column(Integer, primary_key=True)

    # What data is this about?
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=False)

    # Where did it come from?
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    source_document_url = Column(String(500), nullable=True)
    source_document_page = Column(Integer, nullable=True)
    source_document_section = Column(String(255), nullable=True)

    # How was it extracted?
    extraction_method = Column(
        String(50), nullable=False
    )  # Manual, Automated, API
    extracted_by = Column(String(255), nullable=True)  # Person or system
    extracted_at = Column(DateTime, nullable=False)

    # Validation
    validated = Column(Boolean, nullable=False, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    # Cross-validation
    cross_validated_source_id = Column(
        Integer, ForeignKey("data_sources.id"), nullable=True
    )
    matches_cross_validation = Column(Boolean, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    confidence_level = Column(String(20), nullable=True)  # High, Medium, Low

    # Relationships
    source = relationship("DataSource", foreign_keys=[source_id])
    cross_validation_source = relationship(
        "DataSource", foreign_keys=[cross_validated_source_id]
    )

    def __repr__(self) -> str:
        """String representation of DataLineage."""
        return f"<DataLineage(table={self.table_name}, record_id={self.record_id}, field={self.field_name})>"


# Note: PensionPlan, PensionContribution, PensionProjection, OPEBLiability,
# and PensionAssumptionChange are defined in models/pensions.py
# They are imported via forward reference to avoid circular imports.

# RiskScore will be implemented in models/risk.py when we implement risk scoring.
