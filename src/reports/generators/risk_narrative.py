"""
Risk Narrative Generator.

Converts risk scores and fiscal metrics into human-readable narratives.
Explains fiscal challenges in accessible language for public communication.

Example output:
    "Vallejo's fiscal stress score of 68/100 (High) reflects significant challenges.
     Primary driver: pensions only 62% funded with $2.3B unfunded liability. At current
     trends, general fund reserves will be exhausted by FY2029, creating immediate budget
     crisis. Key risk indicators: structural deficit of $45M (15% of revenues), pension
     contributions consuming 38% of payroll, and fund balance below recommended 10% threshold."
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .base_generator import BaseReportGenerator


class RiskNarrativeGenerator(BaseReportGenerator):
    """Generate human-readable risk narratives."""

    def __init__(self, db: Session):
        """Initialize risk narrative generator."""
        super().__init__(db, template_name="risk_narrative.html")

    def get_report_context(
        self,
        city_id: int = 1,  # Default: Vallejo
        fiscal_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get context for risk narrative.

        Args:
            city_id: City ID (default: 1 for Vallejo)
            fiscal_year: Fiscal year (default: latest)

        Returns:
            Context dictionary for template rendering
        """
        from src.database.models.core import City, FiscalYear
        from src.database.models.pensions import PensionPlan
        from src.database.models.projections import FiscalCliffAnalysis
        from src.database.models.risk import RiskIndicatorScore, RiskScore

        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City ID {city_id} not found")

        # Get fiscal year
        if fiscal_year is None:
            fy = (
                self.db.query(FiscalYear)
                .filter(FiscalYear.city_id == city_id)
                .order_by(FiscalYear.year.desc())
                .first()
            )
        else:
            fy = (
                self.db.query(FiscalYear)
                .filter(
                    FiscalYear.city_id == city_id,
                    FiscalYear.year == fiscal_year,
                )
                .first()
            )

        if not fy:
            raise ValueError("No fiscal year data found")

        fiscal_year = fy.year

        # Get risk score
        risk_score = (
            self.db.query(RiskScore)
            .filter(
                RiskScore.fiscal_year_id == fy.id,
                RiskScore.is_deleted == False,
            )
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )

        if not risk_score:
            raise ValueError(f"No risk score found for {city.name} FY{fiscal_year}")

        # Get fiscal summary
        fiscal_summary = self._get_fiscal_year_summary(city_id, fiscal_year)

        # Get pension data
        pension_plans = (
            self.db.query(PensionPlan)
            .filter(
                PensionPlan.fiscal_year_id == fy.id,
                PensionPlan.is_deleted == False,
            )
            .all()
        )

        avg_funded_ratio = None
        total_ual = 0
        total_contribution = 0

        if pension_plans:
            funded_ratios = [p.funded_ratio for p in pension_plans if p.funded_ratio]
            if funded_ratios:
                avg_funded_ratio = sum(funded_ratios) / len(funded_ratios)

            total_ual = sum(p.unfunded_actuarial_liability or 0 for p in pension_plans)
            total_contribution = sum(p.total_employer_contribution or 0 for p in pension_plans)

        # Get fiscal cliff analysis
        fiscal_cliff = (
            self.db.query(FiscalCliffAnalysis)
            .filter(
                FiscalCliffAnalysis.city_id == city_id,
                FiscalCliffAnalysis.base_fiscal_year_id == fy.id,
            )
            .first()
        )

        # Get top risk indicators
        top_indicators = (
            self.db.query(RiskIndicatorScore)
            .filter(
                RiskIndicatorScore.risk_score_id == risk_score.id,
                RiskIndicatorScore.is_deleted == False,
            )
            .order_by(RiskIndicatorScore.indicator_score.desc())
            .limit(5)
            .all()
        )

        # Generate narrative components
        narrative = self._generate_narrative(
            city_name=city.name,
            fiscal_year=fiscal_year,
            risk_score=risk_score,
            fiscal_summary=fiscal_summary,
            avg_funded_ratio=avg_funded_ratio,
            total_ual=total_ual,
            total_contribution=total_contribution,
            fiscal_cliff=fiscal_cliff,
            top_indicators=top_indicators,
        )

        return {
            "city_name": city.name,
            "fiscal_year": fiscal_year,
            "narrative": narrative,
            "risk_score": risk_score,
            "fiscal_summary": fiscal_summary,
            "pension_summary": {
                "avg_funded_ratio": avg_funded_ratio,
                "total_ual": total_ual,
                "total_contribution": total_contribution,
            },
            "fiscal_cliff": fiscal_cliff,
            "top_indicators": top_indicators,
        }

    def _generate_narrative(
        self,
        city_name: str,
        fiscal_year: int,
        risk_score,
        fiscal_summary: Dict[str, Any],
        avg_funded_ratio: Optional[float],
        total_ual: float,
        total_contribution: float,
        fiscal_cliff,
        top_indicators: List,
    ) -> Dict[str, str]:
        """
        Generate narrative sections.

        Args:
            city_name: City name
            fiscal_year: Fiscal year
            risk_score: RiskScore object
            fiscal_summary: Fiscal summary dictionary
            avg_funded_ratio: Average pension funded ratio
            total_ual: Total unfunded actuarial liability
            total_contribution: Total pension contribution
            fiscal_cliff: FiscalCliffAnalysis object
            top_indicators: Top risk indicators

        Returns:
            Dictionary with narrative sections
        """
        # Executive summary
        executive_summary = self._generate_executive_summary(
            city_name,
            fiscal_year,
            risk_score,
            fiscal_summary,
            avg_funded_ratio,
            total_ual,
            fiscal_cliff,
        )

        # Primary drivers analysis
        primary_drivers = self._generate_primary_drivers(
            risk_score,
            fiscal_summary,
            avg_funded_ratio,
            total_ual,
            total_contribution,
        )

        # Fiscal cliff warning
        fiscal_cliff_text = self._generate_fiscal_cliff_warning(
            fiscal_year,
            fiscal_cliff,
            fiscal_summary,
        )

        # Key risk indicators
        key_indicators_text = self._generate_key_indicators(
            fiscal_summary,
            avg_funded_ratio,
            total_contribution,
            top_indicators,
        )

        # Conclusion
        conclusion = self._generate_conclusion(
            city_name,
            risk_score,
            fiscal_cliff,
        )

        return {
            "executive_summary": executive_summary,
            "primary_drivers": primary_drivers,
            "fiscal_cliff_warning": fiscal_cliff_text,
            "key_indicators": key_indicators_text,
            "conclusion": conclusion,
            "full_narrative": f"{executive_summary} {primary_drivers} {fiscal_cliff_text} {key_indicators_text}",
        }

    def _generate_executive_summary(
        self,
        city_name: str,
        fiscal_year: int,
        risk_score,
        fiscal_summary: Dict[str, Any],
        avg_funded_ratio: Optional[float],
        total_ual: float,
        fiscal_cliff,
    ) -> str:
        """Generate executive summary paragraph."""
        score = float(risk_score.overall_score)
        level = risk_score.risk_level.capitalize()

        # Determine severity language
        if score >= 75:
            severity = "severe"
        elif score >= 50:
            severity = "significant"
        else:
            severity = "moderate"

        summary = (
            f"{city_name}'s fiscal stress score of {score:.0f}/100 ({level}) "
            f"for FY{fiscal_year} reflects {severity} financial challenges. "
        )

        # Add primary challenge
        if avg_funded_ratio and avg_funded_ratio < 0.70:
            summary += (
                f"The city's pension system is only {avg_funded_ratio:.0%} funded "
                f"with {self.format_currency(total_ual, compact=True)} in unfunded liabilities. "
            )

        if fiscal_summary.get("operating_balance") and fiscal_summary["operating_balance"] < 0:
            deficit = abs(fiscal_summary["operating_balance"])
            summary += (
                f"The city is running a structural deficit of "
                f"{self.format_currency(deficit, compact=True)}, "
                f"depleting reserves. "
            )

        if fiscal_cliff and fiscal_cliff.has_fiscal_cliff:
            years_until = fiscal_cliff.years_until_cliff or 0
            if years_until <= 5:
                summary += (
                    f"At current trends, general fund reserves will be exhausted by "
                    f"FY{fiscal_cliff.fiscal_cliff_year}, creating an immediate budget crisis."
                )

        return summary

    def _generate_primary_drivers(
        self,
        risk_score,
        fiscal_summary: Dict[str, Any],
        avg_funded_ratio: Optional[float],
        total_ual: float,
        total_contribution: float,
    ) -> str:
        """Generate primary drivers analysis."""
        drivers = []

        # Identify top 3 category scores
        categories = [
            ("Pension stress", risk_score.pension_stress_score),
            ("Structural imbalance", risk_score.structural_balance_score),
            ("Liquidity crisis", risk_score.liquidity_score),
            ("Revenue sustainability", risk_score.revenue_sustainability_score),
            ("Debt burden", risk_score.debt_burden_score),
        ]

        sorted_categories = sorted(categories, key=lambda x: x[1], reverse=True)
        top_drivers = sorted_categories[:3]

        text = "Primary drivers of fiscal stress: "

        for i, (name, score) in enumerate(top_drivers):
            if i > 0:
                text += ", "

            text += f"{name.lower()} ({score:.0f}/100)"

            # Add context for top driver
            if i == 0:
                if "pension" in name.lower() and avg_funded_ratio:
                    text += (
                        f" driven by pensions only {avg_funded_ratio:.0%} funded "
                        f"with {self.format_currency(total_ual, compact=True)} unfunded liability"
                    )
                elif "structural" in name.lower() and fiscal_summary.get("operating_balance"):
                    deficit = abs(fiscal_summary["operating_balance"])
                    if fiscal_summary.get("total_revenues"):
                        deficit_pct = (deficit / fiscal_summary["total_revenues"]) * 100
                        text += (
                            f" with structural deficit of "
                            f"{self.format_currency(deficit, compact=True)} ({deficit_pct:.0f}% of revenues)"
                        )
                elif "liquidity" in name.lower() and fiscal_summary.get("fund_balance_ratio"):
                    fb_ratio = fiscal_summary["fund_balance_ratio"]
                    text += f" with fund balance at {self.format_percent(fb_ratio)} of expenditures"

        text += ". "

        return text

    def _generate_fiscal_cliff_warning(
        self,
        fiscal_year: int,
        fiscal_cliff,
        fiscal_summary: Dict[str, Any],
    ) -> str:
        """Generate fiscal cliff warning."""
        if not fiscal_cliff or not fiscal_cliff.has_fiscal_cliff:
            return "Current projections do not show immediate reserve depletion. "

        cliff_year = fiscal_cliff.fiscal_cliff_year
        years_until = fiscal_cliff.years_until_cliff or 0

        if years_until <= 3:
            urgency = "imminent"
        elif years_until <= 5:
            urgency = "near-term"
        else:
            urgency = "long-term"

        text = (
            f"At current trends, the city faces a fiscal cliff in FY{cliff_year} "
            f"({years_until} years away) when reserves will be exhausted—"
            f"an {urgency} crisis. "
        )

        # Add correction required
        if fiscal_cliff.revenue_increase_needed_percent:
            rev_increase = fiscal_cliff.revenue_increase_needed_percent
            text += (
                f"Avoiding this outcome would require either a "
                f"{rev_increase:.0f}% increase in revenues "
            )

            if fiscal_cliff.expenditure_decrease_needed_percent:
                exp_decrease = fiscal_cliff.expenditure_decrease_needed_percent
                text += f"or a {exp_decrease:.0f}% reduction in expenditures. "
            else:
                text += ". "

        return text

    def _generate_key_indicators(
        self,
        fiscal_summary: Dict[str, Any],
        avg_funded_ratio: Optional[float],
        total_contribution: float,
        top_indicators: List,
    ) -> str:
        """Generate key risk indicators text."""
        indicators = []

        # Fund balance ratio
        if fiscal_summary.get("fund_balance_ratio"):
            fb_ratio = fiscal_summary["fund_balance_ratio"]
            if fb_ratio < 0.10:
                indicators.append(
                    f"fund balance below recommended 10% threshold at {self.format_percent(fb_ratio)}"
                )

        # Structural deficit
        if fiscal_summary.get("operating_balance") and fiscal_summary["operating_balance"] < 0:
            deficit = abs(fiscal_summary["operating_balance"])
            if fiscal_summary.get("total_revenues"):
                deficit_pct = (deficit / fiscal_summary["total_revenues"]) * 100
                indicators.append(
                    f"structural deficit of {self.format_currency(deficit, compact=True)} "
                    f"({deficit_pct:.0f}% of revenues)"
                )

        # Pension contribution burden
        if total_contribution and fiscal_summary.get("total_expenditures"):
            contrib_pct = (total_contribution / fiscal_summary["total_expenditures"]) * 100
            if contrib_pct > 30:
                indicators.append(
                    f"pension contributions consuming {contrib_pct:.0f}% of total budget"
                )

        # Pension funded ratio
        if avg_funded_ratio and avg_funded_ratio < 0.70:
            indicators.append(f"pension system only {self.format_percent(avg_funded_ratio)} funded")

        if indicators:
            text = "Key risk indicators: "
            text += ", ".join(indicators)
            text += ". "
            return text

        return ""

    def _generate_conclusion(
        self,
        city_name: str,
        risk_score,
        fiscal_cliff,
    ) -> str:
        """Generate conclusion."""
        score = float(risk_score.overall_score)

        if score >= 75:
            severity = "Immediate action is required to avoid fiscal insolvency"
        elif score >= 50:
            severity = "Significant reforms are needed to restore fiscal sustainability"
        else:
            severity = "Continued monitoring and proactive management are recommended"

        text = f"{severity}. "

        if fiscal_cliff and fiscal_cliff.has_fiscal_cliff:
            years_until = fiscal_cliff.years_until_cliff or 0
            if years_until <= 5:
                text += (
                    f"Without corrective measures, {city_name} faces reserve depletion "
                    f"within {years_until} years, forcing drastic service cuts or insolvency. "
                )

        text += (
            "This analysis is based on transparent, auditable data with complete lineage "
            "to source documents. All methodologies and raw data are publicly available "
            "for independent verification."
        )

        return text

    def generate_plain_text(
        self,
        city_id: int = 1,
        fiscal_year: Optional[int] = None,
    ) -> str:
        """
        Generate plain text narrative (no HTML).

        Args:
            city_id: City ID
            fiscal_year: Fiscal year

        Returns:
            Plain text narrative
        """
        context = self.get_report_context(city_id, fiscal_year)
        narrative = context["narrative"]

        return narrative["full_narrative"]
