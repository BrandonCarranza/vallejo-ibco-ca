"""
Admin-only data refresh status endpoints.

Provides endpoints for monitoring data refresh operations,
checking for new source documents, and viewing refresh history.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.database.models.core import City, FiscalYear
from src.database.models.refresh import (
    RefreshCheck,
    RefreshNotification,
    RefreshOperation,
)

router = APIRouter(prefix="/admin/refresh", tags=["admin", "refresh"])


# Response models
class RefreshCheckResponse(BaseModel):
    """Refresh check response model."""

    id: int
    check_type: str
    performed_at: datetime
    new_document_found: bool
    document_url: Optional[str] = None
    document_title: Optional[str] = None
    fiscal_year: Optional[int] = None
    notification_sent: bool


class RefreshNotificationResponse(BaseModel):
    """Refresh notification response model."""

    id: int
    notification_type: str
    fiscal_year: int
    sent_at: datetime
    sent_to: str
    document_url: str
    acknowledged: bool
    data_entry_completed: bool


class RefreshOperationResponse(BaseModel):
    """Refresh operation response model."""

    id: int
    fiscal_year: int
    operation_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    validation_passed: Optional[bool] = None
    risk_score_change: Optional[Dict[str, int]] = None
    fiscal_cliff_change: Optional[Dict[str, int]] = None
    report_generated: bool


class DataCompletenessResponse(BaseModel):
    """Data completeness response model."""

    fiscal_year: int
    cafr_available: bool
    calpers_available: bool
    revenues_complete: bool
    expenditures_complete: bool
    pension_data_complete: bool
    data_quality_score: Optional[int] = None


class RefreshStatusResponse(BaseModel):
    """Complete refresh status response."""

    city_id: int
    city_name: str
    last_cafr_check: Optional[datetime] = None
    last_calpers_check: Optional[datetime] = None
    pending_notifications: int
    in_progress_operations: int
    recent_checks: List[RefreshCheckResponse]
    recent_operations: List[RefreshOperationResponse]
    data_completeness: List[DataCompletenessResponse]
    next_expected_cafr: Optional[str] = None
    next_expected_calpers: Optional[str] = None


class TriggerCheckRequest(BaseModel):
    """Request model for manually triggering a check."""

    check_type: str = Field(
        ..., description="Type of check: 'cafr' or 'calpers'"
    )


@router.get("/status", response_model=RefreshStatusResponse)
async def get_refresh_status(
    city_id: int = Query(..., description="City ID to check refresh status for"),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive data refresh status for a city.

    Shows:
    - When last checks were performed
    - Pending notifications
    - In-progress operations
    - Recent refresh history
    - Data completeness for all fiscal years
    """
    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Get last CAFR check
    last_cafr_check = (
        db.query(RefreshCheck)
        .filter(
            RefreshCheck.city_id == city_id,
            RefreshCheck.check_type == "cafr_availability"
        )
        .order_by(desc(RefreshCheck.performed_at))
        .first()
    )

    # Get last CalPERS check
    last_calpers_check = (
        db.query(RefreshCheck)
        .filter(
            RefreshCheck.city_id == city_id,
            RefreshCheck.check_type == "calpers_valuation"
        )
        .order_by(desc(RefreshCheck.performed_at))
        .first()
    )

    # Count pending notifications
    pending_notifications = (
        db.query(RefreshNotification)
        .filter(
            RefreshNotification.city_id == city_id,
            RefreshNotification.data_entry_completed == False
        )
        .count()
    )

    # Count in-progress operations
    in_progress_operations = (
        db.query(RefreshOperation)
        .filter(
            RefreshOperation.city_id == city_id,
            RefreshOperation.status == "in_progress"
        )
        .count()
    )

    # Get recent checks (last 10)
    recent_checks = (
        db.query(RefreshCheck)
        .filter(RefreshCheck.city_id == city_id)
        .order_by(desc(RefreshCheck.performed_at))
        .limit(10)
        .all()
    )

    # Get recent operations (last 10)
    recent_operations = (
        db.query(RefreshOperation)
        .filter(RefreshOperation.city_id == city_id)
        .order_by(desc(RefreshOperation.started_at))
        .limit(10)
        .all()
    )

    # Get data completeness for all fiscal years
    fiscal_years = (
        db.query(FiscalYear)
        .filter(FiscalYear.city_id == city_id)
        .order_by(desc(FiscalYear.year))
        .all()
    )

    data_completeness = [
        DataCompletenessResponse(
            fiscal_year=fy.year,
            cafr_available=fy.cafr_available,
            calpers_available=fy.calpers_valuation_available,
            revenues_complete=fy.revenues_complete,
            expenditures_complete=fy.expenditures_complete,
            pension_data_complete=fy.pension_data_complete,
            data_quality_score=fy.data_quality_score,
        )
        for fy in fiscal_years
    ]

    # Calculate next expected dates
    # CAFRs typically published quarterly, CalPERS annually in July
    next_expected_cafr = "Next quarterly check (Jan/Apr/Jul/Oct 15th)"
    next_expected_calpers = "Next annual check (July 15th)"

    return RefreshStatusResponse(
        city_id=city_id,
        city_name=city.name,
        last_cafr_check=last_cafr_check.performed_at if last_cafr_check else None,
        last_calpers_check=last_calpers_check.performed_at if last_calpers_check else None,
        pending_notifications=pending_notifications,
        in_progress_operations=in_progress_operations,
        recent_checks=[
            RefreshCheckResponse(
                id=check.id,
                check_type=check.check_type,
                performed_at=check.performed_at,
                new_document_found=check.new_document_found,
                document_url=check.document_url,
                document_title=check.document_title,
                fiscal_year=check.fiscal_year,
                notification_sent=check.notification_sent,
            )
            for check in recent_checks
        ],
        recent_operations=[
            RefreshOperationResponse(
                id=op.id,
                fiscal_year=op.fiscal_year,
                operation_type=op.operation_type,
                status=op.status,
                started_at=op.started_at,
                completed_at=op.completed_at,
                duration_seconds=op.duration_seconds,
                validation_passed=op.validation_passed,
                risk_score_change={
                    "previous": op.previous_risk_score,
                    "new": op.new_risk_score,
                } if op.previous_risk_score and op.new_risk_score else None,
                fiscal_cliff_change={
                    "previous": op.previous_fiscal_cliff_year,
                    "new": op.new_fiscal_cliff_year,
                } if op.previous_fiscal_cliff_year and op.new_fiscal_cliff_year else None,
                report_generated=op.report_generated,
            )
            for op in recent_operations
        ],
        data_completeness=data_completeness,
        next_expected_cafr=next_expected_cafr,
        next_expected_calpers=next_expected_calpers,
    )


@router.get("/operations/{operation_id}", response_model=RefreshOperationResponse)
async def get_operation_details(
    operation_id: int = Path(..., description="Refresh operation ID"),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific refresh operation.
    """
    operation = (
        db.query(RefreshOperation)
        .filter(RefreshOperation.id == operation_id)
        .first()
    )

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return RefreshOperationResponse(
        id=operation.id,
        fiscal_year=operation.fiscal_year,
        operation_type=operation.operation_type,
        status=operation.status,
        started_at=operation.started_at,
        completed_at=operation.completed_at,
        duration_seconds=operation.duration_seconds,
        validation_passed=operation.validation_passed,
        risk_score_change={
            "previous": operation.previous_risk_score,
            "new": operation.new_risk_score,
        } if operation.previous_risk_score and operation.new_risk_score else None,
        fiscal_cliff_change={
            "previous": operation.previous_fiscal_cliff_year,
            "new": operation.new_fiscal_cliff_year,
        } if operation.previous_fiscal_cliff_year and operation.new_fiscal_cliff_year else None,
        report_generated=operation.report_generated,
    )


@router.post("/trigger-check/{city_id}")
async def trigger_manual_check(
    city_id: int = Path(..., description="City ID"),
    request: TriggerCheckRequest = ...,
    db: Session = Depends(get_db),
):
    """
    Manually trigger a check for new source documents.

    Useful for testing or when you know a new document has been published.
    """
    from src.data_pipeline.orchestration.refresh_workflows import DataRefreshOrchestrator

    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    orchestrator = DataRefreshOrchestrator(db)

    if request.check_type.lower() == "cafr":
        result = orchestrator.run_quarterly_check(city_id)
        return {
            "success": True,
            "check_type": "cafr",
            "city": city.name,
            "new_document_found": result["cafr_found"],
            "notification_sent": result["notification_sent"],
        }
    elif request.check_type.lower() == "calpers":
        result = orchestrator.run_annual_check(city_id)
        return {
            "success": True,
            "check_type": "calpers",
            "city": city.name,
            "new_document_found": result["calpers_found"],
            "notification_sent": result["notification_sent"],
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid check_type. Must be 'cafr' or 'calpers'"
        )


@router.post("/trigger-pipeline/{city_id}/{fiscal_year}")
async def trigger_post_entry_pipeline(
    city_id: int = Path(..., description="City ID"),
    fiscal_year: int = Path(..., description="Fiscal year"),
    operation_type: str = Query("cafr_entry", description="Operation type"),
    db: Session = Depends(get_db),
):
    """
    Manually trigger the post-entry pipeline after data has been entered.

    This will:
    1. Validate the newly entered data
    2. Recalculate risk scores
    3. Regenerate financial projections
    4. Generate change report
    """
    from src.data_pipeline.orchestration.refresh_workflows import DataRefreshOrchestrator

    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Get fiscal year
    fy = (
        db.query(FiscalYear)
        .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
        .first()
    )
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    orchestrator = DataRefreshOrchestrator(db)

    try:
        operation = orchestrator.trigger_post_entry_pipeline(
            city_id, fiscal_year, operation_type
        )

        return {
            "success": True,
            "operation_id": operation.id,
            "status": operation.status,
            "validation_passed": operation.validation_passed,
            "risk_calculation_success": operation.risk_calculation_success,
            "projection_success": operation.projection_success,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run post-entry pipeline: {str(e)}"
        )


@router.get("/notifications/{city_id}", response_model=List[RefreshNotificationResponse])
async def get_notifications(
    city_id: int = Path(..., description="City ID"),
    pending_only: bool = Query(False, description="Show only pending notifications"),
    db: Session = Depends(get_db),
):
    """
    Get all refresh notifications for a city.
    """
    query = db.query(RefreshNotification).filter(RefreshNotification.city_id == city_id)

    if pending_only:
        query = query.filter(RefreshNotification.data_entry_completed == False)

    notifications = query.order_by(desc(RefreshNotification.sent_at)).all()

    return [
        RefreshNotificationResponse(
            id=notif.id,
            notification_type=notif.notification_type,
            fiscal_year=notif.fiscal_year,
            sent_at=notif.sent_at,
            sent_to=notif.sent_to,
            document_url=notif.document_url,
            acknowledged=notif.acknowledged,
            data_entry_completed=notif.data_entry_completed,
        )
        for notif in notifications
    ]
