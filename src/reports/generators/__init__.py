"""
Report generators for IBCo public reports and narratives.

This module provides automated report generation in multiple formats:
- HTML (web-optimized, responsive)
- PDF (printable, archival)
- JSON (machine-readable for researchers)

Report types:
- Fiscal Summary Report: Complete fiscal status overview
- Risk Narrative: Human-readable risk assessment
- Projection Scenario Report: Multi-scenario comparison
"""

from .base_generator import BaseReportGenerator
from .fiscal_summary_report import FiscalSummaryReportGenerator
from .risk_narrative import RiskNarrativeGenerator
from .projection_scenario_report import ProjectionScenarioReportGenerator

__all__ = [
    "BaseReportGenerator",
    "FiscalSummaryReportGenerator",
    "RiskNarrativeGenerator",
    "ProjectionScenarioReportGenerator",
]
