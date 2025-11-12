"""
Pydantic schemas for stakeholder communication API.
"""
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.database.models.stakeholders import (
    AlertSeverity,
    NotificationStatus,
    NotificationType,
    SubscriberCategory,
    SubscriberStatus,
)


# ============================================================================
# Subscriber Schemas
# ============================================================================


class SubscriberBase(BaseModel):
    """Base subscriber schema."""

    email: EmailStr = Field(..., description="Email address")
    name: Optional[str] = Field(None, max_length=255, description="Name (person or organization)")
    organization: Optional[str] = Field(None, max_length=255, description="Organization name")
    category: SubscriberCategory = Field(..., description="Subscriber category")

    subscribed_to_quarterly_updates: bool = Field(default=True, description="Subscribe to quarterly updates")
    subscribed_to_alerts: bool = Field(default=True, description="Subscribe to automated alerts")
    subscribed_to_press_releases: bool = Field(default=True, description="Subscribe to press releases")

    city_id: Optional[int] = Field(None, description="Filter to specific city only")
    notes: Optional[str] = Field(None, description="Internal notes")


class SubscriberCreate(SubscriberBase):
    """Schema for creating a subscriber."""

    pass


class SubscriberUpdate(BaseModel):
    """Schema for updating a subscriber."""

    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)
    category: Optional[SubscriberCategory] = None
    status: Optional[SubscriberStatus] = None

    subscribed_to_quarterly_updates: Optional[bool] = None
    subscribed_to_alerts: Optional[bool] = None
    subscribed_to_press_releases: Optional[bool] = None

    city_id: Optional[int] = None
    notes: Optional[str] = None


class SubscriberResponse(SubscriberBase):
    """Schema for subscriber response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SubscriberStatus

    subscription_date: datetime
    unsubscribe_date: Optional[datetime] = None

    last_email_sent: Optional[datetime] = None
    email_bounce_count: int

    created_at: datetime
    updated_at: datetime


class SubscriberListResponse(BaseModel):
    """Paginated list of subscribers."""

    subscribers: List[SubscriberResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UnsubscribeRequest(BaseModel):
    """Request to unsubscribe."""

    token: str = Field(..., description="Unsubscribe token from email")


# ============================================================================
# Alert Rule Schemas
# ============================================================================


class AlertRuleBase(BaseModel):
    """Base alert rule schema."""

    rule_name: str = Field(..., max_length=100, description="Unique rule name")
    description: str = Field(..., description="Rule description")
    notification_type: NotificationType = Field(..., description="Type of notification")

    metric_name: Optional[str] = Field(None, max_length=100, description="Metric to monitor")
    threshold_value: Optional[Decimal] = Field(None, description="Threshold value for alert")
    change_threshold: Optional[Decimal] = Field(None, description="Minimum change to trigger")
    direction: Optional[str] = Field(None, max_length=20, description="increase, decrease, or either")

    severity: AlertSeverity = Field(default=AlertSeverity.INFO, description="Alert severity")
    message_template: Optional[str] = Field(None, description="Message template")

    city_id: Optional[int] = Field(None, description="Apply to specific city only")

    is_enabled: bool = Field(default=True, description="Is rule enabled")
    cooldown_hours: int = Field(default=24, ge=0, description="Cooldown period in hours")


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating an alert rule."""

    pass


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""

    description: Optional[str] = None
    notification_type: Optional[NotificationType] = None

    metric_name: Optional[str] = Field(None, max_length=100)
    threshold_value: Optional[Decimal] = None
    change_threshold: Optional[Decimal] = None
    direction: Optional[str] = Field(None, max_length=20)

    severity: Optional[AlertSeverity] = None
    message_template: Optional[str] = None

    city_id: Optional[int] = None

    is_enabled: Optional[bool] = None
    cooldown_hours: Optional[int] = Field(None, ge=0)


class AlertRuleResponse(AlertRuleBase):
    """Schema for alert rule response."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    last_triggered_at: Optional[datetime] = None
    last_triggered_value: Optional[Decimal] = None

    created_at: datetime
    updated_at: datetime


class AlertRuleListResponse(BaseModel):
    """List of alert rules."""

    rules: List[AlertRuleResponse]
    total: int


# ============================================================================
# Notification Schemas
# ============================================================================


class NotificationBase(BaseModel):
    """Base notification schema."""

    notification_type: NotificationType = Field(..., description="Notification type")
    severity: AlertSeverity = Field(default=AlertSeverity.INFO, description="Severity")

    subject: str = Field(..., max_length=500, description="Email subject")
    message_text: str = Field(..., description="Plain text message")
    message_html: Optional[str] = Field(None, description="HTML message (optional)")

    city_id: Optional[int] = Field(None, description="Related city")
    alert_rule_id: Optional[int] = Field(None, description="Alert rule that triggered")

    trigger_value: Optional[Decimal] = Field(None, description="Value that triggered alert")
    previous_value: Optional[Decimal] = Field(None, description="Previous value")


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    subscriber_id: int = Field(..., description="Subscriber ID")


class NotificationResponse(NotificationBase):
    """Schema for notification response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subscriber_id: int

    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivery_error: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Alert & Communication Schemas
# ============================================================================


class MetricChange(BaseModel):
    """Schema for reporting a metric change."""

    city_id: int = Field(..., description="City ID")
    metric_name: str = Field(..., description="Metric name (e.g., 'overall_risk_score')")
    current_value: Decimal = Field(..., description="Current metric value")
    previous_value: Optional[Decimal] = Field(None, description="Previous value (for change detection)")

    fiscal_year: Optional[int] = Field(None, description="Fiscal year (if applicable)")


class AlertPreview(BaseModel):
    """Preview of alerts that would be triggered."""

    rule_id: int
    rule_name: str
    notification_type: NotificationType
    severity: AlertSeverity
    would_trigger: bool
    reason: str
    affected_subscribers: int


class AlertsTriggeredResponse(BaseModel):
    """Response after checking/triggering alerts."""

    metric_change: MetricChange
    alerts_checked: int
    alerts_triggered: int
    notifications_queued: int
    previews: List[AlertPreview]


class QuarterlyUpdateRequest(BaseModel):
    """Request to send quarterly update."""

    city_id: int = Field(..., description="City ID")
    quarter: int = Field(..., ge=1, le=4, description="Quarter (1-4)")
    year: int = Field(..., ge=2000, le=2100, description="Year")
    dry_run: bool = Field(default=False, description="Preview without sending")


class QuarterlyUpdateResponse(BaseModel):
    """Response after sending quarterly update."""

    city_id: int
    quarter: int
    year: int
    subscribers_targeted: int
    emails_queued: int
    dry_run: bool
    summary: str


class PressReleaseRequest(BaseModel):
    """Request to generate and send press release."""

    city_id: int = Field(..., description="City ID")
    title: str = Field(..., max_length=500, description="Press release title")
    include_risk_score: bool = Field(default=True, description="Include risk score analysis")
    include_fiscal_cliff: bool = Field(default=True, description="Include fiscal cliff analysis")
    include_decisions: bool = Field(default=False, description="Include recent decisions")
    custom_content: Optional[str] = Field(None, description="Custom content to include")
    dry_run: bool = Field(default=False, description="Preview without sending")


class PressReleaseResponse(BaseModel):
    """Response after generating press release."""

    city_id: int
    title: str
    content_markdown: str
    content_html: str
    subscribers_targeted: int
    emails_queued: int
    dry_run: bool
