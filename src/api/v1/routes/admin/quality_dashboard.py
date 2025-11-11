"""
Admin-only data quality dashboard endpoints.

Provides internal endpoints for monitoring data quality before public release.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.data_quality import (
    DataQualityValidator,
    QualityMetricsCalculator,
    ValidationSeverity,
    ValidationStatus,
)
from src.database.models import City, FiscalYear

router = APIRouter(prefix="/admin/quality", tags=["admin", "quality"])


# Response models
class ValidationAlertResponse(BaseModel):
    """Validation alert response model."""

    severity: str
    category: str
    fiscal_year: int
    message: str
    details: Dict
    recommendation: Optional[str]
    timestamp: str


class QualityMetricsResponse(BaseModel):
    """Quality metrics response model."""

    fiscal_year: int
    completeness_score: float
    consistency_score: float
    overall_score: float
    validation_status: str
    critical_issues: int
    warnings: int
    info_items: int
    calculated_at: str


class QualityDashboardResponse(BaseModel):
    """Complete quality dashboard response."""

    city_id: int
    city_name: str
    metrics: List[QualityMetricsResponse]
    alerts: List[ValidationAlertResponse]
    summary: Dict
    overall_status: str
    can_publish: bool


class FiscalYearQualityResponse(BaseModel):
    """Quality status for a single fiscal year."""

    fiscal_year: int
    metrics: QualityMetricsResponse
    alerts: List[ValidationAlertResponse]
    can_publish: bool


@router.get("/status", response_model=QualityDashboardResponse)
async def get_quality_status(
    city_id: int = Query(..., description="City ID to check quality for"),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive data quality status for a city.

    Returns quality metrics, validation alerts, and publishing readiness
    for all fiscal years of the specified city.

    **This is an admin-only endpoint for internal data validation.**
    """
    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Initialize calculators
    metrics_calculator = QualityMetricsCalculator(db)
    validator = DataQualityValidator(db)

    # Get all fiscal years for city
    fiscal_years = (
        db.query(FiscalYear)
        .filter(FiscalYear.city_id == city_id)
        .order_by(FiscalYear.year.desc())
        .all()
    )

    if not fiscal_years:
        raise HTTPException(
            status_code=404, detail="No fiscal years found for this city"
        )

    # Calculate metrics for each year
    all_metrics = []
    all_alerts = []

    for fy in fiscal_years:
        # Calculate metrics
        metrics = metrics_calculator.calculate_metrics(fy)
        all_metrics.append(metrics)

        # Get validation alerts
        alerts = validator.validate_fiscal_year(fy)
        all_alerts.extend(alerts)

    # Get summary statistics
    summary = metrics_calculator.get_summary_statistics(all_metrics)

    # Determine overall status
    if summary["total_critical_issues"] > 0:
        overall_status = "needs_correction"
    elif summary["years_validated"] == summary["total_years"]:
        overall_status = "ready_to_publish"
    elif summary["avg_overall_score"] >= 80.0:
        overall_status = "in_review"
    else:
        overall_status = "pending"

    # Can publish if all years are validated
    can_publish = all(m.can_publish() for m in all_metrics)

    return QualityDashboardResponse(
        city_id=city.id,
        city_name=city.name,
        metrics=[
            QualityMetricsResponse(**m.to_dict()) for m in all_metrics
        ],
        alerts=[
            ValidationAlertResponse(**a.to_dict()) for a in all_alerts
        ],
        summary=summary,
        overall_status=overall_status,
        can_publish=can_publish,
    )


@router.get("/fiscal-year/{year}", response_model=FiscalYearQualityResponse)
async def get_fiscal_year_quality(
    year: int,
    city_id: int = Query(..., description="City ID"),
    db: Session = Depends(get_db),
):
    """
    Get data quality status for a specific fiscal year.

    Returns detailed quality metrics and validation alerts for a single
    fiscal year.

    **This is an admin-only endpoint for internal data validation.**
    """
    # Get fiscal year
    fiscal_year = (
        db.query(FiscalYear)
        .filter(FiscalYear.city_id == city_id, FiscalYear.year == year)
        .first()
    )

    if not fiscal_year:
        raise HTTPException(
            status_code=404,
            detail=f"Fiscal year {year} not found for city ID {city_id}",
        )

    # Calculate metrics
    metrics_calculator = QualityMetricsCalculator(db)
    metrics = metrics_calculator.calculate_metrics(fiscal_year)

    # Get validation alerts
    validator = DataQualityValidator(db)
    alerts = validator.validate_fiscal_year(fiscal_year)

    return FiscalYearQualityResponse(
        fiscal_year=year,
        metrics=QualityMetricsResponse(**metrics.to_dict()),
        alerts=[ValidationAlertResponse(**a.to_dict()) for a in alerts],
        can_publish=metrics.can_publish(),
    )


@router.get("/alerts", response_model=List[ValidationAlertResponse])
async def get_validation_alerts(
    city_id: int = Query(..., description="City ID"),
    severity: Optional[str] = Query(
        None, description="Filter by severity (critical/warning/info)"
    ),
    category: Optional[str] = Query(
        None, description="Filter by category (completeness/financial/pension/reconciliation/anomaly)"
    ),
    fiscal_year: Optional[int] = Query(None, description="Filter by fiscal year"),
    db: Session = Depends(get_db),
):
    """
    Get validation alerts for a city with optional filters.

    Returns list of validation alerts sorted by severity (critical first).

    **This is an admin-only endpoint for internal data validation.**
    """
    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Get fiscal years (filter if specified)
    query = db.query(FiscalYear).filter(FiscalYear.city_id == city_id)
    if fiscal_year:
        query = query.filter(FiscalYear.year == fiscal_year)

    fiscal_years = query.all()

    if not fiscal_years:
        return []

    # Collect all alerts
    validator = DataQualityValidator(db)
    all_alerts = []

    for fy in fiscal_years:
        alerts = validator.validate_fiscal_year(fy)
        all_alerts.extend(alerts)

    # Apply filters
    filtered_alerts = all_alerts

    if severity:
        try:
            severity_enum = ValidationSeverity(severity.lower())
            filtered_alerts = [
                a for a in filtered_alerts if a.severity == severity_enum
            ]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}. Must be critical, warning, or info",
            )

    if category:
        filtered_alerts = [
            a for a in filtered_alerts if a.category == category.lower()
        ]

    # Sort by severity (critical first) then by fiscal year
    severity_order = {
        ValidationSeverity.CRITICAL: 0,
        ValidationSeverity.WARNING: 1,
        ValidationSeverity.INFO: 2,
    }
    filtered_alerts.sort(
        key=lambda a: (severity_order[a.severity], -a.fiscal_year)
    )

    return [ValidationAlertResponse(**a.to_dict()) for a in filtered_alerts]


@router.get("/summary", response_model=Dict)
async def get_quality_summary(
    city_id: int = Query(..., description="City ID"),
    db: Session = Depends(get_db),
):
    """
    Get high-level quality summary for a city.

    Returns aggregated statistics across all fiscal years.

    **This is an admin-only endpoint for internal data validation.**
    """
    # Get city
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Calculate metrics for all fiscal years
    metrics_calculator = QualityMetricsCalculator(db)
    metrics_by_year = metrics_calculator.calculate_metrics_for_city(city_id)

    if not metrics_by_year:
        raise HTTPException(
            status_code=404, detail="No fiscal years found for this city"
        )

    metrics_list = list(metrics_by_year.values())
    summary = metrics_calculator.get_summary_statistics(metrics_list)

    # Add city info
    summary["city_id"] = city.id
    summary["city_name"] = city.name
    summary["years_analyzed"] = list(metrics_by_year.keys())

    # Add readiness info
    summary["ready_to_publish"] = all(m.can_publish() for m in metrics_list)
    summary["needs_attention"] = [
        year
        for year, metrics in metrics_by_year.items()
        if not metrics.can_publish()
    ]

    return summary
