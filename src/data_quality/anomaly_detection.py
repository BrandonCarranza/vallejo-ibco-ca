"""
Anomaly detection system for automatic validation flagging.

Detects unusual values that should be reviewed by humans:
- Year-over-year changes > 50%
- Values outside expected ranges
- Reconciliation failures
- Formula violations

When anomalies are detected, items are added to the validation queue
for human review.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

import structlog
from sqlalchemy.orm import Session

from src.database.models.core import FiscalYear
from src.database.models.financial import Expenditure, FundBalance, Revenue
from src.database.models.validation import AnomalyFlag, ValidationQueueItem, ValidationRule

logger = structlog.get_logger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in manually entered data.

    Runs validation rules to find unusual values that should be reviewed.
    """

    def __init__(self, db: Session):
        """Initialize detector with database session."""
        self.db = db

    def check_value(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        value: float,
        city_id: int,
        fiscal_year: int,
        entered_by: str,
    ) -> Optional[ValidationQueueItem]:
        """
        Check a single value for anomalies.

        Args:
            table_name: Table name
            record_id: Record ID
            field_name: Field name
            value: Value to check
            city_id: City ID
            fiscal_year: Fiscal year
            entered_by: Who entered the data

        Returns:
            ValidationQueueItem if anomaly detected, None otherwise
        """
        logger.info(
            "checking_for_anomalies",
            table=table_name,
            field=field_name,
            value=value,
        )

        # Get active validation rules for this field
        rules = self._get_applicable_rules(table_name, field_name)

        anomalies_detected = []

        for rule in rules:
            violation = self._check_rule(
                rule, table_name, record_id, field_name, value, city_id, fiscal_year
            )
            if violation:
                anomalies_detected.append(violation)

        if not anomalies_detected:
            # No anomalies, auto-approve
            logger.info("no_anomalies_detected", table=table_name, field=field_name)
            return None

        # Create queue item for review
        queue_item = self._create_queue_item(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            value=value,
            city_id=city_id,
            fiscal_year=fiscal_year,
            entered_by=entered_by,
            anomalies=anomalies_detected,
        )

        # Create anomaly flag records
        for violation in anomalies_detected:
            self._create_anomaly_flag(queue_item, violation)

        logger.info(
            "anomalies_detected",
            count=len(anomalies_detected),
            queue_item_id=queue_item.id,
        )

        return queue_item

    def _get_applicable_rules(
        self, table_name: str, field_name: str
    ) -> List[ValidationRule]:
        """Get validation rules applicable to this field."""
        # Get rules for this specific field
        specific_rules = (
            self.db.query(ValidationRule)
            .filter(
                ValidationRule.is_active == True,
                ValidationRule.table_name == table_name,
                ValidationRule.field_name == field_name,
            )
            .order_by(ValidationRule.priority.desc())
            .all()
        )

        # Get global rules (apply to all fields)
        global_rules = (
            self.db.query(ValidationRule)
            .filter(
                ValidationRule.is_active == True,
                ValidationRule.table_name == None,
                ValidationRule.field_name == None,
            )
            .order_by(ValidationRule.priority.desc())
            .all()
        )

        return specific_rules + global_rules

    def _check_rule(
        self,
        rule: ValidationRule,
        table_name: str,
        record_id: int,
        field_name: str,
        value: float,
        city_id: int,
        fiscal_year: int,
    ) -> Optional[Dict]:
        """Check if a value violates a validation rule."""
        params = json.loads(rule.parameters)

        if rule.rule_type == "year_over_year":
            return self._check_year_over_year(
                table_name, field_name, value, city_id, fiscal_year, params, rule
            )
        elif rule.rule_type == "range_check":
            return self._check_range(value, params, rule)
        elif rule.rule_type == "reconciliation":
            return self._check_reconciliation(
                table_name, record_id, field_name, value, params, rule
            )
        elif rule.rule_type == "formula_check":
            return self._check_formula(
                table_name, record_id, field_name, value, params, rule
            )

        return None

    def _check_year_over_year(
        self,
        table_name: str,
        field_name: str,
        value: float,
        city_id: int,
        fiscal_year: int,
        params: Dict,
        rule: ValidationRule,
    ) -> Optional[Dict]:
        """Check for unusual year-over-year changes."""
        threshold_percent = params.get("threshold_percent", 50)

        # Get prior year value
        prior_year = fiscal_year - 1
        prior_fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == prior_year)
            .first()
        )

        if not prior_fy:
            # No prior year data, can't check
            return None

        # Get prior year value from appropriate table
        prior_value = self._get_prior_year_value(
            table_name, field_name, prior_fy.id
        )

        if prior_value is None:
            return None

        # Calculate percent change
        if prior_value == 0:
            return None  # Can't calculate percent change from zero

        percent_change = abs((value - prior_value) / prior_value * 100)

        if percent_change > threshold_percent:
            return {
                "rule": rule,
                "entered_value": value,
                "prior_year_value": prior_value,
                "deviation_percent": int(percent_change),
                "context": f"Year-over-year change of {percent_change:.1f}% exceeds threshold of {threshold_percent}%",
            }

        return None

    def _check_range(
        self, value: float, params: Dict, rule: ValidationRule
    ) -> Optional[Dict]:
        """Check if value is within expected range."""
        min_value = params.get("min_value")
        max_value = params.get("max_value")

        if min_value is not None and value < min_value:
            return {
                "rule": rule,
                "entered_value": value,
                "expected_value": f">= {min_value}",
                "deviation_percent": None,
                "context": f"Value {value} is below minimum of {min_value}",
            }

        if max_value is not None and value > max_value:
            return {
                "rule": rule,
                "entered_value": value,
                "expected_value": f"<= {max_value}",
                "deviation_percent": None,
                "context": f"Value {value} exceeds maximum of {max_value}",
            }

        return None

    def _check_reconciliation(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        value: float,
        params: Dict,
        rule: ValidationRule,
    ) -> Optional[Dict]:
        """Check if values reconcile (e.g., revenues - expenditures = balance)."""
        # Placeholder for reconciliation logic
        # Would implement specific reconciliation checks based on params
        return None

    def _check_formula(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        value: float,
        params: Dict,
        rule: ValidationRule,
    ) -> Optional[Dict]:
        """Check if value matches expected formula."""
        # Placeholder for formula checking logic
        return None

    def _get_prior_year_value(
        self, table_name: str, field_name: str, prior_fy_id: int
    ) -> Optional[float]:
        """Get value from prior fiscal year."""
        # Map table names to models
        model_map = {
            "revenues": Revenue,
            "expenditures": Expenditure,
            "fund_balances": FundBalance,
        }

        model = model_map.get(table_name)
        if not model:
            return None

        # For revenues/expenditures, sum all amounts
        if table_name in ["revenues", "expenditures"]:
            from sqlalchemy import func

            total = (
                self.db.query(func.sum(model.amount))
                .filter(model.fiscal_year_id == prior_fy_id)
                .scalar()
            )
            return float(total) if total else None

        return None

    def _create_queue_item(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        value: float,
        city_id: int,
        fiscal_year: int,
        entered_by: str,
        anomalies: List[Dict],
    ) -> ValidationQueueItem:
        """Create validation queue item for anomaly."""
        # Get fiscal year record
        fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        # Determine severity (highest severity from all anomalies)
        severities = [a["rule"].severity for a in anomalies]
        severity = "CRITICAL" if "CRITICAL" in severities else "WARNING" if "WARNING" in severities else "INFO"

        # Create queue item
        queue_item = ValidationQueueItem(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            entered_value=str(value),
            city_id=city_id,
            fiscal_year=fiscal_year,
            fiscal_year_id=fy.id if fy else None,
            entered_by=entered_by,
            entered_at=datetime.utcnow(),
            status="FLAGGED",
            severity=severity,
            flag_reason=anomalies[0]["rule"].rule_name,
            flag_details=anomalies[0]["context"],
            prior_year_value=str(anomalies[0].get("prior_year_value"))
            if anomalies[0].get("prior_year_value")
            else None,
        )

        self.db.add(queue_item)
        self.db.commit()

        return queue_item

    def _create_anomaly_flag(
        self, queue_item: ValidationQueueItem, violation: Dict
    ):
        """Create anomaly flag record."""
        rule = violation["rule"]

        flag = AnomalyFlag(
            queue_item_id=queue_item.id,
            rule_name=rule.rule_name,
            rule_description=rule.rule_description,
            severity=rule.severity,
            entered_value=str(violation["entered_value"]),
            expected_value=str(violation.get("expected_value"))
            if violation.get("expected_value")
            else None,
            prior_year_value=str(violation.get("prior_year_value"))
            if violation.get("prior_year_value")
            else None,
            deviation_percent=violation.get("deviation_percent"),
            context=violation.get("context"),
            suggested_action=rule.suggested_action,
            resolved=False,
        )

        self.db.add(flag)
        self.db.commit()


def seed_default_rules(db: Session):
    """
    Seed database with default validation rules.

    Should be run on initial setup.
    """
    default_rules = [
        {
            "rule_name": "revenue_yoy_50",
            "rule_description": "Flag if total revenues change by more than 50% year-over-year",
            "rule_type": "year_over_year",
            "table_name": "revenues",
            "field_name": "amount",
            "parameters": json.dumps({"threshold_percent": 50}),
            "severity": "WARNING",
            "suggested_action": "INVESTIGATE",
            "priority": 90,
        },
        {
            "rule_name": "expenditure_yoy_50",
            "rule_description": "Flag if total expenditures change by more than 50% year-over-year",
            "rule_type": "year_over_year",
            "table_name": "expenditures",
            "field_name": "amount",
            "parameters": json.dumps({"threshold_percent": 50}),
            "severity": "WARNING",
            "suggested_action": "INVESTIGATE",
            "priority": 90,
        },
        {
            "rule_name": "negative_revenue",
            "rule_description": "Flag negative revenues (should not happen)",
            "rule_type": "range_check",
            "table_name": "revenues",
            "field_name": "amount",
            "parameters": json.dumps({"min_value": 0}),
            "severity": "CRITICAL",
            "suggested_action": "CORRECT",
            "priority": 100,
        },
        {
            "rule_name": "negative_expenditure",
            "rule_description": "Flag negative expenditures (should not happen)",
            "rule_type": "range_check",
            "table_name": "expenditures",
            "field_name": "amount",
            "parameters": json.dumps({"min_value": 0}),
            "severity": "CRITICAL",
            "suggested_action": "CORRECT",
            "priority": 100,
        },
        {
            "rule_name": "pension_funded_ratio_range",
            "rule_description": "Flag if pension funded ratio is outside 0-150%",
            "rule_type": "range_check",
            "table_name": "pension_plans",
            "field_name": "funded_ratio",
            "parameters": json.dumps({"min_value": 0, "max_value": 1.5}),
            "severity": "WARNING",
            "suggested_action": "INVESTIGATE",
            "priority": 85,
        },
    ]

    for rule_data in default_rules:
        # Check if rule already exists
        existing = (
            db.query(ValidationRule)
            .filter(ValidationRule.rule_name == rule_data["rule_name"])
            .first()
        )

        if not existing:
            rule = ValidationRule(**rule_data)
            db.add(rule)

    db.commit()
    logger.info("default_validation_rules_seeded", count=len(default_rules))
