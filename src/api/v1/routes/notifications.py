"""
Public API routes for notifications and alerts.

Provides automated alerts when key metrics change and allows
public subscription to updates.
"""
from typing import List, Optional
from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.v1.schemas.stakeholders import (
    AlertPreview,
    AlertsTriggeredResponse,
    MetricChange,
    NotificationListResponse,
    NotificationResponse,
    SubscriberCreate,
    SubscriberResponse,
    UnsubscribeRequest,
)
from src.database.models.stakeholders import (
    AlertRule,
    AlertSeverity,
    Notification,
    NotificationStatus,
    NotificationType,
    Subscriber,
    SubscriberStatus,
)
from src.database.models.core import City

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ============================================================================
# Public Subscription
# ============================================================================


@router.post("/subscribe", response_model=SubscriberResponse, status_code=201)
async def subscribe(
    subscriber: SubscriberCreate,
    db: Session = Depends(get_db)
):
    """
    Subscribe to IBCo notifications.

    **Public endpoint** - No authentication required.

    Subscribe to receive:
    - Quarterly fiscal updates
    - Automated alerts (risk score changes, fiscal cliff updates, etc.)
    - Press releases

    **Privacy:**
    - One-way communication only (no replies expected)
    - Easy unsubscribe link in every email
    - GDPR compliant
    - No third-party sharing

    **Categories:**
    - `media`: Journalists and news organizations
    - `council`: City council members and elected officials
    - `civil_society`: Community groups and nonprofits
    - `researcher`: Academics and policy researchers
    - `public`: General public subscribers
    """
    # Check if email already exists
    existing = db.query(Subscriber).filter(Subscriber.email == subscriber.email).first()

    if existing:
        if existing.status == SubscriberStatus.UNSUBSCRIBED:
            # Re-subscribe
            existing.status = SubscriberStatus.ACTIVE
            existing.subscription_date = datetime.utcnow()
            existing.unsubscribe_date = None

            # Update preferences
            for field, value in subscriber.model_dump().items():
                setattr(existing, field, value)

            db.commit()
            db.refresh(existing)
            return existing
        else:
            raise HTTPException(
                status_code=409,
                detail="Email already subscribed. Check your inbox for existing subscription."
            )

    # Verify city if specified
    if subscriber.city_id:
        city = db.query(City).filter(City.id == subscriber.city_id).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

    # Generate unsubscribe token
    unsubscribe_token = secrets.token_urlsafe(32)

    # Create subscriber
    db_subscriber = Subscriber(
        **subscriber.model_dump(),
        status=SubscriberStatus.ACTIVE,
        unsubscribe_token=unsubscribe_token
    )

    db.add(db_subscriber)
    db.commit()
    db.refresh(db_subscriber)

    # TODO: Send welcome email with unsubscribe link

    return db_subscriber


@router.post("/unsubscribe", status_code=204)
async def unsubscribe(
    request: UnsubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from all notifications.

    **Public endpoint** - No authentication required.

    Uses the unsubscribe token from email footer link.
    One-click unsubscribe compliant with email best practices.
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.unsubscribe_token == request.token
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe token")

    # Unsubscribe
    subscriber.status = SubscriberStatus.UNSUBSCRIBED
    subscriber.unsubscribe_date = datetime.utcnow()

    db.commit()

    return None


# ============================================================================
# Metric Change Alerts
# ============================================================================


@router.post("/check-alerts", response_model=AlertsTriggeredResponse)
async def check_alerts(
    metric_change: MetricChange,
    trigger: bool = Query(
        default=True,
        description="Actually trigger alerts (False = preview only)"
    ),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Check if metric change triggers any alerts.

    **Internal endpoint** - Typically called by system when data updates.

    When key metrics change (risk score, fiscal cliff, pension ratio, etc.),
    this endpoint checks configured alert rules and sends notifications
    to subscribed stakeholders.

    **Use cases:**
    - Risk score increases by 5+ points
    - Fiscal cliff year moves closer (e.g., FY2031 → FY2029)
    - Pension funded ratio drops below 70%
    - New data entered

    **Parameters:**
    - `trigger=true`: Queue notifications for delivery
    - `trigger=false`: Preview which alerts would fire (dry run)

    **Alert Format:**
    - Brief summary of change
    - Link to detailed analysis
    - Comparison to previous value
    - Automated, non-partisan, data-only
    """
    # Verify city exists
    city = db.query(City).filter(City.id == metric_change.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Get active alert rules for this metric/city
    query = db.query(AlertRule).filter(
        AlertRule.is_enabled == True,
        AlertRule.is_deleted == False
    )

    # Filter by metric if specified
    if metric_change.metric_name:
        query = query.filter(AlertRule.metric_name == metric_change.metric_name)

    # Filter by city (either specific city or global rules)
    query = query.filter(
        (AlertRule.city_id == metric_change.city_id) |
        (AlertRule.city_id == None)
    )

    rules = query.all()

    # Check each rule
    alerts_checked = len(rules)
    alerts_triggered = 0
    notifications_queued = 0
    previews = []

    for rule in rules:
        should_trigger = rule.should_trigger(
            current_value=float(metric_change.current_value),
            previous_value=float(metric_change.previous_value) if metric_change.previous_value else None
        )

        # Count active subscribers for this rule
        subscriber_query = db.query(Subscriber).filter(
            Subscriber.status == SubscriberStatus.ACTIVE,
            Subscriber.subscribed_to_alerts == True,
            Subscriber.is_deleted == False
        )

        if rule.city_id:
            # City-specific rule: only subscribers for this city or no city filter
            subscriber_query = subscriber_query.filter(
                (Subscriber.city_id == rule.city_id) |
                (Subscriber.city_id == None)
            )

        affected_subscribers = subscriber_query.count()

        # Generate preview
        if should_trigger:
            reason = f"Triggered: {metric_change.metric_name} changed to {metric_change.current_value}"
            if metric_change.previous_value:
                change = metric_change.current_value - metric_change.previous_value
                reason += f" (change: {change:+.1f})"
        else:
            reason = "Did not meet trigger conditions"

        preview = AlertPreview(
            rule_id=rule.id,
            rule_name=rule.rule_name,
            notification_type=rule.notification_type,
            severity=rule.severity,
            would_trigger=should_trigger,
            reason=reason,
            affected_subscribers=affected_subscribers
        )
        previews.append(preview)

        # Actually trigger if requested
        if should_trigger and trigger:
            alerts_triggered += 1

            # Update rule's last triggered
            rule.last_triggered_at = datetime.utcnow()
            rule.last_triggered_value = metric_change.current_value

            # Queue notifications for subscribers
            subscribers = subscriber_query.all()

            for subscriber in subscribers:
                # Generate message from template
                message = rule.message_template or rule.description
                message = message.format(
                    city_name=city.name,
                    metric_name=metric_change.metric_name,
                    current_value=metric_change.current_value,
                    previous_value=metric_change.previous_value or "N/A",
                    change=metric_change.current_value - (metric_change.previous_value or 0)
                )

                subject = f"IBCo Alert: {rule.rule_name} - {city.name}"

                # Create notification
                notification = Notification(
                    subscriber_id=subscriber.id,
                    notification_type=rule.notification_type,
                    severity=rule.severity,
                    subject=subject,
                    message_text=message,
                    city_id=metric_change.city_id,
                    alert_rule_id=rule.id,
                    trigger_value=metric_change.current_value,
                    previous_value=metric_change.previous_value,
                    status=NotificationStatus.PENDING
                )

                db.add(notification)
                notifications_queued += 1

            db.commit()

            # TODO: Queue background task to actually send emails

    return AlertsTriggeredResponse(
        metric_change=metric_change,
        alerts_checked=alerts_checked,
        alerts_triggered=alerts_triggered,
        notifications_queued=notifications_queued,
        previews=previews
    )


# ============================================================================
# Notification History (Public)
# ============================================================================


@router.get("/recent", response_model=NotificationListResponse)
async def get_recent_notifications(
    city_id: Optional[int] = Query(None, description="Filter by city"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    Get recent public notifications.

    **Public endpoint** - No authentication required.

    View recent alerts and notifications sent by the system.
    Demonstrates transparency about what information is being
    communicated to stakeholders.

    **Use cases:**
    - See what alerts have been triggered recently
    - Understand notification patterns
    - Public accountability for automated communications
    """
    query = db.query(Notification).filter(
        Notification.status == NotificationStatus.SENT,
        Notification.is_deleted == False
    )

    # Apply filters
    if city_id is not None:
        query = query.filter(Notification.city_id == city_id)

    if notification_type is not None:
        query = query.filter(Notification.notification_type == notification_type)

    if severity is not None:
        query = query.filter(Notification.severity == severity)

    # Get total count
    total = query.count()

    # Apply pagination
    notifications = query.order_by(desc(Notification.sent_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific notification.

    **Public endpoint** - No authentication required.

    View details of a sent notification (subscriber email is NOT included
    for privacy).
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.status == NotificationStatus.SENT,
        Notification.is_deleted == False
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification
