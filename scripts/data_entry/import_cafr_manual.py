"""
Manual CAFR data import script.

For MVP: manually transcribe CAFR data into CSV, then import.
This is faster and more reliable than building PDF extraction.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from src.config.database import SessionLocal
from src.database.models.core import City, FiscalYear, DataSource, DataLineage
from src.database.models.financial import (
    Revenue, Expenditure, FundBalance,
    RevenueCategory, ExpenditureCategory
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class CAFRImporter:
    """Import manually transcribed CAFR data."""

    def __init__(self, db: Session):
        self.db = db
        self.validation_errors: List[str] = []
        self.warnings: List[str] = []

    def import_from_csv(
        self,
        city_name: str,
        fiscal_year: int,
        revenues_csv: Path,
        expenditures_csv: Path,
        fund_balance_csv: Path,
        cafr_url: str,
        transcribed_by: str
    ) -> bool:
        """
        Import CAFR data from CSV files.

        CSV Format:

        revenues.csv:
        category,fund_type,budget_amount,actual_amount,notes

        expenditures.csv:
        category,department,fund_type,budget_amount,actual_amount,notes

        fund_balance.csv:
        fund_type,nonspendable,restricted,committed,assigned,unassigned,total
        """
        logger.info(f"Starting CAFR import for {city_name} FY {fiscal_year}")

        # Get or create city
        city = self.get_or_create_city(city_name)

        # Get or create fiscal year
        fy = self.get_or_create_fiscal_year(city.id, fiscal_year, cafr_url)

        # Create data source record
        data_source = self.create_data_source(city_name, fiscal_year, cafr_url)

        # Import revenues
        if revenues_csv.exists():
            logger.info(f"Importing revenues from {revenues_csv}")
            revenue_count = self.import_revenues(fy.id, revenues_csv, data_source.id, transcribed_by)
            logger.info(f"Imported {revenue_count} revenue records")
        else:
            self.warnings.append(f"Revenue file not found: {revenues_csv}")

        # Import expenditures
        if expenditures_csv.exists():
            logger.info(f"Importing expenditures from {expenditures_csv}")
            exp_count = self.import_expenditures(fy.id, expenditures_csv, data_source.id, transcribed_by)
            logger.info(f"Imported {exp_count} expenditure records")
        else:
            self.warnings.append(f"Expenditure file not found: {expenditures_csv}")

        # Import fund balance
        if fund_balance_csv.exists():
            logger.info(f"Importing fund balance from {fund_balance_csv}")
            self.import_fund_balance(fy.id, fund_balance_csv, data_source.id, transcribed_by)
            logger.info("Imported fund balance")
        else:
            self.warnings.append(f"Fund balance file not found: {fund_balance_csv}")

        # Validate imported data
        self.validate_fiscal_year_data(fy.id)

        if self.validation_errors:
            logger.error("Validation errors found:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
            return False

        if self.warnings:
            logger.warning("Warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        # Mark fiscal year as complete
        fy.revenues_complete = True
        fy.expenditures_complete = True
        self.db.commit()

        logger.info("Import completed successfully")
        return True

    def get_or_create_city(self, city_name: str) -> City:
        """Get existing city or create new one."""
        city = self.db.query(City).filter(City.name == city_name).first()

        if not city:
            logger.info(f"Creating new city: {city_name}")
            city = City(
                name=city_name,
                state="CA",
                county="Unknown",  # TODO: Add county info
                fiscal_year_end_month=6,
                fiscal_year_end_day=30,
            )
            self.db.add(city)
            self.db.commit()
            self.db.refresh(city)

        return city

    def get_or_create_fiscal_year(
        self,
        city_id: int,
        year: int,
        cafr_url: str
    ) -> FiscalYear:
        """Get existing fiscal year or create new one."""
        fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id,
            FiscalYear.year == year
        ).first()

        if not fy:
            logger.info(f"Creating fiscal year {year}")
            fy = FiscalYear(
                city_id=city_id,
                year=year,
                start_date=date(year - 1, 7, 1),
                end_date=date(year, 6, 30),
                cafr_available=True,
                cafr_url=cafr_url,
            )
            self.db.add(fy)
            self.db.commit()
            self.db.refresh(fy)

        return fy

    def create_data_source(
        self,
        city_name: str,
        fiscal_year: int,
        cafr_url: str
    ) -> DataSource:
        """Create data source record for this CAFR."""
        source = DataSource(
            name=f"{city_name} CAFR FY{fiscal_year}",
            source_type="CAFR",
            organization=f"City of {city_name}",
            url=cafr_url,
            description=f"Comprehensive Annual Financial Report for {city_name} fiscal year {fiscal_year}",
            reliability_rating="High",
            access_method="Manual",
            expected_update_frequency="Annual",
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def import_revenues(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> int:
        """Import revenue data from CSV."""
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Get or create category
                    category = self.get_or_create_revenue_category(row['category'])

                    # Create revenue record
                    revenue = Revenue(
                        fiscal_year_id=fiscal_year_id,
                        category_id=category.id,
                        fund_type=row.get('fund_type', 'General'),
                        budget_amount=self.parse_decimal(row.get('budget_amount')),
                        actual_amount=self.parse_decimal(row['actual_amount']),
                        source_document_type="CAFR",
                        is_estimated=False,
                        confidence_level="High",
                        notes=row.get('notes'),
                    )

                    # Calculate variance if budget provided
                    if revenue.budget_amount:
                        revenue.variance_amount = revenue.actual_amount - revenue.budget_amount
                        if revenue.budget_amount > 0:
                            revenue.variance_percent = (
                                (revenue.variance_amount / revenue.budget_amount) * 100
                            )

                    self.db.add(revenue)
                    self.db.flush()  # Get ID

                    # Create lineage record
                    self.create_lineage_record(
                        "revenues",
                        revenue.id,
                        "actual_amount",
                        source_id,
                        transcribed_by
                    )

                    count += 1

                except Exception as e:
                    self.validation_errors.append(
                        f"Error importing revenue '{row.get('category')}': {e}"
                    )

        self.db.commit()
        return count

    def import_expenditures(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> int:
        """Import expenditure data from CSV."""
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    category = self.get_or_create_expenditure_category(row['category'])

                    expenditure = Expenditure(
                        fiscal_year_id=fiscal_year_id,
                        category_id=category.id,
                        fund_type=row.get('fund_type', 'General'),
                        department=row.get('department'),
                        budget_amount=self.parse_decimal(row.get('budget_amount')),
                        actual_amount=self.parse_decimal(row['actual_amount']),
                        source_document_type="CAFR",
                        is_estimated=False,
                        confidence_level="High",
                        notes=row.get('notes'),
                    )

                    if expenditure.budget_amount:
                        expenditure.variance_amount = expenditure.actual_amount - expenditure.budget_amount
                        if expenditure.budget_amount > 0:
                            expenditure.variance_percent = (
                                (expenditure.variance_amount / expenditure.budget_amount) * 100
                            )

                    self.db.add(expenditure)
                    self.db.flush()

                    self.create_lineage_record(
                        "expenditures",
                        expenditure.id,
                        "actual_amount",
                        source_id,
                        transcribed_by
                    )

                    count += 1

                except Exception as e:
                    self.validation_errors.append(
                        f"Error importing expenditure '{row.get('category')}': {e}"
                    )

        self.db.commit()
        return count

    def import_fund_balance(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> None:
        """Import fund balance from CSV."""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fund_balance = FundBalance(
                    fiscal_year_id=fiscal_year_id,
                    fund_type=row.get('fund_type', 'General'),
                    nonspendable=self.parse_decimal(row.get('nonspendable', 0)),
                    restricted=self.parse_decimal(row.get('restricted', 0)),
                    committed=self.parse_decimal(row.get('committed', 0)),
                    assigned=self.parse_decimal(row.get('assigned', 0)),
                    unassigned=self.parse_decimal(row.get('unassigned', 0)),
                    total_fund_balance=self.parse_decimal(row['total']),
                    source_document_type="CAFR",
                )

                self.db.add(fund_balance)
                self.db.flush()

                self.create_lineage_record(
                    "fund_balances",
                    fund_balance.id,
                    "total_fund_balance",
                    source_id,
                    transcribed_by
                )

        self.db.commit()

    def get_or_create_revenue_category(self, category_name: str) -> RevenueCategory:
        """Get or create revenue category."""
        category = self.db.query(RevenueCategory).filter(
            RevenueCategory.standard_name == category_name
        ).first()

        if not category:
            # Simple categorization - can be enhanced later
            level1 = category_name.split(" - ")[0] if " - " in category_name else category_name

            category = RevenueCategory(
                category_level1=level1,
                standard_name=category_name,
                is_recurring=True,
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        return category

    def get_or_create_expenditure_category(self, category_name: str) -> ExpenditureCategory:
        """Get or create expenditure category."""
        category = self.db.query(ExpenditureCategory).filter(
            ExpenditureCategory.standard_name == category_name
        ).first()

        if not category:
            level1 = category_name.split(" - ")[0] if " - " in category_name else category_name

            category = ExpenditureCategory(
                category_level1=level1,
                standard_name=category_name,
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        return category

    def create_lineage_record(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        source_id: int,
        transcribed_by: str
    ) -> None:
        """Create data lineage record."""
        lineage = DataLineage(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            source_id=source_id,
            extraction_method="Manual",
            extracted_by=transcribed_by,
            extracted_at=datetime.utcnow(),
            validated=True,  # Assume manual entry is validated
            confidence_level="High",
        )
        self.db.add(lineage)

    def validate_fiscal_year_data(self, fiscal_year_id: int) -> None:
        """Validate imported data for internal consistency."""
        from sqlalchemy import func

        # Check that revenues sum correctly
        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == fiscal_year_id
        ).scalar() or 0

        if total_revenues == 0:
            self.validation_errors.append("Total revenues is zero")

        # Check that expenditures sum correctly
        total_expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == fiscal_year_id
        ).scalar() or 0

        if total_expenditures == 0:
            self.validation_errors.append("Total expenditures is zero")

        # Check for negative values (should be rare)
        negative_revenues = self.db.query(Revenue).filter(
            Revenue.fiscal_year_id == fiscal_year_id,
            Revenue.actual_amount < 0
        ).count()

        if negative_revenues > 0:
            self.warnings.append(f"{negative_revenues} negative revenue values found")

        logger.info(f"Validation: Total revenues = ${total_revenues:,.2f}")
        logger.info(f"Validation: Total expenditures = ${total_expenditures:,.2f}")
        logger.info(f"Validation: Operating balance = ${total_revenues - total_expenditures:,.2f}")

    @staticmethod
    def parse_decimal(value: Any) -> Decimal:
        """Parse string to Decimal, handling currency formatting."""
        if value is None or value == '':
            return Decimal(0)

        # Remove currency symbols, commas, parentheses
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
            # Handle parentheses as negative
            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]

        return Decimal(value)


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 7:
        print("Usage: python import_cafr_manual.py CITY_NAME YEAR REVENUES_CSV EXPENDITURES_CSV FUND_BALANCE_CSV CAFR_URL [TRANSCRIBED_BY]")
        print()
        print("Example:")
        print("  python import_cafr_manual.py Vallejo 2024 revenues_2024.csv expenditures_2024.csv fund_balance_2024.csv https://example.com/cafr.pdf 'John Doe'")
        sys.exit(1)

    city_name = sys.argv[1]
    year = int(sys.argv[2])
    revenues_csv = Path(sys.argv[3])
    expenditures_csv = Path(sys.argv[4])
    fund_balance_csv = Path(sys.argv[5])
    cafr_url = sys.argv[6]
    transcribed_by = sys.argv[7] if len(sys.argv) > 7 else "Unknown"

    db = SessionLocal()
    try:
        importer = CAFRImporter(db)
        success = importer.import_from_csv(
            city_name=city_name,
            fiscal_year=year,
            revenues_csv=revenues_csv,
            expenditures_csv=expenditures_csv,
            fund_balance_csv=fund_balance_csv,
            cafr_url=cafr_url,
            transcribed_by=transcribed_by
        )

        if success:
            print("✅ Import completed successfully!")
            sys.exit(0)
        else:
            print("❌ Import completed with errors")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
