#!/usr/bin/env python3
"""
Comprehensive Data Quality Report Generator

Generates detailed quality reports in HTML and JSON formats showing:
- Year-by-year quality breakdown
- Validation alerts with explanations
- Anomaly summary
- Recommendations for follow-up

Usage:
    poetry run python scripts/validation/generate_quality_report.py [options]

Examples:
    # Generate report for Vallejo
    poetry run python scripts/validation/generate_quality_report.py --city Vallejo

    # Generate for specific fiscal year
    poetry run python scripts/validation/generate_quality_report.py --city Vallejo --fiscal-year 2024

    # Output to specific directory
    poetry run python scripts/validation/generate_quality_report.py --city Vallejo --output-dir reports/
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tabulate import tabulate

from src.config.settings import settings
from src.data_quality import (
    DataQualityValidator,
    QualityMetricsCalculator,
    ValidationSeverity,
)
from src.database.models import City, FiscalYear


def generate_html_report(
    city: City,
    fiscal_years: List[FiscalYear],
    metrics_list: List,
    alerts_by_year: Dict[int, List],
    summary: Dict,
    output_path: Path,
) -> None:
    """Generate HTML quality report."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <title>Data Quality Report - " + city.name + "</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 40px; }",
        "        h1 { color: #333; }",
        "        h2 { color: #666; margin-top: 30px; }",
        "        table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
        "        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
        "        th { background-color: #4CAF50; color: white; }",
        "        tr:nth-child(even) { background-color: #f2f2f2; }",
        "        .critical { color: #d32f2f; font-weight: bold; }",
        "        .warning { color: #f57c00; }",
        "        .info { color: #1976d2; }",
        "        .good { color: #388e3c; }",
        "        .summary-box { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }",
        "        .alert-box { background: #fff3e0; padding: 15px; margin: 10px 0; border-left: 4px solid #f57c00; }",
        "        .alert-box.critical { background: #ffebee; border-left-color: #d32f2f; }",
        "        .recommendation { font-style: italic; color: #666; margin-top: 10px; }",
        "    </style>",
        "</head>",
        "<body>",
        f"    <h1>Data Quality Report: {city.name}</h1>",
        f"    <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>",
        "",
        "    <div class='summary-box'>",
        "        <h2>Summary</h2>",
        f"        <p><strong>Total Years Analyzed:</strong> {summary['total_years']}</p>",
        f"        <p><strong>Average Completeness:</strong> {summary['avg_completeness']:.1f}%</p>",
        f"        <p><strong>Average Consistency:</strong> {summary['avg_consistency']:.1f}%</p>",
        f"        <p><strong>Average Overall Score:</strong> {summary['avg_overall_score']:.1f}%</p>",
        f"        <p class='{'critical' if summary['total_critical_issues'] > 0 else 'good'}'><strong>Critical Issues:</strong> {summary['total_critical_issues']}</p>",
        f"        <p class='{'warning' if summary['total_warnings'] > 0 else 'good'}'><strong>Warnings:</strong> {summary['total_warnings']}</p>",
        f"        <p><strong>Years Validated:</strong> {summary['years_validated']} / {summary['total_years']}</p>",
        "    </div>",
    ]

    # Metrics table
    html_parts.extend([
        "    <h2>Quality Metrics by Fiscal Year</h2>",
        "    <table>",
        "        <thead>",
        "            <tr>",
        "                <th>Fiscal Year</th>",
        "                <th>Completeness</th>",
        "                <th>Consistency</th>",
        "                <th>Overall Score</th>",
        "                <th>Status</th>",
        "                <th>Critical</th>",
        "                <th>Warnings</th>",
        "            </tr>",
        "        </thead>",
        "        <tbody>",
    ])

    for metrics in metrics_list:
        score_class = "good" if metrics.overall_score >= 95 else "warning" if metrics.overall_score >= 80 else "critical"
        html_parts.append(
            f"            <tr>"
            f"<td>{metrics.fiscal_year}</td>"
            f"<td>{metrics.completeness_score:.1f}%</td>"
            f"<td>{metrics.consistency_score:.1f}%</td>"
            f"<td class='{score_class}'>{metrics.overall_score:.1f}%</td>"
            f"<td>{metrics.validation_status.value}</td>"
            f"<td class='{'critical' if metrics.critical_issues > 0 else ''}'>{metrics.critical_issues}</td>"
            f"<td class='{'warning' if metrics.warnings > 0 else ''}'>{metrics.warnings}</td>"
            f"</tr>"
        )

    html_parts.extend([
        "        </tbody>",
        "    </table>",
    ])

    # Alerts by year
    if any(alerts_by_year.values()):
        html_parts.append("    <h2>Validation Alerts</h2>")

        for year in sorted(alerts_by_year.keys(), reverse=True):
            alerts = alerts_by_year[year]
            if not alerts:
                continue

            html_parts.append(f"    <h3>Fiscal Year {year}</h3>")

            for alert in alerts:
                alert_class = alert.severity.value
                html_parts.extend([
                    f"    <div class='alert-box {alert_class}'>",
                    f"        <p class='{alert_class}'><strong>{alert.severity.value.upper()}</strong> - {alert.category}</p>",
                    f"        <p>{alert.message}</p>",
                    "        <p><strong>Details:</strong></p>",
                    "        <ul>",
                ])

                for key, value in alert.details.items():
                    html_parts.append(f"            <li><strong>{key}:</strong> {value}</li>")

                html_parts.append("        </ul>")

                if alert.recommendation:
                    html_parts.append(f"        <p class='recommendation'><strong>Recommendation:</strong> {alert.recommendation}</p>")

                html_parts.append("    </div>")

    html_parts.extend([
        "</body>",
        "</html>",
    ])

    # Write HTML file
    with open(output_path, "w") as f:
        f.write("\n".join(html_parts))


def generate_json_report(
    city: City,
    fiscal_years: List[FiscalYear],
    metrics_list: List,
    alerts_by_year: Dict[int, List],
    summary: Dict,
    output_path: Path,
) -> None:
    """Generate JSON quality report."""
    report = {
        "city": {
            "id": city.id,
            "name": city.name,
        },
        "generated_at": datetime.utcnow().isoformat(),
        "summary": summary,
        "metrics_by_year": [m.to_dict() for m in metrics_list],
        "alerts_by_year": {
            str(year): [a.to_dict() for a in alerts]
            for year, alerts in alerts_by_year.items()
        },
        "fiscal_years_analyzed": [fy.year for fy in fiscal_years],
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)


def print_console_report(
    city: City,
    metrics_list: List,
    summary: Dict,
) -> None:
    """Print summary report to console."""
    print(f"\n{'='*80}")
    print(f"DATA QUALITY REPORT: {city.name}")
    print(f"{'='*80}\n")

    # Summary
    print("SUMMARY:")
    print(f"  Total Years Analyzed:     {summary['total_years']}")
    print(f"  Average Completeness:     {summary['avg_completeness']:.1f}%")
    print(f"  Average Consistency:      {summary['avg_consistency']:.1f}%")
    print(f"  Average Overall Score:    {summary['avg_overall_score']:.1f}%")
    print(f"  Critical Issues:          {summary['total_critical_issues']}")
    print(f"  Warnings:                 {summary['total_warnings']}")
    print(f"  Years Validated:          {summary['years_validated']} / {summary['total_years']}")
    print()

    # Metrics table
    table_data = []
    for metrics in metrics_list:
        status_symbol = "✓" if metrics.can_publish() else "⚠" if metrics.warnings > 0 else "✗"
        table_data.append([
            f"{status_symbol} FY{metrics.fiscal_year}",
            f"{metrics.completeness_score:.1f}%",
            f"{metrics.consistency_score:.1f}%",
            f"{metrics.overall_score:.1f}%",
            metrics.validation_status.value,
            metrics.critical_issues,
            metrics.warnings,
        ])

    headers = ["Year", "Complete", "Consistent", "Overall", "Status", "Critical", "Warnings"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

    # Publishing status
    can_publish = all(m.can_publish() for m in metrics_list)
    if can_publish:
        print("✓ ALL DATA READY TO PUBLISH")
    else:
        needs_attention = [m.fiscal_year for m in metrics_list if not m.can_publish()]
        print(f"⚠ YEARS NEEDING ATTENTION: {', '.join(map(str, needs_attention))}")

    print(f"\n{'='*80}\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive data quality report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--city",
        default="Vallejo",
        help="City name (default: Vallejo)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        help="Specific fiscal year (default: all years)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Output directory for reports (default: reports/)",
    )
    parser.add_argument(
        "--format",
        choices=["html", "json", "both"],
        default="both",
        help="Report format (default: both)",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Create database engine
    engine = create_engine(settings.database_url, echo=False)

    with Session(engine) as session:
        # Get city
        city = session.query(City).filter(City.name == args.city).first()
        if not city:
            print(f"Error: City '{args.city}' not found")
            return 1

        # Get fiscal years
        query = session.query(FiscalYear).filter(FiscalYear.city_id == city.id)
        if args.fiscal_year:
            query = query.filter(FiscalYear.year == args.fiscal_year)

        fiscal_years = query.order_by(FiscalYear.year.desc()).all()

        if not fiscal_years:
            print(f"Error: No fiscal years found for {args.city}")
            return 1

        print(f"\nAnalyzing data quality for {len(fiscal_years)} fiscal year(s)...")

        # Calculate metrics and collect alerts
        metrics_calculator = QualityMetricsCalculator(session)
        validator = DataQualityValidator(session)

        metrics_list = []
        alerts_by_year = {}

        for fy in fiscal_years:
            metrics = metrics_calculator.calculate_metrics(fy)
            alerts = validator.validate_fiscal_year(fy)

            metrics_list.append(metrics)
            alerts_by_year[fy.year] = alerts

        # Get summary
        summary = metrics_calculator.get_summary_statistics(metrics_list)

        # Print console report
        print_console_report(city, metrics_list, summary)

        # Generate HTML report
        if args.format in ["html", "both"]:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            html_path = args.output_dir / f"quality_report_{city.name.lower()}_{timestamp}.html"
            generate_html_report(
                city, fiscal_years, metrics_list, alerts_by_year, summary, html_path
            )
            print(f"✓ HTML report generated: {html_path}")

        # Generate JSON report
        if args.format in ["json", "both"]:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            json_path = args.output_dir / f"quality_report_{city.name.lower()}_{timestamp}.json"
            generate_json_report(
                city, fiscal_years, metrics_list, alerts_by_year, summary, json_path
            )
            print(f"✓ JSON report generated: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
