#!/usr/bin/env python3
"""
Detect and flag discrepancies between stated and restated financial data.

This script compares:
- Stated data (from original CAFR when data was current)
- Restated data (from later CAFRs' statistical sections)

Example:
    FY2020 Revenue stated in FY2020 CAFR: $100M
    FY2020 Revenue restated in FY2024 CAFR: $95M
    → Discrepancy: -$5M (-5.0%)

Usage:
    python scripts/validation/detect_restatement_discrepancies.py --fiscal-year 2020
    python scripts/validation/detect_restatement_discrepancies.py --all
    python scripts/validation/detect_restatement_discrepancies.py --cafr-year 2024

Severity Levels:
    - Minor: <1% difference
    - Moderate: 1-5% difference
    - Major: 5-10% difference
    - Critical: >10% difference
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

# Add src to path for imports
sys.path.insert(0, '/app')

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.database.models import (
    Revenue,
    Expenditure,
    FundBalance,
    PensionContribution,
    FiscalYear,
)
from src.database.models.validation import RestatementDiscrepancy

logger = get_logger(__name__)


class RestatementDiscrepancyDetector:
    """Detect and analyze discrepancies between stated and restated data."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_severity(self, percent_diff: float) -> str:
        """
        Calculate severity level based on percentage difference.

        Rules:
        - >10%: Critical (major accounting issue)
        - 5-10%: Major (significant restatement)
        - 1-5%: Moderate (notable adjustment)
        - <1%: Minor (rounding or small correction)
        """
        abs_pct = abs(percent_diff)

        if abs_pct > 10.0:
            return 'Critical'
        elif abs_pct > 5.0:
            return 'Major'
        elif abs_pct > 1.0:
            return 'Moderate'
        else:
            return 'Minor'

    def detect_revenue_discrepancies(
        self,
        fiscal_year_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect revenue discrepancies between stated and restated values.

        Args:
            fiscal_year_id: Specific fiscal year to check (or None for all)

        Returns:
            List of discrepancy records
        """
        discrepancies = []

        # Query for stated revenues (primary versions)
        stated_query = self.db.query(Revenue).filter(
            Revenue.is_primary_version == True,
            Revenue.data_version_type == 'stated'
        )

        if fiscal_year_id:
            stated_query = stated_query.filter(Revenue.fiscal_year_id == fiscal_year_id)

        stated_revenues = stated_query.all()

        logger.info(f"Checking {len(stated_revenues)} stated revenue records...")

        for stated in stated_revenues:
            # Find all restated versions of this revenue
            restated_versions = self.db.query(Revenue).filter(
                Revenue.fiscal_year_id == stated.fiscal_year_id,
                Revenue.category_id == stated.category_id,
                Revenue.fund_type == stated.fund_type,
                Revenue.data_version_type == 'restated',
                Revenue.source_cafr_year > stated.source_cafr_year  # Later CAFRs only
            ).all()

            for restated in restated_versions:
                # Calculate discrepancy
                absolute_diff = float(restated.actual_amount - stated.actual_amount)

                # Skip if values are identical
                if abs(absolute_diff) < 0.01:  # Within 1 cent
                    continue

                # Calculate percentage difference
                if stated.actual_amount != 0:
                    percent_diff = (absolute_diff / float(stated.actual_amount)) * 100
                else:
                    percent_diff = None

                severity = self.calculate_severity(percent_diff) if percent_diff else 'Minor'

                # Check if this discrepancy already exists
                existing = self.db.query(RestatementDiscrepancy).filter(
                    RestatementDiscrepancy.table_name == 'revenues',
                    RestatementDiscrepancy.fiscal_year_id == stated.fiscal_year_id,
                    RestatementDiscrepancy.stated_record_id == stated.id,
                    RestatementDiscrepancy.restated_record_id == restated.id
                ).first()

                if existing:
                    logger.debug(f"Discrepancy already logged: Revenue FY{stated.fiscal_year_id} (ID {stated.id})")
                    continue

                discrepancy = {
                    'table_name': 'revenues',
                    'fiscal_year_id': stated.fiscal_year_id,
                    'field_name': 'actual_amount',
                    'stated_value': float(stated.actual_amount),
                    'stated_source_cafr_year': stated.source_cafr_year,
                    'stated_record_id': stated.id,
                    'restated_value': float(restated.actual_amount),
                    'restated_source_cafr_year': restated.source_cafr_year,
                    'restated_record_id': restated.id,
                    'absolute_difference': absolute_diff,
                    'percent_difference': percent_diff,
                    'severity': severity,
                    'restatement_reason': restated.restatement_reason,
                    'category': stated.category.standard_name if stated.category else 'Unknown'
                }

                discrepancies.append(discrepancy)

        return discrepancies

    def detect_expenditure_discrepancies(
        self,
        fiscal_year_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Detect expenditure discrepancies (similar to revenues)."""
        discrepancies = []

        stated_query = self.db.query(Expenditure).filter(
            Expenditure.is_primary_version == True,
            Expenditure.data_version_type == 'stated'
        )

        if fiscal_year_id:
            stated_query = stated_query.filter(Expenditure.fiscal_year_id == fiscal_year_id)

        stated_expenditures = stated_query.all()

        logger.info(f"Checking {len(stated_expenditures)} stated expenditure records...")

        for stated in stated_expenditures:
            restated_versions = self.db.query(Expenditure).filter(
                Expenditure.fiscal_year_id == stated.fiscal_year_id,
                Expenditure.category_id == stated.category_id,
                Expenditure.fund_type == stated.fund_type,
                Expenditure.data_version_type == 'restated',
                Expenditure.source_cafr_year > stated.source_cafr_year
            ).all()

            for restated in restated_versions:
                absolute_diff = float(restated.actual_amount - stated.actual_amount)

                if abs(absolute_diff) < 0.01:
                    continue

                percent_diff = (absolute_diff / float(stated.actual_amount)) * 100 if stated.actual_amount != 0 else None
                severity = self.calculate_severity(percent_diff) if percent_diff else 'Minor'

                existing = self.db.query(RestatementDiscrepancy).filter(
                    RestatementDiscrepancy.table_name == 'expenditures',
                    RestatementDiscrepancy.fiscal_year_id == stated.fiscal_year_id,
                    RestatementDiscrepancy.stated_record_id == stated.id,
                    RestatementDiscrepancy.restated_record_id == restated.id
                ).first()

                if existing:
                    continue

                discrepancy = {
                    'table_name': 'expenditures',
                    'fiscal_year_id': stated.fiscal_year_id,
                    'field_name': 'actual_amount',
                    'stated_value': float(stated.actual_amount),
                    'stated_source_cafr_year': stated.source_cafr_year,
                    'stated_record_id': stated.id,
                    'restated_value': float(restated.actual_amount),
                    'restated_source_cafr_year': restated.source_cafr_year,
                    'restated_record_id': restated.id,
                    'absolute_difference': absolute_diff,
                    'percent_difference': percent_diff,
                    'severity': severity,
                    'restatement_reason': restated.restatement_reason,
                    'category': stated.category.standard_name if stated.category else 'Unknown'
                }

                discrepancies.append(discrepancy)

        return discrepancies

    def save_discrepancies(self, discrepancies: List[Dict[str, Any]]) -> int:
        """
        Save detected discrepancies to database.

        Returns:
            Number of new discrepancies saved
        """
        count = 0

        for disc in discrepancies:
            # Determine if manual review is required
            requires_review = disc['severity'] in ['Major', 'Critical']

            discrepancy_record = RestatementDiscrepancy(
                table_name=disc['table_name'],
                fiscal_year_id=disc['fiscal_year_id'],
                field_name=disc['field_name'],
                stated_value=Decimal(str(disc['stated_value'])),
                stated_source_cafr_year=disc['stated_source_cafr_year'],
                stated_record_id=disc['stated_record_id'],
                restated_value=Decimal(str(disc['restated_value'])),
                restated_source_cafr_year=disc['restated_source_cafr_year'],
                restated_record_id=disc['restated_record_id'],
                absolute_difference=Decimal(str(disc['absolute_difference'])),
                percent_difference=Decimal(str(disc['percent_difference'])) if disc['percent_difference'] else None,
                severity=disc['severity'],
                restatement_reason=disc.get('restatement_reason'),
                requires_review=requires_review,
                detected_date=datetime.utcnow()
            )

            self.db.add(discrepancy_record)
            count += 1

        if count > 0:
            self.db.commit()
            logger.info(f"✅ Saved {count} new restatement discrepancies")

        return count

    def generate_report(self, discrepancies: List[Dict[str, Any]]) -> str:
        """Generate human-readable discrepancy report."""
        if not discrepancies:
            return "✅ No restatement discrepancies detected."

        report = ["=" * 80]
        report.append("RESTATEMENT DISCREPANCY REPORT")
        report.append("=" * 80)
        report.append("")

        # Group by severity
        by_severity = {'Critical': [], 'Major': [], 'Moderate': [], 'Minor': []}
        for disc in discrepancies:
            by_severity[disc['severity']].append(disc)

        # Summary
        report.append(f"Total Discrepancies Found: {len(discrepancies)}")
        report.append(f"  - Critical (>10%): {len(by_severity['Critical'])}")
        report.append(f"  - Major (5-10%): {len(by_severity['Major'])}")
        report.append(f"  - Moderate (1-5%): {len(by_severity['Moderate'])}")
        report.append(f"  - Minor (<1%): {len(by_severity['Minor'])}")
        report.append("")

        # Details by severity (highest first)
        for severity in ['Critical', 'Major', 'Moderate', 'Minor']:
            if not by_severity[severity]:
                continue

            report.append(f"\n{'=' * 80}")
            report.append(f"{severity.upper()} DISCREPANCIES ({len(by_severity[severity])})")
            report.append('=' * 80)

            for disc in by_severity[severity]:
                fy = self.db.query(FiscalYear).get(disc['fiscal_year_id'])
                fy_year = fy.year if fy else '?'

                report.append(f"\n📊 FY{fy_year} {disc['table_name'].title()} - {disc.get('category', 'Unknown')}")
                report.append(f"   Stated (FY{disc['stated_source_cafr_year']} CAFR):  ${disc['stated_value']:,.2f}")
                report.append(f"   Restated (FY{disc['restated_source_cafr_year']} CAFR): ${disc['restated_value']:,.2f}")
                report.append(f"   Difference: ${disc['absolute_difference']:,.2f} ({disc['percent_difference']:+.2f}%)")

                if disc.get('restatement_reason'):
                    report.append(f"   Reason: {disc['restatement_reason']}")

                report.append(f"   ⚠️ Action: {'REQUIRES MANUAL REVIEW' if severity in ['Major', 'Critical'] else 'Log for reference'}")

        report.append("\n" + "=" * 80)
        report.append("END REPORT")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Detect restatement discrepancies between stated and restated CAFR data'
    )
    parser.add_argument(
        '--fiscal-year',
        type=int,
        help='Check specific fiscal year (e.g., 2020)'
    )
    parser.add_argument(
        '--cafr-year',
        type=int,
        help='Check discrepancies introduced by specific CAFR year (e.g., 2024)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all fiscal years'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        default=True,
        help='Save discrepancies to database (default: True)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report without saving to database'
    )

    args = parser.parse_args()

    # Database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        detector = RestatementDiscrepancyDetector(db)

        logger.info("🔍 Starting restatement discrepancy detection...")

        # Determine fiscal year ID if specified
        fiscal_year_id = None
        if args.fiscal_year:
            fy = db.query(FiscalYear).filter(FiscalYear.year == args.fiscal_year).first()
            if not fy:
                logger.error(f"❌ Fiscal year {args.fiscal_year} not found in database")
                sys.exit(1)
            fiscal_year_id = fy.id
            logger.info(f"Checking fiscal year {args.fiscal_year}")

        # Detect discrepancies
        all_discrepancies = []

        logger.info("Checking revenues...")
        revenue_discrepancies = detector.detect_revenue_discrepancies(fiscal_year_id)
        all_discrepancies.extend(revenue_discrepancies)

        logger.info("Checking expenditures...")
        expenditure_discrepancies = detector.detect_expenditure_discrepancies(fiscal_year_id)
        all_discrepancies.extend(expenditure_discrepancies)

        # Generate report
        report = detector.generate_report(all_discrepancies)
        print(report)

        # Save to database (unless report-only)
        if all_discrepancies and not args.report_only:
            count = detector.save_discrepancies(all_discrepancies)
            logger.info(f"✅ Saved {count} discrepancies to database")
            logger.info("💡 Review required discrepancies: query restatement_discrepancies where requires_review=true")

        logger.info("✅ Discrepancy detection complete")

    except Exception as e:
        logger.error(f"❌ Error during discrepancy detection: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
