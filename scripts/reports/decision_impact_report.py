#!/usr/bin/env python3
"""
Decision Impact Report Generator

Generates quarterly reports showing:
- All logged decisions
- Predicted vs. actual fiscal impacts
- Prediction accuracy analysis
- Insights and learnings

Transparent reporting of both successes and failures builds
institutional credibility and demonstrates analytical rigor.

Usage:
    python scripts/reports/decision_impact_report.py --city-id 1 --quarter Q4 --year 2024
    python scripts/reports/decision_impact_report.py --city-id 1 --output decision_impact_Q4_2024.md
"""

import argparse
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.database.session import get_session
from src.database.models.civic import (
    Decision,
    DecisionCategory,
    DecisionStatus,
    Outcome,
    OutcomeStatus,
)
from src.database.models.core import City
from src.analytics.decision_impact import DecisionAccuracyTracker
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DecisionImpactReportGenerator:
    """Generate quarterly decision impact reports."""

    def __init__(self, db: Session):
        self.db = db
        self.tracker = DecisionAccuracyTracker(db)

    def generate_report(
        self,
        city_id: int,
        year: int,
        quarter: int,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate quarterly decision impact report.

        Args:
            city_id: City ID
            year: Report year
            quarter: Quarter number (1-4)
            output_path: Optional output file path

        Returns:
            Report content as markdown string
        """
        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City {city_id} not found")

        # Determine quarter date range
        quarter_start, quarter_end = self._get_quarter_dates(year, quarter)

        # Generate report sections
        report = []
        report.append(self._generate_header(city, year, quarter))
        report.append(self._generate_executive_summary(city_id, quarter_start, quarter_end))
        report.append(self._generate_decisions_logged(city_id, quarter_start, quarter_end))
        report.append(self._generate_predictions_vs_actuals(city_id, quarter_start, quarter_end))
        report.append(self._generate_accuracy_analysis(city_id, year))
        report.append(self._generate_insights(city_id, quarter_start, quarter_end))
        report.append(self._generate_footer())

        markdown_content = "\n\n".join(report)

        # Write to file if specified
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown_content)
            logger.info(f"Report written to {output_path}")

        return markdown_content

    def _generate_header(self, city: City, year: int, quarter: int) -> str:
        """Generate report header."""
        quarter_name = f"Q{quarter} {year}"
        return f"""# Decision Impact Report: {city.name}
## {quarter_name}

**Generated:** {datetime.now().strftime('%B %d, %Y')}

---

## About This Report

This report tracks city council decisions and ballot measures, comparing predicted
fiscal impacts to actual outcomes. Transparent tracking of both successes and failures
demonstrates analytical rigor and builds institutional credibility.

**Key Principles:**
- **Transparency**: Report all predictions, accurate and inaccurate
- **Accountability**: Acknowledge errors and explain variances
- **Learning**: Use accuracy data to improve future predictions
- **Credibility**: Build public trust through honest assessment
"""

    def _generate_executive_summary(
        self,
        city_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate executive summary."""
        # Count decisions by status
        total_decisions = self.db.query(Decision).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.is_deleted == False
        ).count()

        approved = self.db.query(Decision).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.status == DecisionStatus.APPROVED,
            Decision.is_deleted == False
        ).count()

        with_outcomes = self.db.query(Decision).join(Decision.outcomes).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.is_deleted == False
        ).distinct().count()

        # Get accuracy metrics for completed decisions
        accuracy_metrics = self.tracker.calculate_accuracy_metrics(
            city_id=city_id,
            start_date=start_date,
            end_date=end_date
        )

        content = f"""## Executive Summary

**Quarter Highlights:**

- **{total_decisions} decisions** logged this quarter
- **{approved} decisions** approved by council/voters
- **{with_outcomes} decisions** have outcome tracking initiated
"""

        if accuracy_metrics.get('count', 0) > 0:
            avg_acc = accuracy_metrics['avg_accuracy_percent']
            within_10 = accuracy_metrics['decisions_within_10_percent']
            total = accuracy_metrics['count']

            content += f"""
**Prediction Accuracy:**

- **{total} decisions** with final outcomes available
- **Average accuracy:** {avg_acc:.1f}% of predicted impact
- **{within_10} of {total}** predictions within 10% of actual (highly accurate)
"""

            if avg_acc >= 90:
                content += "\n✓ **Excellent** prediction accuracy this quarter\n"
            elif avg_acc >= 80:
                content += "\n✓ **Good** prediction accuracy this quarter\n"
            else:
                content += "\n⚠ **Below target** - see variance analysis below\n"
        else:
            content += """
**Prediction Accuracy:**

- No final outcomes available yet for this quarter's decisions
- Predictions pending verification as actual data becomes available
"""

        return content

    def _generate_decisions_logged(
        self,
        city_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate section listing all decisions logged this quarter."""
        decisions = self.db.query(Decision).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.is_deleted == False
        ).order_by(Decision.decision_date).all()

        if not decisions:
            return "## Decisions Logged This Quarter\n\nNo decisions logged this quarter."

        content = f"## Decisions Logged This Quarter\n\n"
        content += f"**Total: {len(decisions)} decisions**\n\n"

        # Group by category
        by_category = {}
        for decision in decisions:
            category = decision.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(decision)

        for category, cat_decisions in sorted(by_category.items()):
            content += f"### {category.replace('_', ' ').title()}\n\n"

            for decision in cat_decisions:
                content += f"#### {decision.title}\n\n"
                content += f"**Date:** {decision.decision_date.strftime('%B %d, %Y')}  \n"
                content += f"**Status:** {decision.status.value.replace('_', ' ').title()}  \n"

                if decision.predicted_annual_impact:
                    impact = decision.predicted_annual_impact
                    impact_str = f"${abs(impact):,.0f}"
                    if impact > 0:
                        content += f"**Predicted Impact:** +{impact_str} annual revenue  \n"
                    else:
                        content += f"**Predicted Impact:** -{impact_str} annual cost  \n"

                    if decision.prediction_confidence:
                        content += f"**Confidence:** {decision.prediction_confidence.title()}  \n"

                content += f"\n{decision.description}\n\n"

                # Show any outcomes
                if decision.outcomes.count() > 0:
                    latest_outcome = decision.latest_outcome
                    if latest_outcome:
                        content += f"**Outcome Status:** {latest_outcome.status.value.title()}  \n"
                        if latest_outcome.actual_annual_impact:
                            actual = latest_outcome.actual_annual_impact
                            actual_str = f"${abs(actual):,.0f}"
                            if actual > 0:
                                content += f"**Actual Impact:** +{actual_str} annual revenue  \n"
                            else:
                                content += f"**Actual Impact:** -{actual_str} annual cost  \n"

                            if latest_outcome.accuracy_percent:
                                content += f"**Accuracy:** {latest_outcome.accuracy_percent:.1f}%  \n"

                        content += "\n"

                content += "---\n\n"

        return content

    def _generate_predictions_vs_actuals(
        self,
        city_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate predictions vs. actuals comparison table."""
        # Get decisions with final outcomes
        decisions = self.db.query(Decision).options(
            joinedload(Decision.outcomes)
        ).join(Decision.outcomes).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.is_deleted == False,
            Outcome.status == OutcomeStatus.FINAL
        ).distinct().all()

        if not decisions:
            return """## Predictions vs. Actuals

No final outcomes available for this quarter's decisions yet.
Predictions will be verified as actual data becomes available over the next 6-12 months.
"""

        content = "## Predictions vs. Actuals\n\n"
        content += "| Decision | Predicted | Actual | Accuracy | Variance |\n"
        content += "|----------|-----------|--------|----------|----------|\n"

        for decision in decisions:
            latest_outcome = decision.latest_outcome
            if not latest_outcome or not latest_outcome.actual_annual_impact:
                continue

            predicted = decision.predicted_annual_impact or Decimal(0)
            actual = latest_outcome.actual_annual_impact
            accuracy = latest_outcome.accuracy_percent or Decimal(0)

            # Format amounts
            pred_str = self._format_impact(predicted)
            actual_str = self._format_impact(actual)
            acc_str = f"{accuracy:.1f}%"

            # Calculate variance
            variance = abs(float(actual) - float(predicted))
            var_str = f"${variance:,.0f}"

            # Accuracy indicator
            if 90 <= accuracy <= 110:
                acc_indicator = f"✓ {acc_str}"
            elif 75 <= accuracy <= 125:
                acc_indicator = f"○ {acc_str}"
            else:
                acc_indicator = f"⚠ {acc_str}"

            title_short = decision.title[:40] + "..." if len(decision.title) > 40 else decision.title
            content += f"| {title_short} | {pred_str} | {actual_str} | {acc_indicator} | {var_str} |\n"

        content += "\n**Legend:**  \n"
        content += "✓ = Within 10% (highly accurate)  \n"
        content += "○ = Within 25% (acceptable)  \n"
        content += "⚠ = >25% variance (needs analysis)\n"

        return content

    def _generate_accuracy_analysis(self, city_id: int, year: int) -> str:
        """Generate year-to-date accuracy analysis."""
        # Get YTD metrics
        ytd_start = date(year, 1, 1)
        ytd_end = date(year, 12, 31)

        metrics = self.tracker.calculate_accuracy_metrics(
            city_id=city_id,
            start_date=ytd_start,
            end_date=ytd_end
        )

        if metrics.get('count', 0) == 0:
            return """## Accuracy Analysis (Year-to-Date)

No decisions with final outcomes yet for {year}. Building track record...
"""

        content = f"## Accuracy Analysis (Year-to-Date)\n\n"

        avg_acc = metrics['avg_accuracy_percent']
        median_acc = metrics['median_accuracy_percent']
        count = metrics['count']
        within_10 = metrics['decisions_within_10_percent']
        within_25 = metrics['decisions_within_25_percent']
        avg_error = metrics.get('avg_absolute_error', 0)

        content += f"**Overall Performance ({count} decisions with final outcomes):**\n\n"
        content += f"- **Average Accuracy:** {avg_acc:.1f}%\n"
        content += f"- **Median Accuracy:** {median_acc:.1f}%\n"
        content += f"- **Highly Accurate (±10%):** {within_10} of {count} ({within_10/count*100:.0f}%)\n"
        content += f"- **Acceptable (±25%):** {within_25} of {count} ({within_25/count*100:.0f}%)\n"
        content += f"- **Average Absolute Error:** ${avg_error:,.0f}\n\n"

        # Accuracy by category
        content += "### Accuracy by Decision Category\n\n"
        content += "| Category | Decisions | Avg Accuracy | Median Accuracy |\n"
        content += "|----------|-----------|--------------|------------------|\n"

        for category in DecisionCategory:
            cat_metrics = self.tracker.calculate_accuracy_metrics(
                city_id=city_id,
                category=category,
                start_date=ytd_start,
                end_date=ytd_end
            )

            if cat_metrics.get('count', 0) > 0:
                cat_count = cat_metrics['count']
                cat_avg = cat_metrics['avg_accuracy_percent']
                cat_median = cat_metrics['median_accuracy_percent']

                cat_name = category.value.replace('_', ' ').title()
                content += f"| {cat_name} | {cat_count} | {cat_avg:.1f}% | {cat_median:.1f}% |\n"

        return content

    def _generate_insights(
        self,
        city_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate insights and learnings."""
        content = "## Insights & Learnings\n\n"

        # Get decisions with variance explanations
        decisions_with_variance = self.db.query(Decision).join(Decision.outcomes).filter(
            Decision.city_id == city_id,
            Decision.decision_date >= start_date,
            Decision.decision_date <= end_date,
            Decision.is_deleted == False,
            Outcome.variance_explanation.isnot(None)
        ).all()

        if decisions_with_variance:
            content += "### Why Predictions Differed from Actuals\n\n"

            for decision in decisions_with_variance:
                latest_outcome = decision.latest_outcome
                if latest_outcome and latest_outcome.variance_explanation:
                    content += f"**{decision.title}**\n\n"
                    content += f"{latest_outcome.variance_explanation}\n\n"

        # General insights
        content += "### Key Takeaways\n\n"

        # Calculate some statistics for insights
        metrics = self.tracker.calculate_accuracy_metrics(
            city_id=city_id,
            start_date=start_date,
            end_date=end_date
        )

        if metrics.get('count', 0) > 0:
            avg_acc = metrics['avg_accuracy_percent']

            if avg_acc >= 90:
                content += "- ✓ **Strong prediction accuracy** demonstrates robust analytical methodology\n"
            elif avg_acc >= 80:
                content += "- ○ **Good prediction accuracy** with room for refinement\n"
            else:
                content += "- ⚠ **Below-target accuracy** requires methodology review\n"

            within_10_pct = (metrics['decisions_within_10_percent'] / metrics['count']) * 100

            if within_10_pct >= 75:
                content += f"- ✓ **Highly reliable predictions:** {within_10_pct:.0f}% within 10% of actual\n"
            elif within_10_pct >= 50:
                content += f"- ○ **Mostly reliable:** {within_10_pct:.0f}% within 10% of actual\n"
            else:
                content += f"- ⚠ **Reliability concerns:** Only {within_10_pct:.0f}% within 10% of actual\n"

        content += "- **Transparency builds trust:** Honest reporting of both successes and failures\n"
        content += "- **Continuous improvement:** Using accuracy data to refine prediction models\n"
        content += "- **Institutional credibility:** Track record demonstrates analytical rigor\n\n"

        content += "### Areas for Improvement\n\n"
        content += "Based on this quarter's outcomes, we will:\n\n"
        content += "1. Continue refining category-specific prediction models\n"
        content += "2. Increase confidence intervals for high-uncertainty decisions\n"
        content += "3. Seek early outcome data (6-month actuals) for faster feedback\n"
        content += "4. Improve documentation of assumptions and methodology\n"

        return content

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """---

## Methodology & Transparency

**Prediction Methodology:**

Fiscal impact predictions use category-specific models based on:
- Historical financial data
- Industry benchmarks
- Actuarial analysis (where applicable)
- Expert judgment and assumptions

**Accuracy Measurement:**

Accuracy = (Actual Impact / Predicted Impact) × 100%

- 100% = Perfect prediction
- >100% = Actual exceeded prediction
- <100% = Actual less than prediction
- 90-110% = Highly accurate
- 75-125% = Acceptable variance

**Why Transparency Matters:**

Public reporting of prediction accuracy:
1. **Builds institutional credibility** through accountability
2. **Demonstrates analytical rigor** and continuous improvement
3. **Enables public verification** of claims and methodology
4. **Acknowledges uncertainty** inherent in fiscal projections
5. **Shows commitment to truth** over political convenience

---

**Questions or corrections?** Contact: data@ibco-ca.us

**Data lineage:** All decisions link to source documents (council agendas, ballot measures, etc.)
View complete audit trail at: https://api.ibco-ca.us/api/v1/decisions
"""

    def _get_quarter_dates(self, year: int, quarter: int) -> tuple[date, date]:
        """Get start and end dates for a quarter."""
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }

        if quarter not in quarter_months:
            raise ValueError(f"Invalid quarter: {quarter}. Must be 1-4.")

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

    def _format_impact(self, amount: Decimal) -> str:
        """Format fiscal impact amount."""
        if amount > 0:
            return f"+${amount:,.0f}"
        elif amount < 0:
            return f"-${abs(amount):,.0f}"
        else:
            return "$0"


def main():
    parser = argparse.ArgumentParser(
        description="Generate quarterly decision impact report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Q4 2024 report
  python scripts/reports/decision_impact_report.py --city-id 1 --year 2024 --quarter 4

  # Save to specific file
  python scripts/reports/decision_impact_report.py --city-id 1 --year 2024 --quarter 4 \\
    --output reports/decisions/vallejo_Q4_2024.md

  # Generate report for custom date range
  python scripts/reports/decision_impact_report.py --city-id 1 --year 2024 --quarter 3
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
        help="Report year"
    )
    parser.add_argument(
        "--quarter",
        type=int,
        required=True,
        choices=[1, 2, 3, 4],
        help="Quarter number (1-4)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: print to stdout)"
    )

    args = parser.parse_args()

    # Generate report
    with get_session() as db:
        generator = DecisionImpactReportGenerator(db)

        try:
            report = generator.generate_report(
                city_id=args.city_id,
                year=args.year,
                quarter=args.quarter,
                output_path=args.output
            )

            if not args.output:
                print(report)

            print(f"\n✓ Report generated successfully", file=sys.stderr)

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
