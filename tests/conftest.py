"""
Pytest fixtures for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from decimal import Decimal

from src.database.base import Base
from src.database.models.core import City, FiscalYear
from src.database.models.financial import (
    Revenue, Expenditure, FundBalance,
    RevenueCategory, ExpenditureCategory
)
from src.database.models.pensions import PensionPlan


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_city(test_db):
    """Create a sample city for testing."""
    city = City(
        name="TestCity",
        state="CA",
        county="Test County",
        population=100000,
        fiscal_year_end_month=6,
        fiscal_year_end_day=30,
    )
    test_db.add(city)
    test_db.commit()
    test_db.refresh(city)
    return city


@pytest.fixture
def sample_fiscal_year(test_db, sample_city):
    """Create a sample fiscal year."""
    fy = FiscalYear(
        city_id=sample_city.id,
        year=2024,
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
        cafr_available=True,
        revenues_complete=True,
        expenditures_complete=True,
        pension_data_complete=True,
    )
    test_db.add(fy)
    test_db.commit()
    test_db.refresh(fy)
    return fy


@pytest.fixture
def sample_financial_data(test_db, sample_fiscal_year):
    """Create sample financial data."""
    # Create categories
    rev_category = RevenueCategory(
        category_level1="Taxes",
        standard_name="Property Taxes",
        is_recurring=True,
    )
    exp_category = ExpenditureCategory(
        category_level1="Public Safety",
        standard_name="Police",
    )
    test_db.add(rev_category)
    test_db.add(exp_category)
    test_db.commit()

    # Create revenues
    revenue = Revenue(
        fiscal_year_id=sample_fiscal_year.id,
        category_id=rev_category.id,
        fund_type="General",
        actual_amount=Decimal("50000000"),
        source_document_type="CAFR",
    )
    test_db.add(revenue)

    # Create expenditures
    expenditure = Expenditure(
        fiscal_year_id=sample_fiscal_year.id,
        category_id=exp_category.id,
        fund_type="General",
        actual_amount=Decimal("48000000"),
        source_document_type="CAFR",
    )
    test_db.add(expenditure)

    # Create fund balance
    fund_balance = FundBalance(
        fiscal_year_id=sample_fiscal_year.id,
        fund_type="General",
        total_fund_balance=Decimal("10000000"),
        source_document_type="CAFR",
    )
    test_db.add(fund_balance)

    # Create pension plan
    pension = PensionPlan(
        fiscal_year_id=sample_fiscal_year.id,
        plan_name="Miscellaneous",
        valuation_date=date(2024, 6, 30),
        total_pension_liability=Decimal("200000000"),
        fiduciary_net_position=Decimal("130000000"),
        net_pension_liability=Decimal("70000000"),
        unfunded_actuarial_liability=Decimal("70000000"),
        funded_ratio=Decimal("0.65"),
        total_employer_contribution=Decimal("10000000"),
        discount_rate=Decimal("0.068"),
        source_document="CalPERS Valuation",
    )
    test_db.add(pension)

    test_db.commit()

    return {
        "revenue": revenue,
        "expenditure": expenditure,
        "fund_balance": fund_balance,
        "pension": pension,
    }
