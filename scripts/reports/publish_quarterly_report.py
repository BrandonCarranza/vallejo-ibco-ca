#!/usr/bin/env python3
"""
Publish Quarterly Report

Orchestrates generation and publication of all IBCo reports:
- Fiscal Summary Report
- Risk Narrative
- Projection Scenario Report
- Press Release Template

Publishes to static website (ibco-ca.us/reports/) and archives prior reports.
Sends email notifications to stakeholder list.

Usage:
    python publish_quarterly_report.py --city-id 1 --fiscal-year 2024 --quarter Q3
    python publish_quarterly_report.py --send-notifications
"""

import argparse
from pathlib import Path
import shutil
from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from src.database.session import SessionLocal
from src.reports.generators import (
    FiscalSummaryReportGenerator,
    RiskNarrativeGenerator,
    ProjectionScenarioReportGenerator,
)


class QuarterlyReportPublisher:
    """Orchestrates quarterly report publication."""

    def __init__(self, db: Session, output_dir: Path):
        """
        Initialize publisher.

        Args:
            db: Database session
            output_dir: Base output directory for reports
        """
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def publish_all_reports(
        self,
        city_id: int,
        fiscal_year: int,
        quarter: str,
        send_notifications: bool = False,
    ) -> Dict[str, List[Path]]:
        """
        Generate and publish all reports.

        Args:
            city_id: City ID
            fiscal_year: Fiscal year
            quarter: Quarter (e.g., "Q3")
            send_notifications: Whether to send email notifications

        Returns:
            Dictionary mapping report type to list of generated file paths
        """
        print(f"\n{'=' * 60}")
        print(f"Publishing Quarterly Reports: FY{fiscal_year} {quarter}")
        print(f"{'=' * 60}\n")

        # Create quarter directory
        quarter_dir = self.output_dir / f"FY{fiscal_year}_{quarter}"
        quarter_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # 1. Generate Fiscal Summary Report
        print("[1/4] Generating Fiscal Summary Report...")
        fiscal_gen = FiscalSummaryReportGenerator(self.db)
        fiscal_files = fiscal_gen.generate_all_formats(
            quarter_dir,
            f"fiscal_summary_FY{fiscal_year}_{quarter}",
        )
        generated_files["fiscal_summary"] = list(fiscal_files.values())
        print(f"✓ Generated {len(fiscal_files)} files")

        # 2. Generate Risk Narrative
        print("\n[2/4] Generating Risk Narrative...")
        risk_gen = RiskNarrativeGenerator(self.db)
        risk_files = risk_gen.generate_all_formats(
            quarter_dir,
            f"risk_narrative_FY{fiscal_year}_{quarter}",
        )
        generated_files["risk_narrative"] = list(risk_files.values())
        print(f"✓ Generated {len(risk_files)} files")

        # 3. Generate Projection Scenario Report
        print("\n[3/4] Generating Projection Scenario Report...")
        proj_gen = ProjectionScenarioReportGenerator(self.db)
        proj_files = proj_gen.generate_all_formats(
            quarter_dir,
            f"projection_scenarios_FY{fiscal_year}_{quarter}",
        )
        generated_files["projections"] = list(proj_files.values())
        print(f"✓ Generated {len(proj_files)} files")

        # 4. Generate Press Release Template
        print("\n[4/4] Generating Press Release Template...")
        press_release_path = self._generate_press_release(
            quarter_dir,
            city_id,
            fiscal_year,
            quarter,
        )
        generated_files["press_release"] = [press_release_path]
        print(f"✓ Generated press release template")

        # Archive old reports
        print("\nArchiving previous reports...")
        self._archive_old_reports()

        # Create index.html for quarter
        print("Creating quarter index...")
        self._create_quarter_index(quarter_dir, fiscal_year, quarter, generated_files)

        # Update main index
        print("Updating main index...")
        self._update_main_index()

        # Send notifications if requested
        if send_notifications:
            print("\nSending email notifications...")
            self._send_notifications(fiscal_year, quarter, quarter_dir)

        print(f"\n{'=' * 60}")
        print("✓ Quarterly Reports Published Successfully!")
        print(f"{'=' * 60}")
        print(f"\nOutput directory: {quarter_dir}")
        print(f"Total files generated: {sum(len(files) for files in generated_files.values())}\n")

        return generated_files

    def _generate_press_release(
        self,
        output_dir: Path,
        city_id: int,
        fiscal_year: int,
        quarter: str,
    ) -> Path:
        """Generate press release template."""
        # Get risk narrative for summary
        risk_gen = RiskNarrativeGenerator(self.db)
        context = risk_gen.get_report_context(city_id, fiscal_year)

        narrative = context["narrative"]["executive_summary"]
        risk_score = context["risk_score"]

        press_release = f"""
FOR IMMEDIATE RELEASE

Contact: IBCo Vallejo Console
Website: ibco-ca.us
Email: contact@ibco-ca.us

{context['city_name']} Fiscal Analysis: FY{fiscal_year} {quarter} Update

{context['city_name'].upper()}, CA - [{datetime.now().strftime('%B %d, %Y')}] - The Independent Budget
and Civic Observatory (IBCo) has released its quarterly fiscal analysis for the City of
{context['city_name']}, revealing important insights into the city's financial condition.

KEY FINDINGS:

• Fiscal Stress Score: {risk_score.overall_score:.0f}/100 ({risk_score.risk_level.capitalize()})
• Overall Assessment: {narrative}

BACKGROUND:

IBCo provides transparent, data-driven fiscal analysis of California municipalities using
publicly available financial documents. All data is manually entered from official CAFR and
CalPERS reports with complete lineage tracking for full accountability.

REPORTS AVAILABLE:

• Fiscal Summary Report: Comprehensive overview of revenues, expenditures, and fiscal health
• Risk Narrative: Plain-language explanation of fiscal challenges
• Projection Scenarios: 10-year outlook under different assumptions

All reports are available at: https://ibco-ca.us/reports/FY{fiscal_year}_{quarter}/

ABOUT IBCo:

The Independent Budget and Civic Observatory is a non-partisan civic accountability
initiative providing transparent fiscal analysis of California municipalities. IBCo's
mission is to make complex municipal finances accessible to citizens, journalists, and
policymakers.

For more information or to request interviews, visit ibco-ca.us.

###
"""

        output_path = output_dir / f"press_release_FY{fiscal_year}_{quarter}.txt"
        output_path.write_text(press_release)

        return output_path

    def _archive_old_reports(self):
        """Move old reports to archive directory."""
        archive_dir = self.output_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Archive reports older than current quarter
        # (Implementation would check dates and move files)
        pass

    def _create_quarter_index(
        self,
        quarter_dir: Path,
        fiscal_year: int,
        quarter: str,
        generated_files: Dict[str, List[Path]],
    ):
        """Create index.html for quarter directory."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBCo Reports - FY{fiscal_year} {quarter}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #2196F3; }}
        .report-section {{ margin: 30px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }}
        a {{ color: #2196F3; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>IBCo Fiscal Reports - FY{fiscal_year} {quarter}</h1>
    <p>Generated: {datetime.now().strftime('%B %d, %Y')}</p>

    <div class="report-section">
        <h2>Fiscal Summary Report</h2>
        <p>Comprehensive overview of revenues, expenditures, and fiscal health.</p>
        <p>
            <a href="fiscal_summary_FY{fiscal_year}_{quarter}.html">HTML</a> |
            <a href="fiscal_summary_FY{fiscal_year}_{quarter}.pdf">PDF</a> |
            <a href="fiscal_summary_FY{fiscal_year}_{quarter}.json">JSON</a>
        </p>
    </div>

    <div class="report-section">
        <h2>Risk Narrative</h2>
        <p>Plain-language explanation of fiscal challenges and risk factors.</p>
        <p>
            <a href="risk_narrative_FY{fiscal_year}_{quarter}.html">HTML</a> |
            <a href="risk_narrative_FY{fiscal_year}_{quarter}.pdf">PDF</a> |
            <a href="risk_narrative_FY{fiscal_year}_{quarter}.json">JSON</a>
        </p>
    </div>

    <div class="report-section">
        <h2>Projection Scenarios</h2>
        <p>10-year fiscal outlook under base, optimistic, and pessimistic scenarios.</p>
        <p>
            <a href="projection_scenarios_FY{fiscal_year}_{quarter}.html">HTML</a> |
            <a href="projection_scenarios_FY{fiscal_year}_{quarter}.pdf">PDF</a> |
            <a href="projection_scenarios_FY{fiscal_year}_{quarter}.json">JSON</a>
        </p>
    </div>

    <div class="report-section">
        <h2>Press Release</h2>
        <p>Template for media distribution.</p>
        <p><a href="press_release_FY{fiscal_year}_{quarter}.txt">Download TXT</a></p>
    </div>

    <p><a href="../index.html">← Back to All Reports</a></p>
</body>
</html>
"""

        index_path = quarter_dir / "index.html"
        index_path.write_text(html)

    def _update_main_index(self):
        """Update main reports index.html."""
        # Scan all quarter directories and generate index
        quarters = sorted(
            [d for d in self.output_dir.iterdir() if d.is_dir() and d.name.startswith("FY")],
            reverse=True,
        )

        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IBCo Fiscal Reports Archive</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }
        h1 { color: #2196F3; }
        .quarter-list { list-style: none; padding: 0; }
        .quarter-list li { margin: 15px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        a { color: #2196F3; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>IBCo Fiscal Reports Archive</h1>
    <p>All published quarterly fiscal reports for Vallejo, CA.</p>

    <h2>Available Reports</h2>
    <ul class="quarter-list">
"""

        for quarter_dir in quarters:
            if quarter_dir.name != "archive":
                html += f'        <li><a href="{quarter_dir.name}/index.html">{quarter_dir.name}</a></li>\n'

        html += """
    </ul>

    <h2>About These Reports</h2>
    <p>IBCo provides transparent, data-driven fiscal analysis using publicly available financial documents.
    All data is manually entered from official CAFR and CalPERS reports with complete lineage tracking.</p>

    <p><a href="archive/">View Archived Reports →</a></p>
</body>
</html>
"""

        index_path = self.output_dir / "index.html"
        index_path.write_text(html)

    def _send_notifications(self, fiscal_year: int, quarter: str, quarter_dir: Path):
        """Send email notifications to stakeholder list."""
        # This would integrate with email service (SendGrid, SMTP, etc.)
        # For now, just print notification
        print(f"Email notification would be sent for FY{fiscal_year} {quarter}")
        print(f"Report URL: https://ibco-ca.us/reports/{quarter_dir.name}/")


def main():
    parser = argparse.ArgumentParser(description="Publish quarterly IBCo reports")
    parser.add_argument("--city-id", type=int, default=1, help="City ID (default: 1 for Vallejo)")
    parser.add_argument("--fiscal-year", type=int, required=True, help="Fiscal year")
    parser.add_argument("--quarter", default="Q3", help="Quarter (e.g., Q3)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/var/www/ibco-ca.us/reports"),
        help="Output directory for reports",
    )
    parser.add_argument(
        "--send-notifications",
        action="store_true",
        help="Send email notifications to stakeholders",
    )

    args = parser.parse_args()

    # Initialize database session
    db = SessionLocal()

    try:
        publisher = QuarterlyReportPublisher(db, args.output_dir)

        generated_files = publisher.publish_all_reports(
            city_id=args.city_id,
            fiscal_year=args.fiscal_year,
            quarter=args.quarter,
            send_notifications=args.send_notifications,
        )

        print("✓ Publication complete!")
        print(f"\nGenerated files:")
        for report_type, files in generated_files.items():
            print(f"  {report_type}: {len(files)} files")

    finally:
        db.close()


if __name__ == "__main__":
    main()
