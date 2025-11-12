"""
Stakeholder communication and notification models.

Tracks subscribers, automated alerts, and notification history.
Enables transparent communication with media, council, and civil society.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from enum import Enum

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
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base

if TYPE_CHECKING:
    from src.database.models.core import City


class SubscriberCategory(str, Enum):
    """Categories of stakeholders."""

    MEDIA = "media"  # Journalists, news organizations
    COUNCIL = "council"  # City council members, elected officials
    CIVIL_SOCIETY = "civil_society"  # Community groups, nonprofits
    RESEARCHER = "researcher"  # Academics, policy researchers
    PUBLIC = "public"  # General public subscribers
    OTHER = "other"  # Other stakeholders


class SubscriberStatus(str, Enum):
    """Subscriber status."""

    ACTIVE = "active"  # Receiving notifications
    UNSUBSCRIBED = "unsubscribed"  # Opted out
    BOUNCED = "bounced"  # Email bounced
    INACTIVE = "inactive"  # Manually deactivated


class NotificationType(str, Enum):
    """Types of notifications."""

    RISK_SCORE_CHANGE = "risk_score_change"  # Risk score increased/decreased
    FISCAL_CLIFF_CHANGE = "fiscal_cliff_change"  # Fiscal cliff year changed
    PENSION_THRESHOLD = "pension_threshold"  # Pension funded ratio threshold
    NEW_DATA = "new_data"  # New data entered
    QUARTERLY_UPDATE = "quarterly_update"  # Quarterly summary
    PRESS_RELEASE = "press_release"  # Press release issued
    DECISION_OUTCOME = "decision_outcome"  # Decision outcome tracked
    CUSTOM = "custom"  # Custom notification


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"  # Queued for delivery
    SENT = "sent"  # Successfully sent
    FAILED = "failed"  # Delivery failed
    BOUNCED = "bounced"  # Email bounced


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"  # Informational
    WARNING = "warning"  # Warning level
    CRITICAL = "critical"  # Critical alert


class Subscriber(Base, AuditMixin):
    """
    Email subscribers for stakeholder communications.

    Manages subscriber list for automated alerts, quarterly updates,
    and press releases. Privacy-respecting with easy unsubscribe.
    """

    __tablename__ = "subscribers"
    __table_args__ = (
        Index("ix_subscribers_email", "email"),
        Index("ix_subscribers_category", "category"),
        Index("ix_subscribers_status", "status"),
    )

    id = Column(Integer, primary_key=True)

    # Contact Information
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)  # Optional: person/organization name
    organization = Column(String(255), nullable=True)  # Optional: organization

    # Categorization
    category = Column(SQLEnum(SubscriberCategory), nullable=False)
    status = Column(SQLEnum(SubscriberStatus), nullable=False, default=SubscriberStatus.ACTIVE)

    # Subscription Preferences
    subscribed_to_quarterly_updates = Column(Boolean, nullable=False, default=True)
    subscribed_to_alerts = Column(Boolean, nullable=False, default=True)
    subscribed_to_press_releases = Column(Boolean, nullable=False, default=True)

    # City Filter (optional - subscribe to specific city only)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)

    # Privacy & Compliance
    subscription_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    unsubscribe_date = Column(DateTime, nullable=True)
    unsubscribe_token = Column(String(100), nullable=True, unique=True)  # For one-click unsubscribe

    # Email Delivery Tracking
    last_email_sent = Column(DateTime, nullable=True)
    email_bounce_count = Column(Integer, nullable=False, default=0)
    last_bounce_date = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)  # Internal notes about subscriber

    # Relationships
    city = relationship("City", foreign_keys=[city_id])
    notifications = relationship("Notification", back_populates="subscriber", lazy="dynamic")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Subscriber(id={self.id}, email='{self.email}', category='{self.category}')>"

    def is_active(self) -> bool:
        """Check if subscriber should receive emails."""
        return (
            self.status == SubscriberStatus.ACTIVE
            and not self.is_deleted
            and self.email_bounce_count < 3  # Stop after 3 bounces
        )


class AlertRule(Base, AuditMixin):
    """
    Configuration for automated alerts.

    Defines when to send notifications based on metric changes.
    Examples:
    - Risk score increases by 5+ points
    - Fiscal cliff year moves 2+ years closer
    - Pension funded ratio drops below 70%
    """

    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("ix_alert_rules_type", "notification_type"),
        Index("ix_alert_rules_enabled", "is_enabled"),
    )

    id = Column(Integer, primary_key=True)

    # Rule Configuration
    rule_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)

    # Trigger Conditions
    metric_name = Column(String(100), nullable=True)  # e.g., "overall_risk_score"
    threshold_value = Column(Numeric(10, 2), nullable=True)  # e.g., 70.0
    change_threshold = Column(Numeric(10, 2), nullable=True)  # e.g., 5.0 (change by 5 points)
    direction = Column(String(20), nullable=True)  # "increase", "decrease", "either"

    # Alert Configuration
    severity = Column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.INFO)
    message_template = Column(Text, nullable=True)  # Template for alert message

    # Filtering
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)  # Apply to specific city only

    # Control
    is_enabled = Column(Boolean, nullable=False, default=True)
    cooldown_hours = Column(Integer, nullable=False, default=24)  # Don't re-alert within X hours

    # Last Triggered
    last_triggered_at = Column(DateTime, nullable=True)
    last_triggered_value = Column(Numeric(10, 2), nullable=True)

    # Relationships
    city = relationship("City", foreign_keys=[city_id])

    def __repr__(self) -> str:
        """String representation."""
        return f"<AlertRule(id={self.id}, name='{self.rule_name}', type='{self.notification_type}')>"

    def should_trigger(self, current_value: float, previous_value: Optional[float] = None) -> bool:
        """
        Determine if rule should trigger based on values.

        Args:
            current_value: Current metric value
            previous_value: Previous metric value (for change detection)

        Returns:
            True if rule should trigger
        """
        if not self.is_enabled:
            return False

        # Check cooldown
        if self.last_triggered_at:
            hours_since_last = (datetime.utcnow() - self.last_triggered_at).total_seconds() / 3600
            if hours_since_last < self.cooldown_hours:
                return False

        # Check threshold condition
        if self.threshold_value is not None:
            if self.direction == "increase" and current_value <= float(self.threshold_value):
                return False
            if self.direction == "decrease" and current_value >= float(self.threshold_value):
                return False
            if self.direction is None and current_value < float(self.threshold_value):
                return False

        # Check change threshold
        if self.change_threshold is not None and previous_value is not None:
            change = abs(current_value - previous_value)
            if change < float(self.change_threshold):
                return False

            if self.direction == "increase" and current_value <= previous_value:
                return False
            if self.direction == "decrease" and current_value >= previous_value:
                return False

        return True


class Notification(Base, AuditMixin):
    """
    Notification history.

    Tracks all notifications sent to subscribers, including automated alerts,
    quarterly updates, and press releases.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_subscriber", "subscriber_id"),
        Index("ix_notifications_type", "notification_type"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_sent_date", "sent_at"),
    )

    id = Column(Integer, primary_key=True)

    # Recipient
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)

    # Notification Details
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.INFO)

    subject = Column(String(500), nullable=False)
    message_text = Column(Text, nullable=False)  # Plain text version
    message_html = Column(Text, nullable=True)  # HTML version (optional)

    # Context
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)

    # Related Entities (optional)
    risk_score_id = Column(Integer, nullable=True)
    decision_id = Column(Integer, nullable=True)
    fiscal_year_id = Column(Integer, nullable=True)

    # Metadata
    trigger_value = Column(Numeric(10, 2), nullable=True)  # Value that triggered alert
    previous_value = Column(Numeric(10, 2), nullable=True)  # Previous value for comparison

    # Delivery Status
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    sent_at = Column(DateTime, nullable=True)
    delivery_error = Column(Text, nullable=True)

    # Email Tracking
    email_message_id = Column(String(255), nullable=True)  # Email provider message ID
    opened_at = Column(DateTime, nullable=True)  # If tracking opens
    clicked_at = Column(DateTime, nullable=True)  # If tracking link clicks

    # Relationships
    subscriber = relationship("Subscriber", back_populates="notifications")
    city = relationship("City", foreign_keys=[city_id])
    alert_rule = relationship("AlertRule", foreign_keys=[alert_rule_id])

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Notification(id={self.id}, type='{self.notification_type}', "
            f"subscriber_id={self.subscriber_id}, status='{self.status}')>"
        )
