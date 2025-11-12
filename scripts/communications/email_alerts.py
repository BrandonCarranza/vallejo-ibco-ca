#!/usr/bin/env python3
"""
Quarterly Email Alerts Script

Sends quarterly fiscal update emails to subscribers.

Summary includes:
- Risk score trend
- New data entered
- Projection updates
- Links to latest reports and dashboards
- Source documents

Usage:
    python scripts/communications/email_alerts.py --city-id 1 --quarter 4 --year 2024
    python scripts/communications/email_alerts.py --city-id 1 --quarter 4 --year 2024 --dry-run
"""

import argparse
import sys
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.database.models.stakeholders import Subscriber, SubscriberStatus, Notification, NotificationStatus, NotificationType, AlertSeverity
from src.database.models.core import City, FiscalYear
from src.database.models.risk import RiskScore
from src.database.models.projections import FiscalCliffAnalysis, ProjectionScenario
from src.database.models.civic import Decision, DecisionStatus
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class QuarterlyEmailGenerator:
    """Generate and send quarterly update emails."""

    def __init__(self, db: Session):
        self.db = db

    def send_quarterly_update(
        self,
        city_id: int,
        quarter: int,
        year: int,
        dry_run: bool = False
    ) -> Dict:
        """
        Send quarterly update to all subscribers.

        Args:
            city_id: City ID
            quarter: Quarter (1-4)
            year: Year
            dry_run: If True, preview without sending

        Returns:
            Dictionary with send statistics
        """
        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City {city_id} not found")

        # Get quarter date range
        quarter_start, quarter_end = self._get_quarter_dates(year, quarter)

        # Get subscribers
        subscribers = self._get_active_subscribers(city_id)

        if not subscribers:
            logger.warning(f"No active subscribers for city {city_id}")
            return {
                "subscribers_targeted": 0,
                "emails_queued": 0,
                "dry_run": dry_run
            }

        # Generate email content
        content = self._generate_quarterly_content(
            city=city,
            quarter=quarter,
            year=year,
            quarter_start=quarter_start,
            quarter_end=quarter_end
        )

        emails_queued = 0

        for subscriber in subscribers:
            # Personalize and send
            personalized_content = self._personalize_content(content, subscriber)

            if dry_run:
                logger.info(f"[DRY RUN] Would send to {subscriber.email}")
                logger.debug(f"Subject: {personalized_content['subject']}")
                logger.debug(f"Content preview: {personalized_content['text'][:200]}...")
            else:
                # Queue notification
                notification = Notification(
                    subscriber_id=subscriber.id,
                    notification_type=NotificationType.QUARTERLY_UPDATE,
                    severity=AlertSeverity.INFO,
                    subject=personalized_content['subject'],
                    message_text=personalized_content['text'],
                    message_html=personalized_content['html'],
                    city_id=city_id,
                    status=NotificationStatus.PENDING
                )

                self.db.add(notification)
                emails_queued += 1

                # TODO: Actually send email via email service provider
                # For now, just queue the notification

        if not dry_run:
            self.db.commit()

        return {
            "subscribers_targeted": len(subscribers),
            "emails_queued": emails_queued,
            "dry_run": dry_run,
            "subject": content['subject'],
            "preview": content['text'][:500]
        }

    def _get_active_subscribers(self, city_id: int) -> List[Subscriber]:
        """Get active subscribers for quarterly updates."""
        return self.db.query(Subscriber).filter(
            Subscriber.status == SubscriberStatus.ACTIVE,
            Subscriber.subscribed_to_quarterly_updates == True,
            Subscriber.is_deleted == False,
            Subscriber.email_bounce_count < 3
        ).filter(
            (Subscriber.city_id == city_id) | (Subscriber.city_id == None)
        ).all()

    def _generate_quarterly_content(
        self,
        city: City,
        quarter: int,
        year: int,
        quarter_start: date,
        quarter_end: date
    ) -> Dict[str, str]:
        """Generate quarterly update email content."""
        # Get latest fiscal data
        latest_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city.id
        ).order_by(desc(FiscalYear.year)).first()

        # Get latest risk score
        latest_risk = None
        if latest_fy:
            latest_risk = self.db.query(RiskScore).filter(
                RiskScore.fiscal_year_id == latest_fy.id
            ).first()

        # Get fiscal cliff analysis
        base_scenario = self.db.query(ProjectionScenario).filter(
            ProjectionScenario.scenario_code == 'base'
        ).first()

        fiscal_cliff = None
        if base_scenario:
            fiscal_cliff = self.db.query(FiscalCliffAnalysis).filter(
                FiscalCliffAnalysis.city_id == city.id,
                FiscalCliffAnalysis.scenario_id == base_scenario.id
            ).order_by(desc(FiscalCliffAnalysis.created_at)).first()

        # Get recent decisions
        recent_decisions = self.db.query(Decision).filter(
            Decision.city_id == city.id,
            Decision.decision_date >= quarter_start,
            Decision.decision_date <= quarter_end,
            Decision.status == DecisionStatus.APPROVED,
            Decision.is_deleted == False
        ).count()

        # Build subject
        quarter_name = f"Q{quarter} {year}"
        subject = f"IBCo Vallejo Fiscal Analysis: {quarter_name} Update"

        # Build text content
        text_content = self._build_text_content(
            city=city,
            quarter_name=quarter_name,
            latest_risk=latest_risk,
            fiscal_cliff=fiscal_cliff,
            recent_decisions=recent_decisions
        )

        # Build HTML content
        html_content = self._build_html_content(
            city=city,
            quarter_name=quarter_name,
            latest_risk=latest_risk,
            fiscal_cliff=fiscal_cliff,
            recent_decisions=recent_decisions
        )

        return {
            "subject": subject,
            "text": text_content,
            "html": html_content
        }

    def _build_text_content(
        self,
        city: City,
        quarter_name: str,
        latest_risk: Optional[RiskScore],
        fiscal_cliff: Optional[FiscalCliffAnalysis],
        recent_decisions: int
    ) -> str:
        """Build plain text email content."""
        lines = []

        lines.append(f"IBCo Vallejo Fiscal Analysis - {quarter_name} Update")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Independent Budget & Oversight Console update for {city.name}")
        lines.append("")

        # Risk Score
        lines.append("RISK SCORE")
        lines.append("-" * 60)
        if latest_risk:
            score = float(latest_risk.overall_score)
            level = latest_risk.risk_level.upper()
            lines.append(f"Current Score: {score:.1f}/100 ({level})")
            lines.append(f"Data as of: FY{latest_risk.fiscal_year.year}")
            lines.append("")
            lines.append("Category Breakdown:")
            lines.append(f"  - Pension Stress: {float(latest_risk.pension_stress_score):.1f}/100")
            lines.append(f"  - Structural Balance: {float(latest_risk.structural_balance_score):.1f}/100")
            lines.append(f"  - Liquidity: {float(latest_risk.liquidity_score):.1f}/100")
            lines.append(f"  - Revenue Sustainability: {float(latest_risk.revenue_sustainability_score):.1f}/100")
            lines.append(f"  - Debt Burden: {float(latest_risk.debt_burden_score):.1f}/100")
        else:
            lines.append("Risk score calculation in progress...")
        lines.append("")

        # Fiscal Cliff
        lines.append("FISCAL PROJECTIONS")
        lines.append("-" * 60)
        if fiscal_cliff:
            if fiscal_cliff.has_fiscal_cliff:
                lines.append(f"⚠ FISCAL CLIFF PROJECTED")
                lines.append(f"  Year: FY{fiscal_cliff.fiscal_cliff_year}")
                lines.append(f"  Years Until: {fiscal_cliff.years_until_cliff}")
                lines.append(f"  Cumulative Deficit: ${fiscal_cliff.cumulative_deficit_at_cliff:,.0f}")
            else:
                lines.append("✓ No fiscal cliff projected in 10-year window")
        else:
            lines.append("Fiscal projections being updated...")
        lines.append("")

        # Recent Activity
        lines.append("THIS QUARTER")
        lines.append("-" * 60)
        if recent_decisions > 0:
            lines.append(f"- {recent_decisions} city council decisions logged and tracked")
        lines.append("- New financial data entered from official sources")
        lines.append("- Risk scores and projections updated")
        lines.append("")

        # Links
        lines.append("EXPLORE THE DATA")
        lines.append("-" * 60)
        lines.append("Interactive Dashboards:")
        lines.append("  https://dashboard.ibco-ca.us")
        lines.append("")
        lines.append("API Documentation:")
        lines.append("  https://api.ibco-ca.us/docs")
        lines.append("")
        lines.append("Source Documents:")
        lines.append("  https://docs.ibco-ca.us/sources")
        lines.append("")

        # Methodology
        lines.append("ABOUT THIS DATA")
        lines.append("-" * 60)
        lines.append("IBCo is an independent civic transparency project.")
        lines.append("All data manually entered from official documents (CAFRs,")
        lines.append("actuarial reports, city budgets) with complete audit trail.")
        lines.append("")
        lines.append("Strictly non-partisan: We present data without policy advocacy.")
        lines.append("Risk scores are stress indicators, not bankruptcy predictions.")
        lines.append("")

        # Footer
        lines.append("MANAGE SUBSCRIPTION")
        lines.append("-" * 60)
        lines.append("Update preferences: https://ibco-ca.us/preferences")
        lines.append("Unsubscribe: {{unsubscribe_link}}")
        lines.append("")
        lines.append("Questions? data@ibco-ca.us")
        lines.append("")
        lines.append("---")
        lines.append("Independent Budget & Oversight Console")
        lines.append("https://ibco-ca.us")

        return "\n".join(lines)

    def _build_html_content(
        self,
        city: City,
        quarter_name: str,
        latest_risk: Optional[RiskScore],
        fiscal_cliff: Optional[FiscalCliffAnalysis],
        recent_decisions: int
    ) -> str:
        """Build HTML email content."""
        # Use template approach for HTML
        template_path = Path(__file__).parent.parent.parent / "templates" / "emails" / "quarterly_update.html"

        if template_path.exists():
            # TODO: Use Jinja2 to render template
            pass

        # Fallback: simple HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBCo {quarter_name} Update</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #2196F3; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">IBCo Vallejo Console</h1>
        <p style="margin: 10px 0 0 0;">{quarter_name} Fiscal Update</p>
    </div>

    <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
        <h2 style="color: #2196F3; margin-top: 0;">Risk Score</h2>
"""

        if latest_risk:
            score = float(latest_risk.overall_score)
            level = latest_risk.risk_level.upper()
            color = "#D32F2F" if score >= 75 else "#FF5722" if score >= 50 else "#FFC107" if score >= 25 else "#4CAF50"

            html += f"""
        <div style="background-color: white; padding: 15px; border-left: 4px solid {color};">
            <p style="font-size: 24px; margin: 0; font-weight: bold; color: {color};">{score:.1f}/100</p>
            <p style="margin: 5px 0; color: #666;">{level} RISK</p>
            <p style="margin: 5px 0; font-size: 14px; color: #999;">FY{latest_risk.fiscal_year.year}</p>
        </div>
"""
        else:
            html += "<p>Risk score calculation in progress...</p>"

        html += """
    </div>

    <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
        <h2 style="color: #2196F3; margin-top: 0;">Fiscal Projections</h2>
"""

        if fiscal_cliff:
            if fiscal_cliff.has_fiscal_cliff:
                html += f"""
        <div style="background-color: #FFF3E0; padding: 15px; border-left: 4px solid #FF9800;">
            <p style="margin: 0; font-weight: bold; color: #E65100;">⚠ Fiscal Cliff Projected</p>
            <p style="margin: 10px 0 5px 0;">Year: FY{fiscal_cliff.fiscal_cliff_year}</p>
            <p style="margin: 5px 0;">Years Until: {fiscal_cliff.years_until_cliff}</p>
            <p style="margin: 5px 0;">Cumulative Deficit: ${fiscal_cliff.cumulative_deficit_at_cliff:,.0f}</p>
        </div>
"""
            else:
                html += """
        <div style="background-color: #E8F5E9; padding: 15px; border-left: 4px solid #4CAF50;">
            <p style="margin: 0; color: #2E7D32;">✓ No fiscal cliff projected in 10-year window</p>
        </div>
"""

        html += """
    </div>

    <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
        <h2 style="color: #2196F3; margin-top: 0;">This Quarter</h2>
        <ul style="margin: 10px 0; padding-left: 20px;">
"""

        if recent_decisions > 0:
            html += f"            <li>{recent_decisions} city council decisions logged and tracked</li>\n"

        html += """
            <li>New financial data entered from official sources</li>
            <li>Risk scores and projections updated</li>
        </ul>
    </div>

    <div style="padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
        <h2 style="color: #2196F3; margin-top: 0;">Explore the Data</h2>
        <p>
            <a href="https://dashboard.ibco-ca.us" style="color: #2196F3; text-decoration: none;">📊 Interactive Dashboards</a><br>
            <a href="https://api.ibco-ca.us/docs" style="color: #2196F3; text-decoration: none;">🔌 API Documentation</a><br>
            <a href="https://docs.ibco-ca.us/sources" style="color: #2196F3; text-decoration: none;">📄 Source Documents</a>
        </p>
    </div>

    <div style="padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-top: 1px solid #ddd;">
        <p style="font-size: 12px; color: #666; margin: 0;">
            <strong>About This Data:</strong> IBCo is an independent civic transparency project.
            All data manually entered from official documents with complete audit trail.
            Strictly non-partisan: we present data without policy advocacy.
        </p>
    </div>

    <div style="padding: 20px; text-align: center; font-size: 12px; color: #999;">
        <p>
            <a href="{{unsubscribe_link}}" style="color: #999;">Unsubscribe</a> |
            <a href="https://ibco-ca.us/preferences" style="color: #999;">Update Preferences</a>
        </p>
        <p>Independent Budget & Oversight Console<br>
        <a href="https://ibco-ca.us" style="color: #999;">ibco-ca.us</a></p>
    </div>
</body>
</html>
"""

        return html

    def _personalize_content(self, content: Dict[str, str], subscriber: Subscriber) -> Dict[str, str]:
        """Personalize email content for subscriber."""
        unsubscribe_link = f"https://ibco-ca.us/unsubscribe?token={subscriber.unsubscribe_token}"

        return {
            "subject": content["subject"],
            "text": content["text"].replace("{{unsubscribe_link}}", unsubscribe_link),
            "html": content["html"].replace("{{unsubscribe_link}}", unsubscribe_link)
        }

    def _get_quarter_dates(self, year: int, quarter: int) -> tuple:
        """Get start and end dates for a quarter."""
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }

        if quarter not in quarter_months:
            raise ValueError(f"Invalid quarter: {quarter}")

        start_month, end_month = quarter_months[quarter]

        # Last day of quarter
        if end_month == 12:
            end_day = 31
        elif end_month in [4, 6, 9, 11]:
            end_day = 30
        else:
            end_day = 31

        return (
            date(year, start_month, 1),
            date(year, end_month, end_day)
        )


def main():
    parser = argparse.ArgumentParser(
        description="Send quarterly fiscal update emails to subscribers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send Q4 2024 update
  python scripts/communications/email_alerts.py --city-id 1 --year 2024 --quarter 4

  # Preview without sending
  python scripts/communications/email_alerts.py --city-id 1 --year 2024 --quarter 4 --dry-run
        """
    )

    parser.add_argument(
        "--city-id",
        type=int,
        required=True,
        help="City ID"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year"
    )
    parser.add_argument(
        "--quarter",
        type=int,
        required=True,
        choices=[1, 2, 3, 4],
        help="Quarter (1-4)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without sending emails"
    )

    args = parser.parse_args()

    # Send quarterly update
    with get_session() as db:
        generator = QuarterlyEmailGenerator(db)

        try:
            result = generator.send_quarterly_update(
                city_id=args.city_id,
                quarter=args.quarter,
                year=args.year,
                dry_run=args.dry_run
            )

            print(f"\n{'=' * 60}")
            print(f"Quarterly Update: Q{args.quarter} {args.year}")
            print(f"{'=' * 60}")
            print(f"Subscribers Targeted: {result['subscribers_targeted']}")
            print(f"Emails Queued: {result['emails_queued']}")
            print(f"Dry Run: {result['dry_run']}")
            print(f"\nSubject: {result['subject']}")
            print(f"\nPreview:\n{result['preview']}...")
            print(f"{'=' * 60}\n")

            if result['dry_run']:
                print("✓ Dry run complete (no emails sent)")
            else:
                print(f"✓ {result['emails_queued']} emails queued for delivery")

        except Exception as e:
            logger.error(f"Error sending quarterly update: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
