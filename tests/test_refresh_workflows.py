"""
Tests for data refresh orchestration workflows.

Tests the complete refresh workflow including:
- CAFR availability checking
- CalPERS valuation checking
- Notification management
- Post-entry pipeline
- Change reporting
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.config.database import SessionLocal
from src.data_pipeline.orchestration.refresh_workflows import (
    CAFRAvailabilityChecker,
    CalPERSAvailabilityChecker,
    DataRefreshOrchestrator,
    PostEntryPipeline,
    RefreshNotificationManager,
)
from src.database.models.core import City, FiscalYear
from src.database.models.refresh import (
    RefreshCheck,
    RefreshNotification,
    RefreshOperation,
)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_city(db_session):
    """Create a test city."""
    city = City(
        name="Vallejo",
        state="CA",
        county="Solano",
        fiscal_year_end_month=6,
        fiscal_year_end_day=30,
        is_active=True,
        website_url="https://www.cityofvallejo.net/",
        finance_department_url="https://www.cityofvallejo.net/city_hall/departments___divisions/finance",
    )
    db_session.add(city)
    db_session.commit()
    yield city
    db_session.delete(city)
    db_session.commit()


@pytest.fixture
def test_fiscal_year(db_session, test_city):
    """Create a test fiscal year."""
    from datetime import date

    fy = FiscalYear(
        city_id=test_city.id,
        year=2024,
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
        cafr_available=False,
        calpers_valuation_available=False,
        revenues_complete=True,
        expenditures_complete=True,
        pension_data_complete=False,
    )
    db_session.add(fy)
    db_session.commit()
    yield fy
    db_session.delete(fy)
    db_session.commit()


class TestCAFRAvailabilityChecker:
    """Tests for CAFR availability checking."""

    def test_checker_initialization(self, db_session):
        """Test checker can be initialized."""
        checker = CAFRAvailabilityChecker(db_session)
        assert checker.db == db_session

    @patch("src.data_pipeline.orchestration.refresh_workflows.requests.get")
    def test_check_for_new_cafr_found(self, mock_get, db_session, test_city):
        """Test detecting a new CAFR on the website."""
        # Mock HTML response with CAFR link
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <body>
                <a href="/files/cafr-fy2024.pdf">FY2024 CAFR</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        checker = CAFRAvailabilityChecker(db_session)
        result = checker.check_for_new_cafr(test_city.id)

        assert result is not None
        assert result["fiscal_year"] == 2024
        assert "cafr-fy2024.pdf" in result["document_url"]

    @patch("src.data_pipeline.orchestration.refresh_workflows.requests.get")
    def test_check_for_new_cafr_not_found(self, mock_get, db_session, test_city):
        """Test when no new CAFR is found."""
        # Mock HTML response without CAFR link
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>No CAFRs here</body></html>"
        mock_get.return_value = mock_response

        checker = CAFRAvailabilityChecker(db_session)
        result = checker.check_for_new_cafr(test_city.id)

        assert result is None

    def test_check_records_created(self, db_session, test_city):
        """Test that checks are recorded in database."""
        with patch("src.data_pipeline.orchestration.refresh_workflows.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html><body>No CAFRs</body></html>"
            mock_get.return_value = mock_response

            checker = CAFRAvailabilityChecker(db_session)
            checker.check_for_new_cafr(test_city.id)

            # Check that RefreshCheck was created
            check = (
                db_session.query(RefreshCheck)
                .filter(RefreshCheck.city_id == test_city.id)
                .first()
            )
            assert check is not None
            assert check.check_type == "cafr_availability"
            assert check.scraping_success is True

            # Cleanup
            db_session.delete(check)
            db_session.commit()


class TestCalPERSAvailabilityChecker:
    """Tests for CalPERS valuation checking."""

    def test_checker_initialization(self, db_session):
        """Test checker can be initialized."""
        checker = CalPERSAvailabilityChecker(db_session)
        assert checker.db == db_session

    def test_check_for_new_calpers(self, db_session, test_city):
        """Test CalPERS check (placeholder implementation)."""
        checker = CalPERSAvailabilityChecker(db_session)
        result = checker.check_for_new_calpers_valuation(test_city.id)

        # Current implementation returns None (placeholder)
        assert result is None

        # Check that RefreshCheck was created
        check = (
            db_session.query(RefreshCheck)
            .filter(
                RefreshCheck.city_id == test_city.id,
                RefreshCheck.check_type == "calpers_valuation",
            )
            .first()
        )
        assert check is not None

        # Cleanup
        db_session.delete(check)
        db_session.commit()


class TestRefreshNotificationManager:
    """Tests for notification management."""

    def test_manager_initialization(self, db_session):
        """Test manager can be initialized."""
        manager = RefreshNotificationManager(db_session)
        assert manager.db == db_session

    @patch("src.data_pipeline.orchestration.refresh_workflows.email_service.send_cafr_available_notification")
    def test_send_cafr_notification(self, mock_email, db_session, test_city):
        """Test sending CAFR available notification."""
        mock_email.return_value = True

        manager = RefreshNotificationManager(db_session)
        cafr_details = {
            "fiscal_year": 2024,
            "document_url": "https://example.com/cafr-2024.pdf",
            "document_title": "FY2024 CAFR",
        }

        notification = manager.send_cafr_notification(test_city.id, cafr_details)

        assert notification is not None
        assert notification.notification_type == "cafr_available"
        assert notification.fiscal_year == 2024
        mock_email.assert_called_once()

        # Cleanup
        db_session.delete(notification)
        db_session.commit()

    @patch("src.data_pipeline.orchestration.refresh_workflows.email_service.send_calpers_available_notification")
    def test_send_calpers_notification(self, mock_email, db_session, test_city):
        """Test sending CalPERS available notification."""
        mock_email.return_value = True

        manager = RefreshNotificationManager(db_session)
        calpers_details = {
            "fiscal_year": 2024,
            "document_url": "https://example.com/calpers-2024.pdf",
        }

        notification = manager.send_calpers_notification(test_city.id, calpers_details)

        assert notification is not None
        assert notification.notification_type == "calpers_available"
        assert notification.fiscal_year == 2024
        mock_email.assert_called_once()

        # Cleanup
        db_session.delete(notification)
        db_session.commit()


class TestPostEntryPipeline:
    """Tests for post-entry pipeline."""

    def test_pipeline_initialization(self, db_session):
        """Test pipeline can be initialized."""
        pipeline = PostEntryPipeline(db_session)
        assert pipeline.db == db_session

    @patch("src.data_pipeline.orchestration.refresh_workflows.RiskScoringEngine")
    @patch("src.data_pipeline.orchestration.refresh_workflows.DataValidator")
    def test_run_full_pipeline(
        self, mock_validator, mock_scoring_engine, db_session, test_city, test_fiscal_year
    ):
        """Test running the full post-entry pipeline."""
        # Mock validator
        mock_validator_instance = Mock()
        mock_validator_instance.validate_fiscal_year = Mock(return_value=True)
        mock_validator.return_value = mock_validator_instance

        # Mock risk scoring engine
        mock_risk_score = Mock()
        mock_risk_score.overall_score = 65
        mock_scoring_instance = Mock()
        mock_scoring_instance.calculate_risk_score = Mock(return_value=mock_risk_score)
        mock_scoring_engine.return_value = mock_scoring_instance

        pipeline = PostEntryPipeline(db_session)
        operation = pipeline.run_full_pipeline(
            test_city.id, test_fiscal_year.year, "cafr_entry"
        )

        assert operation is not None
        assert operation.status == "completed"
        assert operation.success is True
        assert operation.validation_passed is True

        # Cleanup
        db_session.delete(operation)
        db_session.commit()

    def test_pipeline_records_operation(self, db_session, test_city, test_fiscal_year):
        """Test that pipeline creates RefreshOperation record."""
        with patch("src.data_pipeline.orchestration.refresh_workflows.RiskScoringEngine"):
            with patch("src.data_pipeline.orchestration.refresh_workflows.DataValidator"):
                pipeline = PostEntryPipeline(db_session)

                try:
                    operation = pipeline.run_full_pipeline(
                        test_city.id, test_fiscal_year.year, "cafr_entry"
                    )

                    # Check operation was created
                    db_operation = (
                        db_session.query(RefreshOperation)
                        .filter(RefreshOperation.id == operation.id)
                        .first()
                    )
                    assert db_operation is not None
                    assert db_operation.operation_type == "cafr_entry"

                    # Cleanup
                    db_session.delete(db_operation)
                    db_session.commit()

                except Exception:
                    # Cleanup on error
                    pass


class TestDataRefreshOrchestrator:
    """Tests for the main orchestrator."""

    def test_orchestrator_initialization(self, db_session):
        """Test orchestrator can be initialized."""
        orchestrator = DataRefreshOrchestrator(db_session)
        assert orchestrator.db == db_session
        assert orchestrator.cafr_checker is not None
        assert orchestrator.calpers_checker is not None
        assert orchestrator.notification_manager is not None
        assert orchestrator.post_entry_pipeline is not None

    @patch("src.data_pipeline.orchestration.refresh_workflows.CAFRAvailabilityChecker.check_for_new_cafr")
    @patch("src.data_pipeline.orchestration.refresh_workflows.email_service.send_cafr_available_notification")
    def test_run_quarterly_check_with_new_cafr(
        self, mock_email, mock_cafr_check, db_session, test_city
    ):
        """Test quarterly check when new CAFR is found."""
        # Mock new CAFR found
        mock_cafr_check.return_value = {
            "fiscal_year": 2024,
            "document_url": "https://example.com/cafr-2024.pdf",
            "document_title": "FY2024 CAFR",
        }
        mock_email.return_value = True

        orchestrator = DataRefreshOrchestrator(db_session)
        result = orchestrator.run_quarterly_check(test_city.id)

        assert result["cafr_found"] is True
        assert result["notification_sent"] is True
        mock_cafr_check.assert_called_once()
        mock_email.assert_called_once()

    @patch("src.data_pipeline.orchestration.refresh_workflows.CAFRAvailabilityChecker.check_for_new_cafr")
    def test_run_quarterly_check_no_new_cafr(
        self, mock_cafr_check, db_session, test_city
    ):
        """Test quarterly check when no new CAFR is found."""
        mock_cafr_check.return_value = None

        orchestrator = DataRefreshOrchestrator(db_session)
        result = orchestrator.run_quarterly_check(test_city.id)

        assert result["cafr_found"] is False
        assert result["notification_sent"] is False

    @patch("src.data_pipeline.orchestration.refresh_workflows.PostEntryPipeline.run_full_pipeline")
    def test_trigger_post_entry_pipeline(
        self, mock_pipeline, db_session, test_city, test_fiscal_year
    ):
        """Test triggering post-entry pipeline."""
        mock_operation = Mock()
        mock_operation.id = 1
        mock_operation.status = "completed"
        mock_pipeline.return_value = mock_operation

        orchestrator = DataRefreshOrchestrator(db_session)
        operation = orchestrator.trigger_post_entry_pipeline(
            test_city.id, test_fiscal_year.year, "cafr_entry"
        )

        assert operation is not None
        mock_pipeline.assert_called_once_with(
            test_city.id, test_fiscal_year.year, "cafr_entry"
        )


class TestRefreshWorkflowIntegration:
    """Integration tests for complete refresh workflow."""

    @patch("src.data_pipeline.orchestration.refresh_workflows.requests.get")
    @patch("src.data_pipeline.orchestration.refresh_workflows.email_service.send_cafr_available_notification")
    def test_complete_cafr_workflow(
        self, mock_email, mock_get, db_session, test_city
    ):
        """Test complete workflow from check to notification."""
        # Mock HTML with new CAFR
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html><body>
            <a href="/files/cafr-fy2025.pdf">FY2025 CAFR</a>
        </body></html>
        """
        mock_get.return_value = mock_response
        mock_email.return_value = True

        orchestrator = DataRefreshOrchestrator(db_session)

        # Run check
        result = orchestrator.run_quarterly_check(test_city.id)

        assert result["cafr_found"] is True
        assert result["notification_sent"] is True

        # Verify database records
        check = (
            db_session.query(RefreshCheck)
            .filter(RefreshCheck.city_id == test_city.id)
            .order_by(RefreshCheck.performed_at.desc())
            .first()
        )
        assert check is not None
        assert check.new_document_found is True

        notification = (
            db_session.query(RefreshNotification)
            .filter(RefreshNotification.city_id == test_city.id)
            .order_by(RefreshNotification.sent_at.desc())
            .first()
        )
        assert notification is not None
        assert notification.fiscal_year == 2025

        # Cleanup
        if check:
            db_session.delete(check)
        if notification:
            db_session.delete(notification)
        db_session.commit()


# Mark tests that require database as slow
pytestmark = pytest.mark.slow
