"""
Database models for IBCo Vallejo Console.

Organized by domain:
- core: Cities, fiscal years, data sources, data lineage
- financial: Revenues, expenditures, fund balances
- pensions: Pension plans, contributions, projections, OPEB
- risk: Risk scores, indicators, trends, benchmarks
- projections: Financial projections, scenarios, fiscal cliff analysis
- refresh: Data refresh operations, notifications, schedules
"""

# Core models
from src.database.models.core import City, DataLineage, DataSource, FiscalYear

# Financial models
from src.database.models.financial import (
    Expenditure,
    ExpenditureCategory,
    FundBalance,
    Revenue,
    RevenueCategory,
)

# Pension models
from src.database.models.pensions import (
    OPEBLiability,
    PensionAssumptionChange,
    PensionContribution,
    PensionPlan,
    PensionProjection,
)

# Risk models
from src.database.models.risk import (
    BenchmarkComparison,
    RiskIndicator,
    RiskIndicatorScore,
    RiskScore,
    RiskTrend,
)

# Projection models
from src.database.models.projections import (
    FiscalCliffAnalysis,
    FinancialProjection,
    ProjectionScenario,
    ScenarioAssumption,
)

# Refresh models
from src.database.models.refresh import (
    DataRefreshSchedule,
    RefreshCheck,
    RefreshNotification,
    RefreshOperation,
)

__all__ = [
    # Core models
    "City",
    "FiscalYear",
    "DataSource",
    "DataLineage",
    # Financial models
    "Revenue",
    "RevenueCategory",
    "Expenditure",
    "ExpenditureCategory",
    "FundBalance",
    # Pension models
    "PensionPlan",
    "PensionContribution",
    "PensionProjection",
    "OPEBLiability",
    "PensionAssumptionChange",
    # Risk models
    "RiskIndicator",
    "RiskScore",
    "RiskIndicatorScore",
    "RiskTrend",
    "BenchmarkComparison",
    # Projection models
    "ProjectionScenario",
    "FinancialProjection",
    "ScenarioAssumption",
    "FiscalCliffAnalysis",
    # Refresh models
    "RefreshCheck",
    "RefreshNotification",
    "RefreshOperation",
    "DataRefreshSchedule",
]
