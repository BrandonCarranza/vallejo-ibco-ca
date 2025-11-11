"""
Data quality validation rules for manually-entered fiscal data.

Implements comprehensive validation framework to catch:
- Transcription errors (typos, magnitude errors)
- Math errors (fund balance reconciliation)
- Year-over-year anomalies
- Missing data
- Temporal inconsistencies
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import (
    City,
    Expenditure,
    FiscalYear,
    FundBalance,
    PensionContribution,
    PensionPlan,
    Revenue,
)


class ValidationSeverity(str, Enum):
    """Validation alert severity levels."""

    CRITICAL = "critical"  # Missing core data, reconciliation failures
    WARNING = "warning"  # Anomalous changes, potential issues
    INFO = "info"  # Data entered but not reviewed


class ValidationAlert:
    """Represents a data quality validation alert."""

    def __init__(
        self,
        severity: ValidationSeverity,
        category: str,
        fiscal_year: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recommendation: Optional[str] = None,
    ):
        self.severity = severity
        self.category = category
        self.fiscal_year = fiscal_year
        self.message = message
        self.details = details or {}
        self.recommendation = recommendation
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "fiscal_year": self.fiscal_year,
            "message": self.message,
            "details": self.details,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class DataQualityValidator:
    """
    Comprehensive data quality validator for manually-entered fiscal data.

    Implements validation rules across multiple dimensions:
    - Type and range checks
    - Cross-table reconciliation
    - Year-over-year anomaly detection
    - Temporal consistency
    """

    # Validation thresholds
    RECONCILIATION_TOLERANCE = Decimal("0.02")  # 2%
    ANOMALY_THRESHOLD = Decimal("0.25")  # 25% change flags anomaly
    FUNDED_RATIO_MIN = Decimal("0.0")
    FUNDED_RATIO_MAX = Decimal("1.50")  # 150%
    CONTRIBUTION_RATE_MAX = Decimal("0.50")  # 50% of payroll

    def __init__(self, db: Session):
        """Initialize validator with database session."""
        self.db = db
        self.alerts: List[ValidationAlert] = []

    def validate_fiscal_year(self, fiscal_year: FiscalYear) -> List[ValidationAlert]:
        """
        Run all validation rules for a fiscal year.

        Args:
            fiscal_year: FiscalYear to validate

        Returns:
            List of validation alerts
        """
        self.alerts = []

        # Core data completeness
        self._validate_data_completeness(fiscal_year)

        # Financial validations
        self._validate_financial_data(fiscal_year)

        # Pension validations
        self._validate_pension_data(fiscal_year)

        # Cross-table reconciliation
        self._validate_fund_balance_reconciliation(fiscal_year)

        # Year-over-year anomalies
        self._validate_temporal_consistency(fiscal_year)

        return self.alerts

    def _validate_data_completeness(self, fiscal_year: FiscalYear) -> None:
        """Validate that core data is present."""
        # Check for revenues
        revenue_count = (
            self.db.query(Revenue)
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if revenue_count == 0:
            self.alerts.append(
                ValidationAlert(
                    severity=ValidationSeverity.CRITICAL,
                    category="completeness",
                    fiscal_year=fiscal_year.year,
                    message="No revenue data found",
                    details={"table": "revenues", "count": 0},
                    recommendation="Import revenue data from CAFR",
                )
            )

        # Check for expenditures
        expenditure_count = (
            self.db.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if expenditure_count == 0:
            self.alerts.append(
                ValidationAlert(
                    severity=ValidationSeverity.CRITICAL,
                    category="completeness",
                    fiscal_year=fiscal_year.year,
                    message="No expenditure data found",
                    details={"table": "expenditures", "count": 0},
                    recommendation="Import expenditure data from CAFR",
                )
            )

        # Check for fund balance
        fund_balance = (
            self.db.query(FundBalance)
            .filter(FundBalance.fiscal_year_id == fiscal_year.id)
            .first()
        )
        if not fund_balance:
            self.alerts.append(
                ValidationAlert(
                    severity=ValidationSeverity.CRITICAL,
                    category="completeness",
                    fiscal_year=fiscal_year.year,
                    message="No fund balance data found",
                    details={"table": "fund_balances"},
                    recommendation="Import fund balance data from CAFR",
                )
            )

        # Check for pension data (warning, not critical)
        pension_count = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fiscal_year.id)
            .count()
        )
        if pension_count == 0:
            self.alerts.append(
                ValidationAlert(
                    severity=ValidationSeverity.WARNING,
                    category="completeness",
                    fiscal_year=fiscal_year.year,
                    message="No pension plan data found",
                    details={"table": "pension_plans", "count": 0},
                    recommendation="Import pension data from CalPERS valuation",
                )
            )

    def _validate_financial_data(self, fiscal_year: FiscalYear) -> None:
        """Validate financial data ranges and types."""
        # Validate revenues
        revenues = (
            self.db.query(Revenue)
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .all()
        )

        for revenue in revenues:
            # Check for negative revenues
            if revenue.amount < 0:
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.CRITICAL,
                        category="financial",
                        fiscal_year=fiscal_year.year,
                        message=f"Negative revenue amount: {revenue.category.name if revenue.category else 'Unknown'}",
                        details={
                            "revenue_id": revenue.id,
                            "amount": float(revenue.amount),
                            "category": revenue.category.name if revenue.category else None,
                        },
                        recommendation="Verify revenue amount in source document",
                    )
                )

            # Check for suspiciously large amounts (likely magnitude error)
            if revenue.amount > Decimal("10000000000"):  # $10 billion
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.WARNING,
                        category="financial",
                        fiscal_year=fiscal_year.year,
                        message=f"Unusually large revenue amount: {revenue.category.name if revenue.category else 'Unknown'}",
                        details={
                            "revenue_id": revenue.id,
                            "amount": float(revenue.amount),
                            "category": revenue.category.name if revenue.category else None,
                        },
                        recommendation="Check if amount should be in thousands/millions (possible magnitude error)",
                    )
                )

        # Validate expenditures
        expenditures = (
            self.db.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .all()
        )

        for expenditure in expenditures:
            # Check for negative expenditures
            if expenditure.amount < 0:
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.CRITICAL,
                        category="financial",
                        fiscal_year=fiscal_year.year,
                        message=f"Negative expenditure amount: {expenditure.category.name if expenditure.category else 'Unknown'}",
                        details={
                            "expenditure_id": expenditure.id,
                            "amount": float(expenditure.amount),
                            "category": expenditure.category.name if expenditure.category else None,
                        },
                        recommendation="Verify expenditure amount in source document",
                    )
                )

            # Check for suspiciously large amounts
            if expenditure.amount > Decimal("10000000000"):  # $10 billion
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.WARNING,
                        category="financial",
                        fiscal_year=fiscal_year.year,
                        message=f"Unusually large expenditure amount: {expenditure.category.name if expenditure.category else 'Unknown'}",
                        details={
                            "expenditure_id": expenditure.id,
                            "amount": float(expenditure.amount),
                            "category": expenditure.category.name if expenditure.category else None,
                        },
                        recommendation="Check if amount should be in thousands/millions (possible magnitude error)",
                    )
                )

    def _validate_pension_data(self, fiscal_year: FiscalYear) -> None:
        """Validate pension data ranges."""
        pension_plans = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fiscal_year.id)
            .all()
        )

        for plan in pension_plans:
            # Validate funded ratio
            if plan.funded_ratio is not None:
                if plan.funded_ratio < self.FUNDED_RATIO_MIN or plan.funded_ratio > self.FUNDED_RATIO_MAX:
                    self.alerts.append(
                        ValidationAlert(
                            severity=ValidationSeverity.WARNING,
                            category="pension",
                            fiscal_year=fiscal_year.year,
                            message=f"Funded ratio out of expected range: {plan.plan_name}",
                            details={
                                "plan_id": plan.id,
                                "plan_name": plan.plan_name,
                                "funded_ratio": float(plan.funded_ratio),
                                "expected_range": f"{float(self.FUNDED_RATIO_MIN):.0%} - {float(self.FUNDED_RATIO_MAX):.0%}",
                            },
                            recommendation="Verify funded ratio in CalPERS valuation report",
                        )
                    )

            # Validate UAL is non-negative
            if plan.unfunded_liability is not None and plan.unfunded_liability < 0:
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.WARNING,
                        category="pension",
                        fiscal_year=fiscal_year.year,
                        message=f"Negative unfunded liability: {plan.plan_name}",
                        details={
                            "plan_id": plan.id,
                            "plan_name": plan.plan_name,
                            "unfunded_liability": float(plan.unfunded_liability),
                        },
                        recommendation="Verify UAL calculation (should be positive for underfunded plans)",
                    )
                )

        # Validate contribution rates
        contributions = (
            self.db.query(PensionContribution)
            .filter(PensionContribution.fiscal_year_id == fiscal_year.id)
            .all()
        )

        for contribution in contributions:
            if contribution.contribution_rate is not None:
                if contribution.contribution_rate > self.CONTRIBUTION_RATE_MAX:
                    self.alerts.append(
                        ValidationAlert(
                            severity=ValidationSeverity.WARNING,
                            category="pension",
                            fiscal_year=fiscal_year.year,
                            message=f"Unusually high contribution rate: {contribution.plan_name}",
                            details={
                                "contribution_id": contribution.id,
                                "plan_name": contribution.plan_name,
                                "contribution_rate": float(contribution.contribution_rate),
                            },
                            recommendation="Verify contribution rate in CalPERS valuation (>50% is unusual)",
                        )
                    )

    def _validate_fund_balance_reconciliation(self, fiscal_year: FiscalYear) -> None:
        """Validate fund balance reconciliation formula."""
        # Get fund balance
        fund_balance = (
            self.db.query(FundBalance)
            .filter(FundBalance.fiscal_year_id == fiscal_year.id)
            .first()
        )

        if not fund_balance:
            return  # Already flagged in completeness check

        # Calculate total revenues
        total_revenues = (
            self.db.query(func.sum(Revenue.amount))
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        # Calculate total expenditures
        total_expenditures = (
            self.db.query(func.sum(Expenditure.amount))
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        # Expected ending balance
        expected_ending = (
            fund_balance.beginning_balance + total_revenues - total_expenditures
        )

        # Calculate variance
        variance = abs(fund_balance.ending_balance - expected_ending)
        if fund_balance.ending_balance != 0:
            variance_percent = variance / abs(fund_balance.ending_balance)
        else:
            variance_percent = Decimal("0")

        # Check if variance exceeds tolerance
        if variance_percent > self.RECONCILIATION_TOLERANCE:
            self.alerts.append(
                ValidationAlert(
                    severity=ValidationSeverity.CRITICAL,
                    category="reconciliation",
                    fiscal_year=fiscal_year.year,
                    message="Fund balance reconciliation failure",
                    details={
                        "beginning_balance": float(fund_balance.beginning_balance),
                        "revenues": float(total_revenues),
                        "expenditures": float(total_expenditures),
                        "expected_ending": float(expected_ending),
                        "actual_ending": float(fund_balance.ending_balance),
                        "variance": float(variance),
                        "variance_percent": float(variance_percent),
                    },
                    recommendation=(
                        "Formula: ending = beginning + revenues - expenditures. "
                        "Check for missing transfers, interfund activity, or transcription errors."
                    ),
                )
            )

    def _validate_temporal_consistency(self, fiscal_year: FiscalYear) -> None:
        """Validate year-over-year changes for anomalies."""
        # Get previous fiscal year
        prev_fy = (
            self.db.query(FiscalYear)
            .filter(
                FiscalYear.city_id == fiscal_year.city_id,
                FiscalYear.year == fiscal_year.year - 1,
            )
            .first()
        )

        if not prev_fy:
            # No prior year to compare
            return

        # Compare total revenues
        current_revenues = (
            self.db.query(func.sum(Revenue.amount))
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        prev_revenues = (
            self.db.query(func.sum(Revenue.amount))
            .filter(Revenue.fiscal_year_id == prev_fy.id)
            .scalar()
            or Decimal("0")
        )

        if prev_revenues > 0:
            revenue_change_percent = (current_revenues - prev_revenues) / prev_revenues

            if abs(revenue_change_percent) > self.ANOMALY_THRESHOLD:
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.WARNING,
                        category="anomaly",
                        fiscal_year=fiscal_year.year,
                        message=f"Large year-over-year revenue change: {revenue_change_percent:+.1%}",
                        details={
                            "prior_year": prev_fy.year,
                            "prior_revenues": float(prev_revenues),
                            "current_revenues": float(current_revenues),
                            "change_percent": float(revenue_change_percent),
                        },
                        recommendation=(
                            "Verify this change is accurate. If correct, add annotation "
                            "explaining the cause (e.g., new tax, one-time windfall, etc.)"
                        ),
                    )
                )

        # Compare total expenditures
        current_expenditures = (
            self.db.query(func.sum(Expenditure.amount))
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        prev_expenditures = (
            self.db.query(func.sum(Expenditure.amount))
            .filter(Expenditure.fiscal_year_id == prev_fy.id)
            .scalar()
            or Decimal("0")
        )

        if prev_expenditures > 0:
            expenditure_change_percent = (
                current_expenditures - prev_expenditures
            ) / prev_expenditures

            if abs(expenditure_change_percent) > self.ANOMALY_THRESHOLD:
                self.alerts.append(
                    ValidationAlert(
                        severity=ValidationSeverity.WARNING,
                        category="anomaly",
                        fiscal_year=fiscal_year.year,
                        message=f"Large year-over-year expenditure change: {expenditure_change_percent:+.1%}",
                        details={
                            "prior_year": prev_fy.year,
                            "prior_expenditures": float(prev_expenditures),
                            "current_expenditures": float(current_expenditures),
                            "change_percent": float(expenditure_change_percent),
                        },
                        recommendation=(
                            "Verify this change is accurate. If correct, add annotation "
                            "explaining the cause (e.g., major capital project, service cuts, etc.)"
                        ),
                    )
                )

    def get_alerts_by_severity(
        self, severity: ValidationSeverity
    ) -> List[ValidationAlert]:
        """Get all alerts of a specific severity level."""
        return [alert for alert in self.alerts if alert.severity == severity]

    def has_critical_alerts(self) -> bool:
        """Check if any critical alerts exist."""
        return any(alert.severity == ValidationSeverity.CRITICAL for alert in self.alerts)

    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by severity."""
        return {
            "critical": len(self.get_alerts_by_severity(ValidationSeverity.CRITICAL)),
            "warning": len(self.get_alerts_by_severity(ValidationSeverity.WARNING)),
            "info": len(self.get_alerts_by_severity(ValidationSeverity.INFO)),
            "total": len(self.alerts),
        }
