"""
Database models for tracking data refresh operations and notifications.

Tracks when we check for new source documents (CAFRs, CalPERS valuations),
when notifications are sent to operators, and when data is successfully refreshed.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base

if TYPE_CHECKING:
    from src.database.models.core import City, FiscalYear


class RefreshCheck(Base, AuditMixin):
    """
    Records of automatic checks for new source documents.

    Tracks when we check external sources (Vallejo finance website, CalPERS)
    to see if new reports have been published.
    """

    __tablename__ = "refresh_checks"
    __table_args__ = (
        Index("ix_refresh_check_city_type", "city_id", "check_type"),
        Index("ix_refresh_check_performed_at", "performed_at"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Check Details
    check_type = Column(
        String(50), nullable=False
    )  # "cafr_availability", "calpers_valuation"
    check_frequency = Column(String(20), nullable=False)  # "quarterly", "annual"
    performed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Results
    new_document_found = Column(Boolean, nullable=False, default=False)
    document_url = Column(String(500), nullable=True)
    document_title = Column(String(255), nullable=True)
    fiscal_year = Column(Integer, nullable=True)  # Which FY is this document for?

    # Scraping Details
    source_url_checked = Column(String(500), nullable=False)
    scraping_method = Column(String(100), nullable=True)
    scraping_success = Column(Boolean, nullable=False, default=True)
    scraping_error = Column(Text, nullable=True)

    # Next Steps
    notification_needed = Column(Boolean, nullable=False, default=False)
    notification_sent = Column(Boolean, nullable=False, default=False)
    notification_sent_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    check_metadata = Column(Text, nullable=True)  # JSON string for additional data

    # Relationships
    city = relationship("City")

    def __repr__(self) -> str:
        """String representation of RefreshCheck."""
        return (
            f"<RefreshCheck(id={self.id}, city_id={self.city_id}, "
            f"type='{self.check_type}', new_found={self.new_document_found})>"
        )


class RefreshNotification(Base, AuditMixin):
    """
    Notifications sent to operators about new data to enter.

    Tracks email notifications telling operators that new CAFRs or CalPERS
    valuations are available and need to be manually transcribed.
    """

    __tablename__ = "refresh_notifications"
    __table_args__ = (
        Index("ix_refresh_notification_city_fy", "city_id", "fiscal_year"),
        Index("ix_refresh_notification_sent_at", "sent_at"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)

    # Notification Details
    notification_type = Column(
        String(50), nullable=False
    )  # "cafr_available", "calpers_available"
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_to = Column(String(255), nullable=False)  # Email address(es)

    # Document Information
    document_url = Column(String(500), nullable=False)
    document_title = Column(String(255), nullable=True)
    estimated_entry_time = Column(Integer, nullable=True)  # Minutes

    # Status Tracking
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)

    data_entry_started = Column(Boolean, nullable=False, default=False)
    data_entry_started_at = Column(DateTime, nullable=True)

    data_entry_completed = Column(Boolean, nullable=False, default=False)
    data_entry_completed_at = Column(DateTime, nullable=True)
    data_entry_completed_by = Column(String(255), nullable=True)

    # Follow-up
    reminder_sent = Column(Boolean, nullable=False, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")

    def __repr__(self) -> str:
        """String representation of RefreshNotification."""
        return (
            f"<RefreshNotification(id={self.id}, city_id={self.city_id}, "
            f"type='{self.notification_type}', fy={self.fiscal_year})>"
        )


class RefreshOperation(Base, AuditMixin):
    """
    Complete data refresh operations from entry to validation to analytics.

    Tracks the full lifecycle of a data refresh: manual entry, validation,
    risk recalculation, projection updates, and report generation.
    """

    __tablename__ = "refresh_operations"
    __table_args__ = (
        Index("ix_refresh_operation_city_fy", "city_id", "fiscal_year"),
        Index("ix_refresh_operation_started_at", "started_at"),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)
    fiscal_year = Column(Integer, nullable=False)

    # Operation Type
    operation_type = Column(
        String(50), nullable=False
    )  # "cafr_entry", "calpers_entry", "full_refresh"

    # Timeline
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Manual Entry Phase
    data_entry_started_at = Column(DateTime, nullable=True)
    data_entry_completed_at = Column(DateTime, nullable=True)
    data_entered_by = Column(String(255), nullable=True)

    # Validation Phase
    validation_started_at = Column(DateTime, nullable=True)
    validation_completed_at = Column(DateTime, nullable=True)
    validation_passed = Column(Boolean, nullable=True)
    validation_errors = Column(Text, nullable=True)  # JSON array of errors

    # Risk Scoring Phase
    risk_calculation_started_at = Column(DateTime, nullable=True)
    risk_calculation_completed_at = Column(DateTime, nullable=True)
    risk_calculation_success = Column(Boolean, nullable=True)
    previous_risk_score = Column(Integer, nullable=True)
    new_risk_score = Column(Integer, nullable=True)

    # Projection Phase
    projection_started_at = Column(DateTime, nullable=True)
    projection_completed_at = Column(DateTime, nullable=True)
    projection_success = Column(Boolean, nullable=True)
    previous_fiscal_cliff_year = Column(Integer, nullable=True)
    new_fiscal_cliff_year = Column(Integer, nullable=True)

    # Report Generation Phase
    report_generated = Column(Boolean, nullable=False, default=False)
    report_generated_at = Column(DateTime, nullable=True)
    report_url = Column(String(500), nullable=True)
    report_sent_to_stakeholders = Column(Boolean, nullable=False, default=False)

    # Overall Status
    status = Column(
        String(50), nullable=False, default="in_progress"
    )  # in_progress, completed, failed
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data

    # Relationships
    city = relationship("City")
    fiscal_year_record = relationship("FiscalYear", foreign_keys=[fiscal_year_id])

    def __repr__(self) -> str:
        """String representation of RefreshOperation."""
        return (
            f"<RefreshOperation(id={self.id}, city_id={self.city_id}, "
            f"type='{self.operation_type}', fy={self.fiscal_year}, status='{self.status}')>"
        )


class DataRefreshSchedule(Base, AuditMixin):
    """
    Configuration for automatic refresh check schedules.

    Defines when to check for new documents (quarterly for CAFRs,
    annually for CalPERS valuations).
    """

    __tablename__ = "data_refresh_schedules"
    __table_args__ = (Index("ix_refresh_schedule_city_type", "city_id", "check_type"),)

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Schedule Configuration
    check_type = Column(
        String(50), nullable=False
    )  # "cafr_availability", "calpers_valuation"
    check_frequency = Column(String(20), nullable=False)  # "quarterly", "annual"
    cron_expression = Column(String(100), nullable=True)  # For custom schedules

    # Expected Timing
    expected_publication_months = Column(
        String(100), nullable=True
    )  # e.g., "1,4,7,10" for quarterly
    expected_publication_day = Column(Integer, nullable=True)

    # URLs to Check
    source_url = Column(String(500), nullable=False)
    source_check_method = Column(String(50), nullable=False)  # "scrape_page", "rss_feed"

    # Notification Settings
    send_notifications = Column(Boolean, nullable=False, default=True)
    notification_recipients = Column(Text, nullable=False)  # JSON array of emails

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    last_check_at = Column(DateTime, nullable=True)
    next_check_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")

    def __repr__(self) -> str:
        """String representation of DataRefreshSchedule."""
        return (
            f"<DataRefreshSchedule(id={self.id}, city_id={self.city_id}, "
            f"type='{self.check_type}', active={self.is_active})>"
        )
