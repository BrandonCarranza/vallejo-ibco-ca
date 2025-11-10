"""
Scenario projection engine.

Combines revenue/expenditure projections and identifies fiscal cliff.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import City, FiscalYear
from src.database.models.financial import FundBalance
from src.database.models.projections import (
    ProjectionScenario, FinancialProjection, FiscalCliffAnalysis
)
from src.analytics.projections.revenue_model import RevenueProjector
from src.analytics.projections.expenditure_model import ExpenditureProjector
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ScenarioEngine:
    """Generate complete financial scenarios and identify fiscal cliff."""

    def __init__(self, db: Session, city_id: int):
        self.db = db
        self.city_id = city_id
        self.revenue_projector = RevenueProjector(db, city_id)
        self.expenditure_projector = ExpenditureProjector(db, city_id)

    def run_scenario(
        self,
        base_year: int,
        years_ahead: int = 10,
        scenario_code: str = "base",
        model_version: str = "1.0"
    ) -> Tuple[List[FinancialProjection], FiscalCliffAnalysis]:
        """
        Run complete financial scenario.

        Returns:
            Tuple of (projections, fiscal_cliff_analysis)
        """
        logger.info(
            f"Running {scenario_code} scenario for city {self.city_id}, "
            f"base year {base_year}, {years_ahead} years ahead"
        )

        # Get or create scenario
        scenario = self._get_or_create_scenario(scenario_code)

        # Get base fiscal year
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year == base_year
        ).first()

        if not base_fy:
            raise ValueError(f"Fiscal year {base_year} not found for city {self.city_id}")

        # Get starting fund balance
        starting_fund_balance = self._get_starting_fund_balance(base_fy.id)

        # Project revenues and expenditures
        revenue_projections = self.revenue_projector.project_revenues(
            base_year, years_ahead, scenario_code
        )
        expenditure_projections = self.expenditure_projector.project_expenditures(
            base_year, years_ahead, scenario_code
        )

        # Combine into financial projections
        projections = []
        current_fund_balance = starting_fund_balance

        for i in range(years_ahead):
            rev_proj = revenue_projections[i]
            exp_proj = expenditure_projections[i]

            # Calculate structural balance
            operating_surplus = rev_proj["projected_revenue"] - exp_proj["projected_total_expenditures"]
            operating_margin = (operating_surplus / rev_proj["projected_revenue"]) * 100

            # Calculate fund balance
            beginning_balance = current_fund_balance
            ending_balance = beginning_balance + operating_surplus
            current_fund_balance = ending_balance

            # Calculate fund balance ratio
            fund_balance_ratio = ending_balance / exp_proj["projected_total_expenditures"]

            # Health flags
            is_deficit = operating_surplus < 0
            is_depleting_reserves = ending_balance < beginning_balance
            reserves_below_minimum = fund_balance_ratio < 0.10  # Below 10%

            # Create FinancialProjection object
            projection = FinancialProjection(
                city_id=self.city_id,
                base_fiscal_year_id=base_fy.id,
                scenario_id=scenario.id,
                projection_year=rev_proj["projection_year"],
                years_ahead=rev_proj["years_ahead"],
                projection_date=datetime.utcnow(),
                projection_model_version=model_version,
                # Revenues
                total_revenues_projected=Decimal(str(rev_proj["projected_revenue"])),
                revenue_growth_rate=Decimal(str(rev_proj["growth_rate_used"])),
                # Expenditures
                total_expenditures_projected=Decimal(str(exp_proj["projected_total_expenditures"])),
                pension_costs_projected=Decimal(str(exp_proj["projected_pension_costs"])),
                other_costs_projected=Decimal(str(exp_proj["projected_base_costs"])),
                pension_growth_rate=Decimal(str(
                    (exp_proj["projected_pension_costs"] / expenditure_projections[i-1]["projected_pension_costs"] - 1)
                    if i > 0 else 0.05
                )),
                # Structural balance
                operating_surplus_deficit=Decimal(str(operating_surplus)),
                operating_margin_percent=Decimal(str(operating_margin)),
                # Fund balance
                beginning_fund_balance=Decimal(str(beginning_balance)),
                ending_fund_balance=Decimal(str(ending_balance)),
                fund_balance_ratio=Decimal(str(fund_balance_ratio)),
                # Health flags
                is_deficit=is_deficit,
                is_depleting_reserves=is_depleting_reserves,
                reserves_below_minimum=reserves_below_minimum,
                is_fiscal_cliff=False,  # Will update after identifying cliff
                # Additional metadata
                assumptions={
                    "scenario": scenario_code,
                    "revenue_growth": rev_proj["growth_rate_used"],
                    "pension_percentage": exp_proj["pension_percentage"],
                    "used_calpers_data": exp_proj["used_calpers_data"],
                },
                confidence_level=self._determine_confidence(rev_proj["years_ahead"]),
            )

            projections.append(projection)

        # Identify fiscal cliff
        fiscal_cliff_analysis = self._identify_fiscal_cliff(
            base_fy.id,
            scenario.id,
            projections,
            base_year
        )

        # Mark fiscal cliff year if exists
        if fiscal_cliff_analysis.has_fiscal_cliff:
            for projection in projections:
                if projection.projection_year == fiscal_cliff_analysis.fiscal_cliff_year:
                    projection.is_fiscal_cliff = True
                    break

        logger.info(
            f"Scenario complete. Fiscal cliff: {fiscal_cliff_analysis.has_fiscal_cliff}, "
            f"Year: {fiscal_cliff_analysis.fiscal_cliff_year}"
        )

        return projections, fiscal_cliff_analysis

    def run_all_scenarios(
        self,
        base_year: int,
        years_ahead: int = 10
    ) -> Dict[str, Tuple[List[FinancialProjection], FiscalCliffAnalysis]]:
        """
        Run all three standard scenarios: base, optimistic, pessimistic.

        Returns: Dict mapping scenario code to (projections, analysis)
        """
        results = {}

        for scenario_code in ["base", "optimistic", "pessimistic"]:
            projections, analysis = self.run_scenario(
                base_year, years_ahead, scenario_code
            )
            results[scenario_code] = (projections, analysis)

        return results

    def _get_starting_fund_balance(self, fiscal_year_id: int) -> float:
        """Get total fund balance for base year."""
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == fiscal_year_id,
            FundBalance.fund_type == "General"
        ).first()

        if fund_balance and fund_balance.total_fund_balance:
            return float(fund_balance.total_fund_balance)

        # Fallback: estimate from expenditures (assume 15% reserve)
        logger.warning(
            f"No fund balance found for fiscal year {fiscal_year_id}, "
            "estimating from expenditures"
        )
        from src.database.models.financial import Expenditure
        total_exp = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        return float(total_exp) * 0.15

    def _get_or_create_scenario(self, scenario_code: str) -> ProjectionScenario:
        """Get or create projection scenario record."""
        scenario = self.db.query(ProjectionScenario).filter(
            ProjectionScenario.scenario_code == scenario_code
        ).first()

        if scenario:
            return scenario

        # Create scenario
        scenario_configs = {
            "base": {
                "name": "Base Case",
                "description": "Current trends continue - historical growth rates applied",
                "is_baseline": True,
                "display_order": 1,
            },
            "optimistic": {
                "name": "Optimistic",
                "description": "Better outcomes - higher revenue growth, slower cost growth",
                "is_baseline": False,
                "display_order": 2,
            },
            "pessimistic": {
                "name": "Pessimistic",
                "description": "Worse outcomes - lower revenue growth, faster cost growth",
                "is_baseline": False,
                "display_order": 3,
            },
        }

        config = scenario_configs.get(scenario_code, scenario_configs["base"])

        scenario = ProjectionScenario(
            scenario_name=config["name"],
            scenario_code=scenario_code,
            description=config["description"],
            is_baseline=config["is_baseline"],
            display_order=config["display_order"],
            is_active=True,
        )

        self.db.add(scenario)
        self.db.flush()  # Get ID without committing

        logger.info(f"Created scenario: {scenario.scenario_name}")
        return scenario

    def _identify_fiscal_cliff(
        self,
        base_fiscal_year_id: int,
        scenario_id: int,
        projections: List[FinancialProjection],
        base_year: int
    ) -> FiscalCliffAnalysis:
        """
        Identify fiscal cliff year.

        Fiscal cliff = year when fund balance hits zero (reserves exhausted).
        """
        has_cliff = False
        cliff_year = None
        years_until_cliff = None
        reserves_exhausted_year = None
        cumulative_deficit = 0.0

        # Find first year where ending fund balance <= 0
        for projection in projections:
            if float(projection.ending_fund_balance) <= 0:
                has_cliff = True
                cliff_year = projection.projection_year
                reserves_exhausted_year = projection.projection_year
                years_until_cliff = projection.years_ahead
                cumulative_deficit = abs(float(projection.ending_fund_balance))
                break

        # Determine severity
        if not has_cliff:
            severity = "none"
        elif years_until_cliff <= 2:
            severity = "immediate"
        elif years_until_cliff <= 5:
            severity = "near_term"
        else:
            severity = "long_term"

        # Generate summary
        summary = self._generate_cliff_summary(
            has_cliff, cliff_year, years_until_cliff, severity, projections
        )

        # Calculate how much change needed to avoid cliff
        revenue_increase_needed = None
        expenditure_decrease_needed = None

        if has_cliff:
            revenue_increase_needed, expenditure_decrease_needed = \
                self._calculate_adjustments_needed(projections, cliff_year)

        # Create analysis
        analysis = FiscalCliffAnalysis(
            city_id=self.city_id,
            base_fiscal_year_id=base_fiscal_year_id,
            scenario_id=scenario_id,
            analysis_date=datetime.utcnow(),
            has_fiscal_cliff=has_cliff,
            fiscal_cliff_year=cliff_year,
            years_until_cliff=years_until_cliff,
            reserves_exhausted_year=reserves_exhausted_year,
            cumulative_deficit_at_cliff=Decimal(str(cumulative_deficit)) if has_cliff else None,
            severity=severity,
            summary=summary,
            revenue_increase_needed_percent=Decimal(str(revenue_increase_needed)) if revenue_increase_needed else None,
            expenditure_decrease_needed_percent=Decimal(str(expenditure_decrease_needed)) if expenditure_decrease_needed else None,
        )

        return analysis

    def _generate_cliff_summary(
        self,
        has_cliff: bool,
        cliff_year: int | None,
        years_until_cliff: int | None,
        severity: str,
        projections: List[FinancialProjection]
    ) -> str:
        """Generate human-readable summary of fiscal cliff analysis."""
        if not has_cliff:
            return (
                "No fiscal cliff identified within projection period. "
                "City maintains positive fund balance throughout projection."
            )

        summary = f"FISCAL CLIFF IDENTIFIED: Reserves projected to be exhausted in {cliff_year} "
        summary += f"({years_until_cliff} years from base year).\n\n"

        if severity == "immediate":
            summary += "SEVERITY: IMMEDIATE - Crisis within 2 years.\n\n"
        elif severity == "near_term":
            summary += "SEVERITY: NEAR-TERM - Crisis within 5 years.\n\n"
        else:
            summary += "SEVERITY: LONG-TERM - Crisis beyond 5 years.\n\n"

        # Add deficits leading to cliff
        deficit_years = [p for p in projections if p.is_deficit and p.projection_year <= cliff_year]
        if deficit_years:
            summary += f"Path to crisis: {len(deficit_years)} consecutive deficit years.\n"
            total_deficit = sum(float(p.operating_surplus_deficit) for p in deficit_years)
            summary += f"Cumulative deficit: ${abs(total_deficit):,.0f}\n\n"

        # Pension cost growth
        cliff_projection = next(p for p in projections if p.projection_year == cliff_year)
        first_projection = projections[0]
        pension_growth = (
            float(cliff_projection.pension_costs_projected) /
            float(first_projection.pension_costs_projected) - 1
        ) * 100
        summary += f"Pension costs grow {pension_growth:.0f}% by cliff year.\n"

        return summary

    def _calculate_adjustments_needed(
        self,
        projections: List[FinancialProjection],
        cliff_year: int
    ) -> Tuple[float, float]:
        """
        Calculate how much revenues need to increase or expenditures decrease
        to avoid fiscal cliff.
        """
        # Find cliff year projection
        cliff_proj = next(p for p in projections if p.projection_year == cliff_year)

        # Calculate cumulative deficit up to cliff
        cumulative_deficit = abs(float(cliff_proj.ending_fund_balance))

        # How much would revenue need to increase (averaged across years)?
        years_to_cliff = cliff_proj.years_ahead
        avg_revenue = sum(float(p.total_revenues_projected) for p in projections[:years_to_cliff]) / years_to_cliff
        revenue_increase_needed = (cumulative_deficit / years_to_cliff / avg_revenue) * 100

        # How much would expenditures need to decrease?
        avg_expenditure = sum(float(p.total_expenditures_projected) for p in projections[:years_to_cliff]) / years_to_cliff
        expenditure_decrease_needed = (cumulative_deficit / years_to_cliff / avg_expenditure) * 100

        return revenue_increase_needed, expenditure_decrease_needed

    def _determine_confidence(self, years_ahead: int) -> str:
        """Determine confidence level based on projection horizon."""
        if years_ahead <= 2:
            return "high"
        elif years_ahead <= 5:
            return "medium"
        else:
            return "low"

    def save_scenario(
        self,
        projections: List[FinancialProjection],
        analysis: FiscalCliffAnalysis
    ) -> None:
        """
        Save scenario results to database.

        Call after run_scenario() to persist results.
        """
        # Add all projections
        for projection in projections:
            self.db.add(projection)

        # Add analysis
        self.db.add(analysis)

        # Commit
        self.db.commit()

        logger.info(
            f"Saved scenario: {len(projections)} projections, "
            f"fiscal cliff: {analysis.has_fiscal_cliff}"
        )

    def compare_scenarios(
        self,
        base_year: int,
        years_ahead: int = 10
    ) -> Dict[str, Any]:
        """
        Run and compare all scenarios.

        Returns: Comparison summary with key differences
        """
        results = self.run_all_scenarios(base_year, years_ahead)

        comparison = {
            "base_year": base_year,
            "projection_years": years_ahead,
            "scenarios": {},
        }

        for scenario_code, (projections, analysis) in results.items():
            final_proj = projections[-1]

            comparison["scenarios"][scenario_code] = {
                "has_fiscal_cliff": analysis.has_fiscal_cliff,
                "fiscal_cliff_year": analysis.fiscal_cliff_year,
                "years_until_cliff": analysis.years_until_cliff,
                "severity": analysis.severity,
                "final_fund_balance": float(final_proj.ending_fund_balance),
                "final_year_deficit": float(final_proj.operating_surplus_deficit),
                "revenue_increase_needed": float(analysis.revenue_increase_needed_percent or 0),
                "expenditure_decrease_needed": float(analysis.expenditure_decrease_needed_percent or 0),
            }

        # Calculate differences between scenarios
        base_cliff = comparison["scenarios"]["base"]["fiscal_cliff_year"]
        opt_cliff = comparison["scenarios"]["optimistic"]["fiscal_cliff_year"]
        pes_cliff = comparison["scenarios"]["pessimistic"]["fiscal_cliff_year"]

        comparison["scenario_spread"] = {
            "best_case_vs_base": (opt_cliff - base_cliff) if (opt_cliff and base_cliff) else None,
            "worst_case_vs_base": (pes_cliff - base_cliff) if (pes_cliff and base_cliff) else None,
        }

        return comparison
