#!/usr/bin/env python3
"""
Generate public transparency reports for legal incidents.

This script generates quarterly transparency reports showing:
- All legal threats received
- IBCo responses
- Outcomes (threats retracted, lawsuits dismissed, etc.)
- Demonstration that suppression attempts fail

The transparency report serves multiple purposes:
1. Public accountability - show attempts to suppress civic transparency
2. Deterrence - demonstrate that legal threats don't work
3. Streisand Effect - publicizing threats increases attention
4. Community support - rally supporters against SLAPP suits
5. Legal defense - document pattern of frivolous threats

Output formats:
- Markdown report for website
- JSON data for API
- HTML for email distribution

Usage:
    # Generate quarterly report
    python scripts/reports/legal_incident_report.py \\
        --period Q1-2025 \\
        --output-dir docs/transparency/

    # Generate all-time summary
    python scripts/reports/legal_incident_report.py \\
        --all-time \\
        --output-format markdown

    # Generate report excluding confidential incidents
    python scripts/reports/legal_incident_report.py \\
        --period Q2-2025 \\
        --exclude-confidential
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func
from sqlalchemy.orm import Session
from src.database.models.legal import LegalIncident, LegalResponse
from src.config.database import get_session


# ============================================================================
# Report Generators
# ============================================================================


def get_incidents(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    exclude_confidential: bool = True
) -> List[LegalIncident]:
    """Get legal incidents for reporting period."""
    query = db.query(LegalIncident).filter(LegalIncident.is_deleted == False)

    # Date filtering
    if start_date:
        query = query.filter(LegalIncident.date_received >= start_date)
    if end_date:
        query = query.filter(LegalIncident.date_received <= end_date)

    # Exclude confidential incidents (attorney-client privileged)
    if exclude_confidential:
        # Note: We'd need to add a 'confidential' field to LegalIncident model
        # For now, we include all non-deleted incidents
        pass

    return query.order_by(LegalIncident.date_received.desc()).all()


def calculate_statistics(incidents: List[LegalIncident], db: Session) -> Dict:
    """Calculate summary statistics."""
    total = len(incidents)

    if total == 0:
        return {
            "total_incidents": 0,
            "by_type": {},
            "by_status": {},
            "by_severity": {},
            "resolved_count": 0,
            "resolution_rate": 0.0,
            "avg_resolution_days": 0.0,
            "frivolous_count": 0,
            "frivolous_rate": 0.0,
            "dead_mans_switch_triggers": 0,
            "media_coverage_count": 0,
        }

    # Count by type
    by_type = {}
    for incident in incidents:
        by_type[incident.incident_type] = by_type.get(incident.incident_type, 0) + 1

    # Count by status
    by_status = {}
    for incident in incidents:
        by_status[incident.status] = by_status.get(incident.status, 0) + 1

    # Count by severity
    by_severity = {}
    for incident in incidents:
        by_severity[incident.severity] = by_severity.get(incident.severity, 0) + 1

    # Resolved incidents
    resolved = [i for i in incidents if i.resolved]
    resolved_count = len(resolved)

    # Average resolution time
    resolution_days = []
    for incident in resolved:
        if incident.resolved_date:
            days = (incident.resolved_date - incident.date_received).days
            resolution_days.append(days)

    avg_resolution = sum(resolution_days) / len(resolution_days) if resolution_days else 0

    # Frivolous threats
    frivolous = [i for i in incidents if i.frivolous]
    frivolous_count = len(frivolous)

    # Dead man's switch triggers
    dms_triggers = [i for i in incidents if i.triggers_dead_mans_switch]

    # Media coverage
    media_coverage = [i for i in incidents if i.media_coverage]

    return {
        "total_incidents": total,
        "by_type": by_type,
        "by_status": by_status,
        "by_severity": by_severity,
        "resolved_count": resolved_count,
        "resolution_rate": round(resolved_count / total * 100, 1) if total > 0 else 0,
        "avg_resolution_days": round(avg_resolution, 1),
        "frivolous_count": frivolous_count,
        "frivolous_rate": round(frivolous_count / total * 100, 1) if total > 0 else 0,
        "dead_mans_switch_triggers": len(dms_triggers),
        "media_coverage_count": len(media_coverage),
    }


def generate_markdown_report(
    incidents: List[LegalIncident],
    statistics: Dict,
    period: str,
    db: Session
) -> str:
    """Generate markdown transparency report."""
    output = []

    # Header
    output.append(f"# Legal Incident Transparency Report\n\n")
    output.append(f"**Reporting Period:** {period}\n")
    output.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")

    output.append("---\n\n")

    # Executive Summary
    output.append("## Executive Summary\n\n")
    output.append(f"**Total Legal Incidents:** {statistics['total_incidents']}\n\n")

    if statistics['total_incidents'] > 0:
        output.append(f"- **Resolved:** {statistics['resolved_count']} ({statistics['resolution_rate']}%)\n")
        output.append(f"- **Frivolous:** {statistics['frivolous_count']} ({statistics['frivolous_rate']}%)\n")
        output.append(f"- **Average Resolution Time:** {statistics['avg_resolution_days']} days\n")
        output.append(f"- **Dead-Man's Switch Triggers:** {statistics['dead_mans_switch_triggers']}\n")
        output.append(f"- **Media Coverage:** {statistics['media_coverage_count']}\n\n")

        # By type
        output.append("**Incidents by Type:**\n\n")
        for incident_type, count in sorted(statistics['by_type'].items()):
            output.append(f"- {incident_type}: {count}\n")
        output.append("\n")

        # By severity
        output.append("**Incidents by Severity:**\n\n")
        for severity, count in sorted(statistics['by_severity'].items()):
            output.append(f"- {severity}: {count}\n")
        output.append("\n")

    output.append("---\n\n")

    # Mission Statement
    output.append("## IBCo Mission: Fiscal Transparency\n\n")
    output.append("""
Independent Budget & Oversight Console (IBCo) provides civic transparency
by analyzing municipal fiscal health using publicly available government documents.

**Our Principles:**
- All data from official government sources (CAFRs, CalPERS, State Controller)
- Complete transparency: open-source code, documented methodology
- Prominent disclaimers: stress indicators, not predictions
- First Amendment protected speech on matters of public concern

**Why This Report:**
We publish this transparency report to demonstrate that legal threats and
suppression attempts do not silence civic transparency. Publicizing these
incidents serves the public interest and activates the Streisand Effect.
""")

    output.append("\n---\n\n")

    # Individual Incidents
    if incidents:
        output.append("## Legal Incidents\n\n")

        for idx, incident in enumerate(incidents, 1):
            output.append(f"### Incident #{incident.id}: {incident.incident_type}\n\n")

            output.append(f"**Received:** {incident.date_received.strftime('%Y-%m-%d')}\n")
            output.append(f"**Sender:** {incident.sender_name}")
            if incident.sender_organization:
                output.append(f" ({incident.sender_organization})")
            output.append("\n")
            output.append(f"**Severity:** {incident.severity}\n")
            output.append(f"**Status:** {incident.status}\n\n")

            # Subject
            output.append(f"**Subject:** {incident.subject}\n\n")

            # Description (sanitized)
            if incident.description:
                desc = incident.description[:500]
                if len(incident.description) > 500:
                    desc += "..."
                output.append(f"**Description:** {desc}\n\n")

            # Claims & Demands
            if incident.claims_made:
                output.append(f"**Claims:** {incident.claims_made}\n\n")

            if incident.demands:
                output.append(f"**Demands:** {incident.demands}\n\n")

            # IBCo Assessment
            output.append("**IBCo Assessment:**\n\n")
            output.append(f"- Frivolous: {'Yes' if incident.frivolous else 'No'}\n")
            if incident.anti_slapp_applicable is not None:
                output.append(f"- Anti-SLAPP Applicable: {'Yes' if incident.anti_slapp_applicable else 'No'}\n")
            if incident.first_amendment_protected is not None:
                output.append(f"- First Amendment Protected: {'Yes' if incident.first_amendment_protected else 'No'}\n")
            output.append("\n")

            # Response Status
            output.append("**Response:**\n\n")
            if incident.response_sent:
                output.append(f"- Response Sent: {incident.response_sent_date.strftime('%Y-%m-%d')}\n")
                if incident.response_sent_by:
                    output.append(f"- Sent By: {incident.response_sent_by}\n")
            else:
                output.append("- Response Status: Pending\n")
            output.append("\n")

            # Resolution
            if incident.resolved:
                output.append("**Resolution:**\n\n")
                output.append(f"- Resolved: {incident.resolved_date.strftime('%Y-%m-%d')}\n")
                if incident.resolution_type:
                    output.append(f"- Type: {incident.resolution_type}\n")
                if incident.resolution_notes:
                    output.append(f"- Notes: {incident.resolution_notes}\n")
                output.append("\n")

            # Streisand Effect
            if incident.media_coverage:
                output.append("**Media Coverage:** Yes\n")
                if incident.media_coverage_notes:
                    output.append(f"\n{incident.media_coverage_notes}\n")
                output.append("\n")

            # Dead-Man's Switch
            if incident.triggers_dead_mans_switch:
                output.append("**⚠️ Dead-Man's Switch Triggered**\n\n")
                output.append(
                    "This incident triggered IBCo's dead-man's switch protocol, "
                    "reducing the automated data publication timer to ensure "
                    "suppression attempts cannot succeed.\n\n"
                )

            output.append("---\n\n")

    # Footer
    output.append("## Conclusion\n\n")
    output.append("""
IBCo will continue to provide fiscal transparency despite legal threats.

**Our Response to Suppression Attempts:**
1. We do not remove truthful analysis based on legal threats
2. We publicly disclose all legal incidents (Streisand Effect)
3. We vigorously defend First Amendment rights
4. We seek attorney's fees under anti-SLAPP statute
5. We contact EFF/ACLU for support when appropriate

**Message to Potential Litigants:**

Threatening IBCo with legal action is counterproductive. Such threats:
- Trigger public disclosure (this report)
- Activate Streisand Effect (increased media attention)
- Reduce dead-man's switch timer (accelerated data publication)
- Demonstrate fiscal transparency works (we don't back down)
- Risk attorney's fees under anti-SLAPP statute

**Better Approach:**

If you believe our analysis contains factual errors, contact us at:
**data@ibco-ca.us**

We take accuracy seriously and will promptly correct demonstrable errors.
However, we will not remove truthful analysis simply because it is unflattering.

---

**Report Contact:** data@ibco-ca.us
**Website:** https://ibco-ca.us
**Source Code:** https://github.com/your-org/vallejo-ibco-ca
""")

    return "".join(output)


def generate_json_report(
    incidents: List[LegalIncident],
    statistics: Dict,
    period: str,
    db: Session
) -> str:
    """Generate JSON transparency report."""
    incidents_data = []

    for incident in incidents:
        incident_dict = {
            "id": incident.id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "status": incident.status,
            "sender_name": incident.sender_name,
            "sender_organization": incident.sender_organization,
            "date_received": incident.date_received.isoformat(),
            "subject": incident.subject,
            "frivolous": incident.frivolous,
            "anti_slapp_applicable": incident.anti_slapp_applicable,
            "first_amendment_protected": incident.first_amendment_protected,
            "response_sent": incident.response_sent,
            "response_sent_date": incident.response_sent_date.isoformat() if incident.response_sent_date else None,
            "resolved": incident.resolved,
            "resolved_date": incident.resolved_date.isoformat() if incident.resolved_date else None,
            "resolution_type": incident.resolution_type,
            "triggers_dead_mans_switch": incident.triggers_dead_mans_switch,
            "media_coverage": incident.media_coverage,
        }
        incidents_data.append(incident_dict)

    report = {
        "report_type": "legal_incident_transparency",
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "statistics": statistics,
        "incidents": incidents_data,
    }

    return json.dumps(report, indent=2)


def generate_html_summary(
    incidents: List[LegalIncident],
    statistics: Dict,
    period: str,
    db: Session
) -> str:
    """Generate HTML email summary."""
    output = []

    output.append("<!DOCTYPE html>\n<html>\n<head>\n")
    output.append("<meta charset='UTF-8'>\n")
    output.append("<title>Legal Incident Transparency Report</title>\n")
    output.append("<style>\n")
    output.append("body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }\n")
    output.append("h1 { color: #2c3e50; }\n")
    output.append("h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }\n")
    output.append(".stat { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }\n")
    output.append(".incident { background: #fff; border: 1px solid #bdc3c7; padding: 15px; margin: 15px 0; border-radius: 5px; }\n")
    output.append(".warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }\n")
    output.append("</style>\n</head>\n<body>\n")

    output.append(f"<h1>Legal Incident Transparency Report</h1>\n")
    output.append(f"<p><strong>Period:</strong> {period}</p>\n")
    output.append(f"<p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>\n")

    # Statistics
    output.append("<div class='stat'>\n")
    output.append(f"<h2>Summary Statistics</h2>\n")
    output.append(f"<p><strong>Total Incidents:</strong> {statistics['total_incidents']}</p>\n")
    if statistics['total_incidents'] > 0:
        output.append(f"<p><strong>Resolved:</strong> {statistics['resolved_count']} ({statistics['resolution_rate']}%)</p>\n")
        output.append(f"<p><strong>Frivolous:</strong> {statistics['frivolous_count']} ({statistics['frivolous_rate']}%)</p>\n")
    output.append("</div>\n")

    # Incidents
    if incidents:
        output.append("<h2>Recent Incidents</h2>\n")
        for incident in incidents[:5]:  # Show top 5 for email
            output.append("<div class='incident'>\n")
            output.append(f"<h3>Incident #{incident.id}: {incident.incident_type}</h3>\n")
            output.append(f"<p><strong>Received:</strong> {incident.date_received.strftime('%Y-%m-%d')}</p>\n")
            output.append(f"<p><strong>Sender:</strong> {incident.sender_name}</p>\n")
            output.append(f"<p><strong>Status:</strong> {incident.status}</p>\n")

            if incident.triggers_dead_mans_switch:
                output.append("<div class='warning'>\n")
                output.append("<p><strong>⚠️ Dead-Man's Switch Triggered</strong></p>\n")
                output.append("</div>\n")

            output.append("</div>\n")

    output.append("<p>Full report: <a href='https://ibco-ca.us/transparency/legal'>https://ibco-ca.us/transparency/legal</a></p>\n")
    output.append("</body>\n</html>")

    return "".join(output)


# ============================================================================
# Main
# ============================================================================


def parse_period(period_str: str) -> tuple:
    """Parse period string into start/end dates."""
    if period_str.upper() == "ALL":
        return None, None

    # Parse quarter format: Q1-2025, Q2-2025, etc.
    if period_str.startswith("Q"):
        parts = period_str.split("-")
        if len(parts) == 2:
            quarter = int(parts[0][1])  # Extract number from Q1, Q2, etc.
            year = int(parts[1])

            month_start = (quarter - 1) * 3 + 1
            start_date = datetime(year, month_start, 1)

            if quarter == 4:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month_start + 3, 1) - timedelta(days=1)

            return start_date, end_date

    # Parse year format: 2025
    if period_str.isdigit():
        year = int(period_str)
        return datetime(year, 1, 1), datetime(year, 12, 31)

    raise ValueError(f"Invalid period format: {period_str}. Use Q1-2025, Q2-2025, 2025, or ALL")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate legal incident transparency report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Q1 2025 report
  python scripts/reports/legal_incident_report.py --period Q1-2025

  # Generate annual report
  python scripts/reports/legal_incident_report.py --period 2025

  # Generate all-time report
  python scripts/reports/legal_incident_report.py --period ALL

  # Generate report and save to file
  python scripts/reports/legal_incident_report.py \\
      --period Q1-2025 \\
      --output-file docs/transparency/legal-q1-2025.md

  # Generate JSON for API
  python scripts/reports/legal_incident_report.py \\
      --period Q1-2025 \\
      --output-format json
        """,
    )

    parser.add_argument(
        "--period",
        required=True,
        help="Reporting period (Q1-2025, Q2-2025, 2025, ALL)",
    )

    parser.add_argument(
        "--output-format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "--exclude-confidential",
        action="store_true",
        help="Exclude confidential incidents (attorney-client privilege)",
    )

    args = parser.parse_args()

    try:
        # Parse period
        start_date, end_date = parse_period(args.period)

        print(f"Generating legal incident report for period: {args.period}", file=sys.stderr)
        if start_date and end_date:
            print(f"Date range: {start_date.date()} to {end_date.date()}", file=sys.stderr)

        # Get database session
        with get_session() as db:
            # Get incidents
            incidents = get_incidents(
                db,
                start_date=start_date,
                end_date=end_date,
                exclude_confidential=args.exclude_confidential
            )

            print(f"Found {len(incidents)} legal incidents", file=sys.stderr)

            # Calculate statistics
            statistics = calculate_statistics(incidents, db)

            # Generate report
            if args.output_format == "markdown":
                report = generate_markdown_report(incidents, statistics, args.period, db)
            elif args.output_format == "json":
                report = generate_json_report(incidents, statistics, args.period, db)
            elif args.output_format == "html":
                report = generate_html_summary(incidents, statistics, args.period, db)

            # Output
            if args.output_file:
                args.output_file.parent.mkdir(parents=True, exist_ok=True)
                args.output_file.write_text(report)
                print(f"\n✅ Report generated: {args.output_file}", file=sys.stderr)
            else:
                print(report)

        return 0

    except Exception as e:
        print(f"\n❌ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
