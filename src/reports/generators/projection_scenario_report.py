"""
Projection Scenario Report Generator.

Compares fiscal projection scenarios side-by-side:
- Base case: Current trends continue
- Optimistic: Pension reform + revenue growth
- Pessimistic: Pension costs accelerate + revenue decline

For each scenario: fiscal cliff year, cumulative deficit, policy implications.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .base_generator import BaseReportGenerator


class ProjectionScenarioReportGenerator(BaseReportGenerator):
    """Generate projection scenario comparison reports."""

    def __init__(self, db: Session):
        """Initialize projection scenario report generator."""
        super().__init__(db, template_name="projection_scenario_report.html")

    def get_report_context(
        self,
        city_id: int = 1,
        base_fiscal_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get context for projection scenario report.

        Args:
            city_id: City ID
            base_fiscal_year: Base fiscal year for projections

        Returns:
            Context dictionary
        """
        from src.database.models.core import City, FiscalYear
        from src.database.models.projections import (
            FiscalCliffAnalysis,
            ProjectionScenario,
        )

        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City ID {city_id} not found")

        # Get base fiscal year
        if base_fiscal_year is None:
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
                    FiscalYear.year == base_fiscal_year,
                )
                .first()
            )

        if not fy:
            raise ValueError("No fiscal year data found")

        base_fiscal_year = fy.year

        # Get all scenarios
        scenarios = self.db.query(ProjectionScenario).filter(
            ProjectionScenario.is_active == True
        ).order_by(ProjectionScenario.display_order).all()

        # Get fiscal cliff analyses for each scenario
        scenario_data = []
        for scenario in scenarios:
            cliff = (
                self.db.query(FiscalCliffAnalysis)
                .filter(
                    FiscalCliffAnalysis.city_id == city_id,
                    FiscalCliffAnalysis.base_fiscal_year_id == fy.id,
                    FiscalCliffAnalysis.scenario_id == scenario.id,
                )
                .first()
            )

            scenario_data.append({
                "scenario": scenario,
                "cliff_analysis": cliff,
            })

        # Generate comparison
        comparison = self._generate_comparison(scenario_data, base_fiscal_year)

        return {
            "city_name": city.name,
            "base_fiscal_year": base_fiscal_year,
            "scenarios": scenario_data,
            "comparison": comparison,
        }

    def _generate_comparison(
        self,
        scenario_data: List[Dict[str, Any]],
        base_fiscal_year: int,
    ) -> Dict[str, Any]:
        """Generate scenario comparison analysis."""
        comparison = {
            "best_case": None,
            "worst_case": None,
            "most_likely": None,
            "key_differences": [],
        }

        # Find best and worst case
        valid_scenarios = [s for s in scenario_data if s["cliff_analysis"]]

        if valid_scenarios:
            # Sort by years until cliff (more years = better)
            sorted_scenarios = sorted(
                valid_scenarios,
                key=lambda x: x["cliff_analysis"].years_until_cliff or 0 if x["cliff_analysis"].has_fiscal_cliff else 999,
                reverse=True,
            )

            comparison["best_case"] = sorted_scenarios[0]
            comparison["worst_case"] = sorted_scenarios[-1]

            # Most likely is typically the base case
            base_case = next(
                (s for s in scenario_data if s["scenario"].is_baseline),
                scenario_data[0] if scenario_data else None,
            )
            comparison["most_likely"] = base_case

        return comparison
