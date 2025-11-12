#!/usr/bin/env python3
"""
Scheduled data refresh checker.

Runs periodic checks for new source documents (CAFRs, CalPERS valuations)
and sends notifications when new data is available.

Usage:
    # Run as a daemon (recommended for production)
    python scripts/maintenance/schedule_refresh.py

    # Run with custom configuration
    python scripts/maintenance/schedule_refresh.py --check-interval 3600

    # Run once (for testing)
    python scripts/maintenance/schedule_refresh.py --run-once
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from src.config.database import SessionLocal
from src.config.settings import settings
from src.data_pipeline.orchestration.refresh_workflows import DataRefreshOrchestrator
from src.database.models.core import City

logger = structlog.get_logger(__name__)


class DataRefreshScheduler:
    """Scheduler for periodic data refresh checks."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BlockingScheduler()
        self.orchestrator = None  # Will be created per job with fresh DB session

    def quarterly_cafr_check(self):
        """
        Quarterly check for new CAFRs.

        Runs on the 15th of January, April, July, and October.
        (CAFRs are typically published a few months after fiscal year end)
        """
        logger.info("running_scheduled_quarterly_check")

        db = SessionLocal()
        try:
            orchestrator = DataRefreshOrchestrator(db)

            # Get all active cities
            cities = db.query(City).filter(City.is_active == True).all()

            for city in cities:
                logger.info("checking_cafr_for_city", city=city.name)
                try:
                    result = orchestrator.run_quarterly_check(city.id)

                    if result["cafr_found"]:
                        logger.info(
                            "new_cafr_found_and_notified",
                            city=city.name,
                            notification_sent=result["notification_sent"],
                        )
                    else:
                        logger.info("no_new_cafr", city=city.name)

                except Exception as e:
                    logger.error("cafr_check_failed", city=city.name, error=str(e))

        finally:
            db.close()

    def annual_calpers_check(self):
        """
        Annual check for new CalPERS valuations.

        Runs in July (CalPERS typically publishes valuations in summer).
        """
        logger.info("running_scheduled_annual_check")

        db = SessionLocal()
        try:
            orchestrator = DataRefreshOrchestrator(db)

            # Get all active cities
            cities = db.query(City).filter(City.is_active == True).all()

            for city in cities:
                logger.info("checking_calpers_for_city", city=city.name)
                try:
                    result = orchestrator.run_annual_check(city.id)

                    if result["calpers_found"]:
                        logger.info(
                            "new_calpers_found_and_notified",
                            city=city.name,
                            notification_sent=result["notification_sent"],
                        )
                    else:
                        logger.info("no_new_calpers", city=city.name)

                except Exception as e:
                    logger.error("calpers_check_failed", city=city.name, error=str(e))

        finally:
            db.close()

    def setup_jobs(self):
        """Configure scheduled jobs."""
        # Quarterly CAFR checks: 15th of Jan, Apr, Jul, Oct at 9:00 AM
        self.scheduler.add_job(
            self.quarterly_cafr_check,
            CronTrigger(month="1,4,7,10", day=15, hour=9, minute=0),
            id="quarterly_cafr_check",
            name="Quarterly CAFR Availability Check",
            replace_existing=True,
        )
        logger.info("scheduled_quarterly_cafr_check", schedule="15th of Jan/Apr/Jul/Oct at 9:00 AM")

        # Annual CalPERS check: 15th of July at 10:00 AM
        self.scheduler.add_job(
            self.annual_calpers_check,
            CronTrigger(month=7, day=15, hour=10, minute=0),
            id="annual_calpers_check",
            name="Annual CalPERS Valuation Check",
            replace_existing=True,
        )
        logger.info("scheduled_annual_calpers_check", schedule="July 15th at 10:00 AM")

    def run_once(self):
        """Run all checks once (for testing)."""
        logger.info("running_all_checks_once")
        self.quarterly_cafr_check()
        self.annual_calpers_check()
        logger.info("all_checks_complete")

    def start(self):
        """Start the scheduler."""
        logger.info("starting_refresh_scheduler")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("scheduler_stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Data refresh scheduler")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run all checks once and exit (for testing)",
    )
    parser.add_argument(
        "--cafr-only",
        action="store_true",
        help="Run only CAFR check (with --run-once)",
    )
    parser.add_argument(
        "--calpers-only",
        action="store_true",
        help="Run only CalPERS check (with --run-once)",
    )

    args = parser.parse_args()

    # Configure logging
    logger.info(
        "data_refresh_scheduler_starting",
        environment=settings.environment,
        run_once=args.run_once,
    )

    scheduler_instance = DataRefreshScheduler()

    if args.run_once:
        # Run checks once for testing
        if args.cafr_only:
            scheduler_instance.quarterly_cafr_check()
        elif args.calpers_only:
            scheduler_instance.annual_calpers_check()
        else:
            scheduler_instance.run_once()
    else:
        # Set up scheduled jobs and run as daemon
        scheduler_instance.setup_jobs()
        scheduler_instance.start()


if __name__ == "__main__":
    main()
