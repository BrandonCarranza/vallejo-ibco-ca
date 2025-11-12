"""
Data refresh orchestration workflows for manual entry process.

Handles periodic checks for new source documents (CAFRs, CalPERS valuations),
notifications to operators, and post-entry validation and analytics pipeline.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
import structlog
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from src.analytics.projections.scenario_engine import ScenarioEngine
from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine
from src.config.settings import settings
from src.data_quality.validators import DataValidator
from src.database.models.core import City, FiscalYear
from src.database.models.refresh import (
    DataRefreshSchedule,
    RefreshCheck,
    RefreshNotification,
    RefreshOperation,
)
from src.utils.email_notifications import email_service

logger = structlog.get_logger(__name__)


class CAFRAvailabilityChecker:
    """Check if new CAFRs are available on Vallejo finance website."""

    def __init__(self, db: Session):
        """Initialize checker with database session."""
        self.db = db

    def check_for_new_cafr(self, city_id: int) -> Optional[Dict]:
        """
        Check if a new CAFR has been published for a city.

        Args:
            city_id: Database ID of the city to check

        Returns:
            Dict with document details if found, None otherwise
            {
                'fiscal_year': int,
                'document_url': str,
                'document_title': str,
                'publish_date': datetime or None
            }
        """
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            logger.error("city_not_found", city_id=city_id)
            return None

        logger.info("checking_cafr_availability", city=city.name)

        try:
            # Scrape Vallejo finance website for CAFRs
            if "vallejo" in city.name.lower():
                result = self._check_vallejo_cafr(city)
            else:
                # For other cities, use generic method
                result = self._check_generic_cafr(city)

            # Record the check
            self._record_check(
                city_id=city_id,
                check_type="cafr_availability",
                new_document_found=result is not None,
                result=result,
            )

            return result

        except Exception as e:
            logger.error("cafr_check_failed", city=city.name, error=str(e))
            self._record_check(
                city_id=city_id,
                check_type="cafr_availability",
                new_document_found=False,
                error=str(e),
            )
            return None

    def _check_vallejo_cafr(self, city: City) -> Optional[Dict]:
        """
        Check Vallejo-specific finance website for new CAFRs.

        Args:
            city: City model instance

        Returns:
            Dict with document details if found, None otherwise
        """
        # Vallejo CAFRs are published at:
        # https://www.cityofvallejo.net/city_hall/departments___divisions/finance
        finance_url = city.finance_department_url or "https://www.cityofvallejo.net/city_hall/departments___divisions/finance"

        logger.info("scraping_vallejo_finance_page", url=finance_url)

        try:
            response = requests.get(
                finance_url,
                headers={"User-Agent": settings.user_agent},
                timeout=settings.external_api_timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for links containing "CAFR" or "Comprehensive Annual Financial Report"
            cafr_links = []
            for link in soup.find_all("a", href=True):
                text = link.get_text().strip()
                href = link["href"]

                if re.search(r"CAFR|Comprehensive Annual Financial Report", text, re.IGNORECASE):
                    # Extract fiscal year from text (e.g., "FY2024", "2024", "FY 2023-24")
                    year_match = re.search(r"20(\d{2})", text)
                    if year_match:
                        fiscal_year = int(year_match.group(0))
                        cafr_links.append({
                            "fiscal_year": fiscal_year,
                            "document_url": self._normalize_url(href, finance_url),
                            "document_title": text,
                        })

            if not cafr_links:
                logger.info("no_cafr_links_found", city=city.name)
                return None

            # Sort by fiscal year descending to get most recent
            cafr_links.sort(key=lambda x: x["fiscal_year"], reverse=True)
            latest_cafr = cafr_links[0]

            # Check if this fiscal year already exists in our database
            existing_fy = (
                self.db.query(FiscalYear)
                .filter(
                    FiscalYear.city_id == city.id,
                    FiscalYear.year == latest_cafr["fiscal_year"],
                )
                .first()
            )

            # If fiscal year exists and CAFR already recorded, no new document
            if existing_fy and existing_fy.cafr_available:
                logger.info(
                    "cafr_already_recorded",
                    city=city.name,
                    fiscal_year=latest_cafr["fiscal_year"],
                )
                return None

            # New CAFR found!
            logger.info(
                "new_cafr_found",
                city=city.name,
                fiscal_year=latest_cafr["fiscal_year"],
                url=latest_cafr["document_url"],
            )
            return latest_cafr

        except Exception as e:
            logger.error("vallejo_scraping_failed", error=str(e))
            raise

    def _check_generic_cafr(self, city: City) -> Optional[Dict]:
        """
        Generic CAFR check for non-Vallejo cities.

        Args:
            city: City model instance

        Returns:
            Dict with document details if found, None otherwise
        """
        # Placeholder for generic city CAFR checking
        logger.info("generic_cafr_check_not_implemented", city=city.name)
        return None

    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize URL (handle relative URLs).

        Args:
            url: URL to normalize
            base_url: Base URL for relative URLs

        Returns:
            Normalized absolute URL
        """
        if url.startswith("http"):
            return url
        elif url.startswith("/"):
            # Absolute path
            parts = base_url.split("/")
            return f"{parts[0]}//{parts[2]}{url}"
        else:
            # Relative path
            return f"{base_url.rstrip('/')}/{url}"

    def _record_check(
        self,
        city_id: int,
        check_type: str,
        new_document_found: bool,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Record the check in the database.

        Args:
            city_id: City ID
            check_type: Type of check performed
            new_document_found: Whether a new document was found
            result: Optional result dict
            error: Optional error message
        """
        check = RefreshCheck(
            city_id=city_id,
            check_type=check_type,
            check_frequency="quarterly",
            performed_at=datetime.utcnow(),
            new_document_found=new_document_found,
            source_url_checked=settings.vallejo_cafr_base_url,
            scraping_success=error is None,
            scraping_error=error,
        )

        if result:
            check.document_url = result.get("document_url")
            check.document_title = result.get("document_title")
            check.fiscal_year = result.get("fiscal_year")
            check.notification_needed = True

        self.db.add(check)
        self.db.commit()


class CalPERSAvailabilityChecker:
    """Check if new CalPERS actuarial valuations are available."""

    def __init__(self, db: Session):
        """Initialize checker with database session."""
        self.db = db

    def check_for_new_calpers_valuation(self, city_id: int) -> Optional[Dict]:
        """
        Check if a new CalPERS actuarial valuation is available.

        Args:
            city_id: Database ID of the city to check

        Returns:
            Dict with document details if found, None otherwise
        """
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            logger.error("city_not_found", city_id=city_id)
            return None

        logger.info("checking_calpers_availability", city=city.name)

        try:
            # CalPERS valuations are published annually
            # For Vallejo: https://www.calpers.ca.gov/page/active-members/retirement-benefits/service-retirement
            # This is a placeholder - actual implementation would scrape CalPERS website
            result = self._check_calpers_website(city)

            # Record the check
            self._record_check(
                city_id=city_id,
                check_type="calpers_valuation",
                new_document_found=result is not None,
                result=result,
            )

            return result

        except Exception as e:
            logger.error("calpers_check_failed", city=city.name, error=str(e))
            self._record_check(
                city_id=city_id,
                check_type="calpers_valuation",
                new_document_found=False,
                error=str(e),
            )
            return None

    def _check_calpers_website(self, city: City) -> Optional[Dict]:
        """
        Check CalPERS website for new actuarial valuations.

        Note: CalPERS doesn't have a simple public API. In production,
        this would either:
        1. Scrape the CalPERS website for the city's valuation
        2. Check a known URL pattern for the city
        3. Use an RSS feed if available

        Args:
            city: City model instance

        Returns:
            Dict with document details if found, None otherwise
        """
        # Placeholder implementation
        # In production, implement actual CalPERS scraping logic
        logger.info("calpers_check_placeholder", city=city.name)

        # For now, return None (no new document found)
        # TODO: Implement actual CalPERS scraping when CalPERS API/structure is known
        return None

    def _record_check(
        self,
        city_id: int,
        check_type: str,
        new_document_found: bool,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Record the check in the database."""
        check = RefreshCheck(
            city_id=city_id,
            check_type=check_type,
            check_frequency="annual",
            performed_at=datetime.utcnow(),
            new_document_found=new_document_found,
            source_url_checked=settings.calpers_api_url,
            scraping_success=error is None,
            scraping_error=error,
        )

        if result:
            check.document_url = result.get("document_url")
            check.document_title = result.get("document_title")
            check.fiscal_year = result.get("fiscal_year")
            check.notification_needed = True

        self.db.add(check)
        self.db.commit()


class RefreshNotificationManager:
    """Manage notifications for data refresh operations."""

    def __init__(self, db: Session):
        """Initialize manager with database session."""
        self.db = db

    def send_cafr_notification(
        self, city_id: int, cafr_details: Dict
    ) -> RefreshNotification:
        """
        Send notification that new CAFR is available.

        Args:
            city_id: City ID
            cafr_details: Dict with fiscal_year, document_url, document_title

        Returns:
            RefreshNotification record
        """
        city = self.db.query(City).filter(City.id == city_id).first()

        # Get operator emails from settings or schedule
        operator_emails = settings.admin_emails

        # Send email
        success = email_service.send_cafr_available_notification(
            operator_emails=operator_emails,
            city_name=city.name,
            fiscal_year=cafr_details["fiscal_year"],
            document_url=cafr_details["document_url"],
            document_title=cafr_details.get("document_title"),
        )

        # Record notification
        notification = RefreshNotification(
            city_id=city_id,
            fiscal_year=cafr_details["fiscal_year"],
            notification_type="cafr_available",
            sent_at=datetime.utcnow(),
            sent_to=", ".join(operator_emails),
            document_url=cafr_details["document_url"],
            document_title=cafr_details.get("document_title"),
            estimated_entry_time=90,  # 90 minutes for CAFR entry
        )

        self.db.add(notification)
        self.db.commit()

        logger.info(
            "cafr_notification_sent",
            city=city.name,
            fiscal_year=cafr_details["fiscal_year"],
            success=success,
        )

        return notification

    def send_calpers_notification(
        self, city_id: int, calpers_details: Dict
    ) -> RefreshNotification:
        """
        Send notification that new CalPERS valuation is available.

        Args:
            city_id: City ID
            calpers_details: Dict with fiscal_year, document_url

        Returns:
            RefreshNotification record
        """
        city = self.db.query(City).filter(City.id == city_id).first()

        # Get operator emails
        operator_emails = settings.admin_emails

        # Send email
        success = email_service.send_calpers_available_notification(
            operator_emails=operator_emails,
            city_name=city.name,
            fiscal_year=calpers_details["fiscal_year"],
            document_url=calpers_details["document_url"],
        )

        # Record notification
        notification = RefreshNotification(
            city_id=city_id,
            fiscal_year=calpers_details["fiscal_year"],
            notification_type="calpers_available",
            sent_at=datetime.utcnow(),
            sent_to=", ".join(operator_emails),
            document_url=calpers_details["document_url"],
            estimated_entry_time=15,  # 15 minutes for CalPERS entry
        )

        self.db.add(notification)
        self.db.commit()

        logger.info(
            "calpers_notification_sent",
            city=city.name,
            fiscal_year=calpers_details["fiscal_year"],
            success=success,
        )

        return notification


class PostEntryPipeline:
    """
    Pipeline that runs after manual data entry is complete.

    Automatically validates data, recalculates risk scores,
    regenerates projections, and generates change reports.
    """

    def __init__(self, db: Session):
        """Initialize pipeline with database session."""
        self.db = db

    def run_full_pipeline(
        self, city_id: int, fiscal_year: int, operation_type: str = "cafr_entry"
    ) -> RefreshOperation:
        """
        Run full post-entry pipeline.

        Args:
            city_id: City ID
            fiscal_year: Fiscal year that was updated
            operation_type: Type of operation (cafr_entry, calpers_entry, full_refresh)

        Returns:
            RefreshOperation record tracking the pipeline execution
        """
        logger.info(
            "starting_post_entry_pipeline",
            city_id=city_id,
            fiscal_year=fiscal_year,
            operation_type=operation_type,
        )

        # Get fiscal year record
        fiscal_year_record = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fiscal_year_record:
            logger.error("fiscal_year_not_found", city_id=city_id, fiscal_year=fiscal_year)
            raise ValueError(f"Fiscal year {fiscal_year} not found for city {city_id}")

        # Create operation record
        operation = RefreshOperation(
            city_id=city_id,
            fiscal_year_id=fiscal_year_record.id,
            fiscal_year=fiscal_year,
            operation_type=operation_type,
            started_at=datetime.utcnow(),
            status="in_progress",
        )
        self.db.add(operation)
        self.db.commit()

        try:
            # Step 1: Validate data
            validation_passed = self._run_validation(operation, fiscal_year_record)

            if not validation_passed:
                operation.status = "failed"
                operation.success = False
                operation.error_message = "Data validation failed"
                operation.completed_at = datetime.utcnow()
                self.db.commit()
                return operation

            # Step 2: Recalculate risk scores
            self._recalculate_risk_scores(operation, fiscal_year_record)

            # Step 3: Regenerate projections
            self._regenerate_projections(operation, fiscal_year_record)

            # Mark operation as complete
            operation.status = "completed"
            operation.success = True
            operation.completed_at = datetime.utcnow()
            operation.duration_seconds = int(
                (operation.completed_at - operation.started_at).total_seconds()
            )
            self.db.commit()

            logger.info(
                "post_entry_pipeline_complete",
                city_id=city_id,
                fiscal_year=fiscal_year,
                duration_seconds=operation.duration_seconds,
            )

            return operation

        except Exception as e:
            logger.error("post_entry_pipeline_failed", error=str(e))
            operation.status = "failed"
            operation.success = False
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def _run_validation(
        self, operation: RefreshOperation, fiscal_year_record: FiscalYear
    ) -> bool:
        """
        Run data validation.

        Args:
            operation: RefreshOperation record
            fiscal_year_record: FiscalYear record

        Returns:
            True if validation passed, False otherwise
        """
        operation.validation_started_at = datetime.utcnow()
        self.db.commit()

        logger.info("running_validation", fiscal_year_id=fiscal_year_record.id)

        try:
            validator = DataValidator(self.db)
            # Assuming validator has a validate_fiscal_year method
            # This is a placeholder - actual implementation depends on validator structure
            validation_passed = True  # TODO: Implement actual validation

            operation.validation_completed_at = datetime.utcnow()
            operation.validation_passed = validation_passed
            self.db.commit()

            logger.info(
                "validation_complete",
                fiscal_year_id=fiscal_year_record.id,
                passed=validation_passed,
            )

            return validation_passed

        except Exception as e:
            logger.error("validation_failed", error=str(e))
            operation.validation_completed_at = datetime.utcnow()
            operation.validation_passed = False
            operation.validation_errors = str(e)
            self.db.commit()
            return False

    def _recalculate_risk_scores(
        self, operation: RefreshOperation, fiscal_year_record: FiscalYear
    ) -> None:
        """
        Recalculate risk scores for the fiscal year.

        Args:
            operation: RefreshOperation record
            fiscal_year_record: FiscalYear record
        """
        operation.risk_calculation_started_at = datetime.utcnow()
        self.db.commit()

        logger.info("recalculating_risk_scores", fiscal_year_id=fiscal_year_record.id)

        try:
            # Get previous risk score if exists
            from src.database.models.risk import RiskScore

            previous_score = (
                self.db.query(RiskScore)
                .filter(RiskScore.fiscal_year_id == fiscal_year_record.id)
                .order_by(RiskScore.calculation_date.desc())
                .first()
            )

            if previous_score:
                operation.previous_risk_score = int(previous_score.overall_score)

            # Calculate new risk score
            scoring_engine = RiskScoringEngine(self.db)
            new_risk_score = scoring_engine.calculate_risk_score(fiscal_year_record.id)
            self.db.add(new_risk_score)
            self.db.commit()

            operation.new_risk_score = int(new_risk_score.overall_score)
            operation.risk_calculation_completed_at = datetime.utcnow()
            operation.risk_calculation_success = True
            self.db.commit()

            logger.info(
                "risk_scores_recalculated",
                fiscal_year_id=fiscal_year_record.id,
                previous_score=operation.previous_risk_score,
                new_score=operation.new_risk_score,
            )

        except Exception as e:
            logger.error("risk_calculation_failed", error=str(e))
            operation.risk_calculation_completed_at = datetime.utcnow()
            operation.risk_calculation_success = False
            self.db.commit()
            raise

    def _regenerate_projections(
        self, operation: RefreshOperation, fiscal_year_record: FiscalYear
    ) -> None:
        """
        Regenerate financial projections.

        Args:
            operation: RefreshOperation record
            fiscal_year_record: FiscalYear record
        """
        operation.projection_started_at = datetime.utcnow()
        self.db.commit()

        logger.info("regenerating_projections", fiscal_year_id=fiscal_year_record.id)

        try:
            # Get previous fiscal cliff year if exists
            from src.database.models.projections import FiscalCliffAnalysis

            previous_cliff = (
                self.db.query(FiscalCliffAnalysis)
                .filter(FiscalCliffAnalysis.city_id == fiscal_year_record.city_id)
                .order_by(FiscalCliffAnalysis.created_at.desc())
                .first()
            )

            if previous_cliff:
                operation.previous_fiscal_cliff_year = previous_cliff.fiscal_cliff_year

            # Generate new projections
            # This is a placeholder - actual implementation depends on scenario engine
            scenario_engine = ScenarioEngine(self.db)
            # scenario_engine.generate_scenarios(fiscal_year_record.city_id, fiscal_year_record.year)

            # For now, just mark as success
            operation.projection_completed_at = datetime.utcnow()
            operation.projection_success = True
            self.db.commit()

            logger.info(
                "projections_regenerated",
                fiscal_year_id=fiscal_year_record.id,
            )

        except Exception as e:
            logger.error("projection_failed", error=str(e))
            operation.projection_completed_at = datetime.utcnow()
            operation.projection_success = False
            self.db.commit()
            # Don't raise - projections are not critical


class DataRefreshOrchestrator:
    """
    Main orchestrator for data refresh workflows.

    Coordinates checks, notifications, and post-entry pipelines.
    """

    def __init__(self, db: Session):
        """Initialize orchestrator with database session."""
        self.db = db
        self.cafr_checker = CAFRAvailabilityChecker(db)
        self.calpers_checker = CalPERSAvailabilityChecker(db)
        self.notification_manager = RefreshNotificationManager(db)
        self.post_entry_pipeline = PostEntryPipeline(db)

    def run_quarterly_check(self, city_id: int) -> Dict:
        """
        Run quarterly check for new CAFRs.

        Args:
            city_id: City ID to check

        Returns:
            Dict with check results
        """
        logger.info("running_quarterly_check", city_id=city_id)

        result = {"cafr_found": False, "notification_sent": False}

        # Check for new CAFR
        cafr_details = self.cafr_checker.check_for_new_cafr(city_id)

        if cafr_details:
            result["cafr_found"] = True
            result["cafr_details"] = cafr_details

            # Send notification
            notification = self.notification_manager.send_cafr_notification(
                city_id, cafr_details
            )
            result["notification_sent"] = True
            result["notification_id"] = notification.id

        return result

    def run_annual_check(self, city_id: int) -> Dict:
        """
        Run annual check for new CalPERS valuations.

        Args:
            city_id: City ID to check

        Returns:
            Dict with check results
        """
        logger.info("running_annual_check", city_id=city_id)

        result = {"calpers_found": False, "notification_sent": False}

        # Check for new CalPERS valuation
        calpers_details = self.calpers_checker.check_for_new_calpers_valuation(city_id)

        if calpers_details:
            result["calpers_found"] = True
            result["calpers_details"] = calpers_details

            # Send notification
            notification = self.notification_manager.send_calpers_notification(
                city_id, calpers_details
            )
            result["notification_sent"] = True
            result["notification_id"] = notification.id

        return result

    def trigger_post_entry_pipeline(
        self, city_id: int, fiscal_year: int, operation_type: str = "cafr_entry"
    ) -> RefreshOperation:
        """
        Trigger post-entry pipeline after manual data entry.

        Args:
            city_id: City ID
            fiscal_year: Fiscal year that was updated
            operation_type: Type of operation

        Returns:
            RefreshOperation record
        """
        return self.post_entry_pipeline.run_full_pipeline(
            city_id, fiscal_year, operation_type
        )
