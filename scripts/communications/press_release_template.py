#!/usr/bin/env python3
"""
Press Release Template Generator

Auto-generates press releases from quarterly fiscal data.

Template: "IBCo Vallejo Fiscal Analysis: Q3 2024 Update"
Includes: risk score, key findings, fiscal cliff analysis, methodology quote

Ready for media distribution.

Usage:
    python scripts/communications/press_release_template.py --city-id 1 --quarter 4 --year 2024
    python scripts/communications/press_release_template.py --city-id 1 --quarter 4 --year 2024 --output press_release_Q4_2024.md
    python scripts/communications/press_release_template.py --city-id 1 --quarter 4 --year 2024 --dry-run
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
from src.database.models.stakeholders import Subscriber, SubscriberStatus, SubscriberCategory, Notification, NotificationStatus, NotificationType, AlertSeverity
from src.database.models.core import City, FiscalYear
from src.database.models.risk import RiskScore
from src.database.models.projections import FiscalCliffAnalysis, ProjectionScenario
from src.database.models.civic import Decision, DecisionStatus, Outcome, OutcomeStatus
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class PressReleaseGenerator:
    """Generate press releases from fiscal data."""

    def __init__(self, db: Session):
        self.db = db

    def generate_press_release(
        self,
        city_id: int,
        quarter: int,
        year: int,
        title: Optional[str] = None,
        include_risk_score: bool = True,
        include_fiscal_cliff: bool = True,
        include_decisions: bool = False,
        custom_content: Optional[str] = None,
        output_path: Optional[Path] = None,
        dry_run: bool = False
    ) -> Dict:
        """
        Generate press release.

        Args:
            city_id: City ID
            quarter: Quarter (1-4)
            year: Year
            title: Optional custom title
            include_risk_score: Include risk score analysis
            include_fiscal_cliff: Include fiscal cliff analysis
            include_decisions: Include recent decisions
            custom_content: Optional custom content to append
            output_path: Optional file to write to
            dry_run: If True, don't send emails

        Returns:
            Dictionary with press release content and send stats
        """
        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City {city_id} not found")

        # Generate content
        quarter_name = f"Q{quarter} {year}"
        default_title = f"IBCo Vallejo Fiscal Analysis: {quarter_name} Update"
        press_release_title = title or default_title

        # Build press release
        markdown = self._build_press_release(
            city=city,
            quarter=quarter,
            year=year,
            title=press_release_title,
            include_risk_score=include_risk_score,
            include_fiscal_cliff=include_fiscal_cliff,
            include_decisions=include_decisions,
            custom_content=custom_content
        )

        # Convert to HTML (simple conversion)
        html = self._markdown_to_html(markdown)

        # Write to file if specified
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown)
            logger.info(f"Press release written to {output_path}")

        # Get media subscribers
        media_subscribers = self._get_media_subscribers(city_id)

        emails_queued = 0

        if not dry_run and media_subscribers:
            # Queue notifications for media subscribers
            for subscriber in media_subscribers:
                notification = Notification(
                    subscriber_id=subscriber.id,
                    notification_type=NotificationType.PRESS_RELEASE,
                    severity=AlertSeverity.INFO,
                    subject=f"PRESS RELEASE: {press_release_title}",
                    message_text=markdown,
                    message_html=html,
                    city_id=city_id,
                    status=NotificationStatus.PENDING
                )

                self.db.add(notification)
                emails_queued += 1

            self.db.commit()

        return {
            "city_id": city_id,
            "title": press_release_title,
            "content_markdown": markdown,
            "content_html": html,
            "subscribers_targeted": len(media_subscribers),
            "emails_queued": emails_queued,
            "dry_run": dry_run
        }

    def _build_press_release(
        self,
        city: City,
        quarter: int,
        year: int,
        title: str,
        include_risk_score: bool,
        include_fiscal_cliff: bool,
        include_decisions: bool,
        custom_content: Optional[str]
    ) -> str:
        """Build press release markdown content."""
        lines = []

        # Header
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**FOR IMMEDIATE RELEASE**  ")
        lines.append(f"{datetime.now().strftime('%B %d, %Y')}")
        lines.append("")
        lines.append(f"**Contact:**  ")
        lines.append(f"IBCo Data Team  ")
        lines.append(f"data@ibco-ca.us  ")
        lines.append(f"https://ibco-ca.us")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Lede
        quarter_start, quarter_end = self._get_quarter_dates(year, quarter)
        quarter_name = f"Q{quarter} {year}"

        lines.append(f"**{city.name.upper()}, CA** — The Independent Budget & Oversight Console (IBCo) ")
        lines.append(f"has released its {quarter_name} fiscal analysis for {city.name}, providing ")
        lines.append(f"independent, non-partisan analysis of the city's financial health.")
        lines.append("")

        # Risk Score Section
        if include_risk_score:
            lines.append(self._generate_risk_score_section(city.id))

        # Fiscal Cliff Section
        if include_fiscal_cliff:
            lines.append(self._generate_fiscal_cliff_section(city.id))

        # Decisions Section
        if include_decisions:
            lines.append(self._generate_decisions_section(city.id, quarter_start, quarter_end))

        # Custom Content
        if custom_content:
            lines.append("")
            lines.append(custom_content)
            lines.append("")

        # Data Transparency Quote
        lines.append("## About the Data")
        lines.append("")
        lines.append('"All data is manually entered from official city documents with complete ')
        lines.append('audit trail," explains the IBCo team. "Every data point links back to source ')
        lines.append('documents—CAFRs, actuarial reports, city budgets—with page numbers and ')
        lines.append('upload timestamps. This enables full transparency and reproducibility."')
        lines.append("")

        # Methodology
        lines.append("Risk scores are composite indicators of fiscal stress calculated from ")
        lines.append("multiple financial ratios across five categories: Pension Stress, Structural ")
        lines.append("Balance, Liquidity & Reserves, Revenue Sustainability, and Debt Burden. ")
        lines.append("Scores range from 0 (low stress) to 100 (severe stress).")
        lines.append("")
        lines.append("**Important:** Risk scores are stress indicators, not bankruptcy predictions. ")
        lines.append("They provide relative assessment of fiscal challenges, not probability forecasts.")
        lines.append("")

        # Non-partisan statement
        lines.append("## Non-Partisan Analysis")
        lines.append("")
        lines.append("IBCo is strictly non-partisan: we present data without policy advocacy. ")
        lines.append('"We let the data speak for itself," the team notes. "Our role is to provide ')
        lines.append('transparent, accurate information. Policy decisions remain with elected officials ')
        lines.append('and voters."')
        lines.append("")

        # Access Information
        lines.append("## Access the Data")
        lines.append("")
        lines.append("All data and analysis are publicly available:")
        lines.append("")
        lines.append("- **Interactive Dashboards:** https://dashboard.ibco-ca.us")
        lines.append("- **API Access:** https://api.ibco-ca.us/docs")
        lines.append("- **Source Documents:** https://docs.ibco-ca.us/sources")
        lines.append("- **Methodology:** https://docs.ibco-ca.us/methodology")
        lines.append("")

        # About IBCo
        lines.append("## About IBCo")
        lines.append("")
        lines.append(f"The Independent Budget & Oversight Console is a civic transparency project ")
        lines.append(f"providing independent fiscal analysis for California municipalities. IBCo ")
        lines.append(f"tracks financial data, risk indicators, and fiscal projections to enable ")
        lines.append(f"informed public discourse. All data is public, non-partisan, and fully documented.")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("###")
        lines.append("")
        lines.append("*For more information, contact: data@ibco-ca.us*")

        return "\n".join(lines)

    def _generate_risk_score_section(self, city_id: int) -> str:
        """Generate risk score section."""
        # Get latest risk score
        latest_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id
        ).order_by(desc(FiscalYear.year)).first()

        if not latest_fy:
            return ""

        latest_risk = self.db.query(RiskScore).filter(
            RiskScore.fiscal_year_id == latest_fy.id
        ).first()

        if not latest_risk:
            return ""

        lines = []
        lines.append("## Fiscal Risk Score")
        lines.append("")

        score = float(latest_risk.overall_score)
        level = latest_risk.risk_level
        fy = latest_risk.fiscal_year.year

        lines.append(f"The city's composite fiscal risk score stands at **{score:.1f} out of 100** ")
        lines.append(f"({level} risk) based on FY{fy} data. This score reflects:")
        lines.append("")

        # Category breakdown
        categories = {
            "Pension Stress": float(latest_risk.pension_stress_score),
            "Structural Balance": float(latest_risk.structural_balance_score),
            "Liquidity & Reserves": float(latest_risk.liquidity_score),
            "Revenue Sustainability": float(latest_risk.revenue_sustainability_score),
            "Debt Burden": float(latest_risk.debt_burden_score)
        }

        for category, cat_score in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{category}:** {cat_score:.1f}/100")

        lines.append("")

        # Interpretation
        if score >= 75:
            lines.append("A severe risk score indicates significant fiscal challenges requiring immediate attention.")
        elif score >= 50:
            lines.append("A high risk score indicates notable fiscal challenges that warrant close monitoring.")
        elif score >= 25:
            lines.append("A moderate risk score indicates manageable fiscal challenges with some areas of concern.")
        else:
            lines.append("A low risk score indicates relatively stable fiscal conditions.")

        lines.append("")

        return "\n".join(lines)

    def _generate_fiscal_cliff_section(self, city_id: int) -> str:
        """Generate fiscal cliff analysis section."""
        # Get base scenario fiscal cliff
        base_scenario = self.db.query(ProjectionScenario).filter(
            ProjectionScenario.scenario_code == 'base'
        ).first()

        if not base_scenario:
            return ""

        fiscal_cliff = self.db.query(FiscalCliffAnalysis).filter(
            FiscalCliffAnalysis.city_id == city_id,
            FiscalCliffAnalysis.scenario_id == base_scenario.id
        ).order_by(desc(FiscalCliffAnalysis.created_at)).first()

        if not fiscal_cliff:
            return ""

        lines = []
        lines.append("## Fiscal Projections")
        lines.append("")

        if fiscal_cliff.has_fiscal_cliff:
            cliff_year = fiscal_cliff.fiscal_cliff_year
            years_until = fiscal_cliff.years_until_cliff
            deficit = fiscal_cliff.cumulative_deficit_at_cliff

            lines.append(f"IBCo's 10-year fiscal projections indicate a potential **fiscal cliff in FY{cliff_year}** ")
            lines.append(f"({years_until} years from now) under baseline assumptions. At that point, cumulative ")
            lines.append(f"deficit is projected to reach **${deficit:,.0f}**.")
            lines.append("")
            lines.append("A 'fiscal cliff' occurs when a city's general fund reserves are projected to be ")
            lines.append("exhausted, potentially requiring emergency measures such as service cuts, tax increases, ")
            lines.append("or state intervention.")
            lines.append("")
            lines.append("IBCo also models optimistic and pessimistic scenarios to account for economic uncertainty.")
        else:
            lines.append("IBCo's 10-year fiscal projections show **no fiscal cliff** under baseline assumptions, ")
            lines.append("indicating that current revenues are projected to cover expenditures with adequate reserves.")
            lines.append("")
            lines.append("However, projections remain subject to economic conditions, policy changes, and ")
            lines.append("unforeseen events.")

        lines.append("")

        return "\n".join(lines)

    def _generate_decisions_section(self, city_id: int, quarter_start: date, quarter_end: date) -> str:
        """Generate recent decisions section."""
        # Get approved decisions this quarter
        decisions = self.db.query(Decision).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= quarter_start,
            Decision.decision_date <= quarter_end,
            Decision.status == DecisionStatus.APPROVED,
            Decision.is_deleted == False
        ).all()

        if not decisions:
            return ""

        lines = []
        lines.append("## Decision Tracking")
        lines.append("")
        lines.append(f"This quarter, IBCo logged **{len(decisions)} city council decisions** with fiscal impact ")
        lines.append(f"predictions. Transparent tracking of predictions versus actual outcomes builds institutional ")
        lines.append(f"credibility.")
        lines.append("")

        # Highlight significant decisions
        significant = [d for d in decisions if d.predicted_annual_impact and abs(d.predicted_annual_impact) >= 1000000]

        if significant:
            lines.append("### Notable Decisions:")
            lines.append("")

            for decision in significant[:3]:  # Top 3
                impact = decision.predicted_annual_impact
                impact_str = f"+${abs(impact):,.0f}" if impact > 0 else f"-${abs(impact):,.0f}"

                lines.append(f"- **{decision.title}** ({decision.decision_date.strftime('%B %d')})")
                lines.append(f"  - Predicted fiscal impact: {impact_str} annually")

                # If outcome available
                if decision.latest_outcome and decision.latest_outcome.status == OutcomeStatus.FINAL:
                    actual = decision.latest_outcome.actual_annual_impact
                    accuracy = decision.prediction_accuracy_percent

                    if accuracy:
                        lines.append(f"  - Actual outcome: ${abs(actual):,.0f} ({accuracy:.0f}% of prediction)")

                lines.append("")

        return "\n".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        # For production, use a proper markdown library
        # This is a basic implementation

        html_lines = ["<html><body style='font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;'>"]

        for line in markdown.split("\n"):
            line = line.strip()

            if not line:
                html_lines.append("<br>")
            elif line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<strong>{line[2:-2]}</strong>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line == "---":
                html_lines.append("<hr>")
            else:
                # Convert **bold** inline
                line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
                html_lines.append(f"<p>{line}</p>")

        html_lines.append("</body></html>")

        return "\n".join(html_lines)

    def _get_media_subscribers(self, city_id: int) -> List[Subscriber]:
        """Get media subscribers for press releases."""
        return self.db.query(Subscriber).filter(
            Subscriber.status == SubscriberStatus.ACTIVE,
            Subscriber.subscribed_to_press_releases == True,
            Subscriber.category.in_([SubscriberCategory.MEDIA, SubscriberCategory.PUBLIC]),
            Subscriber.is_deleted == False,
            Subscriber.email_bounce_count < 3
        ).filter(
            (Subscriber.city_id == city_id) | (Subscriber.city_id == None)
        ).all()

    def _get_quarter_dates(self, year: int, quarter: int) -> tuple:
        """Get start and end dates for a quarter."""
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }

        start_month, end_month = quarter_months[quarter]

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
        description="Generate press release from quarterly fiscal data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Q4 2024 press release
  python scripts/communications/press_release_template.py --city-id 1 --year 2024 --quarter 4

  # Save to file
  python scripts/communications/press_release_template.py --city-id 1 --year 2024 --quarter 4 \\
    --output press_releases/vallejo_Q4_2024.md

  # Preview without sending
  python scripts/communications/press_release_template.py --city-id 1 --year 2024 --quarter 4 --dry-run
        """
    )

    parser.add_argument("--city-id", type=int, required=True, help="City ID")
    parser.add_argument("--year", type=int, required=True, help="Year")
    parser.add_argument("--quarter", type=int, required=True, choices=[1, 2, 3, 4], help="Quarter (1-4)")
    parser.add_argument("--title", type=str, help="Custom press release title")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--no-risk-score", action="store_true", help="Exclude risk score analysis")
    parser.add_argument("--no-fiscal-cliff", action="store_true", help="Exclude fiscal cliff analysis")
    parser.add_argument("--include-decisions", action="store_true", help="Include recent decisions")
    parser.add_argument("--custom-content", type=str, help="Custom content to append")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending emails")

    args = parser.parse_args()

    # Generate press release
    with get_session() as db:
        generator = PressReleaseGenerator(db)

        try:
            result = generator.generate_press_release(
                city_id=args.city_id,
                quarter=args.quarter,
                year=args.year,
                title=args.title,
                include_risk_score=not args.no_risk_score,
                include_fiscal_cliff=not args.no_fiscal_cliff,
                include_decisions=args.include_decisions,
                custom_content=args.custom_content,
                output_path=args.output,
                dry_run=args.dry_run
            )

            print(f"\n{'=' * 60}")
            print(f"Press Release Generated")
            print(f"{'=' * 60}")
            print(f"Title: {result['title']}")
            print(f"Subscribers Targeted: {result['subscribers_targeted']}")
            print(f"Emails Queued: {result['emails_queued']}")
            print(f"Dry Run: {result['dry_run']}")

            if args.output:
                print(f"Saved to: {args.output}")

            print(f"{'=' * 60}\n")

            if not args.output:
                print(result['content_markdown'])

            if result['dry_run']:
                print("\n✓ Dry run complete (no emails sent)")
            else:
                print(f"\n✓ Press release ready and {result['emails_queued']} emails queued")

        except Exception as e:
            logger.error(f"Error generating press release: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
