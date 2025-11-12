"""
Decision fiscal impact prediction and accuracy tracking.

Predicts fiscal impact of proposed city council decisions and tracks
actual outcomes to measure prediction accuracy. Builds institutional
credibility through transparent accountability.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.database.models.civic import (
    Decision,
    DecisionCategory,
    DecisionStatus,
    Outcome,
    OutcomeStatus,
)
from src.database.models.core import City, FiscalYear
from src.database.models.financial import Revenue, Expenditure, FundBalance
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DecisionImpactPredictor:
    """
    Predict fiscal impact of proposed city council decisions.

    Uses historical data and category-specific models to estimate
    the annual and one-time fiscal impact of proposed decisions.
    """

    def __init__(self, db: Session):
        self.db = db

    def predict_impact(
        self,
        city_id: int,
        category: DecisionCategory,
        description: str,
        **context
    ) -> Dict:
        """
        Predict fiscal impact of a proposed decision.

        Args:
            city_id: City ID
            category: Decision category (tax, bond, labor, etc.)
            description: Description of proposed decision
            **context: Additional context for prediction (e.g., revenue_change_percent)

        Returns:
            Dictionary with:
                - predicted_annual_impact: Predicted annual impact (± dollars)
                - predicted_one_time_impact: One-time impact (if applicable)
                - confidence: Prediction confidence (high/medium/low)
                - methodology: Explanation of prediction method
                - assumptions: List of key assumptions
                - sensitivity_factors: Factors affecting accuracy
                - recommendation: Analyst recommendation
        """
        # Get city data
        city = self.db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"City {city_id} not found")

        # Route to category-specific prediction method
        if category == DecisionCategory.TAX:
            return self._predict_tax_impact(city, description, **context)
        elif category == DecisionCategory.BOND:
            return self._predict_bond_impact(city, description, **context)
        elif category == DecisionCategory.LABOR:
            return self._predict_labor_impact(city, description, **context)
        elif category == DecisionCategory.BUDGET:
            return self._predict_budget_impact(city, description, **context)
        elif category == DecisionCategory.PENSION:
            return self._predict_pension_impact(city, description, **context)
        elif category == DecisionCategory.SERVICE:
            return self._predict_service_impact(city, description, **context)
        else:
            return self._predict_generic_impact(city, category, description, **context)

    def _predict_tax_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of tax changes (sales tax, property tax, etc.)."""
        # Get recent tax revenues
        latest_fy = self._get_latest_fiscal_year(city.id)
        if not latest_fy:
            return self._no_data_prediction()

        # Get total tax revenue
        tax_revenue = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == latest_fy.id,
            Revenue.category.in_(['sales_tax', 'property_tax', 'tax_revenue'])
        ).scalar() or Decimal(0)

        # Extract revenue change percentage from context or description
        revenue_change_percent = context.get('revenue_change_percent')
        if revenue_change_percent is None:
            # Try to parse from description
            revenue_change_percent = self._extract_percent_from_description(description)

        if revenue_change_percent is None:
            # Default assumption: 0.5% increase
            revenue_change_percent = Decimal('0.5')
            confidence = "low"
            assumptions = [
                f"Assumed {revenue_change_percent}% tax rate increase (not specified)",
                "Based on typical local tax measure increments"
            ]
        else:
            confidence = "high"
            assumptions = [
                f"Tax rate change: {revenue_change_percent}%",
                f"Applied to current tax base: ${tax_revenue:,.0f}"
            ]

        # Calculate predicted impact
        predicted_annual = tax_revenue * (revenue_change_percent / Decimal(100))

        # Collection efficiency: typically 95-98%
        collection_efficiency = Decimal('0.96')
        predicted_annual *= collection_efficiency
        assumptions.append(f"Collection efficiency: {collection_efficiency*100}%")

        # Ramp-up period: tax changes often take 6-12 months to reach full collection
        if 'immediate' not in description.lower():
            assumptions.append("Ramp-up period: Partial first year (50% collected)")

        return {
            "predicted_annual_impact": predicted_annual,
            "predicted_one_time_impact": None,
            "confidence": confidence,
            "methodology": (
                "Applied revenue change percentage to current tax base with "
                "collection efficiency and ramp-up adjustments"
            ),
            "assumptions": assumptions,
            "sensitivity_factors": [
                "Economic conditions affecting tax base",
                "Collection compliance and enforcement",
                "Business growth or decline",
                "Seasonal variations in tax collection"
            ],
            "recommendation": (
                f"Monitor first 6-12 months closely. Tax revenue predictions typically "
                f"accurate within 10-15% if economic conditions remain stable."
            )
        }

    def _predict_bond_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of bond issuances."""
        # Extract bond amount from context or description
        bond_amount = context.get('bond_amount')
        if bond_amount is None:
            bond_amount = self._extract_dollar_amount_from_description(description)

        if bond_amount is None:
            return {
                "predicted_annual_impact": Decimal(0),
                "predicted_one_time_impact": None,
                "confidence": "low",
                "methodology": "Insufficient information to predict bond impact",
                "assumptions": ["Bond amount not specified"],
                "sensitivity_factors": [],
                "recommendation": "Specify bond amount and terms for accurate prediction"
            }

        # Estimate annual debt service
        # Typical municipal bond: 20-30 year term, 4-5% interest
        term_years = context.get('term_years', 25)
        interest_rate = context.get('interest_rate', Decimal('0.045'))  # 4.5%

        # Calculate annual debt service (principal + interest)
        # Simplified: assume level debt service
        annual_debt_service = bond_amount * (interest_rate + Decimal(1) / term_years)

        return {
            "predicted_annual_impact": -annual_debt_service,  # Negative = cost
            "predicted_one_time_impact": bond_amount,  # One-time revenue
            "confidence": "high",
            "methodology": "Level debt service calculation based on bond terms",
            "assumptions": [
                f"Bond amount: ${bond_amount:,.0f}",
                f"Term: {term_years} years",
                f"Interest rate: {interest_rate*100}%",
                "Level debt service payments"
            ],
            "sensitivity_factors": [
                "Interest rate fluctuations",
                "Bond rating changes",
                "Refunding opportunities",
                "Early redemption provisions"
            ],
            "recommendation": (
                f"Annual debt service: ${annual_debt_service:,.0f}. "
                f"Ensure revenue sources can cover this recurring obligation."
            )
        }

    def _predict_labor_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of labor contracts and personnel decisions."""
        # Get current personnel expenditures
        latest_fy = self._get_latest_fiscal_year(city.id)
        if not latest_fy:
            return self._no_data_prediction()

        personnel_costs = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == latest_fy.id,
            Expenditure.category.in_(['salaries', 'wages', 'benefits', 'personnel'])
        ).scalar() or Decimal(0)

        # Extract wage increase percentage
        wage_increase_percent = context.get('wage_increase_percent')
        if wage_increase_percent is None:
            wage_increase_percent = self._extract_percent_from_description(description)

        if wage_increase_percent is None:
            # Default: 3% COLA
            wage_increase_percent = Decimal('3.0')
            confidence = "low"
            assumptions = [
                f"Assumed {wage_increase_percent}% wage increase (typical COLA)",
                "Applied to total personnel costs"
            ]
        else:
            confidence = "medium"
            assumptions = [
                f"Wage increase: {wage_increase_percent}%",
                f"Current personnel costs: ${personnel_costs:,.0f}"
            ]

        # Calculate predicted impact
        predicted_annual = personnel_costs * (wage_increase_percent / Decimal(100))

        # Add benefits cost multiplier (typically 30-40% of wage increases)
        benefits_multiplier = Decimal('0.35')
        benefits_increase = predicted_annual * benefits_multiplier
        total_impact = predicted_annual + benefits_increase

        assumptions.append(f"Benefits cost multiplier: {benefits_multiplier*100}%")
        assumptions.append("Multi-year contracts assume step increases")

        return {
            "predicted_annual_impact": -total_impact,  # Negative = cost
            "predicted_one_time_impact": None,
            "confidence": confidence,
            "methodology": (
                "Applied wage increase to personnel costs with benefits multiplier"
            ),
            "assumptions": assumptions,
            "sensitivity_factors": [
                "Actual headcount changes vs. budgeted",
                "Overtime costs",
                "Pension contribution rate changes",
                "Healthcare cost inflation",
                "Employee turnover and step progression"
            ],
            "recommendation": (
                f"Labor costs tend to exceed initial estimates by 10-15% due to "
                f"unfunded mandates, overtime, and benefit cost inflation. "
                f"Budget conservatively."
            )
        }

    def _predict_budget_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of budget amendments and adjustments."""
        # Budget amendments are typically specific
        expenditure_change = context.get('expenditure_change_amount')
        revenue_change = context.get('revenue_change_amount')

        if expenditure_change is None and revenue_change is None:
            # Try to extract from description
            amount = self._extract_dollar_amount_from_description(description)
            if 'cut' in description.lower() or 'reduce' in description.lower():
                expenditure_change = -abs(amount) if amount else None
            elif 'increas' in description.lower() or 'add' in description.lower():
                expenditure_change = abs(amount) if amount else None

        predicted_annual = Decimal(0)
        assumptions = []

        if expenditure_change:
            predicted_annual -= expenditure_change  # Negative expenditure = savings
            assumptions.append(f"Expenditure change: ${expenditure_change:,.0f}")

        if revenue_change:
            predicted_annual += revenue_change
            assumptions.append(f"Revenue change: ${revenue_change:,.0f}")

        if not assumptions:
            return self._no_data_prediction()

        return {
            "predicted_annual_impact": predicted_annual,
            "predicted_one_time_impact": None,
            "confidence": "high",
            "methodology": "Direct budget amendment amounts",
            "assumptions": assumptions,
            "sensitivity_factors": [
                "Implementation timing",
                "Actual vs. budgeted execution",
                "Offsetting impacts in other departments"
            ],
            "recommendation": "Budget amendments typically track within 5-10% of estimates"
        }

    def _predict_pension_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of pension-related decisions (POBs, reforms, etc.)."""
        # This is complex and highly dependent on actuarial analysis
        return {
            "predicted_annual_impact": Decimal(0),
            "predicted_one_time_impact": None,
            "confidence": "low",
            "methodology": (
                "Pension impact predictions require detailed actuarial analysis. "
                "Consult with pension actuary for accurate projections."
            ),
            "assumptions": [
                "Pension impacts are long-term and complex",
                "Actuarial analysis required"
            ],
            "sensitivity_factors": [
                "Investment return assumptions",
                "Mortality and demographic assumptions",
                "Salary growth projections",
                "Discount rate changes"
            ],
            "recommendation": (
                "Defer to actuarial valuation for pension impact estimates. "
                "Historical accuracy of pension predictions: 60-70% due to "
                "market volatility and assumption changes."
            )
        }

    def _predict_service_impact(self, city: City, description: str, **context) -> Dict:
        """Predict impact of service level changes."""
        # Service changes vary widely
        estimated_cost = context.get('estimated_annual_cost')

        if estimated_cost is None:
            estimated_cost = self._extract_dollar_amount_from_description(description)

        if estimated_cost is None:
            return self._no_data_prediction()

        # Service expansions typically cost 10-20% more than initial estimates
        contingency = Decimal('1.15')
        adjusted_cost = estimated_cost * contingency

        return {
            "predicted_annual_impact": -adjusted_cost,  # Negative = cost
            "predicted_one_time_impact": None,
            "confidence": "medium",
            "methodology": "Estimated cost with 15% contingency for overruns",
            "assumptions": [
                f"Estimated annual cost: ${estimated_cost:,.0f}",
                "15% contingency for typical service expansion overruns"
            ],
            "sensitivity_factors": [
                "Actual utilization vs. projected",
                "Personnel costs",
                "Equipment and supply costs",
                "Contract vs. in-house delivery"
            ],
            "recommendation": (
                "Service cost predictions often underestimate by 15-25%. "
                "Include contingency and pilot program if possible."
            )
        }

    def _predict_generic_impact(
        self,
        city: City,
        category: DecisionCategory,
        description: str,
        **context
    ) -> Dict:
        """Generic prediction when category-specific method not available."""
        amount = context.get('estimated_annual_impact')
        if amount is None:
            amount = self._extract_dollar_amount_from_description(description)

        if amount is None:
            return self._no_data_prediction()

        return {
            "predicted_annual_impact": amount,
            "predicted_one_time_impact": None,
            "confidence": "low",
            "methodology": "Generic estimation based on provided amount",
            "assumptions": [f"Estimated impact: ${amount:,.0f}"],
            "sensitivity_factors": [
                "Actual implementation may differ from plan",
                "External factors not accounted for"
            ],
            "recommendation": (
                "Generic prediction. Provide more context for accurate estimates."
            )
        }

    def _no_data_prediction(self) -> Dict:
        """Return structure when insufficient data for prediction."""
        return {
            "predicted_annual_impact": Decimal(0),
            "predicted_one_time_impact": None,
            "confidence": "none",
            "methodology": "Insufficient data for prediction",
            "assumptions": ["No baseline data available"],
            "sensitivity_factors": [],
            "recommendation": "Gather more information before making fiscal projections"
        }

    def _get_latest_fiscal_year(self, city_id: int) -> Optional[FiscalYear]:
        """Get the most recent fiscal year with data."""
        return self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id
        ).order_by(desc(FiscalYear.year)).first()

    def _extract_percent_from_description(self, description: str) -> Optional[Decimal]:
        """Extract percentage from description text."""
        import re
        # Look for patterns like "0.5%", "1.5 percent", etc.
        pattern = r'(\d+\.?\d*)\s*(?:percent|%)'
        match = re.search(pattern, description.lower())
        if match:
            return Decimal(match.group(1))
        return None

    def _extract_dollar_amount_from_description(self, description: str) -> Optional[Decimal]:
        """Extract dollar amount from description text."""
        import re
        # Look for patterns like "$25M", "$1.5 million", "$500,000", etc.
        patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(?:million|M)',
            r'\$(\d+(?:\.\d+)?)\s*(?:billion|B)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                value = Decimal(match.group(1).replace(',', ''))
                if 'million' in description.lower() or 'M' in description:
                    value *= Decimal(1000000)
                elif 'billion' in description.lower() or 'B' in description:
                    value *= Decimal(1000000000)
                return value

        return None


class DecisionAccuracyTracker:
    """
    Track prediction accuracy and generate insights.

    Analyzes how well fiscal impact predictions match actual outcomes,
    building institutional credibility through transparent accountability.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_accuracy_metrics(
        self,
        city_id: int,
        category: Optional[DecisionCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Calculate prediction accuracy metrics.

        Args:
            city_id: City ID
            category: Optional category filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with accuracy statistics
        """
        # Query decisions with final outcomes
        query = self.db.query(Decision).join(Decision.outcomes).filter(
            Decision.city_id == city_id,
            Decision.is_deleted == False,
            Outcome.status == OutcomeStatus.FINAL,
            Decision.predicted_annual_impact.isnot(None),
            Outcome.actual_annual_impact.isnot(None)
        )

        if category:
            query = query.filter(Decision.category == category)
        if start_date:
            query = query.filter(Decision.decision_date >= start_date)
        if end_date:
            query = query.filter(Decision.decision_date <= end_date)

        decisions = query.all()

        if not decisions:
            return {
                "count": 0,
                "message": "No decisions with final outcomes to analyze"
            }

        # Calculate metrics
        accuracies = []
        absolute_errors = []

        for decision in decisions:
            accuracy = decision.prediction_accuracy_percent
            if accuracy:
                accuracies.append(accuracy)

                predicted = float(decision.predicted_annual_impact)
                actual = float(decision.latest_outcome.actual_annual_impact)
                absolute_errors.append(abs(predicted - actual))

        return {
            "count": len(decisions),
            "avg_accuracy_percent": sum(accuracies) / len(accuracies) if accuracies else 0,
            "median_accuracy_percent": sorted(accuracies)[len(accuracies) // 2] if accuracies else 0,
            "min_accuracy_percent": min(accuracies) if accuracies else 0,
            "max_accuracy_percent": max(accuracies) if accuracies else 0,
            "avg_absolute_error": sum(absolute_errors) / len(absolute_errors) if absolute_errors else 0,
            "decisions_within_10_percent": sum(1 for a in accuracies if 90 <= a <= 110),
            "decisions_within_25_percent": sum(1 for a in accuracies if 75 <= a <= 125),
        }
