"""
Risk scoring engine.

Combines individual indicators into composite risk score.
"""
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from src.database.models.risk import RiskScore, RiskIndicatorScore, RiskIndicator
from src.analytics.risk_scoring.indicators import RiskIndicatorCalculator
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RiskScoringEngine:
    """Calculate composite risk scores."""

    # Category weights (must sum to 1.0)
    CATEGORY_WEIGHTS = {
        "Liquidity": 0.25,
        "Structural": 0.25,
        "Pension": 0.30,
        "Revenue": 0.10,
        "Debt": 0.10,
    }

    # Indicator to category mapping
    INDICATOR_CATEGORIES = {
        "FB_RATIO": "Liquidity",
        "DAYS_CASH": "Liquidity",
        "OP_BALANCE": "Structural",
        "DEFICIT_TREND": "Structural",
        "PENSION_FUNDED": "Pension",
        "UAL_RATIO": "Pension",
        "PENSION_BURDEN": "Pension",
        "REV_VOLATILITY": "Revenue",
        "DEBT_SERVICE": "Debt",
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_risk_score(
        self,
        fiscal_year_id: int,
        model_version: str = "1.0"
    ) -> RiskScore:
        """
        Calculate complete risk score for a fiscal year.

        Returns: RiskScore object (not yet committed to database)
        """
        logger.info(f"Calculating risk score for fiscal year {fiscal_year_id}")

        # Calculate all indicators
        calculator = RiskIndicatorCalculator(self.db, fiscal_year_id)
        indicators = calculator.calculate_all_indicators()

        # Calculate category scores
        category_scores = self._calculate_category_scores(indicators)

        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)

        # Calculate data quality
        indicators_available = sum(1 for i in indicators.values() if i["available"])
        indicators_missing = len(indicators) - indicators_available
        data_completeness = (indicators_available / len(indicators)) * 100

        # Identify top risk factors
        top_risk_factors = self._identify_top_risk_factors(indicators)

        # Generate summary
        summary = self._generate_summary(
            overall_score,
            risk_level,
            category_scores,
            top_risk_factors
        )

        # Create RiskScore object
        risk_score = RiskScore(
            fiscal_year_id=fiscal_year_id,
            calculation_date=datetime.utcnow(),
            model_version=model_version,
            overall_score=Decimal(str(overall_score)),
            risk_level=risk_level,
            liquidity_score=Decimal(str(category_scores["Liquidity"])),
            structural_balance_score=Decimal(str(category_scores["Structural"])),
            pension_stress_score=Decimal(str(category_scores["Pension"])),
            revenue_sustainability_score=Decimal(str(category_scores["Revenue"])),
            debt_burden_score=Decimal(str(category_scores["Debt"])),
            data_completeness_percent=Decimal(str(data_completeness)),
            indicators_available=indicators_available,
            indicators_missing=indicators_missing,
            data_as_of_date=datetime.utcnow(),
            top_risk_factors=top_risk_factors,
            summary=summary,
            validated=False,
        )

        # Store individual indicator scores
        for indicator_code, indicator_data in indicators.items():
            if not indicator_data["available"]:
                continue

            indicator_score = RiskIndicatorScore(
                risk_score=risk_score,
                indicator_code=indicator_code,
                indicator_value=Decimal(str(indicator_data["value"])),
                indicator_score=Decimal(str(indicator_data["score"])),
                threshold_category=indicator_data["threshold"],
                weight=Decimal(str(self._get_indicator_weight(indicator_code))),
                contribution_to_overall=Decimal(str(
                    indicator_data["score"] * self._get_indicator_weight(indicator_code)
                )),
            )
            risk_score.indicator_scores.append(indicator_score)

        logger.info(
            f"Risk score calculated: {overall_score:.1f} ({risk_level}), "
            f"data completeness: {data_completeness:.0f}%"
        )

        return risk_score

    def _calculate_category_scores(
        self,
        indicators: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate score for each category."""
        category_scores = {}

        for category in self.CATEGORY_WEIGHTS.keys():
            # Get indicators for this category
            category_indicators = [
                ind for code, ind in indicators.items()
                if self.INDICATOR_CATEGORIES.get(code) == category and ind["available"]
            ]

            if not category_indicators:
                # No data for this category - use neutral score
                category_scores[category] = 50.0
                logger.warning(f"No indicators available for category: {category}")
                continue

            # Average score across available indicators
            scores = [ind["score"] for ind in category_indicators]
            category_scores[category] = sum(scores) / len(scores)

        return category_scores

    def _calculate_overall_score(
        self,
        category_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted overall score."""
        overall = 0.0

        for category, score in category_scores.items():
            weight = self.CATEGORY_WEIGHTS[category]
            overall += score * weight

        return round(overall, 2)

    def _determine_risk_level(self, overall_score: float) -> str:
        """Classify risk level based on score."""
        if overall_score < 25:
            return "low"
        elif overall_score < 50:
            return "moderate"
        elif overall_score < 75:
            return "high"
        else:
            return "severe"

    def _identify_top_risk_factors(
        self,
        indicators: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify top 5 risk factors."""
        # Filter available indicators and sort by score
        available = [
            {
                "indicator": ind["indicator_code"],
                "name": ind["indicator_name"],
                "score": ind["score"],
                "value": ind["value"],
                "threshold": ind["threshold"],
                "interpretation": ind.get("interpretation", ""),
            }
            for ind in indicators.values()
            if ind["available"] and ind["score"] is not None
        ]

        # Sort by score (highest = worst)
        available.sort(key=lambda x: x["score"], reverse=True)

        return available[:5]

    def _generate_summary(
        self,
        overall_score: float,
        risk_level: str,
        category_scores: Dict[str, float],
        top_risk_factors: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary."""
        level_descriptions = {
            "low": "shows healthy fiscal conditions",
            "moderate": "shows some fiscal stress indicators",
            "high": "shows significant fiscal stress",
            "severe": "shows severe fiscal stress"
        }

        summary = f"Fiscal stress score of {overall_score:.0f}/100 {level_descriptions[risk_level]}.\n\n"

        # Worst category
        worst_category = max(category_scores, key=category_scores.get)
        summary += f"Primary concern: {worst_category} (score: {category_scores[worst_category]:.0f}).\n\n"

        # Top risk factors
        if top_risk_factors:
            summary += "Key risk factors:\n"
            for factor in top_risk_factors[:3]:
                summary += f"- {factor['name']}: {factor['interpretation']}\n"

        return summary

    def _get_indicator_weight(self, indicator_code: str) -> float:
        """Get weight for a specific indicator within its category."""
        category = self.INDICATOR_CATEGORIES.get(indicator_code)
        if not category:
            return 0.0

        # Count indicators in this category
        category_indicators = [
            code for code, cat in self.INDICATOR_CATEGORIES.items()
            if cat == category
        ]

        # Equal weight within category
        return self.CATEGORY_WEIGHTS[category] / len(category_indicators)
