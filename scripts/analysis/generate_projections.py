#!/usr/bin/env python3
"""
Financial Projection Generation Script

Generates 10-year financial projections using base, optimistic, and pessimistic scenarios.
Identifies fiscal cliff year and validates projection outputs.

Usage:
    poetry run python scripts/analysis/generate_projections.py [options]

Examples:
    # Generate projections from most recent fiscal year
    poetry run python scripts/analysis/generate_projections.py

    # Generate from specific base year
    poetry run python scripts/analysis/generate_projections.py --base-year 2024

    # Generate specific scenario
    poetry run python scripts/analysis/generate_projections.py --scenario base

    # Custom projection horizon
    poetry run python scripts/analysis/generate_projections.py --years 15
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session
from tabulate import tabulate

from src.analytics.projections.scenario_engine import ScenarioEngine
from src.config.settings import settings
from src.database.models import City, FinancialProjection, FiscalYear


def generate_projections(
    session: Session,
    city_name: str,
    base_year: int = None,
    scenarios: List[str] = None,
    years_ahead: int = 10,
    model_version: str = "1.0",
) -> Dict[str, List[FinancialProjection]]:
    """
    Generate financial projections for multiple scenarios.

    Args:
        session: Database session
        city_name: Name of city
        base_year: Base fiscal year (if None, uses most recent)
        scenarios: List of scenario codes (default: ["base", "optimistic", "pessimistic"])
        years_ahead: Number of years to project
        model_version: Projection model version

    Returns:
        Dictionary mapping scenario codes to projection lists
    """
    # Get city
    city = session.query(City).filter(City.name == city_name).first()
    if not city:
        print(f"Error: City '{city_name}' not found")
        return {}

    # Get base year
    if base_year is None:
        latest_fy = (
            session.query(FiscalYear)
            .filter(FiscalYear.city_id == city.id)
            .order_by(desc(FiscalYear.year))
            .first()
        )
        if not latest_fy:
            print(f"Error: No fiscal years found for {city_name}")
            return {}
        base_year = latest_fy.year
    else:
        # Verify base year exists
        fy = (
            session.query(FiscalYear)
            .filter(FiscalYear.city_id == city.id, FiscalYear.year == base_year)
            .first()
        )
        if not fy:
            print(f"Error: Fiscal year {base_year} not found for {city_name}")
            return {}

    # Default scenarios
    if scenarios is None:
        scenarios = ["base", "optimistic", "pessimistic"]

    print(f"\nGenerating Financial Projections")
    print(f"City: {city_name}")
    print(f"Base Year: {base_year}")
    print(f"Projection Horizon: {years_ahead} years")
    print(f"Scenarios: {', '.join(scenarios)}")
    print(f"Model Version: {model_version}\n")

    # Initialize scenario engine
    engine = ScenarioEngine(session, city.id)

    results = {}

    for scenario_code in scenarios:
        print(f"Running {scenario_code.upper()} scenario...")

        try:
            # Run scenario
            projections, fiscal_cliff = engine.run_scenario(
                base_year=base_year,
                years_ahead=years_ahead,
                scenario_code=scenario_code,
                model_version=model_version,
            )

            # Save projections
            for projection in projections:
                session.add(projection)

            # Save fiscal cliff analysis
            if fiscal_cliff:
                session.add(fiscal_cliff)

            session.commit()

            results[scenario_code] = projections

            # Print summary
            deficit_years = sum(1 for p in projections if p.is_deficit)
            cliff_year = (
                fiscal_cliff.fiscal_cliff_year
                if fiscal_cliff and fiscal_cliff.fiscal_cliff_year
                else "N/A"
            )

            print(f"  ✓ Generated {len(projections)} projections")
            print(f"  • Deficit years: {deficit_years}/{len(projections)}")
            print(f"  • Fiscal cliff year: {cliff_year}")

            if fiscal_cliff and fiscal_cliff.years_to_depletion:
                print(f"  • Years to depletion: {fiscal_cliff.years_to_depletion}")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            session.rollback()
            continue

    return results


def generate_comparison_report(
    projections_by_scenario: Dict[str, List[FinancialProjection]]
) -> str:
    """
    Generate scenario comparison report.

    Args:
        projections_by_scenario: Dictionary of scenario -> projections

    Returns:
        Formatted report string
    """
    if not projections_by_scenario:
        return "No projections to report."

    # Get base year from first projection
    first_scenario = next(iter(projections_by_scenario.values()))
    base_year = first_scenario[0].base_fiscal_year.year

    report = [
        "\n" + "=" * 140,
        f"FINANCIAL PROJECTIONS COMPARISON REPORT (Base Year: {base_year})",
        "=" * 140,
        "",
    ]

    # Build comparison table
    table_data = []

    # Get all projection years (assume all scenarios have same years)
    years = [p.projection_year for p in first_scenario]

    for year in years:
        row = [str(year)]

        for scenario_name in ["base", "optimistic", "pessimistic"]:
            if scenario_name not in projections_by_scenario:
                row.extend(["N/A", "N/A", "N/A"])
                continue

            projections = projections_by_scenario[scenario_name]
            projection = next((p for p in projections if p.projection_year == year), None)

            if not projection:
                row.extend(["N/A", "N/A", "N/A"])
                continue

            surplus = float(projection.operating_surplus_deficit) / 1_000_000
            fund_balance = float(projection.ending_fund_balance) / 1_000_000
            fb_ratio = float(projection.fund_balance_ratio) * 100

            row.extend(
                [
                    f"${surplus:,.1f}M",
                    f"${fund_balance:,.1f}M",
                    f"{fb_ratio:.1f}%",
                ]
            )

        table_data.append(row)

    headers = ["Year"]
    for scenario in ["Base", "Optimistic", "Pessimistic"]:
        headers.extend([f"{scenario}\nSurplus", f"{scenario}\nFund Bal", f"{scenario}\nFB Ratio"])

    report.append(tabulate(table_data, headers=headers, tablefmt="grid"))
    report.append("")

    # Add fiscal cliff comparison
    report.append("FISCAL CLIFF ANALYSIS:")
    report.append("-" * 80)

    for scenario_name in ["base", "optimistic", "pessimistic"]:
        if scenario_name not in projections_by_scenario:
            continue

        projections = projections_by_scenario[scenario_name]
        if projections:
            # Find first projection with fiscal_cliff_analysis
            cliff_analysis = None
            for p in projections:
                if hasattr(p, "fiscal_cliff") and p.fiscal_cliff:
                    cliff_analysis = p.fiscal_cliff
                    break

            if cliff_analysis:
                cliff_year = cliff_analysis.fiscal_cliff_year or "No cliff detected"
                years_to_depletion = (
                    f"{cliff_analysis.years_to_depletion} years"
                    if cliff_analysis.years_to_depletion
                    else "N/A"
                )
                severity = cliff_analysis.severity_rating or "N/A"

                report.append(
                    f"  {scenario_name.upper():12} - "
                    f"Cliff Year: {cliff_year:8} | "
                    f"Years to Depletion: {years_to_depletion:10} | "
                    f"Severity: {severity}"
                )
            else:
                report.append(f"  {scenario_name.upper():12} - No cliff analysis available")

    report.append("")
    report.append("=" * 140 + "\n")

    return "\n".join(report)


def validate_projections(projections: List[FinancialProjection]) -> None:
    """
    Validate that projections are sensible.

    Args:
        projections: List of projections to validate
    """
    print("\nValidating Projections...")

    issues = []

    for i, proj in enumerate(projections):
        # Check for negative revenues
        if proj.total_revenues_projected < 0:
            issues.append(f"  Year {proj.projection_year}: Negative revenues")

        # Check for extreme growth rates
        if abs(float(proj.revenue_growth_rate)) > 0.20:  # >20% growth
            issues.append(
                f"  Year {proj.projection_year}: "
                f"Extreme revenue growth rate: {proj.revenue_growth_rate:.1%}"
            )

        # Check fund balance progression
        if i > 0:
            prev = projections[i - 1]
            expected_fb = (
                prev.ending_fund_balance
                + proj.total_revenues_projected
                - proj.total_expenditures_projected
            )
            variance = abs(expected_fb - proj.ending_fund_balance)
            if variance > 1000:  # $1000 tolerance for rounding
                issues.append(
                    f"  Year {proj.projection_year}: "
                    f"Fund balance doesn't match formula (variance: ${variance:,.2f})"
                )

    if issues:
        print("  ⚠ Validation Issues Found:")
        for issue in issues:
            print(issue)
    else:
        print("  ✓ All validation checks passed")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate financial projections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--city", default="Vallejo", help="City name (default: Vallejo)")
    parser.add_argument(
        "--base-year",
        type=int,
        help="Base fiscal year (default: most recent year)",
    )
    parser.add_argument(
        "--scenario",
        choices=["base", "optimistic", "pessimistic"],
        help="Specific scenario to run (default: all scenarios)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Number of years to project (default: 10)",
    )
    parser.add_argument(
        "--model-version",
        default="1.0",
        help="Projection model version (default: 1.0)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating comparison report",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation checks on projections",
    )

    args = parser.parse_args()

    # Determine scenarios to run
    scenarios = [args.scenario] if args.scenario else None

    # Create database engine
    engine = create_engine(settings.database_url, echo=False)

    with Session(engine) as session:
        # Generate projections
        projections_by_scenario = generate_projections(
            session=session,
            city_name=args.city,
            base_year=args.base_year,
            scenarios=scenarios,
            years_ahead=args.years,
            model_version=args.model_version,
        )

        if not projections_by_scenario:
            return 1

        total_projections = sum(len(p) for p in projections_by_scenario.values())
        print(f"\n✓ Successfully generated {total_projections} projection(s)")

        # Validate projections
        if args.validate:
            for scenario_name, projections in projections_by_scenario.items():
                print(f"\nValidating {scenario_name} scenario:")
                validate_projections(projections)

        # Generate comparison report
        if not args.no_report and len(projections_by_scenario) > 1:
            report = generate_comparison_report(projections_by_scenario)
            print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
