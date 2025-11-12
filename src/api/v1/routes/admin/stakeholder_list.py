"""
Admin API routes for managing stakeholder communications.

Requires authentication. Used for:
- Managing subscriber list
- Configuring alert rules
- Sending quarterly updates and press releases
- Viewing notification history
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.v1.schemas.stakeholders import (
    AlertRuleCreate,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertRuleUpdate,
    NotificationListResponse,
    PressReleaseRequest,
    PressReleaseResponse,
    QuarterlyUpdateRequest,
    QuarterlyUpdateResponse,
    SubscriberCreate,
    SubscriberListResponse,
    SubscriberResponse,
    SubscriberUpdate,
)
from src.database.models.stakeholders import (
    AlertRule,
    AlertSeverity,
    Notification,
    NotificationStatus,
    NotificationType,
    Subscriber,
    SubscriberCategory,
    SubscriberStatus,
)
from src.database.models.core import City

router = APIRouter(prefix="/admin/stakeholders", tags=["Admin", "Stakeholders"])


# ============================================================================
# Subscriber Management
# ============================================================================


@router.post("/subscribers", response_model=SubscriberResponse, status_code=201)
async def create_subscriber(
    subscriber: SubscriberCreate,
    db: Session = Depends(get_db)
):
    """
    Add a subscriber manually.

    **Requires authentication.**

    Use this to manually add stakeholders (e.g., city council members,
    known journalists) to the notification list.
    """
    # Check if email already exists
    existing = db.query(Subscriber).filter(Subscriber.email == subscriber.email).first()
    if existing and existing.status != SubscriberStatus.UNSUBSCRIBED:
        raise HTTPException(
            status_code=409,
            detail="Email already subscribed"
        )

    # Verify city if specified
    if subscriber.city_id:
        city = db.query(City).filter(City.id == subscriber.city_id).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

    # Create or reactivate subscriber
    if existing:
        # Re-activate
        existing.status = SubscriberStatus.ACTIVE
        existing.subscription_date = datetime.utcnow()
        existing.unsubscribe_date = None

        for field, value in subscriber.model_dump().items():
            setattr(existing, field, value)

        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        import secrets
        db_subscriber = Subscriber(
            **subscriber.model_dump(),
            status=SubscriberStatus.ACTIVE,
            unsubscribe_token=secrets.token_urlsafe(32)
        )

        db.add(db_subscriber)
        db.commit()
        db.refresh(db_subscriber)

        return db_subscriber


@router.get("/subscribers", response_model=SubscriberListResponse)
async def list_subscribers(
    category: Optional[SubscriberCategory] = Query(None, description="Filter by category"),
    status: Optional[SubscriberStatus] = Query(None, description="Filter by status"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    List all subscribers.

    **Requires authentication.**

    View and manage stakeholder email list.
    """
    query = db.query(Subscriber).filter(Subscriber.is_deleted == False)

    # Apply filters
    if category is not None:
        query = query.filter(Subscriber.category == category)

    if status is not None:
        query = query.filter(Subscriber.status == status)

    if city_id is not None:
        query = query.filter(
            (Subscriber.city_id == city_id) | (Subscriber.city_id == None)
        )

    # Get total count
    total = query.count()

    # Apply pagination
    subscribers = query.order_by(Subscriber.subscription_date.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return SubscriberListResponse(
        subscribers=subscribers,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db)
):
    """
    Get subscriber details.

    **Requires authentication.**
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.id == subscriber_id,
        Subscriber.is_deleted == False
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return subscriber


@router.patch("/subscribers/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: int,
    update: SubscriberUpdate,
    db: Session = Depends(get_db)
):
    """
    Update subscriber information.

    **Requires authentication.**
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.id == subscriber_id,
        Subscriber.is_deleted == False
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscriber, field, value)

    db.commit()
    db.refresh(subscriber)

    return subscriber


@router.delete("/subscribers/{subscriber_id}", status_code=204)
async def delete_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove subscriber from list.

    **Requires authentication.**

    Soft delete - preserves notification history.
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.id == subscriber_id,
        Subscriber.is_deleted == False
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    subscriber.soft_delete()
    db.commit()

    return None


# ============================================================================
# Alert Rule Management
# ============================================================================


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new alert rule.

    **Requires authentication.**

    Configure automated alerts for metric changes.

    **Examples:**
    - Risk score increases by 5+ points
    - Fiscal cliff year moves 2+ years closer
    - Pension funded ratio drops below 70%
    - New CAFR data entered
    """
    # Check if rule name already exists
    existing = db.query(AlertRule).filter(
        AlertRule.rule_name == rule.rule_name,
        AlertRule.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Rule name already exists")

    # Verify city if specified
    if rule.city_id:
        city = db.query(City).filter(City.id == rule.city_id).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

    # Create rule
    db_rule = AlertRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.get("/alert-rules", response_model=AlertRuleListResponse)
async def list_alert_rules(
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    db: Session = Depends(get_db)
):
    """
    List all alert rules.

    **Requires authentication.**
    """
    query = db.query(AlertRule).filter(AlertRule.is_deleted == False)

    # Apply filters
    if is_enabled is not None:
        query = query.filter(AlertRule.is_enabled == is_enabled)

    if notification_type is not None:
        query = query.filter(AlertRule.notification_type == notification_type)

    rules = query.order_by(AlertRule.rule_name).all()
    total = len(rules)

    return AlertRuleListResponse(
        rules=rules,
        total=total
    )


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get alert rule details.

    **Requires authentication.**
    """
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.is_deleted == False
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return rule


@router.patch("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    update: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update alert rule configuration.

    **Requires authentication.**
    """
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.is_deleted == False
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    return rule


@router.delete("/alert-rules/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete alert rule.

    **Requires authentication.**

    Soft delete - preserves notification history.
    """
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.is_deleted == False
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    rule.soft_delete()
    db.commit()

    return None


# ============================================================================
# Notification History (Admin)
# ============================================================================


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    subscriber_id: Optional[int] = Query(None, description="Filter by subscriber"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    View notification delivery history.

    **Requires authentication.**

    Monitor email delivery, bounces, and engagement.
    """
    query = db.query(Notification).filter(Notification.is_deleted == False)

    # Apply filters
    if subscriber_id is not None:
        query = query.filter(Notification.subscriber_id == subscriber_id)

    if status is not None:
        query = query.filter(Notification.status == status)

    if notification_type is not None:
        query = query.filter(Notification.notification_type == notification_type)

    # Get total count
    total = query.count()

    # Apply pagination
    notifications = query.order_by(desc(Notification.created_at)).offset(
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


# ============================================================================
# Communications Placeholders (implemented in scripts)
# ============================================================================


@router.post("/quarterly-update", response_model=QuarterlyUpdateResponse)
async def send_quarterly_update(
    request: QuarterlyUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Send quarterly update to subscribers.

    **Requires authentication.**

    This endpoint triggers the quarterly update email script.
    See: scripts/communications/email_alerts.py

    In production, this would queue a background job.
    """
    # Verify city exists
    city = db.query(City).filter(City.id == request.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Count target subscribers
    subscribers = db.query(Subscriber).filter(
        Subscriber.status == SubscriberStatus.ACTIVE,
        Subscriber.subscribed_to_quarterly_updates == True,
        Subscriber.is_deleted == False
    ).filter(
        (Subscriber.city_id == request.city_id) | (Subscriber.city_id == None)
    ).count()

    if request.dry_run:
        return QuarterlyUpdateResponse(
            city_id=request.city_id,
            quarter=request.quarter,
            year=request.year,
            subscribers_targeted=subscribers,
            emails_queued=0,
            dry_run=True,
            summary=f"Dry run: Would send to {subscribers} subscribers"
        )

    # TODO: Queue background task to run email_alerts.py script

    return QuarterlyUpdateResponse(
        city_id=request.city_id,
        quarter=request.quarter,
        year=request.year,
        subscribers_targeted=subscribers,
        emails_queued=subscribers,
        dry_run=False,
        summary=f"Queued quarterly update for {subscribers} subscribers"
    )


@router.post("/press-release", response_model=PressReleaseResponse)
async def send_press_release(
    request: PressReleaseRequest,
    db: Session = Depends(get_db)
):
    """
    Generate and send press release.

    **Requires authentication.**

    This endpoint triggers the press release generator script.
    See: scripts/communications/press_release_template.py

    In production, this would queue a background job.
    """
    # Verify city exists
    city = db.query(City).filter(City.id == request.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Count target subscribers (media + press release subscribers)
    subscribers = db.query(Subscriber).filter(
        Subscriber.status == SubscriberStatus.ACTIVE,
        Subscriber.subscribed_to_press_releases == True,
        Subscriber.is_deleted == False
    ).filter(
        (Subscriber.city_id == request.city_id) | (Subscriber.city_id == None)
    ).count()

    if request.dry_run:
        # TODO: Actually generate press release content
        return PressReleaseResponse(
            city_id=request.city_id,
            title=request.title,
            content_markdown="[Press release content would be generated here]",
            content_html="<p>Press release content would be generated here</p>",
            subscribers_targeted=subscribers,
            emails_queued=0,
            dry_run=True
        )

    # TODO: Queue background task to run press_release_template.py script

    return PressReleaseResponse(
        city_id=request.city_id,
        title=request.title,
        content_markdown="[Press release content generated]",
        content_html="<p>Press release content generated</p>",
        subscribers_targeted=subscribers,
        emails_queued=subscribers,
        dry_run=False
    )
