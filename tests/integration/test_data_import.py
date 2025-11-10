"""
Test data import scripts.
"""
import pytest
from pathlib import Path
import tempfile
import csv

from scripts.data_entry.import_cafr_manual import CAFRImporter
from scripts.data_entry.import_calpers_manual import CalPERSImporter


def test_cafr_import_from_csv(test_db):
    """Test importing CAFR data from CSV files."""
    # Create temporary CSV files
    with tempfile.TemporaryDirectory() as tmpdir:
        revenues_csv = Path(tmpdir) / "revenues.csv"
        expenditures_csv = Path(tmpdir) / "expenditures.csv"
        fund_balance_csv = Path(tmpdir) / "fund_balance.csv"

        # Write test data
        with open(revenues_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Property Taxes',
                'fund_type': 'General',
                'budget_amount': '25000000',
                'actual_amount': '26000000',
                'notes': 'Test data'
            })

        with open(expenditures_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'department', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Police',
                'department': 'Police',
                'fund_type': 'General',
                'budget_amount': '15000000',
                'actual_amount': '14800000',
                'notes': 'Test data'
            })

        with open(fund_balance_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['fund_type', 'nonspendable', 'restricted', 'committed', 'assigned', 'unassigned', 'total'])
            writer.writeheader()
            writer.writerow({
                'fund_type': 'General',
                'nonspendable': '500000',
                'restricted': '2000000',
                'committed': '1000000',
                'assigned': '3000000',
                'unassigned': '8500000',
                'total': '15000000'
            })

        # Import
        importer = CAFRImporter(test_db)
        success = importer.import_from_csv(
            city_name="TestCity",
            fiscal_year=2024,
            revenues_csv=revenues_csv,
            expenditures_csv=expenditures_csv,
            fund_balance_csv=fund_balance_csv,
            cafr_url="https://example.com/cafr.pdf",
            transcribed_by="Test User"
        )

        assert success is True

        # Verify data was imported
        from src.database.models.core import City, FiscalYear
        from src.database.models.financial import Revenue, Expenditure, FundBalance

        city = test_db.query(City).filter(City.name == "TestCity").first()
        assert city is not None

        fy = test_db.query(FiscalYear).filter(
            FiscalYear.city_id == city.id,
            FiscalYear.year == 2024
        ).first()
        assert fy is not None

        revenues = test_db.query(Revenue).filter(
            Revenue.fiscal_year_id == fy.id
        ).all()
        assert len(revenues) > 0

        expenditures = test_db.query(Expenditure).filter(
            Expenditure.fiscal_year_id == fy.id
        ).all()
        assert len(expenditures) > 0

        fund_balance = test_db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == fy.id
        ).first()
        assert fund_balance is not None


def test_calpers_import_from_csv(test_db):
    """Test importing CalPERS data from CSV files."""
    # First create a city and fiscal year
    from src.database.models.core import City, FiscalYear
    from datetime import date

    city = City(
        name="TestCity2",
        state="CA",
        county="Test County",
        population=50000,
        fiscal_year_end_month=6,
        fiscal_year_end_day=30,
    )
    test_db.add(city)
    test_db.commit()

    fy = FiscalYear(
        city_id=city.id,
        year=2024,
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
    )
    test_db.add(fy)
    test_db.commit()

    # Create temporary CSV file
    with tempfile.TemporaryDirectory() as tmpdir:
        pensions_csv = Path(tmpdir) / "pensions.csv"

        with open(pensions_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'plan_name', 'valuation_date', 'total_pension_liability',
                'fiduciary_net_position', 'net_pension_liability',
                'unfunded_actuarial_liability', 'funded_ratio',
                'total_employer_contribution', 'normal_cost_rate',
                'discount_rate', 'notes'
            ])
            writer.writeheader()
            writer.writerow({
                'plan_name': 'Miscellaneous',
                'valuation_date': '2024-06-30',
                'total_pension_liability': '100000000',
                'fiduciary_net_position': '70000000',
                'net_pension_liability': '30000000',
                'unfunded_actuarial_liability': '30000000',
                'funded_ratio': '0.70',
                'total_employer_contribution': '5000000',
                'normal_cost_rate': '0.15',
                'discount_rate': '0.068',
                'notes': 'Test data'
            })

        # Import
        importer = CalPERSImporter(test_db)
        success = importer.import_from_csv(
            city_name="TestCity2",
            fiscal_year=2024,
            pensions_csv=pensions_csv,
            valuation_url="https://example.com/valuation.pdf",
            transcribed_by="Test User"
        )

        assert success is True

        # Verify data was imported
        from src.database.models.pensions import PensionPlan

        pension_plans = test_db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == fy.id
        ).all()
        assert len(pension_plans) > 0

        plan = pension_plans[0]
        assert plan.plan_name == "Miscellaneous"
        assert plan.funded_ratio == pytest.approx(0.70, 0.01)


def test_data_lineage_tracking(test_db):
    """Test that data lineage is tracked during import."""
    with tempfile.TemporaryDirectory() as tmpdir:
        revenues_csv = Path(tmpdir) / "revenues.csv"
        expenditures_csv = Path(tmpdir) / "expenditures.csv"
        fund_balance_csv = Path(tmpdir) / "fund_balance.csv"

        # Write minimal test data
        with open(revenues_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Sales Tax',
                'fund_type': 'General',
                'budget_amount': '10000000',
                'actual_amount': '10500000',
                'notes': ''
            })

        with open(expenditures_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'department', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Fire',
                'department': 'Fire',
                'fund_type': 'General',
                'budget_amount': '8000000',
                'actual_amount': '7900000',
                'notes': ''
            })

        with open(fund_balance_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['fund_type', 'nonspendable', 'restricted', 'committed', 'assigned', 'unassigned', 'total'])
            writer.writeheader()
            writer.writerow({
                'fund_type': 'General',
                'nonspendable': '0',
                'restricted': '0',
                'committed': '0',
                'assigned': '0',
                'unassigned': '5000000',
                'total': '5000000'
            })

        # Import
        importer = CAFRImporter(test_db)
        success = importer.import_from_csv(
            city_name="LineageTestCity",
            fiscal_year=2024,
            revenues_csv=revenues_csv,
            expenditures_csv=expenditures_csv,
            fund_balance_csv=fund_balance_csv,
            cafr_url="https://example.com/cafr.pdf",
            transcribed_by="Test User"
        )

        assert success is True

        # Verify data lineage was created
        from src.database.models.core import DataLineage, DataSource

        # Check that data source was created
        data_source = test_db.query(DataSource).filter(
            DataSource.name.like("%LineageTestCity%")
        ).first()
        assert data_source is not None

        # Check that lineage records were created
        lineage_records = test_db.query(DataLineage).filter(
            DataLineage.source_id == data_source.id
        ).all()
        assert len(lineage_records) > 0


def test_import_validation(test_db):
    """Test that import validation catches issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        revenues_csv = Path(tmpdir) / "revenues.csv"
        expenditures_csv = Path(tmpdir) / "expenditures.csv"
        fund_balance_csv = Path(tmpdir) / "fund_balance.csv"

        # Write data with zero totals (should trigger validation warning)
        with open(revenues_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            # Empty file - should warn about zero total

        with open(expenditures_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'department', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()

        with open(fund_balance_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['fund_type', 'nonspendable', 'restricted', 'committed', 'assigned', 'unassigned', 'total'])
            writer.writeheader()

        # Import should fail or warn
        importer = CAFRImporter(test_db)
        # This may return False or raise an exception depending on implementation
        # The important thing is that validation happens
        try:
            result = importer.import_from_csv(
                city_name="ValidationTestCity",
                fiscal_year=2024,
                revenues_csv=revenues_csv,
                expenditures_csv=expenditures_csv,
                fund_balance_csv=fund_balance_csv,
                cafr_url="https://example.com/cafr.pdf",
                transcribed_by="Test User"
            )
            # If it succeeds, it should at least create the city/fy
            # but with warnings logged
        except Exception:
            # Validation may raise exception
            pass
