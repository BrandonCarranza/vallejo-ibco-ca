#!/usr/bin/env python3
"""
Generate 'what changed' report after data refresh.

Compares before/after data to highlight significant changes:
- Risk score changes
- Fiscal cliff year movement
- Biggest revenue/expenditure category changes
- Pension liability changes

Usage:
    # Generate report for most recent refresh operation
    python scripts/maintenance/refresh_report.py --city-id 1

    # Generate report for specific operation
    python scripts/maintenance/refresh_report.py --operation-id 42

    # Generate and email to stakeholders
    python scripts/maintenance/refresh_report.py --city-id 1 --email

    # Output HTML file
    python scripts/maintenance/refresh_report.py --city-id 1 --output report.html
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import structlog
from sqlalchemy import desc

from src.config.database import SessionLocal
from src.config.settings import settings
from src.database.models.core import City, FiscalYear
from src.database.models.financial import Expenditure, Revenue
from src.database.models.pensions import PensionPlan
from src.database.models.projections import FiscalCliffAnalysis
from src.database.models.refresh import RefreshOperation
from src.database.models.risk import RiskScore
from src.utils.email_notifications import email_service

logger = structlog.get_logger(__name__)


class RefreshChangeReport:
    """Generate detailed 'what changed' reports after data refresh."""

    def __init__(self, db):
        """Initialize report generator with database session."""
        self.db = db

    def generate_report(
        self, city_id: int, operation_id: Optional[int] = None
    ) -> Dict:
        """
        Generate change report for a refresh operation.

        Args:
            city_id: City ID
            operation_id: Optional specific operation ID. If not provided,
                         uses most recent operation for the city.

        Returns:
            Dict containing report data
        """
        # Get refresh operation
        if operation_id:
            operation = (
                self.db.query(RefreshOperation)
                .filter(RefreshOperation.id == operation_id)
                .first()
            )
        else:
            operation = (
                self.db.query(RefreshOperation)
                .filter(RefreshOperation.city_id == city_id)
                .filter(RefreshOperation.status == "completed")
                .order_by(desc(RefreshOperation.completed_at))
                .first()
            )

        if not operation:
            logger.error("no_operation_found", city_id=city_id, operation_id=operation_id)
            return {}

        city = self.db.query(City).filter(City.id == city_id).first()
        fiscal_year = operation.fiscal_year

        logger.info(
            "generating_refresh_report",
            city=city.name,
            fiscal_year=fiscal_year,
            operation_id=operation.id,
        )

        report = {
            "city_name": city.name,
            "fiscal_year": fiscal_year,
            "operation_id": operation.id,
            "operation_type": operation.operation_type,
            "completed_at": operation.completed_at,
            "duration_seconds": operation.duration_seconds,
        }

        # Risk score changes
        if operation.previous_risk_score and operation.new_risk_score:
            report["risk_score_change"] = self._analyze_risk_score_change(operation)

        # Fiscal cliff changes
        if operation.previous_fiscal_cliff_year and operation.new_fiscal_cliff_year:
            report["fiscal_cliff_change"] = self._analyze_fiscal_cliff_change(operation)

        # Revenue and expenditure changes
        report["financial_changes"] = self._analyze_financial_changes(
            city_id, fiscal_year
        )

        # Pension changes
        report["pension_changes"] = self._analyze_pension_changes(city_id, fiscal_year)

        # Overall assessment
        report["overall_assessment"] = self._generate_overall_assessment(report)

        return report

    def _analyze_risk_score_change(self, operation: RefreshOperation) -> Dict:
        """Analyze risk score changes."""
        prev_score = operation.previous_risk_score
        new_score = operation.new_risk_score
        change = new_score - prev_score
        percent_change = (change / prev_score * 100) if prev_score > 0 else 0

        # Get risk levels
        prev_level = self._determine_risk_level(prev_score)
        new_level = self._determine_risk_level(new_score)

        return {
            "previous_score": prev_score,
            "new_score": new_score,
            "change": change,
            "percent_change": round(percent_change, 2),
            "previous_level": prev_level,
            "new_level": new_level,
            "level_changed": prev_level != new_level,
            "improved": change < 0,  # Lower score is better
        }

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level from score."""
        if score >= 75:
            return "High"
        elif score >= 50:
            return "Medium-High"
        elif score >= 25:
            return "Medium"
        else:
            return "Low"

    def _analyze_fiscal_cliff_change(self, operation: RefreshOperation) -> Dict:
        """Analyze fiscal cliff year changes."""
        prev_year = operation.previous_fiscal_cliff_year
        new_year = operation.new_fiscal_cliff_year
        change = new_year - prev_year if (prev_year and new_year) else 0

        return {
            "previous_year": prev_year,
            "new_year": new_year,
            "change_years": change,
            "moved_earlier": change < 0,
            "moved_later": change > 0,
            "unchanged": change == 0,
        }

    def _analyze_financial_changes(self, city_id: int, fiscal_year: int) -> Dict:
        """Analyze revenue and expenditure changes from previous year."""
        # Get current year totals
        fy_record = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy_record:
            return {}

        current_revenues = (
            self.db.query(Revenue)
            .filter(Revenue.fiscal_year_id == fy_record.id)
            .all()
        )

        current_expenditures = (
            self.db.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fy_record.id)
            .all()
        )

        # Get previous year for comparison
        prev_fy_record = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year - 1)
            .first()
        )

        changes = {
            "total_revenues": sum(r.amount for r in current_revenues if r.amount),
            "total_expenditures": sum(e.amount for e in current_expenditures if e.amount),
        }

        if prev_fy_record:
            prev_revenues = (
                self.db.query(Revenue)
                .filter(Revenue.fiscal_year_id == prev_fy_record.id)
                .all()
            )
            prev_expenditures = (
                self.db.query(Expenditure)
                .filter(Expenditure.fiscal_year_id == prev_fy_record.id)
                .all()
            )

            prev_total_rev = sum(r.amount for r in prev_revenues if r.amount)
            prev_total_exp = sum(e.amount for e in prev_expenditures if e.amount)

            changes["previous_revenues"] = prev_total_rev
            changes["previous_expenditures"] = prev_total_exp
            changes["revenue_change"] = changes["total_revenues"] - prev_total_rev
            changes["expenditure_change"] = changes["total_expenditures"] - prev_total_exp

            if prev_total_rev > 0:
                changes["revenue_percent_change"] = float(
                    (changes["revenue_change"] / prev_total_rev * 100)
                )
            if prev_total_exp > 0:
                changes["expenditure_percent_change"] = float(
                    (changes["expenditure_change"] / prev_total_exp * 100)
                )

        return changes

    def _analyze_pension_changes(self, city_id: int, fiscal_year: int) -> Dict:
        """Analyze pension liability changes."""
        fy_record = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy_record:
            return {}

        pension_plans = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fy_record.id)
            .all()
        )

        if not pension_plans:
            return {}

        total_ual = sum(p.unfunded_liability for p in pension_plans if p.unfunded_liability)
        avg_funded_ratio = (
            sum(p.funded_ratio for p in pension_plans if p.funded_ratio) / len(pension_plans)
            if pension_plans
            else 0
        )

        return {
            "total_unfunded_liability": float(total_ual),
            "average_funded_ratio": float(avg_funded_ratio),
            "plan_count": len(pension_plans),
        }

    def _generate_overall_assessment(self, report: Dict) -> str:
        """Generate overall assessment text."""
        assessments = []

        # Risk score assessment
        if "risk_score_change" in report:
            rsc = report["risk_score_change"]
            if rsc["improved"]:
                assessments.append(
                    f"Risk score improved from {rsc['previous_score']} to {rsc['new_score']} "
                    f"({rsc['change']:+d} points, {rsc['percent_change']:+.1f}%)"
                )
            elif rsc["change"] > 0:
                assessments.append(
                    f"Risk score increased from {rsc['previous_score']} to {rsc['new_score']} "
                    f"({rsc['change']:+d} points, {rsc['percent_change']:+.1f}%)"
                )
            else:
                assessments.append(f"Risk score unchanged at {rsc['new_score']}")

        # Fiscal cliff assessment
        if "fiscal_cliff_change" in report:
            fcc = report["fiscal_cliff_change"]
            if fcc["moved_later"]:
                assessments.append(
                    f"Fiscal cliff moved from {fcc['previous_year']} to {fcc['new_year']} "
                    f"({fcc['change_years']:+d} years - improvement)"
                )
            elif fcc["moved_earlier"]:
                assessments.append(
                    f"Fiscal cliff moved from {fcc['previous_year']} to {fcc['new_year']} "
                    f"({fcc['change_years']:+d} years - concern)"
                )

        return ". ".join(assessments) if assessments else "No significant changes detected."

    def generate_html_report(self, report_data: Dict) -> str:
        """
        Generate HTML formatted report.

        Args:
            report_data: Report data dict

        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Data Refresh Report - {report_data['city_name']} FY{report_data['fiscal_year']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .metric {{
            background-color: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .metric-value {{
            font-size: 1.3em;
            color: #2c3e50;
        }}
        .improved {{ color: #27ae60; }}
        .worsened {{ color: #e74c3c; }}
        .unchanged {{ color: #95a5a6; }}
        .summary {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Data Refresh Report</h1>

        <div class="metric">
            <div class="metric-label">City</div>
            <div class="metric-value">{report_data['city_name']}</div>
        </div>

        <div class="metric">
            <div class="metric-label">Fiscal Year</div>
            <div class="metric-value">FY{report_data['fiscal_year']}</div>
        </div>

        <div class="metric">
            <div class="metric-label">Refresh Completed</div>
            <div class="metric-value">{report_data['completed_at'].strftime('%Y-%m-%d %H:%M:%S') if report_data.get('completed_at') else 'N/A'}</div>
        </div>

        <div class="summary">
            <strong>Overall Assessment:</strong><br>
            {report_data['overall_assessment']}
        </div>
"""

        # Risk score changes
        if "risk_score_change" in report_data:
            rsc = report_data["risk_score_change"]
            status_class = "improved" if rsc["improved"] else "worsened" if rsc["change"] > 0 else "unchanged"

            html += f"""
        <h2>🎯 Risk Score Changes</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Previous</th>
                <th>New</th>
                <th>Change</th>
            </tr>
            <tr>
                <td>Overall Risk Score</td>
                <td>{rsc['previous_score']}</td>
                <td class="{status_class}">{rsc['new_score']}</td>
                <td class="{status_class}">{rsc['change']:+d} ({rsc['percent_change']:+.1f}%)</td>
            </tr>
            <tr>
                <td>Risk Level</td>
                <td>{rsc['previous_level']}</td>
                <td class="{status_class}">{rsc['new_level']}</td>
                <td>{"Changed" if rsc['level_changed'] else "Unchanged"}</td>
            </tr>
        </table>
"""

        # Fiscal cliff changes
        if "fiscal_cliff_change" in report_data:
            fcc = report_data["fiscal_cliff_change"]
            status_class = "improved" if fcc["moved_later"] else "worsened" if fcc["moved_earlier"] else "unchanged"

            html += f"""
        <h2>⚠️ Fiscal Cliff Analysis</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Previous</th>
                <th>New</th>
                <th>Change</th>
            </tr>
            <tr>
                <td>Fiscal Cliff Year</td>
                <td>{fcc['previous_year']}</td>
                <td class="{status_class}">{fcc['new_year']}</td>
                <td class="{status_class}">{fcc['change_years']:+d} years</td>
            </tr>
        </table>
"""

        # Financial changes
        if "financial_changes" in report_data and report_data["financial_changes"]:
            fc = report_data["financial_changes"]
            html += f"""
        <h2>💰 Financial Changes</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Amount</th>
                <th>Change from Prior Year</th>
            </tr>
            <tr>
                <td>Total Revenues</td>
                <td>${fc.get('total_revenues', 0):,.0f}</td>
                <td>{f"${fc.get('revenue_change', 0):+,.0f} ({fc.get('revenue_percent_change', 0):+.1f}%)" if 'revenue_change' in fc else 'N/A'}</td>
            </tr>
            <tr>
                <td>Total Expenditures</td>
                <td>${fc.get('total_expenditures', 0):,.0f}</td>
                <td>{f"${fc.get('expenditure_change', 0):+,.0f} ({fc.get('expenditure_percent_change', 0):+.1f}%)" if 'expenditure_change' in fc else 'N/A'}</td>
            </tr>
        </table>
"""

        # Pension changes
        if "pension_changes" in report_data and report_data["pension_changes"]:
            pc = report_data["pension_changes"]
            html += f"""
        <h2>🏛️ Pension Obligations</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Unfunded Liability</td>
                <td>${pc.get('total_unfunded_liability', 0):,.0f}</td>
            </tr>
            <tr>
                <td>Average Funded Ratio</td>
                <td>{pc.get('average_funded_ratio', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Number of Plans</td>
                <td>{pc.get('plan_count', 0)}</td>
            </tr>
        </table>
"""

        html += """
        <div class="footer">
            <p><strong>IBCo Vallejo Console</strong> - Independent Budget & Civic Oversight<br>
            This report was automatically generated following a data refresh operation.</p>
        </div>
    </div>
</body>
</html>
"""

        return html


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate data refresh change report")
    parser.add_argument("--city-id", type=int, help="City ID")
    parser.add_argument("--operation-id", type=int, help="Specific refresh operation ID")
    parser.add_argument(
        "--email",
        action="store_true",
        help="Email report to stakeholders",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output HTML file path",
    )

    args = parser.parse_args()

    if not args.city_id and not args.operation_id:
        parser.error("Must provide either --city-id or --operation-id")

    db = SessionLocal()
    try:
        reporter = RefreshChangeReport(db)

        # Generate report
        if args.operation_id:
            operation = (
                db.query(RefreshOperation)
                .filter(RefreshOperation.id == args.operation_id)
                .first()
            )
            if not operation:
                logger.error("operation_not_found", operation_id=args.operation_id)
                return
            city_id = operation.city_id
        else:
            city_id = args.city_id

        report_data = reporter.generate_report(city_id, args.operation_id)

        if not report_data:
            logger.error("no_report_data")
            return

        # Generate HTML
        html_report = reporter.generate_html_report(report_data)

        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                f.write(html_report)
            logger.info("report_saved", output=args.output)
            print(f"Report saved to {args.output}")

        # Email if requested
        if args.email:
            city = db.query(City).filter(City.id == city_id).first()

            success = email_service.send_refresh_complete_notification(
                stakeholder_emails=settings.admin_emails,
                city_name=city.name,
                fiscal_year=report_data["fiscal_year"],
                risk_score_change=report_data.get("risk_score_change"),
                fiscal_cliff_change=report_data.get("fiscal_cliff_change"),
            )

            if success:
                logger.info("report_emailed", recipients=settings.admin_emails)
                print("Report emailed to stakeholders")
            else:
                logger.error("report_email_failed")
                print("Failed to email report")

        # Print summary to console
        print("\n" + "=" * 60)
        print(f"Data Refresh Report - {report_data['city_name']} FY{report_data['fiscal_year']}")
        print("=" * 60)
        print(f"\n{report_data['overall_assessment']}\n")

        if "risk_score_change" in report_data:
            rsc = report_data["risk_score_change"]
            print(f"Risk Score: {rsc['previous_score']} → {rsc['new_score']} ({rsc['change']:+d})")

        if "fiscal_cliff_change" in report_data:
            fcc = report_data["fiscal_cliff_change"]
            print(f"Fiscal Cliff Year: {fcc['previous_year']} → {fcc['new_year']}")

        print("\n" + "=" * 60 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
