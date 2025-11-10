"""
Revenue projection model.

Projects future revenues based on historical growth rates.
"""
from typing import List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Revenue
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RevenueProjector:
    """Project future revenues."""

    def __init__(self, db: Session, city_id: int):
        self.db = db
        self.city_id = city_id

    def project_revenues(
        self,
        base_year: int,
        years_ahead: int,
        scenario: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        Project revenues for multiple future years.

        Args:
            base_year: Starting fiscal year
            years_ahead: Number of years to project
            scenario: "base", "optimistic", or "pessimistic"

        Returns: List of projections, one per year
        """
        # Get historical data (5 years)
        historical_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year <= base_year
        ).order_by(FiscalYear.year.desc()).limit(5).all()

        if len(historical_years) < 2:
            raise ValueError("Need at least 2 years of historical data")

        # Calculate historical growth rate
        growth_rate = self._calculate_historical_growth_rate(historical_years)

        # Adjust for scenario
        scenario_growth = self._adjust_for_scenario(growth_rate, scenario)

        # Get base year revenue
        base_fy = [fy for fy in historical_years if fy.year == base_year][0]
        base_revenue = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == base_fy.id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        # Project forward
        projections = []
        current_revenue = float(base_revenue)

        for year in range(1, years_ahead + 1):
            current_revenue *= (1 + scenario_growth)
            projections.append({
                "projection_year": base_year + year,
                "years_ahead": year,
                "projected_revenue": current_revenue,
                "growth_rate_used": scenario_growth,
                "scenario": scenario,
            })

        return projections

    def _calculate_historical_growth_rate(
        self,
        fiscal_years: List[FiscalYear]
    ) -> float:
        """Calculate compound annual growth rate from historical data."""
        revenues = []

        for fy in reversed(fiscal_years):  # Oldest to newest
            total = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)
            revenues.append(float(total))

        if len(revenues) < 2:
            return 0.0

        # CAGR formula: (End/Start)^(1/years) - 1
        years = len(revenues) - 1
        cagr = (revenues[-1] / revenues[0]) ** (1/years) - 1

        logger.info(f"Historical revenue CAGR: {cagr:.2%}")
        return cagr

    def _adjust_for_scenario(self, base_rate: float, scenario: str) -> float:
        """Adjust growth rate based on scenario."""
        if scenario == "optimistic":
            # Use 75th percentile (assume better performance)
            return base_rate * 1.25
        elif scenario == "pessimistic":
            # Use 25th percentile (assume worse performance)
            return base_rate * 0.75
        else:  # base
            return base_rate
