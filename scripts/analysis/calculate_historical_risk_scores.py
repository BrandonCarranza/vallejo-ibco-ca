#!/usr/bin/env python3
"""
Historical Risk Score Calculation Script

Runs risk scoring engine on all loaded fiscal years to generate historical risk scores
and identify risk progression over time.

Usage:
    poetry run python scripts/analysis/calculate_historical_risk_scores.py [options]

Examples:
    # Calculate risk scores for all fiscal years
    poetry run python scripts/analysis/calculate_historical_risk_scores.py

    # Calculate for specific fiscal year
    poetry run python scripts/analysis/calculate_historical_risk_scores.py --fiscal-year 2024

    # Recalculate existing scores
    poetry run python scripts/analysis/calculate_historical_risk_scores.py --recalculate

    # Calculate for specific city
    poetry run python scripts/analysis/calculate_historical_risk_scores.py --city Vallejo
"""

import argparse
import sys
from datetime import datetime
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tabulate import tabulate

from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine
from src.config.settings import settings
from src.database.models import City, FiscalYear, RiskScore


def calculate_risk_scores(
    session: Session,
    city_name: str,
    fiscal_year: int = None,
    recalculate: bool = False,
    model_version: str = "1.0",
) -> List[RiskScore]:
    """
    Calculate risk scores for fiscal years.

    Args:
        session: Database session
        city_name: Name of city
        fiscal_year: Specific year (if None, calculate all)
        recalculate: If True, recalculate existing scores
        model_version: Risk scoring model version

    Returns:
        List of calculated RiskScore objects
    """
    # Get city
    city = session.query(City).filter(City.name == city_name).first()
    if not city:
        print(f"Error: City '{city_name}' not found")
        return []

    # Get fiscal years
    query = session.query(FiscalYear).filter(FiscalYear.city_id == city.id)
    if fiscal_year:
        query = query.filter(FiscalYear.year == fiscal_year)
    fiscal_years = query.order_by(FiscalYear.year).all()

    if not fiscal_years:
        print(f"Error: No fiscal years found for {city_name}")
        return []

    print(f"\nCalculating risk scores for {len(fiscal_years)} fiscal year(s)...")
    print(f"City: {city_name}")
    print(f"Model Version: {model_version}")
    print(f"Recalculate: {recalculate}\n")

    # Initialize scoring engine
    engine = RiskScoringEngine(session)

    calculated_scores = []

    for fy in fiscal_years:
        # Check if score already exists
        existing_score = (
            session.query(RiskScore)
            .filter(RiskScore.fiscal_year_id == fy.id)
            .first()
        )

        if existing_score and not recalculate:
            print(f"  FY{fy.year}: Skipping (score already exists)")
            calculated_scores.append(existing_score)
            continue

        if existing_score and recalculate:
            print(f"  FY{fy.year}: Recalculating existing score...")
            # Delete existing score and related indicator scores
            session.delete(existing_score)
            session.commit()

        # Calculate risk score
        try:
            risk_score = engine.calculate_risk_score(
                fiscal_year_id=fy.id, model_version=model_version
            )

            # Save to database
            session.add(risk_score)
            session.commit()

            print(
                f"  FY{fy.year}: Score = {risk_score.overall_score:.1f} "
                f"({risk_score.risk_level}) | "
                f"Data Completeness = {risk_score.data_completeness_percent:.0f}%"
            )

            calculated_scores.append(risk_score)

        except Exception as e:
            print(f"  FY{fy.year}: ERROR - {str(e)}")
            session.rollback()

    return calculated_scores


def generate_progression_report(risk_scores: List[RiskScore]) -> str:
    """
    Generate risk score progression report.

    Args:
        risk_scores: List of risk scores ordered by year

    Returns:
        Formatted report string
    """
    if not risk_scores:
        return "No risk scores to report."

    # Build table data
    table_data = []
    for score in risk_scores:
        fiscal_year = score.fiscal_year
        table_data.append(
            [
                f"FY{fiscal_year.year}",
                f"{score.overall_score:.1f}",
                score.risk_level,
                f"{score.liquidity_score:.1f}",
                f"{score.structural_balance_score:.1f}",
                f"{score.pension_stress_score:.1f}",
                f"{score.revenue_sustainability_score:.1f}",
                f"{score.debt_burden_score:.1f}",
                f"{score.data_completeness_percent:.0f}%",
            ]
        )

    headers = [
        "Year",
        "Overall",
        "Level",
        "Liquidity",
        "Structural",
        "Pension",
        "Revenue",
        "Debt",
        "Complete",
    ]

    report = [
        "\n" + "=" * 120,
        "RISK SCORE PROGRESSION REPORT",
        "=" * 120,
        "",
        tabulate(table_data, headers=headers, tablefmt="grid"),
        "",
    ]

    # Calculate trend
    if len(risk_scores) >= 2:
        first_score = float(risk_scores[0].overall_score)
        last_score = float(risk_scores[-1].overall_score)
        change = last_score - first_score

        trend = "IMPROVING" if change < 0 else "WORSENING" if change > 0 else "STABLE"
        trend_symbol = "↓" if change < 0 else "↑" if change > 0 else "→"

        report.extend(
            [
                f"TREND: {trend} {trend_symbol}",
                f"  First Year (FY{risk_scores[0].fiscal_year.year}): {first_score:.1f}",
                f"  Last Year (FY{risk_scores[-1].fiscal_year.year}): {last_score:.1f}",
                f"  Change: {change:+.1f} points",
                "",
            ]
        )

    # Identify persistent risk factors
    all_risk_factors = []
    for score in risk_scores:
        if score.top_risk_factors:
            all_risk_factors.extend(score.top_risk_factors)

    if all_risk_factors:
        from collections import Counter

        factor_counts = Counter(all_risk_factors)
        persistent_factors = [
            factor for factor, count in factor_counts.most_common(5) if count >= 2
        ]

        if persistent_factors:
            report.extend(
                [
                    "PERSISTENT RISK FACTORS (appearing in 2+ years):",
                    *[f"  • {factor}" for factor in persistent_factors],
                    "",
                ]
            )

    report.append("=" * 120 + "\n")

    return "\n".join(report)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate historical risk scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--city", default="Vallejo", help="City name (default: Vallejo)"
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        help="Specific fiscal year to calculate (default: all years)",
    )
    parser.add_argument(
        "--recalculate",
        action="store_true",
        help="Recalculate existing risk scores",
    )
    parser.add_argument(
        "--model-version",
        default="1.0",
        help="Risk scoring model version (default: 1.0)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating progression report",
    )

    args = parser.parse_args()

    # Create database engine
    engine = create_engine(settings.database_url, echo=False)

    with Session(engine) as session:
        # Calculate risk scores
        risk_scores = calculate_risk_scores(
            session=session,
            city_name=args.city,
            fiscal_year=args.fiscal_year,
            recalculate=args.recalculate,
            model_version=args.model_version,
        )

        if not risk_scores:
            return 1

        print(f"\n✓ Successfully calculated {len(risk_scores)} risk score(s)")

        # Generate progression report
        if not args.no_report and len(risk_scores) > 0:
            report = generate_progression_report(risk_scores)
            print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
