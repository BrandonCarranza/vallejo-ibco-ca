"""
Individual risk indicator calculations.

Each indicator is a standalone function that:
1. Takes fiscal year data as input
2. Calculates a specific financial ratio
3. Returns the value and metadata
"""
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Revenue, Expenditure, FundBalance, ExpenditureCategory
from src.database.models.pensions import PensionPlan
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RiskIndicatorCalculator:
    """Calculate individual risk indicators."""

    def __init__(self, db: Session, fiscal_year_id: int):
        self.db = db
        self.fiscal_year_id = fiscal_year_id
        self.fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()

        if not self.fiscal_year:
            raise ValueError(f"Fiscal year {fiscal_year_id} not found")

    # ==========================================
    # CATEGORY 1: LIQUIDITY & RESERVES (25% weight)
    # ==========================================

    def calculate_fund_balance_ratio(self) -> Dict[str, Any]:
        """
        Fund Balance Ratio = Fund Balance / Expenditures

        Measures: How many months of reserves does the city have?

        Thresholds:
        - Healthy: >20% (2.4 months)
        - Adequate: 15-20% (1.8-2.4 months)
        - Warning: 10-15% (1.2-1.8 months)
        - Critical: <10% (<1.2 months)
        """
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == self.fiscal_year_id,
            FundBalance.fund_type == "General"
        ).first()

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if not fund_balance or total_expenditures == 0:
            return {
                "indicator_code": "FB_RATIO",
                "value": None,
                "score": None,
                "threshold": None,
                "available": False,
                "notes": "Insufficient data"
            }

        ratio = float(fund_balance.total_fund_balance / total_expenditures)

        # Score based on thresholds
        if ratio >= 0.20:
            score = 0  # Healthy
            threshold = "healthy"
        elif ratio >= 0.15:
            score = 25  # Adequate
            threshold = "adequate"
        elif ratio >= 0.10:
            score = 50  # Warning
            threshold = "warning"
        else:
            score = 100  # Critical
            threshold = "critical"

        return {
            "indicator_code": "FB_RATIO",
            "indicator_name": "Fund Balance Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"{ratio:.1%} of annual expenditures in reserves",
            "notes": None
        }

    def calculate_days_of_cash(self) -> Dict[str, Any]:
        """
        Days of Cash = (Cash + Investments) / (Annual Expenditures / 365)

        Measures: How many days can the city operate with current cash?

        Thresholds:
        - Healthy: >60 days
        - Adequate: 45-60 days
        - Warning: 30-45 days
        - Critical: <30 days
        """
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == self.fiscal_year_id,
            FundBalance.fund_type == "General"
        ).first()

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if not fund_balance or total_expenditures == 0:
            return self._indicator_unavailable("DAYS_CASH", "Days of Cash")

        daily_expenditure = total_expenditures / 365
        days = float(fund_balance.total_fund_balance / daily_expenditure)

        if days >= 60:
            score, threshold = 0, "healthy"
        elif days >= 45:
            score, threshold = 25, "adequate"
        elif days >= 30:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DAYS_CASH",
            "indicator_name": "Days of Cash",
            "value": days,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "days",
            "interpretation": f"Can operate for {days:.0f} days with current reserves",
        }

    def calculate_liquidity_ratio(self) -> Dict[str, Any]:
        """
        Liquidity Ratio = Current Assets / Current Liabilities

        Simplified version (using fund balance as proxy for current assets).

        Thresholds:
        - Healthy: >2.0
        - Adequate: 1.5-2.0
        - Warning: 1.0-1.5
        - Critical: <1.0
        """
        # This requires balance sheet data which may not be available in all CAFRs
        # For MVP, we'll use fund balance ratio as a proxy
        return self._indicator_unavailable(
            "LIQUIDITY_RATIO",
            "Liquidity Ratio",
            notes="Balance sheet data not yet imported"
        )

    # ==========================================
    # CATEGORY 2: STRUCTURAL BALANCE (25% weight)
    # ==========================================

    def calculate_operating_balance(self) -> Dict[str, Any]:
        """
        Operating Balance = (Revenues - Expenditures) / Revenues

        Measures: Structural surplus or deficit?

        Thresholds:
        - Healthy: >5% (surplus)
        - Adequate: 0-5% (balanced)
        - Warning: -5% to 0% (deficit)
        - Critical: <-5% (large deficit)
        """
        total_revenues = self.db.query(
            func.sum(Revenue.actual_amount)
        ).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if total_revenues == 0:
            return self._indicator_unavailable("OP_BALANCE", "Operating Balance")

        balance = float((total_revenues - total_expenditures) / total_revenues)

        if balance >= 0.05:
            score, threshold = 0, "healthy"
        elif balance >= 0:
            score, threshold = 25, "adequate"
        elif balance >= -0.05:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "OP_BALANCE",
            "indicator_name": "Operating Balance",
            "value": balance,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"{'Surplus' if balance >= 0 else 'Deficit'} of {abs(balance):.1%}",
        }

    def calculate_structural_deficit_trend(self) -> Dict[str, Any]:
        """
        Structural Deficit Trend: Count consecutive years with deficit.

        Measures: Is the deficit persistent or one-time?

        Thresholds:
        - Healthy: 0 years
        - Adequate: 1 year
        - Warning: 2 years
        - Critical: 3+ years
        """
        # Get previous fiscal years
        previous_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.fiscal_year.city_id,
            FiscalYear.year < self.fiscal_year.year
        ).order_by(FiscalYear.year.desc()).limit(3).all()

        deficit_years = 0
        for fy in [self.fiscal_year] + previous_years:
            revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)

            expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
                Expenditure.fiscal_year_id == fy.id,
                Expenditure.fund_type == "General"
            ).scalar() or Decimal(0)

            if expenditures > revenues:
                deficit_years += 1
            else:
                break  # Stop counting if not consecutive

        if deficit_years == 0:
            score, threshold = 0, "healthy"
        elif deficit_years == 1:
            score, threshold = 25, "adequate"
        elif deficit_years == 2:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DEFICIT_TREND",
            "indicator_name": "Structural Deficit Trend",
            "value": deficit_years,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "years",
            "interpretation": f"{deficit_years} consecutive years with deficit",
        }

    # ==========================================
    # CATEGORY 3: PENSION STRESS (30% weight)
    # ==========================================

    def calculate_pension_funded_ratio(self) -> Dict[str, Any]:
        """
        Pension Funded Ratio = Assets / Total Pension Liability

        THE KEY PENSION INDICATOR.

        Thresholds:
        - Healthy: >80%
        - Adequate: 70-80%
        - Warning: 60-70%
        - Critical: <60%
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        if not pension_plans:
            return self._indicator_unavailable("PENSION_FUNDED", "Pension Funded Ratio")

        # Weighted average across all plans
        total_liability = sum(p.total_pension_liability for p in pension_plans)
        total_assets = sum(p.fiduciary_net_position for p in pension_plans)

        if total_liability == 0:
            return self._indicator_unavailable("PENSION_FUNDED", "Pension Funded Ratio")

        funded_ratio = float(total_assets / total_liability)

        if funded_ratio >= 0.80:
            score, threshold = 0, "healthy"
        elif funded_ratio >= 0.70:
            score, threshold = 25, "adequate"
        elif funded_ratio >= 0.60:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "PENSION_FUNDED",
            "indicator_name": "Pension Funded Ratio",
            "value": funded_ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"Pensions are {funded_ratio:.1%} funded",
        }

    def calculate_ual_ratio(self) -> Dict[str, Any]:
        """
        UAL Ratio = Unfunded Actuarial Liability / Annual Revenues

        Measures: How large is pension debt relative to revenue?

        Thresholds:
        - Healthy: <1.0x (less than 1 year of revenue)
        - Adequate: 1.0-2.0x
        - Warning: 2.0-3.0x
        - Critical: >3.0x
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        if not pension_plans or total_revenues == 0:
            return self._indicator_unavailable("UAL_RATIO", "UAL Ratio")

        total_ual = sum(p.net_pension_liability for p in pension_plans)
        ratio = float(total_ual / total_revenues)

        if ratio < 1.0:
            score, threshold = 0, "healthy"
        elif ratio < 2.0:
            score, threshold = 25, "adequate"
        elif ratio < 3.0:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "UAL_RATIO",
            "indicator_name": "UAL to Revenue Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"Unfunded pension debt is {ratio:.1f}x annual revenues",
        }

    def calculate_pension_contribution_burden(self) -> Dict[str, Any]:
        """
        Pension Contribution Burden = Annual Pension Payment / Payroll Costs

        Measures: What percentage of payroll goes to pensions?

        Thresholds:
        - Healthy: <20%
        - Adequate: 20-25%
        - Warning: 25-35%
        - Critical: >35%
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        if not pension_plans:
            return self._indicator_unavailable("PENSION_BURDEN", "Pension Contribution Burden")

        total_contributions = sum(
            (p.total_employer_contribution or 0) for p in pension_plans
        )
        total_payroll = sum((p.covered_payroll or 0) for p in pension_plans)

        if total_payroll == 0:
            return self._indicator_unavailable("PENSION_BURDEN", "Pension Contribution Burden")

        burden = float(total_contributions / total_payroll)

        if burden < 0.20:
            score, threshold = 0, "healthy"
        elif burden < 0.25:
            score, threshold = 25, "adequate"
        elif burden < 0.35:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "PENSION_BURDEN",
            "indicator_name": "Pension Contribution Burden",
            "value": burden,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Pension costs are {burden:.1%} of payroll",
        }

    # ==========================================
    # CATEGORY 4: REVENUE SUSTAINABILITY (10% weight)
    # ==========================================

    def calculate_revenue_volatility(self) -> Dict[str, Any]:
        """
        Revenue Volatility = Standard deviation of year-over-year changes

        Measures: How stable are revenues?

        Thresholds:
        - Healthy: <5% (stable)
        - Adequate: 5-10%
        - Warning: 10-15%
        - Critical: >15% (highly volatile)
        """
        # Get 5 years of revenue data
        previous_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.fiscal_year.city_id,
            FiscalYear.year <= self.fiscal_year.year
        ).order_by(FiscalYear.year.desc()).limit(5).all()

        if len(previous_years) < 3:
            return self._indicator_unavailable(
                "REV_VOLATILITY",
                "Revenue Volatility",
                notes="Need 3+ years of data"
            )

        revenues = []
        for fy in previous_years:
            total = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)
            revenues.append(float(total))

        # Calculate year-over-year changes
        changes = []
        for i in range(len(revenues) - 1):
            if revenues[i+1] > 0:
                change = (revenues[i] - revenues[i+1]) / revenues[i+1]
                changes.append(change)

        if not changes:
            return self._indicator_unavailable("REV_VOLATILITY", "Revenue Volatility")

        # Standard deviation
        import statistics
        volatility = statistics.stdev(changes) if len(changes) > 1 else 0

        if volatility < 0.05:
            score, threshold = 0, "healthy"
        elif volatility < 0.10:
            score, threshold = 25, "adequate"
        elif volatility < 0.15:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "REV_VOLATILITY",
            "indicator_name": "Revenue Volatility",
            "value": volatility,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Revenue volatility of {volatility:.1%}",
        }

    # ==========================================
    # CATEGORY 5: DEBT BURDEN (10% weight)
    # ==========================================

    def calculate_debt_service_ratio(self) -> Dict[str, Any]:
        """
        Debt Service Ratio = Annual Debt Payments / Revenues

        Measures: What percentage of revenue goes to debt?

        Thresholds:
        - Healthy: <10%
        - Adequate: 10-15%
        - Warning: 15-20%
        - Critical: >20%
        """
        # Look for debt service in expenditures
        debt_service = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General",
            Expenditure.category.has(ExpenditureCategory.is_debt_service == True)
        ).scalar() or Decimal(0)

        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        if total_revenues == 0:
            return self._indicator_unavailable("DEBT_SERVICE", "Debt Service Ratio")

        ratio = float(debt_service / total_revenues)

        if ratio < 0.10:
            score, threshold = 0, "healthy"
        elif ratio < 0.15:
            score, threshold = 25, "adequate"
        elif ratio < 0.20:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DEBT_SERVICE",
            "indicator_name": "Debt Service Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Debt service is {ratio:.1%} of revenues",
        }

    # ==========================================
    # HELPER METHODS
    # ==========================================

    def _indicator_unavailable(
        self,
        code: str,
        name: str,
        notes: str = "Insufficient data"
    ) -> Dict[str, Any]:
        """Return structure for unavailable indicator."""
        return {
            "indicator_code": code,
            "indicator_name": name,
            "value": None,
            "score": None,
            "threshold": None,
            "available": False,
            "notes": notes
        }

    def calculate_all_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Calculate all risk indicators."""
        indicators = {
            # Liquidity
            "FB_RATIO": self.calculate_fund_balance_ratio(),
            "DAYS_CASH": self.calculate_days_of_cash(),

            # Structural Balance
            "OP_BALANCE": self.calculate_operating_balance(),
            "DEFICIT_TREND": self.calculate_structural_deficit_trend(),

            # Pension Stress
            "PENSION_FUNDED": self.calculate_pension_funded_ratio(),
            "UAL_RATIO": self.calculate_ual_ratio(),
            "PENSION_BURDEN": self.calculate_pension_contribution_burden(),

            # Revenue Sustainability
            "REV_VOLATILITY": self.calculate_revenue_volatility(),

            # Debt
            "DEBT_SERVICE": self.calculate_debt_service_ratio(),
        }

        return indicators
