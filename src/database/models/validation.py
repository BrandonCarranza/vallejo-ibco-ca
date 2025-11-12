"""
Database models for manual review and validation workflow.

Tracks validation states, review queues, anomaly flags, and validation records.
Supports human-in-the-loop validation with peer review and anomaly detection.
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


class ValidationQueueItem(Base, AuditMixin):
    """
    Items pending validation in the review queue.

    Tracks all data that needs human review before being published.
    Items can be newly entered data, flagged anomalies, or reconciliation issues.
    """

    __tablename__ = "validation_queue"
    __table_args__ = (
        Index("ix_validation_queue_status", "status"),
        Index("ix_validation_queue_severity", "severity"),
        Index("ix_validation_queue_city_fy", "city_id", "fiscal_year"),
    )

    id = Column(Integer, primary_key=True)

    # What data needs validation?
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=False)
    entered_value = Column(String(255), nullable=True)

    # Context
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)

    # Who entered it?
    entered_by = Column(String(255), nullable=False)
    entered_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Validation state
    status = Column(
        String(20), nullable=False, default="ENTERED"
    )  # ENTERED, FLAGGED, APPROVED, CORRECTED, PUBLISHED
    severity = Column(
        String(20), nullable=False, default="INFO"
    )  # CRITICAL, WARNING, INFO

    # Why flagged?
    flag_reason = Column(String(255), nullable=True)
    flag_details = Column(Text, nullable=True)

    # Prior value (for comparison)
    prior_year_value = Column(String(255), nullable=True)
    expected_value = Column(String(255), nullable=True)

    # Assignment
    assigned_to = Column(String(255), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Source document reference
    source_document_url = Column(String(500), nullable=True)
    source_document_page = Column(Integer, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    fiscal_year_record = relationship("FiscalYear", foreign_keys=[fiscal_year_id])

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ValidationQueueItem(id={self.id}, status='{self.status}', "
            f"severity='{self.severity}', table='{self.table_name}')>"
        )


class ValidationRecord(Base, AuditMixin):
    """
    Immutable validation records.

    Records every validation action: who validated, what decision,
    when, and why. Never deleted, only appended to.
    """

    __tablename__ = "validation_records"
    __table_args__ = (
        Index("ix_validation_record_queue_item", "queue_item_id"),
        Index("ix_validation_record_validator", "validated_by"),
        Index("ix_validation_record_action", "action"),
    )

    id = Column(Integer, primary_key=True)

    # Link to queue item
    queue_item_id = Column(Integer, ForeignKey("validation_queue.id"), nullable=False)

    # Validation action
    action = Column(String(20), nullable=False)  # APPROVE, CORRECT, REJECT, ESCALATE
    validated_by = Column(String(255), nullable=False)
    validated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Decision details
    validation_notes = Column(Text, nullable=False)
    confidence_adjustment = Column(Integer, nullable=True)  # +/- to confidence score

    # If CORRECT action
    corrected_value = Column(String(255), nullable=True)
    correction_reason = Column(Text, nullable=True)

    # If ESCALATE action
    escalated_to = Column(String(255), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # Relationships
    queue_item = relationship("ValidationQueueItem", backref="validation_records")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ValidationRecord(id={self.id}, action='{self.action}', "
            f"by='{self.validated_by}')>"
        )


class AnomalyFlag(Base, AuditMixin):
    """
    Detected anomalies that triggered validation flags.

    Tracks automated anomaly detection results: what rule was violated,
    how severe, and suggested action.
    """

    __tablename__ = "anomaly_flags"
    __table_args__ = (
        Index("ix_anomaly_flag_queue_item", "queue_item_id"),
        Index("ix_anomaly_flag_rule", "rule_name"),
        Index("ix_anomaly_flag_severity", "severity"),
    )

    id = Column(Integer, primary_key=True)

    # Link to queue item
    queue_item_id = Column(Integer, ForeignKey("validation_queue.id"), nullable=False)

    # Anomaly detection rule
    rule_name = Column(String(100), nullable=False)
    rule_description = Column(Text, nullable=False)

    # Severity
    severity = Column(String(20), nullable=False)  # CRITICAL, WARNING, INFO

    # What was detected?
    entered_value = Column(String(255), nullable=False)
    expected_value = Column(String(255), nullable=True)
    prior_year_value = Column(String(255), nullable=True)
    deviation_percent = Column(Integer, nullable=True)

    # Context
    context = Column(Text, nullable=True)  # Additional context for reviewer

    # Suggested action
    suggested_action = Column(
        String(20), nullable=False
    )  # APPROVE, CORRECT, INVESTIGATE

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    queue_item = relationship("ValidationQueueItem", backref="anomaly_flags")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AnomalyFlag(id={self.id}, rule='{self.rule_name}', "
            f"severity='{self.severity}', resolved={self.resolved})>"
        )


class ValidationRule(Base, AuditMixin):
    """
    Configurable validation rules for anomaly detection.

    Defines rules that trigger automatic flagging of unusual values.
    """

    __tablename__ = "validation_rules"
    __table_args__ = (Index("ix_validation_rule_active", "is_active"),)

    id = Column(Integer, primary_key=True)

    # Rule identification
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_description = Column(Text, nullable=False)
    rule_type = Column(
        String(50), nullable=False
    )  # year_over_year, reconciliation, range_check, formula_check

    # What data does this rule apply to?
    table_name = Column(String(100), nullable=True)  # NULL = applies to all
    field_name = Column(String(100), nullable=True)  # NULL = applies to all fields

    # Rule parameters (JSON)
    parameters = Column(Text, nullable=False)  # JSON string with rule-specific params

    # Severity if violated
    severity = Column(String(20), nullable=False, default="WARNING")

    # Suggested action if violated
    suggested_action = Column(String(20), nullable=False, default="INVESTIGATE")

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=50)  # Higher = run first

    # Notes
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ValidationRule(id={self.id}, name='{self.rule_name}', "
            f"type='{self.rule_type}', active={self.is_active})>"
        )
