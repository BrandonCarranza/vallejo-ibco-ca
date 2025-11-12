"""
Fiscal Summary Report Generator.

Generates comprehensive fiscal status reports including:
- Executive summary
- Revenues (trends, sources, volatility)
- Expenditures (trends, categories, pension burden)
- Pension obligations
- Risk scores
- 10-year projections

Updated quarterly after new data entry.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .base_generator import BaseReportGenerator


class FiscalSummaryReportGenerator(BaseReportGenerator):
    """Generate comprehensive fiscal summary reports."""

    def __init__(self, db: Session):
        """Initialize fiscal summary report generator."""
        super().__init__(db, template_name="fiscal_summary_report.html")

    def get_report_context(
        self,
        city_id: int = 1,
        fiscal_year: Optional[int] = None,
        include_charts: bool = True,
    ) -> Dict[str, Any]:
        """
        Get context for fiscal summary report.

        Args:
            city_id: City ID
            fiscal_year: Fiscal year (default: latest)
            include_charts: Include chart data (default: True)

        Returns:
            Context dictionary
        """
        from src.database.models.core import City, FiscalYear

        # Get city and fiscal year
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City ID {city_id} not found")

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

        # Gather all report sections
        context = {
            "city_name": city.name,
            "fiscal_year": fiscal_year,
            "executive_summary": self._get_executive_summary(city_id, fiscal_year),
            "revenue_analysis": self._get_revenue_analysis(city_id, fiscal_year),
            "expenditure_analysis": self._get_expenditure_analysis(city_id, fiscal_year),
            "pension_analysis": self._get_pension_analysis(city_id, fiscal_year),
            "risk_assessment": self._get_risk_score_summary(city_id, fiscal_year),
            "projections": self._get_projections_summary(city_id, fiscal_year),
        }

        if include_charts:
            context["charts"] = self._get_chart_data(city_id, fiscal_year)

        return context

    def _get_executive_summary(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get executive summary data."""
        fiscal = self._get_fiscal_year_summary(city_id, fiscal_year)
        risk = self._get_risk_score_summary(city_id, fiscal_year)

        # Generate summary text
        summary_text = (
            f"This report provides a comprehensive overview of "
            f"{fiscal.get('city_name', 'Unknown')}'s fiscal condition for FY{fiscal_year}. "
        )

        if fiscal.get("operating_balance"):
            if fiscal["operating_balance"] < 0:
                summary_text += (
                    f"The city faces a structural deficit of "
                    f"{self.format_currency(abs(fiscal['operating_balance']), compact=True)}. "
                )
            else:
                summary_text += (
                    f"The city generated an operating surplus of "
                    f"{self.format_currency(fiscal['operating_balance'], compact=True)}. "
                )

        if risk.get("overall_score"):
            summary_text += (
                f"The fiscal stress score of {risk['overall_score']:.0f}/100 "
                f"({risk['risk_level'].capitalize()}) indicates "
            )
            score = risk["overall_score"]
            if score >= 75:
                summary_text += "severe fiscal challenges requiring immediate action."
            elif score >= 50:
                summary_text += "significant fiscal stress requiring corrective measures."
            else:
                summary_text += "manageable fiscal conditions with proactive monitoring needed."

        return {
            "summary_text": summary_text,
            "fiscal_summary": fiscal,
            "risk_summary": risk,
        }

    def _get_revenue_analysis(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get revenue analysis."""
        from src.database.models.core import FiscalYear
        from src.database.models.financial import Revenue, RevenueCategory

        fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy:
            return {}

        # Get revenue by category
        revenues = (
            self.db.query(Revenue, RevenueCategory)
            .join(RevenueCategory, Revenue.category_id == RevenueCategory.id)
            .filter(Revenue.fiscal_year_id == fy.id, Revenue.is_deleted == False)
            .all()
        )

        by_category = {}
        for rev, cat in revenues:
            level1 = cat.category_level1
            if level1 not in by_category:
                by_category[level1] = 0
            by_category[level1] += float(rev.actual_amount)

        total = sum(by_category.values())

        return {
            "total_revenues": total,
            "by_category": by_category,
            "category_percentages": {k: (v / total * 100) if total > 0 else 0 for k, v in by_category.items()},
        }

    def _get_expenditure_analysis(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get expenditure analysis."""
        from src.database.models.core import FiscalYear
        from src.database.models.financial import Expenditure, ExpenditureCategory

        fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy:
            return {}

        # Get expenditures by category
        expenditures = (
            self.db.query(Expenditure, ExpenditureCategory)
            .join(ExpenditureCategory, Expenditure.category_id == ExpenditureCategory.id)
            .filter(Expenditure.fiscal_year_id == fy.id, Expenditure.is_deleted == False)
            .all()
        )

        by_category = {}
        for exp, cat in expenditures:
            level1 = cat.category_level1
            if level1 not in by_category:
                by_category[level1] = 0
            by_category[level1] += float(exp.actual_amount)

        total = sum(by_category.values())

        return {
            "total_expenditures": total,
            "by_category": by_category,
            "category_percentages": {k: (v / total * 100) if total > 0 else 0 for k, v in by_category.items()},
        }

    def _get_pension_analysis(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get pension analysis."""
        from src.database.models.core import FiscalYear
        from src.database.models.pensions import PensionPlan

        fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy:
            return {}

        plans = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fy.id, PensionPlan.is_deleted == False)
            .all()
        )

        if not plans:
            return {}

        total_liability = sum(float(p.total_pension_liability) for p in plans if p.total_pension_liability)
        total_assets = sum(float(p.fiduciary_net_position) for p in plans if p.fiduciary_net_position)
        total_ual = sum(float(p.unfunded_actuarial_liability) for p in plans if p.unfunded_actuarial_liability)
        avg_funded_ratio = sum(float(p.funded_ratio) for p in plans if p.funded_ratio) / len(plans)

        return {
            "total_liability": total_liability,
            "total_assets": total_assets,
            "total_ual": total_ual,
            "avg_funded_ratio": avg_funded_ratio,
            "plan_count": len(plans),
        }

    def _get_projections_summary(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get projections summary."""
        from src.database.models.core import FiscalYear
        from src.database.models.projections import FiscalCliffAnalysis

        fy = (
            self.db.query(FiscalYear)
            .filter(FiscalYear.city_id == city_id, FiscalYear.year == fiscal_year)
            .first()
        )

        if not fy:
            return {}

        cliff = (
            self.db.query(FiscalCliffAnalysis)
            .filter(
                FiscalCliffAnalysis.city_id == city_id,
                FiscalCliffAnalysis.base_fiscal_year_id == fy.id,
            )
            .first()
        )

        if not cliff:
            return {"has_fiscal_cliff": False}

        return {
            "has_fiscal_cliff": cliff.has_fiscal_cliff,
            "fiscal_cliff_year": cliff.fiscal_cliff_year,
            "years_until_cliff": cliff.years_until_cliff,
            "severity": cliff.severity,
        }

    def _get_chart_data(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """Get chart data (placeholder for Metabase embeds)."""
        return {
            "revenue_trend_url": f"/metabase/public/question/revenue_trend_{city_id}",
            "expenditure_trend_url": f"/metabase/public/question/expenditure_trend_{city_id}",
            "risk_score_url": f"/metabase/public/question/risk_score_{city_id}",
        }
