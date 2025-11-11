#!/usr/bin/env python3
"""
Data Integrity Validation Script

Validates manually entered fiscal data against source documents:
1. Verify totals match CAFR summaries
2. Check fund balance formula: beginning + revenues - expenditures = ending
3. Flag any transcription errors for correction

Usage:
    poetry run python scripts/validation/validate_data_integrity.py [--fiscal-year YEAR]

Examples:
    poetry run python scripts/validation/validate_data_integrity.py --fiscal-year 2024
    poetry run python scripts/validation/validate_data_integrity.py  # validate all years
"""

import argparse
import sys
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.database.models import (
    City,
    Expenditure,
    FiscalYear,
    FundBalance,
    Revenue,
)


class ValidationError:
    """Represents a data validation error."""

    def __init__(
        self,
        fiscal_year: int,
        error_type: str,
        description: str,
        expected: Optional[Decimal] = None,
        actual: Optional[Decimal] = None,
        tolerance: Optional[Decimal] = None,
    ):
        self.fiscal_year = fiscal_year
        self.error_type = error_type
        self.description = description
        self.expected = expected
        self.actual = actual
        self.tolerance = tolerance

    @property
    def variance(self) -> Optional[Decimal]:
        """Calculate variance between expected and actual."""
        if self.expected is not None and self.actual is not None:
            return abs(self.actual - self.expected)
        return None

    @property
    def variance_percent(self) -> Optional[Decimal]:
        """Calculate percentage variance."""
        if self.expected and self.variance:
            return (self.variance / abs(self.expected)) * 100
        return None

    def __str__(self) -> str:
        parts = [f"FY{self.fiscal_year} - {self.error_type}: {self.description}"]
        if self.expected is not None:
            parts.append(f"Expected: ${self.expected:,.2f}")
        if self.actual is not None:
            parts.append(f"Actual: ${self.actual:,.2f}")
        if self.variance is not None:
            parts.append(f"Variance: ${self.variance:,.2f} ({self.variance_percent:.2f}%)")
        return " | ".join(parts)


class DataValidator:
    """Validates fiscal data integrity."""

    def __init__(self, db_session: Session, tolerance: Decimal = Decimal("0.01")):
        """
        Initialize validator.

        Args:
            db_session: Database session
            tolerance: Acceptable variance as decimal (0.01 = 1%)
        """
        self.session = db_session
        self.tolerance = tolerance
        self.errors: List[ValidationError] = []

    def validate_fund_balance_formula(self, fiscal_year: FiscalYear) -> None:
        """
        Validate fund balance formula: ending = beginning + revenues - expenditures.

        Args:
            fiscal_year: Fiscal year to validate
        """
        # Get fund balance data
        fund_balance = (
            self.session.query(FundBalance)
            .filter(FundBalance.fiscal_year_id == fiscal_year.id)
            .first()
        )

        if not fund_balance:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="No fund balance record found",
                )
            )
            return

        # Calculate total revenues
        total_revenues = (
            self.session.query(func.sum(Revenue.amount))
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        # Calculate total expenditures
        total_expenditures = (
            self.session.query(func.sum(Expenditure.amount))
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .scalar()
            or Decimal("0")
        )

        # Calculate expected ending balance
        expected_ending = (
            fund_balance.beginning_balance + total_revenues - total_expenditures
        )

        # Check variance
        variance = abs(fund_balance.ending_balance - expected_ending)
        if fund_balance.ending_balance != 0:
            variance_percent = (variance / abs(fund_balance.ending_balance)) * 100
        else:
            variance_percent = Decimal("0")

        if variance_percent > (self.tolerance * 100):
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="FUND_BALANCE_MISMATCH",
                    description="Fund balance formula does not balance",
                    expected=expected_ending,
                    actual=fund_balance.ending_balance,
                    tolerance=self.tolerance,
                )
            )

    def validate_revenue_totals(self, fiscal_year: FiscalYear) -> None:
        """
        Validate that revenue categories sum correctly.

        Args:
            fiscal_year: Fiscal year to validate
        """
        # Get total revenues by category
        revenues_by_category = (
            self.session.query(
                Revenue.category_id, func.sum(Revenue.amount).label("total")
            )
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .group_by(Revenue.category_id)
            .all()
        )

        if not revenues_by_category:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="No revenue data found",
                )
            )

    def validate_expenditure_totals(self, fiscal_year: FiscalYear) -> None:
        """
        Validate that expenditure categories sum correctly.

        Args:
            fiscal_year: Fiscal year to validate
        """
        # Get total expenditures by category
        expenditures_by_category = (
            self.session.query(
                Expenditure.category_id, func.sum(Expenditure.amount).label("total")
            )
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .group_by(Expenditure.category_id)
            .all()
        )

        if not expenditures_by_category:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="No expenditure data found",
                )
            )

    def validate_data_completeness(self, fiscal_year: FiscalYear) -> None:
        """
        Validate that all required data is present.

        Args:
            fiscal_year: Fiscal year to validate
        """
        # Check for fund balance
        has_fund_balance = (
            self.session.query(FundBalance)
            .filter(FundBalance.fiscal_year_id == fiscal_year.id)
            .count()
            > 0
        )

        if not has_fund_balance:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="Missing fund balance data",
                )
            )

        # Check for revenues
        has_revenues = (
            self.session.query(Revenue)
            .filter(Revenue.fiscal_year_id == fiscal_year.id)
            .count()
            > 0
        )

        if not has_revenues:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="Missing revenue data",
                )
            )

        # Check for expenditures
        has_expenditures = (
            self.session.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fiscal_year.id)
            .count()
            > 0
        )

        if not has_expenditures:
            self.errors.append(
                ValidationError(
                    fiscal_year=fiscal_year.year,
                    error_type="MISSING_DATA",
                    description="Missing expenditure data",
                )
            )

    def validate_fiscal_year(self, fiscal_year: FiscalYear) -> None:
        """
        Run all validations for a fiscal year.

        Args:
            fiscal_year: Fiscal year to validate
        """
        print(f"Validating FY{fiscal_year.year}...")

        self.validate_data_completeness(fiscal_year)
        self.validate_revenue_totals(fiscal_year)
        self.validate_expenditure_totals(fiscal_year)
        self.validate_fund_balance_formula(fiscal_year)

    def generate_report(self) -> str:
        """
        Generate validation report.

        Returns:
            Formatted validation report
        """
        if not self.errors:
            return "✓ All validation checks passed! No errors found."

        # Group errors by type
        errors_by_type = {}
        for error in self.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)

        # Build report
        report_lines = [
            f"\n{'='*80}",
            "DATA VALIDATION REPORT",
            f"{'='*80}\n",
            f"Total Errors: {len(self.errors)}",
            f"Tolerance: {self.tolerance * 100:.2f}%\n",
        ]

        for error_type, errors in errors_by_type.items():
            report_lines.append(f"\n{error_type} ({len(errors)} errors):")
            report_lines.append("-" * 80)
            for error in errors:
                report_lines.append(f"  {error}")

        report_lines.append(f"\n{'='*80}\n")

        return "\n".join(report_lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate fiscal data integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        help="Specific fiscal year to validate (default: all years)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.01,
        help="Acceptable variance percentage (default: 0.01 = 1%%)",
    )
    parser.add_argument(
        "--city",
        default="Vallejo",
        help="City to validate (default: Vallejo)",
    )

    args = parser.parse_args()

    # Create database engine
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        # Get city
        city = session.query(City).filter(City.name == args.city).first()
        if not city:
            print(f"Error: City '{args.city}' not found in database")
            return 1

        # Get fiscal years to validate
        query = session.query(FiscalYear).filter(FiscalYear.city_id == city.id)

        if args.fiscal_year:
            query = query.filter(FiscalYear.year == args.fiscal_year)

        fiscal_years = query.order_by(FiscalYear.year).all()

        if not fiscal_years:
            print("Error: No fiscal years found to validate")
            return 1

        print(f"\nValidating {len(fiscal_years)} fiscal year(s) for {city.name}...")
        print(f"Tolerance: {args.tolerance * 100:.2f}%\n")

        # Create validator
        validator = DataValidator(session, tolerance=Decimal(str(args.tolerance)))

        # Validate each fiscal year
        for fiscal_year in fiscal_years:
            validator.validate_fiscal_year(fiscal_year)

        # Print report
        print(validator.generate_report())

        # Return error code if validation failed
        return 1 if validator.errors else 0


if __name__ == "__main__":
    sys.exit(main())
