"""
Admin endpoints for manual review and validation workflow.

Provides review queue and validation actions (approve/reject/correct).
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.data_quality.anomaly_detection import AnomalyDetector
from src.database.models.validation import (
    AnomalyFlag,
    ValidationQueueItem,
    ValidationRecord,
)

router = APIRouter(prefix="/admin/validation", tags=["admin", "validation"])


# Request/Response models
class QueueItemResponse(BaseModel):
    """Queue item response."""

    id: int
    table_name: str
    record_id: int
    field_name: str
    entered_value: Optional[str]
    status: str
    severity: str
    flag_reason: Optional[str]
    flag_details: Optional[str]
    prior_year_value: Optional[str]
    entered_by: str
    entered_at: datetime
    city_id: int
    fiscal_year: int
    source_document_url: Optional[str]
    source_document_page: Optional[int]


class AnomalyFlagResponse(BaseModel):
    """Anomaly flag response."""

    id: int
    rule_name: str
    rule_description: str
    severity: str
    entered_value: str
    expected_value: Optional[str]
    prior_year_value: Optional[str]
    deviation_percent: Optional[int]
    context: Optional[str]
    suggested_action: str


class ValidationRequest(BaseModel):
    """Validation action request."""

    action: str = Field(..., description="APPROVE, CORRECT, REJECT, ESCALATE")
    validated_by: str = Field(..., description="Validator name/email")
    validation_notes: str = Field(..., description="Validation notes (required)")
    confidence_adjustment: Optional[int] = Field(None, description="+/- confidence")
    corrected_value: Optional[str] = Field(None, description="Corrected value if CORRECT")
    correction_reason: Optional[str] = Field(None, description="Why corrected")
    escalated_to: Optional[str] = Field(None, description="Escalated to who")


@router.get("/review-queue", response_model=List[QueueItemResponse])
async def get_review_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignment"),
    limit: int = Query(50, description="Max items to return"),
    db: Session = Depends(get_db),
):
    """
    Get validation review queue.

    Returns items pending validation, sorted by severity and age.
    """
    query = db.query(ValidationQueueItem)

    # Apply filters
    if status:
        query = query.filter(ValidationQueueItem.status == status)
    else:
        # By default, only show items needing review
        query = query.filter(ValidationQueueItem.status.in_(["ENTERED", "FLAGGED"]))

    if severity:
        query = query.filter(ValidationQueueItem.severity == severity)

    if city_id:
        query = query.filter(ValidationQueueItem.city_id == city_id)

    if assigned_to:
        query = query.filter(ValidationQueueItem.assigned_to == assigned_to)

    # Order by severity (CRITICAL first) then age (oldest first)
    severity_order = {
        "CRITICAL": 1,
        "WARNING": 2,
        "INFO": 3,
    }

    items = (
        query.order_by(ValidationQueueItem.entered_at)
        .limit(limit)
        .all()
    )

    # Sort by severity in Python
    items.sort(key=lambda x: severity_order.get(x.severity, 99))

    return [
        QueueItemResponse(
            id=item.id,
            table_name=item.table_name,
            record_id=item.record_id,
            field_name=item.field_name,
            entered_value=item.entered_value,
            status=item.status,
            severity=item.severity,
            flag_reason=item.flag_reason,
            flag_details=item.flag_details,
            prior_year_value=item.prior_year_value,
            entered_by=item.entered_by,
            entered_at=item.entered_at,
            city_id=item.city_id,
            fiscal_year=item.fiscal_year,
            source_document_url=item.source_document_url,
            source_document_page=item.source_document_page,
        )
        for item in items
    ]


@router.get("/review-queue/{item_id}")
async def get_queue_item_details(
    item_id: int = Path(..., description="Queue item ID"),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a queue item.

    Includes anomaly flags, validation history, and source document references.
    """
    item = db.query(ValidationQueueItem).filter(ValidationQueueItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Get anomaly flags
    flags = db.query(AnomalyFlag).filter(AnomalyFlag.queue_item_id == item_id).all()

    # Get validation history
    history = (
        db.query(ValidationRecord)
        .filter(ValidationRecord.queue_item_id == item_id)
        .order_by(desc(ValidationRecord.validated_at))
        .all()
    )

    return {
        "item": QueueItemResponse(
            id=item.id,
            table_name=item.table_name,
            record_id=item.record_id,
            field_name=item.field_name,
            entered_value=item.entered_value,
            status=item.status,
            severity=item.severity,
            flag_reason=item.flag_reason,
            flag_details=item.flag_details,
            prior_year_value=item.prior_year_value,
            entered_by=item.entered_by,
            entered_at=item.entered_at,
            city_id=item.city_id,
            fiscal_year=item.fiscal_year,
            source_document_url=item.source_document_url,
            source_document_page=item.source_document_page,
        ),
        "anomaly_flags": [
            AnomalyFlagResponse(
                id=flag.id,
                rule_name=flag.rule_name,
                rule_description=flag.rule_description,
                severity=flag.severity,
                entered_value=flag.entered_value,
                expected_value=flag.expected_value,
                prior_year_value=flag.prior_year_value,
                deviation_percent=flag.deviation_percent,
                context=flag.context,
                suggested_action=flag.suggested_action,
            )
            for flag in flags
        ],
        "validation_history": [
            {
                "action": record.action,
                "validated_by": record.validated_by,
                "validated_at": record.validated_at,
                "validation_notes": record.validation_notes,
                "corrected_value": record.corrected_value,
            }
            for record in history
        ],
    }


@router.post("/validate/{item_id}")
async def validate_item(
    item_id: int = Path(..., description="Queue item ID"),
    request: ValidationRequest = ...,
    db: Session = Depends(get_db),
):
    """
    Validate a queue item (approve/correct/reject/escalate).

    Creates immutable validation record and updates item status.
    """
    item = db.query(ValidationQueueItem).filter(ValidationQueueItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Validate action
    valid_actions = ["APPROVE", "CORRECT", "REJECT", "ESCALATE"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
        )

    # Create validation record (immutable)
    record = ValidationRecord(
        queue_item_id=item_id,
        action=request.action,
        validated_by=request.validated_by,
        validated_at=datetime.utcnow(),
        validation_notes=request.validation_notes,
        confidence_adjustment=request.confidence_adjustment,
        corrected_value=request.corrected_value,
        correction_reason=request.correction_reason,
        escalated_to=request.escalated_to,
    )

    db.add(record)

    # Update queue item status
    if request.action == "APPROVE":
        item.status = "APPROVED"
        # Mark anomaly flags as resolved
        db.query(AnomalyFlag).filter(AnomalyFlag.queue_item_id == item_id).update({
            "resolved": True,
            "resolved_at": datetime.utcnow(),
            "resolved_by": request.validated_by,
            "resolution_notes": request.validation_notes,
        })

    elif request.action == "CORRECT":
        item.status = "CORRECTED"
        item.entered_value = request.corrected_value
        # Mark anomaly flags as resolved
        db.query(AnomalyFlag).filter(AnomalyFlag.queue_item_id == item_id).update({
            "resolved": True,
            "resolved_at": datetime.utcnow(),
            "resolved_by": request.validated_by,
            "resolution_notes": f"Corrected: {request.correction_reason}",
        })

    elif request.action == "REJECT":
        item.status = "REJECTED"

    elif request.action == "ESCALATE":
        item.assigned_to = request.escalated_to
        item.notes = f"Escalated by {request.validated_by}: {request.validation_notes}"

    db.commit()

    # Update lineage confidence if adjusted
    if request.confidence_adjustment:
        from src.database.models.core import DataLineage

        lineage = (
            db.query(DataLineage)
            .filter(
                DataLineage.table_name == item.table_name,
                DataLineage.record_id == item.record_id,
                DataLineage.field_name == item.field_name,
            )
            .first()
        )

        if lineage and lineage.confidence_score:
            lineage.confidence_score = max(
                0, min(100, lineage.confidence_score + request.confidence_adjustment)
            )
            db.commit()

    return {
        "success": True,
        "item_id": item_id,
        "action": request.action,
        "new_status": item.status,
        "validation_record_id": record.id,
    }


@router.get("/stats")
async def get_validation_stats(
    city_id: Optional[int] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
):
    """
    Get validation queue statistics.

    Shows counts by status, severity, and age.
    """
    query = db.query(ValidationQueueItem)

    if city_id:
        query = query.filter(ValidationQueueItem.city_id == city_id)

    # Count by status
    status_counts = {}
    for status in ["ENTERED", "FLAGGED", "APPROVED", "CORRECTED", "PUBLISHED", "REJECTED"]:
        count = query.filter(ValidationQueueItem.status == status).count()
        status_counts[status] = count

    # Count by severity (only pending items)
    severity_counts = {}
    for severity in ["CRITICAL", "WARNING", "INFO"]:
        count = (
            query.filter(ValidationQueueItem.status.in_(["ENTERED", "FLAGGED"]))
            .filter(ValidationQueueItem.severity == severity)
            .count()
        )
        severity_counts[severity] = count

    # Count items needing review
    pending_count = query.filter(
        ValidationQueueItem.status.in_(["ENTERED", "FLAGGED"])
    ).count()

    return {
        "pending_review": pending_count,
        "status_counts": status_counts,
        "severity_counts": severity_counts,
    }
