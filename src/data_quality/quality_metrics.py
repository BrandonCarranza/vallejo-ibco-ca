"""
Data quality metrics and scoring for fiscal data.

Calculates:
- Completeness: % of expected fields populated
- Consistency: Cross-table reconciliation score
- Validation status: pending → validated → published
- Quality scorecards by fiscal year
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import (
    Expenditure,
    FiscalYear,
    FundBalance,
    PensionPlan,
    Revenue,
)
from src.data_quality.validators import DataQualityValidator, ValidationSeverity


class ValidationStatus(str, Enum):
    """Validation status for fiscal year data."""

    PENDING = "pending"  # Data entered but not reviewed
    IN_REVIEW = "in_review"  # Currently being reviewed
    VALIDATED = "validated"  # Passed validation, ready to publish
    PUBLISHED = "published"  # Published to public API
    NEEDS_CORRECTION = "needs_correction"  # Has critical issues


class QualityMetrics:
    """Quality metrics for a fiscal year."""

    def __init__(
        self,
        fiscal_year: int,
        completeness_score: float,
        consistency_score: float,
        overall_score: float,
        validation_status: ValidationStatus,
        critical_issues: int = 0,
        warnings: int = 0,
        info_items: int = 0,
    ):
        self.fiscal_year = fiscal_year
        self.completeness_score = completeness_score
        self.consistency_score = consistency_score
        self.overall_score = overall_score
        self.validation_status = validation_status
        self.critical_issues = critical_issues
        self.warnings = warnings
        self.info_items = info_items
        self.calculated_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "fiscal_year": self.fiscal_year,
            "completeness_score": self.completeness_score,
            "consistency_score": self.consistency_score,
            "overall_score": self.overall_score,
            "validation_status": self.validation_status.value,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "info_items": self.info_items,
            "calculated_at": self.calculated_at.isoformat(),
        }

    def can_publish(self) -> bool:
        """Determine if data quality is sufficient for publishing."""
        return (
            self.critical_issues == 0
            and self.overall_score >= 95.0
            and self.validation_status != ValidationStatus.NEEDS_CORRECTION
        )


class QualityMetricsCalculator:
    """Calculate data quality metrics for fiscal years."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = DataQualityValidator(db)

    def calculate_metrics(self, fiscal_year: FiscalYear) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for a fiscal year.

        Args:
            fiscal_year: FiscalYear to analyze

        Returns:
            QualityMetrics object with scores and status
        """
        # Run validation
        alerts = self.validator.validate_fiscal_year(fiscal_year)

        # Count alerts by severity
        alert_summary = self.validator.get_alert_summary()

        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(fiscal_year)

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(fiscal_year, alerts)

        # Calculate overall quality score
        overall_score = self._calculate_overall_score(
            completeness_score, consistency_score, alert_summary
        )

        # Determine validation status
        validation_status = self._determine_validation_status(
            alert_summary, overall_score, fiscal_year
        )

        return QualityMetrics(
            fiscal_year=fiscal_year.year,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            overall_score=overall_score,
            validation_status=validation_status,
            critical_issues=alert_summary["critical"],
            warnings=alert_summary["warning"],
            info_items=alert_summary["info"],
        )

    def _calculate_completeness_score(self, fiscal_year: FiscalYear) -> float:
        """
        Calculate data completeness score (0-100).

        Checks for presence of:
        - Revenues
        - Expenditures
        - Fund balance
        - Pension plans (optional, weighted lower)
        """
        max_points = 100
        points = 0

        # Check revenues (35 points)
        revenue_count = (
            self.db.query(Revenue)
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if revenue_count > 0:
            points += 35

        # Check expenditures (35 points)
        expenditure_count = (
            self.db.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if expenditure_count > 0:
            points += 35

        # Check fund balance (20 points)
        fund_balance = (
            self.db.query(FundBalance)
            .filter(FundBalance.fiscal_year_id == fiscal_year.id)
            .first()
        )
        if fund_balance:
            points += 20

        # Check pension data (10 points)
        pension_count = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if pension_count > 0:
            points += 10

        return (points / max_points) * 100

    def _calculate_consistency_score(
        self, fiscal_year: FiscalYear, alerts: List
    ) -> float:
        """
        Calculate data consistency score (0-100).

        Based on:
        - Fund balance reconciliation
        - Absence of critical data issues
        - Reasonable ranges for all values
        """
        max_points = 100
        points = max_points

        # Deduct points for each alert
        for alert in alerts:
            if alert.severity == ValidationSeverity.CRITICAL:
                points -= 20  # Critical issues heavily penalized
            elif alert.severity == ValidationSeverity.WARNING:
                points -= 5  # Warnings lightly penalized
            # INFO alerts don't reduce score

        # Ensure score doesn't go below 0
        points = max(0, points)

        return points

    def _calculate_overall_score(
        self, completeness: float, consistency: float, alert_summary: Dict[str, int]
    ) -> float:
        """
        Calculate overall quality score (0-100).

        Weighted combination of:
        - Completeness: 40%
        - Consistency: 40%
        - Alert penalty: 20%
        """
        # Base score from completeness and consistency
        base_score = (completeness * 0.4) + (consistency * 0.4)

        # Alert penalty (max 20 points)
        alert_penalty = min(
            20,
            (alert_summary["critical"] * 10) + (alert_summary["warning"] * 2),
        )

        # Calculate final score
        overall = base_score + (20 - alert_penalty)

        return round(max(0, min(100, overall)), 1)

    def _determine_validation_status(
        self, alert_summary: Dict[str, int], overall_score: float, fiscal_year: FiscalYear
    ) -> ValidationStatus:
        """
        Determine validation status based on quality metrics.

        Logic:
        - NEEDS_CORRECTION: Has critical issues
        - VALIDATED: Score >= 95% and no critical issues
        - IN_REVIEW: Score >= 80% but has warnings
        - PENDING: Everything else
        """
        # Check fiscal year validation flag if exists
        if hasattr(fiscal_year, "validation_status") and fiscal_year.validation_status:
            return ValidationStatus(fiscal_year.validation_status)

        # Determine based on quality metrics
        if alert_summary["critical"] > 0:
            return ValidationStatus.NEEDS_CORRECTION

        if overall_score >= 95.0:
            return ValidationStatus.VALIDATED

        if overall_score >= 80.0 and alert_summary["warning"] > 0:
            return ValidationStatus.IN_REVIEW

        return ValidationStatus.PENDING

    def calculate_metrics_for_city(
        self, city_id: int
    ) -> Dict[int, QualityMetrics]:
        """
        Calculate quality metrics for all fiscal years of a city.

        Args:
            city_id: City ID

        Returns:
            Dictionary mapping fiscal year to QualityMetrics
        """
        fiscal_years = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id)
            .order_by(FiscalYear.year)
            .all()
        )

        metrics_by_year = {}
        for fy in fiscal_years:
            metrics = self.calculate_metrics(fy)
            metrics_by_year[fy.year] = metrics

        return metrics_by_year

    def get_summary_statistics(
        self, metrics_list: List[QualityMetrics]
    ) -> Dict[str, any]:
        """
        Get summary statistics across multiple fiscal years.

        Args:
            metrics_list: List of QualityMetrics objects

        Returns:
            Summary statistics dictionary
        """
        if not metrics_list:
            return {
                "total_years": 0,
                "avg_completeness": 0.0,
                "avg_consistency": 0.0,
                "avg_overall_score": 0.0,
                "total_critical_issues": 0,
                "total_warnings": 0,
                "years_validated": 0,
                "years_needing_correction": 0,
            }

        return {
            "total_years": len(metrics_list),
            "avg_completeness": round(
                sum(m.completeness_score for m in metrics_list) / len(metrics_list), 1
            ),
            "avg_consistency": round(
                sum(m.consistency_score for m in metrics_list) / len(metrics_list), 1
            ),
            "avg_overall_score": round(
                sum(m.overall_score for m in metrics_list) / len(metrics_list), 1
            ),
            "total_critical_issues": sum(m.critical_issues for m in metrics_list),
            "total_warnings": sum(m.warnings for m in metrics_list),
            "years_validated": sum(
                1
                for m in metrics_list
                if m.validation_status == ValidationStatus.VALIDATED
            ),
            "years_needing_correction": sum(
                1
                for m in metrics_list
                if m.validation_status == ValidationStatus.NEEDS_CORRECTION
            ),
        }
