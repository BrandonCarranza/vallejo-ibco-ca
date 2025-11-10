"""
Database models for IBCo Vallejo Console.

Organized by domain:
- core: Cities, fiscal years, data sources, data lineage
- financial: Revenues, expenditures, fund balances
- pensions: Pension plans and obligations (to be implemented)
- risk: Risk scores and indicators (to be implemented)
- projections: Financial projections (to be implemented)
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
]
