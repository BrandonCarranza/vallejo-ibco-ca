"""
Manual CalPERS pension data import.

Import pension data transcribed from CalPERS valuation reports.
"""
import csv
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from src.config.database import SessionLocal
from src.database.models.core import City, FiscalYear, DataSource, DataLineage
from src.database.models.pensions import PensionPlan
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class CalPERSImporter:
    """Import CalPERS pension data."""

    def __init__(self, db):
        self.db = db

    def import_from_csv(
        self,
        city_name: str,
        fiscal_year: int,
        pensions_csv: Path,
        valuation_url: str,
        transcribed_by: str
    ) -> bool:
        """
        Import CalPERS data from CSV.

        CSV Format:
        plan_name,valuation_date,total_pension_liability,fiduciary_net_position,
        unfunded_actuarial_liability,funded_ratio,total_employer_contribution,
        discount_rate,notes
        """
        logger.info(f"Importing CalPERS data for {city_name} FY {fiscal_year}")

        # Get fiscal year
        fy = self.db.query(FiscalYear).join(FiscalYear.city).filter(
            City.name == city_name,
            FiscalYear.year == fiscal_year
        ).first()

        if not fy:
            logger.error(f"Fiscal year not found: {city_name} {fiscal_year}")
            return False

        # Create data source
        source = DataSource(
            name=f"{city_name} CalPERS Valuation FY{fiscal_year}",
            source_type="CalPERS",
            organization="CalPERS",
            url=valuation_url,
            reliability_rating="High",
            access_method="Manual",
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        # Import pension plans
        with open(pensions_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pension_plan = PensionPlan(
                    fiscal_year_id=fy.id,
                    plan_name=row['plan_name'],
                    valuation_date=date.fromisoformat(row['valuation_date']),
                    total_pension_liability=Decimal(row['total_pension_liability']),
                    fiduciary_net_position=Decimal(row['fiduciary_net_position']),
                    net_pension_liability=Decimal(row['unfunded_actuarial_liability']),
                    funded_ratio=Decimal(row['funded_ratio']),
                    total_employer_contribution=Decimal(row.get('total_employer_contribution', 0)),
                    discount_rate=Decimal(row.get('discount_rate', 0)),
                    source_document="CalPERS Valuation Report",
                    source_url=valuation_url,
                    is_preliminary=False,
                    confidence_level="High",
                    notes=row.get('notes'),
                )

                self.db.add(pension_plan)
                self.db.flush()

                # Create lineage
                lineage = DataLineage(
                    table_name="pension_plans",
                    record_id=pension_plan.id,
                    field_name="net_pension_liability",
                    source_id=source.id,
                    extraction_method="Manual",
                    extracted_by=transcribed_by,
                    extracted_at=datetime.utcnow(),
                    validated=True,
                    confidence_level="High",
                )
                self.db.add(lineage)

        self.db.commit()

        # Mark pension data as complete
        fy.pension_data_complete = True
        fy.calpers_valuation_available = True
        fy.calpers_valuation_url = valuation_url
        self.db.commit()

        logger.info("CalPERS import completed successfully")
        return True


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 6:
        print("Usage: python import_calpers_manual.py CITY_NAME YEAR PENSIONS_CSV VALUATION_URL TRANSCRIBED_BY")
        print()
        print("Example:")
        print("  python import_calpers_manual.py Vallejo 2024 pensions_2024.csv https://example.com/valuation.pdf 'John Doe'")
        sys.exit(1)

    city_name = sys.argv[1]
    year = int(sys.argv[2])
    pensions_csv = Path(sys.argv[3])
    valuation_url = sys.argv[4]
    transcribed_by = sys.argv[5]

    db = SessionLocal()
    try:
        importer = CalPERSImporter(db)
        success = importer.import_from_csv(
            city_name,
            year,
            pensions_csv,
            valuation_url,
            transcribed_by
        )

        if success:
            print("✅ Import completed successfully!")
            sys.exit(0)
        else:
            print("❌ Import failed")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
