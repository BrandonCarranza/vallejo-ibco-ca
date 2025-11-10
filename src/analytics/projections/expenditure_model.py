"""
Expenditure projection model.

Projects future expenditures with separate treatment of pension costs.
"""
from typing import List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Expenditure
from src.database.models.pension import PensionPlan, PensionProjection
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ExpenditureProjector:
    """Project future expenditures."""

    def __init__(self, db: Session, city_id: int):
        self.db = db
        self.city_id = city_id

    def project_expenditures(
        self,
        base_year: int,
        years_ahead: int,
        scenario: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        Project expenditures for multiple future years.

        Separates pension costs (rapid growth) from base costs (inflation).

        Args:
            base_year: Starting fiscal year
            years_ahead: Number of years to project
            scenario: "base", "optimistic", or "pessimistic"

        Returns: List of projections, one per year
        """
        # Get base year fiscal year
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year == base_year
        ).first()

        if not base_fy:
            raise ValueError(f"Fiscal year {base_year} not found for city {self.city_id}")

        # Get base year expenditures
        base_totals = self._get_base_year_totals(base_fy.id)

        # Check if we have CalPERS published projections
        has_calpers_projections = self._has_calpers_projections(base_fy.id)

        # Project forward
        projections = []
        current_base_costs = base_totals["base_costs"]
        current_pension_costs = base_totals["pension_costs"]

        for year in range(1, years_ahead + 1):
            projection_year = base_year + year

            # Project base costs (inflation-based)
            inflation_rate = self._get_inflation_rate(scenario)
            current_base_costs *= (1 + inflation_rate)

            # Project pension costs
            if has_calpers_projections:
                # Use CalPERS published schedule
                pension_costs = self._get_calpers_projection(base_fy.id, projection_year)
                if pension_costs is not None:
                    current_pension_costs = pension_costs
                else:
                    # CalPERS data doesn't go this far - use growth rate
                    pension_growth_rate = self._get_pension_growth_rate(scenario)
                    current_pension_costs *= (1 + pension_growth_rate)
            else:
                # Use assumed growth rate (higher than inflation)
                pension_growth_rate = self._get_pension_growth_rate(scenario)
                current_pension_costs *= (1 + pension_growth_rate)

            total_expenditures = current_base_costs + current_pension_costs

            projections.append({
                "projection_year": projection_year,
                "years_ahead": year,
                "projected_total_expenditures": total_expenditures,
                "projected_base_costs": current_base_costs,
                "projected_pension_costs": current_pension_costs,
                "pension_percentage": (current_pension_costs / total_expenditures) * 100,
                "scenario": scenario,
                "used_calpers_data": has_calpers_projections,
            })

        return projections

    def _get_base_year_totals(self, fiscal_year_id: int) -> Dict[str, float]:
        """Get base year expenditure totals, separated by type."""
        # Get total pension/OPEB costs
        pension_categories = [
            "Pension Contributions",
            "CalPERS Contributions",
            "Retirement Costs",
            "OPEB",
        ]

        pension_costs = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == fiscal_year_id,
            Expenditure.category_name.in_(pension_categories)
        ).scalar() or Decimal(0)

        # Get total expenditures
        total_expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        # Base costs = everything except pension
        base_costs = total_expenditures - pension_costs

        logger.info(
            f"Base year totals - Total: ${total_expenditures:,.0f}, "
            f"Base: ${base_costs:,.0f}, Pension: ${pension_costs:,.0f} "
            f"({(float(pension_costs)/float(total_expenditures)*100):.1f}%)"
        )

        return {
            "total_expenditures": float(total_expenditures),
            "base_costs": float(base_costs),
            "pension_costs": float(pension_costs),
        }

    def _has_calpers_projections(self, fiscal_year_id: int) -> bool:
        """Check if CalPERS published projections are available."""
        count = self.db.query(func.count(PensionProjection.id)).filter(
            PensionProjection.fiscal_year_id == fiscal_year_id
        ).scalar()

        return count > 0

    def _get_calpers_projection(
        self,
        base_fiscal_year_id: int,
        projection_year: int
    ) -> float | None:
        """Get CalPERS published projection for a specific year."""
        # Get base fiscal year to find projection years ahead
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.id == base_fiscal_year_id
        ).first()

        if not base_fy:
            return None

        years_ahead = projection_year - base_fy.year

        # Query for projection
        projection = self.db.query(PensionProjection).filter(
            PensionProjection.fiscal_year_id == base_fiscal_year_id,
            PensionProjection.projection_year_offset == years_ahead
        ).first()

        if projection and projection.projected_employer_contribution:
            logger.info(
                f"Using CalPERS published projection for year {projection_year}: "
                f"${projection.projected_employer_contribution:,.0f}"
            )
            return float(projection.projected_employer_contribution)

        return None

    def _get_inflation_rate(self, scenario: str) -> float:
        """Get inflation rate for projecting base costs."""
        base_inflation = 0.025  # 2.5% base assumption

        if scenario == "optimistic":
            # Lower inflation (better for budgets)
            return base_inflation * 0.8  # 2.0%
        elif scenario == "pessimistic":
            # Higher inflation (worse for budgets)
            return base_inflation * 1.2  # 3.0%
        else:  # base
            return base_inflation

    def _get_pension_growth_rate(self, scenario: str) -> float:
        """
        Get pension cost growth rate when CalPERS data unavailable.

        Pension costs typically grow faster than inflation due to:
        - Rising UAL amortization payments
        - Lower discount rates increasing liabilities
        - Payroll growth
        """
        base_pension_growth = 0.05  # 5% base assumption

        if scenario == "optimistic":
            # Slower pension cost growth (reforms, higher returns)
            return base_pension_growth * 0.8  # 4.0%
        elif scenario == "pessimistic":
            # Faster pension cost growth (lower returns, higher UAL)
            return base_pension_growth * 1.4  # 7.0%
        else:  # base
            return base_pension_growth

    def project_pension_burden(
        self,
        base_year: int,
        years_ahead: int,
        scenario: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        Project pension burden (pension costs / payroll) over time.

        This is a key metric for fiscal stress.
        """
        # Get base year pension data
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year == base_year
        ).first()

        if not base_fy:
            raise ValueError(f"Fiscal year {base_year} not found")

        # Get base year pension contribution
        base_pension = self.db.query(func.sum(PensionPlan.total_employer_contribution)).filter(
            PensionPlan.fiscal_year_id == base_fy.id
        ).scalar() or Decimal(0)

        # Estimate payroll (usually ~50-60% of non-pension expenditures)
        base_totals = self._get_base_year_totals(base_fy.id)
        estimated_payroll = base_totals["base_costs"] * 0.55

        # Get expenditure projections
        expenditure_projections = self.project_expenditures(
            base_year, years_ahead, scenario
        )

        # Calculate burden over time
        burden_projections = []

        for exp_proj in expenditure_projections:
            # Assume payroll grows with base costs
            year_payroll = estimated_payroll * (
                exp_proj["projected_base_costs"] / base_totals["base_costs"]
            )

            pension_burden = (exp_proj["projected_pension_costs"] / year_payroll) * 100

            burden_projections.append({
                "projection_year": exp_proj["projection_year"],
                "years_ahead": exp_proj["years_ahead"],
                "pension_costs": exp_proj["projected_pension_costs"],
                "estimated_payroll": year_payroll,
                "pension_burden_percent": pension_burden,
                "scenario": scenario,
            })

        return burden_projections
