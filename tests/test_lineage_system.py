"""
Tests for data lineage and audit trail system.

Tests:
- LineageRecorder helper functions
- DataLineageTracer tracing capabilities
- API endpoints for public lineage access
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.analytics.lineage_tracer import DataLineageTracer, LineageNode, LineageChain
from src.config.database import SessionLocal
from src.database.models.core import City, DataLineage, DataSource, FiscalYear
from src.database.models.financial import Revenue
from src.database.models.risk import RiskScore
from src.utils.lineage_helpers import LineageRecorder, record_cafr_entry


@pytest.fixture
def db_session():
    """Create test database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_data_source(db_session):
    """Create test data source."""
    source = DataSource(
        name="Test CAFR FY2024",
        source_type="CAFR",
        organization="City of Vallejo",
        url="https://example.com/cafr-2024.pdf",
        description="Test CAFR",
        access_method="Manual",
        reliability_rating="High",
    )
    db_session.add(source)
    db_session.commit()
    yield source
    db_session.delete(source)
    db_session.commit()


@pytest.fixture
def test_city(db_session):
    """Create test city."""
    city = City(
        name="Test City",
        state="CA",
        county="Test County",
        fiscal_year_end_month=6,
        fiscal_year_end_day=30,
        is_active=True,
    )
    db_session.add(city)
    db_session.commit()
    yield city
    db_session.delete(city)
    db_session.commit()


@pytest.fixture
def test_fiscal_year(db_session, test_city):
    """Create test fiscal year."""
    from datetime import date

    fy = FiscalYear(
        city_id=test_city.id,
        year=2024,
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
    )
    db_session.add(fy)
    db_session.commit()
    yield fy
    db_session.delete(fy)
    db_session.commit()


class TestLineageRecorder:
    """Tests for LineageRecorder helper class."""

    def test_record_manual_entry(self, db_session, test_data_source):
        """Test recording manual entry lineage."""
        recorder = LineageRecorder(db_session)

        lineage = recorder.record_manual_entry(
            table_name="revenues",
            record_id=1,
            field_name="amount",
            source_id=test_data_source.id,
            extracted_by="Jane Doe",
            source_document_page=34,
            source_document_section="Statement of Activities",
            notes="Total revenues from CAFR",
            confidence_score=100,
        )

        assert lineage is not None
        assert lineage.table_name == "revenues"
        assert lineage.field_name == "amount"
        assert lineage.extraction_method == "Manual"
        assert lineage.extracted_by == "Jane Doe"
        assert lineage.source_document_page == 34
        assert lineage.confidence_score == 100
        assert lineage.validated == False

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()

    def test_validate_lineage(self, db_session, test_data_source):
        """Test validating a lineage record."""
        recorder = LineageRecorder(db_session)

        # Create lineage
        lineage = recorder.record_manual_entry(
            table_name="revenues",
            record_id=1,
            field_name="amount",
            source_id=test_data_source.id,
            extracted_by="Jane Doe",
        )

        # Validate it
        validated_lineage = recorder.validate_lineage(
            lineage_id=lineage.id,
            validated_by="John Smith",
            validation_notes="Cross-checked with budget document",
        )

        assert validated_lineage.validated == True
        assert validated_lineage.validated_by == "John Smith"
        assert validated_lineage.validation_notes == "Cross-checked with budget document"
        assert validated_lineage.validated_at is not None

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()

    def test_record_automated_extraction(self, db_session, test_data_source):
        """Test recording automated extraction lineage."""
        recorder = LineageRecorder(db_session)

        lineage = recorder.record_automated_extraction(
            table_name="revenues",
            record_id=1,
            field_name="amount",
            source_id=test_data_source.id,
            extraction_system="PDF_Extractor_v1",
            source_document_page=34,
            confidence_score=92,
        )

        assert lineage is not None
        assert lineage.extraction_method == "Automated"
        assert lineage.extracted_by == "PDF_Extractor_v1"
        assert lineage.confidence_score == 92
        assert lineage.confidence_level == "Medium"

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()

    def test_bulk_record_manual_entry(self, db_session, test_data_source):
        """Test bulk recording of lineage records."""
        recorder = LineageRecorder(db_session)

        field_mappings = {
            "total_revenues": "Total revenues",
            "total_expenditures": "Total expenditures",
            "operating_balance": "Operating balance",
        }

        lineage_records = recorder.bulk_record_manual_entry(
            table_name="fiscal_years",
            record_id=1,
            field_mappings=field_mappings,
            source_id=test_data_source.id,
            extracted_by="Jane Doe",
            source_document_page=34,
        )

        assert len(lineage_records) == 3
        assert all(l.extraction_method == "Manual" for l in lineage_records)
        assert all(l.extracted_by == "Jane Doe" for l in lineage_records)

        # Cleanup
        for lineage in lineage_records:
            db_session.delete(lineage)
        db_session.commit()


class TestDataLineageTracer:
    """Tests for DataLineageTracer."""

    def test_tracer_initialization(self, db_session):
        """Test tracer can be initialized."""
        tracer = DataLineageTracer(db_session)
        assert tracer.db == db_session

    def test_trace_data_point(self, db_session, test_data_source):
        """Test tracing a single data point."""
        # Create lineage record
        recorder = LineageRecorder(db_session)
        lineage = recorder.record_manual_entry(
            table_name="revenues",
            record_id=1,
            field_name="amount",
            source_id=test_data_source.id,
            extracted_by="Jane Doe",
            source_document_page=34,
        )

        # Trace it
        tracer = DataLineageTracer(db_session)
        node = tracer.trace_data_point("revenues", 1, "amount")

        assert node is not None
        assert node.table_name == "revenues"
        assert node.field_name == "amount"
        assert node.extracted_by == "Jane Doe"
        assert node.source_document_page == 34

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()

    def test_trace_nonexistent_data_point(self, db_session):
        """Test tracing a data point with no lineage."""
        tracer = DataLineageTracer(db_session)
        node = tracer.trace_data_point("revenues", 999, "amount")

        assert node is None


class TestLineageNode:
    """Tests for LineageNode class."""

    def test_node_to_dict(self, db_session, test_data_source):
        """Test converting node to dictionary."""
        # Create lineage
        recorder = LineageRecorder(db_session)
        lineage = recorder.record_manual_entry(
            table_name="revenues",
            record_id=1,
            field_name="amount",
            source_id=test_data_source.id,
            extracted_by="Jane Doe",
            source_document_page=34,
            source_document_section="Statement of Activities",
            confidence_score=100,
        )

        node = LineageNode("revenues", 1, "amount", 1000000, lineage)
        node_dict = node.to_dict()

        assert node_dict["table_name"] == "revenues"
        assert node_dict["field_name"] == "amount"
        assert node_dict["value"] == "1000000"
        assert node_dict["source"]["page"] == 34
        assert node_dict["extraction"]["extracted_by"] == "Jane Doe"
        assert node_dict["confidence"]["score"] == 100

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()


class TestLineageConvenienceFunctions:
    """Tests for convenience functions."""

    def test_record_cafr_entry(self, db_session, test_data_source):
        """Test CAFR entry convenience function."""
        lineage = record_cafr_entry(
            db=db_session,
            table_name="revenues",
            record_id=1,
            field_name="amount",
            cafr_source_id=test_data_source.id,
            page_number=34,
            section_name="Statement of Activities",
            entered_by="Jane Doe",
            notes="Total revenues",
        )

        assert lineage is not None
        assert lineage.source_document_page == 34
        assert lineage.source_document_section == "Statement of Activities"
        assert lineage.confidence_score == 100

        # Cleanup
        db_session.delete(lineage)
        db_session.commit()


class TestLineageChain:
    """Tests for LineageChain class."""

    def test_chain_creation(self):
        """Test creating a lineage chain."""
        root = LineageNode("risk_scores", 1, "overall_score", 68)
        chain = LineageChain(root)

        assert chain.root == root
        assert len(chain.nodes) == 1

    def test_add_dependency(self):
        """Test adding dependencies to chain."""
        root = LineageNode("risk_scores", 1, "overall_score", 68)
        chain = LineageChain(root)

        child = LineageNode("pension_plans", 1, "funded_ratio", 0.62)
        chain.add_dependency(root, child)

        assert len(chain.nodes) == 2
        assert len(chain.dependencies) == 1
        assert chain.dependencies[0] == (root, child)


# Mark tests that require database as slow
pytestmark = pytest.mark.slow
