#!/usr/bin/env python3
"""
Import CAFR data with three-tier structure: Tier 1 (Financial), Tier 2 (Notes), Tier 3 (Statistical).

This script handles the complete workflow for entering a single CAFR's data:
1. Tier 1: Financial Section (stated current year data) → PRIMARY FOR ANALYSIS
2. Tier 2: Notes to Financial Statements (methodology, assumptions) → CONTEXT ONLY
3. Tier 3: Statistical Section (10-year historical restated data) → COMPARISON ONLY

CSV Format:
    fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes

Examples:
    # Tier 1: FY2024 stated revenue from FY2024 CAFR
    2024,Property Tax,52000000,tier_1_financial,stated,2024,General,

    # Tier 3: FY2020 restated revenue from FY2024 CAFR statistical section
    2020,Property Tax,48500000,tier_3_statistical,restated,2024,General,GASB 87 reclass

Usage:
    # Import FY2024 CAFR (all three tiers)
    python scripts/data_entry/import_cafr_three_tier.py \\
        --cafr-year 2024 \\
        --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv \\
        --tier3-csv data/raw/cafr/fy2024_tier3_statistical.csv

    # Import only Tier 1 (if statistical section not yet transcribed)
    python scripts/data_entry/import_cafr_three_tier.py \\
        --cafr-year 2024 \\
        --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv

    # Dry run (validate without saving)
    python scripts/data_entry/import_cafr_three_tier.py \\
        --cafr-year 2024 \\
        --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv \\
        --dry-run
"""

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, '/app')

from src.config.settings import settings
from src.config.logging_config import get_logger
from src.database.models import (
    Revenue,
    RevenueCategory,
    Expenditure,
    ExpenditureCategory,
    FundBalance,
    FiscalYear,
    City,
    DataSource,
    DataLineage
)

logger = get_logger(__name__)


class CAFRThreeTierImporter:
    """Import CAFR data with three-tier structure tracking."""

    def __init__(self, db: Session, cafr_year: int, dry_run: bool = False):
        self.db = db
        self.cafr_year = cafr_year
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            'tier1_revenues': 0,
            'tier1_expenditures': 0,
            'tier1_fund_balances': 0,
            'tier3_revenues': 0,
            'tier3_expenditures': 0,
            'tier3_fund_balances': 0,
            'errors': 0,
            'warnings': 0
        }

    def validate_tier(self, tier: str) -> bool:
        """Validate CAFR tier value."""
        valid_tiers = ['tier_1_financial', 'tier_2_notes', 'tier_3_statistical']
        if tier not in valid_tiers:
            logger.error(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
            return False
        return True

    def validate_version_type(self, version_type: str) -> bool:
        """Validate data version type."""
        valid_types = ['stated', 'restated']
        if version_type not in valid_types:
            logger.error(f"Invalid version type: {version_type}. Must be 'stated' or 'restated'")
            return False
        return True

    def validate_tier_version_logic(self, tier: str, version_type: str, fiscal_year: int) -> bool:
        """
        Validate tier and version type are logically consistent.

        Rules:
        1. Tier 1 (Financial Section) → Always 'stated' (current year only)
        2. Tier 3 (Statistical Section) → Can be 'stated' (current year) or 'restated' (historical)
        3. If fiscal_year == cafr_year → should be 'stated'
        4. If fiscal_year < cafr_year → should be 'restated' (Tier 3 only)
        """
        if tier == 'tier_1_financial':
            if version_type != 'stated':
                logger.error(f"Tier 1 (Financial Section) must be 'stated', not '{version_type}'")
                return False
            if fiscal_year != self.cafr_year:
                logger.error(f"Tier 1 data must match CAFR year ({self.cafr_year}), got FY{fiscal_year}")
                return False

        if tier == 'tier_3_statistical':
            if fiscal_year == self.cafr_year:
                if version_type != 'stated':
                    logger.warning(f"⚠️ Tier 3 current year (FY{fiscal_year}) should typically be 'stated'")
            elif fiscal_year < self.cafr_year:
                if version_type != 'restated':
                    logger.error(f"Tier 3 historical data (FY{fiscal_year}) must be 'restated', not '{version_type}'")
                    return False
            else:
                logger.error(f"Invalid: fiscal_year ({fiscal_year}) > cafr_year ({self.cafr_year})")
                return False

        return True

    def get_or_create_fiscal_year(self, year: int, city_id: int) -> Optional[FiscalYear]:
        """Get or create fiscal year record."""
        fy = self.db.query(FiscalYear).filter(
            FiscalYear.year == year,
            FiscalYear.city_id == city_id
        ).first()

        if not fy:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create FiscalYear {year}")
                fy = FiscalYear(id=-1, year=year, city_id=city_id)  # Mock for validation
            else:
                # Create fiscal year (July 1 to June 30 for CA cities)
                from datetime import date
                fy = FiscalYear(
                    city_id=city_id,
                    year=year,
                    start_date=date(year - 1, 7, 1),
                    end_date=date(year, 6, 30)
                )
                self.db.add(fy)
                self.db.flush()
                logger.info(f"✅ Created FiscalYear {year}")

        return fy

    def import_revenues_from_csv(self, csv_path: Path, city_id: int) -> int:
        """
        Import revenues from CSV file.

        CSV Columns:
            fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes
        """
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse row
                    fiscal_year = int(row['fiscal_year'])
                    category_name = row['category'].strip()
                    amount = Decimal(row['amount'].replace(',', '').replace('$', ''))
                    cafr_tier = row['cafr_tier'].strip()
                    data_version_type = row['data_version_type'].strip()
                    source_cafr_year = int(row.get('source_cafr_year', self.cafr_year))
                    fund_type = row.get('fund_type', 'General').strip()
                    notes = row.get('notes', '').strip()

                    # Validation
                    if not self.validate_tier(cafr_tier):
                        self.stats['errors'] += 1
                        continue

                    if not self.validate_version_type(data_version_type):
                        self.stats['errors'] += 1
                        continue

                    if not self.validate_tier_version_logic(cafr_tier, data_version_type, fiscal_year):
                        self.stats['errors'] += 1
                        continue

                    # Get or create fiscal year
                    fy = self.get_or_create_fiscal_year(fiscal_year, city_id)
                    if not fy:
                        logger.error(f"Row {row_num}: Could not create fiscal year {fiscal_year}")
                        self.stats['errors'] += 1
                        continue

                    # Get or create revenue category
                    category = self.db.query(RevenueCategory).filter(
                        RevenueCategory.standard_name == category_name
                    ).first()

                    if not category:
                        if self.dry_run:
                            logger.info(f"[DRY RUN] Would create RevenueCategory: {category_name}")
                            category = RevenueCategory(id=-1, standard_name=category_name)
                        else:
                            category = RevenueCategory(
                                category_level1=category_name,
                                standard_name=category_name
                            )
                            self.db.add(category)
                            self.db.flush()
                            logger.info(f"✅ Created RevenueCategory: {category_name}")

                    # Determine if this is primary version
                    is_primary = (data_version_type == 'stated')

                    # Check for existing record
                    existing = self.db.query(Revenue).filter(
                        Revenue.fiscal_year_id == fy.id,
                        Revenue.category_id == category.id,
                        Revenue.fund_type == fund_type,
                        Revenue.cafr_tier == cafr_tier,
                        Revenue.data_version_type == data_version_type,
                        Revenue.source_cafr_year == source_cafr_year
                    ).first()

                    if existing:
                        logger.warning(f"⚠️ Row {row_num}: Revenue already exists, skipping")
                        self.stats['warnings'] += 1
                        continue

                    # Create revenue record
                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] Would create Revenue: FY{fiscal_year} {category_name} "
                            f"${amount:,.2f} ({cafr_tier}, {data_version_type})"
                        )
                    else:
                        revenue = Revenue(
                            fiscal_year_id=fy.id,
                            category_id=category.id,
                            fund_type=fund_type,
                            actual_amount=amount,
                            cafr_tier=cafr_tier,
                            data_version_type=data_version_type,
                            source_cafr_year=source_cafr_year,
                            is_primary_version=is_primary,
                            restatement_reason=notes if data_version_type == 'restated' else None
                        )
                        self.db.add(revenue)

                    # Update statistics
                    if cafr_tier == 'tier_1_financial':
                        self.stats['tier1_revenues'] += 1
                    elif cafr_tier == 'tier_3_statistical':
                        self.stats['tier3_revenues'] += 1

                    count += 1

                except (ValueError, InvalidOperation, KeyError) as e:
                    logger.error(f"Row {row_num}: Error parsing data: {e}")
                    logger.error(f"Row data: {row}")
                    self.stats['errors'] += 1
                    continue

        if not self.dry_run:
            self.db.commit()

        logger.info(f"✅ Imported {count} revenues from {csv_path.name}")
        return count

    def generate_summary_report(self) -> str:
        """Generate import summary report."""
        report = []
        report.append("=" * 80)
        report.append(f"CAFR FY{self.cafr_year} IMPORT SUMMARY")
        report.append("=" * 80)
        report.append("")

        report.append("📊 Tier 1 (Financial Section - Stated Data):")
        report.append(f"   Revenues:     {self.stats['tier1_revenues']}")
        report.append(f"   Expenditures: {self.stats['tier1_expenditures']}")
        report.append(f"   Fund Balances: {self.stats['tier1_fund_balances']}")
        report.append("")

        report.append("📈 Tier 3 (Statistical Section - Restated Historical Data):")
        report.append(f"   Revenues:     {self.stats['tier3_revenues']}")
        report.append(f"   Expenditures: {self.stats['tier3_expenditures']}")
        report.append(f"   Fund Balances: {self.stats['tier3_fund_balances']}")
        report.append("")

        total_records = sum([
            self.stats['tier1_revenues'],
            self.stats['tier1_expenditures'],
            self.stats['tier1_fund_balances'],
            self.stats['tier3_revenues'],
            self.stats['tier3_expenditures'],
            self.stats['tier3_fund_balances']
        ])

        report.append(f"Total Records: {total_records}")
        report.append(f"Errors: {self.stats['errors']}")
        report.append(f"Warnings: {self.stats['warnings']}")
        report.append("")

        if self.stats['errors'] > 0:
            report.append("⚠️ ERRORS DETECTED - Review log output above")
        else:
            report.append("✅ Import completed successfully")

        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Import CAFR data with three-tier structure tracking'
    )
    parser.add_argument(
        '--cafr-year',
        type=int,
        required=True,
        help='CAFR year being imported (e.g., 2024)'
    )
    parser.add_argument(
        '--city',
        type=str,
        default='Vallejo',
        help='City name (default: Vallejo)'
    )
    parser.add_argument(
        '--tier1-csv',
        type=Path,
        help='Path to Tier 1 (Financial Section) CSV file'
    )
    parser.add_argument(
        '--tier3-csv',
        type=Path,
        help='Path to Tier 3 (Statistical Section) CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate CSV without writing to database'
    )

    args = parser.parse_args()

    # Database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get city
        city = db.query(City).filter(City.name == args.city).first()
        if not city:
            logger.error(f"❌ City '{args.city}' not found in database")
            logger.info("Create city first: INSERT INTO cities (name, state, county) VALUES ('Vallejo', 'CA', 'Solano');")
            sys.exit(1)

        logger.info(f"🏛️ Importing CAFR FY{args.cafr_year} for {city.name}, CA")

        if args.dry_run:
            logger.info("🔍 DRY RUN MODE - No data will be written to database")

        # Initialize importer
        importer = CAFRThreeTierImporter(db, args.cafr_year, args.dry_run)

        # Import Tier 1 (Financial Section)
        if args.tier1_csv:
            logger.info(f"\n📊 Importing Tier 1 (Financial Section): {args.tier1_csv}")
            importer.import_revenues_from_csv(args.tier1_csv, city.id)

        # Import Tier 3 (Statistical Section)
        if args.tier3_csv:
            logger.info(f"\n📈 Importing Tier 3 (Statistical Section): {args.tier3_csv}")
            importer.import_revenues_from_csv(args.tier3_csv, city.id)

        # Generate summary report
        report = importer.generate_summary_report()
        print(report)

        if not args.dry_run and importer.stats['errors'] == 0:
            logger.info("\n🔍 Next step: Run discrepancy detection")
            logger.info(f"   python scripts/validation/detect_restatement_discrepancies.py --cafr-year {args.cafr_year}")

    except Exception as e:
        logger.error(f"❌ Error during import: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
