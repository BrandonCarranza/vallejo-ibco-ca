"""
Data lineage tracer for forensic accountability.

Traces any data point back through its complete provenance chain:
- Risk scores → indicators → source data → CAFR/CalPERS documents
- Complete audit trail with timestamps and personnel
- Confidence scores and validation chains

This module provides forensic-level accountability for all data points
in the system, critical for legal defense and public transparency.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy.orm import Session

from src.database.models.core import City, DataLineage, DataSource, FiscalYear
from src.database.models.financial import Expenditure, Revenue
from src.database.models.pensions import PensionPlan
from src.database.models.risk import RiskIndicatorScore, RiskScore

logger = structlog.get_logger(__name__)


class LineageNode:
    """
    Represents a single node in the data lineage chain.

    Each node tracks:
    - The data point itself (table, record, field, value)
    - Source document (URL, page, section, table)
    - Personnel (who entered it, who validated it)
    - Timestamps (when entered, when validated)
    - Confidence (numeric score 0-100)
    """

    def __init__(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        value: Any,
        lineage_record: Optional[DataLineage] = None,
    ):
        """Initialize lineage node."""
        self.table_name = table_name
        self.record_id = record_id
        self.field_name = field_name
        self.value = value
        self.lineage_record = lineage_record

        # Extracted from lineage_record if available
        self.source_document_url = None
        self.source_document_page = None
        self.source_document_section = None
        self.source_document_table_name = None
        self.source_document_line_item = None
        self.extracted_by = None
        self.extracted_at = None
        self.extraction_method = None
        self.validated = False
        self.validated_by = None
        self.validated_at = None
        self.validation_notes = None
        self.confidence_score = None
        self.confidence_level = None
        self.notes = None
        self.source_name = None

        if lineage_record:
            self._populate_from_lineage()

    def _populate_from_lineage(self):
        """Populate node attributes from lineage record."""
        lineage = self.lineage_record

        self.source_document_url = lineage.source_document_url
        self.source_document_page = lineage.source_document_page
        self.source_document_section = lineage.source_document_section
        self.source_document_table_name = lineage.source_document_table_name
        self.source_document_line_item = lineage.source_document_line_item
        self.extracted_by = lineage.extracted_by
        self.extracted_at = lineage.extracted_at
        self.extraction_method = lineage.extraction_method
        self.validated = lineage.validated
        self.validated_by = lineage.validated_by
        self.validated_at = lineage.validated_at
        self.validation_notes = lineage.validation_notes
        self.confidence_score = lineage.confidence_score
        self.confidence_level = lineage.confidence_level
        self.notes = lineage.notes

        if lineage.source:
            self.source_name = lineage.source.name

    def to_dict(self) -> Dict:
        """Convert node to dictionary representation."""
        return {
            "table_name": self.table_name,
            "record_id": self.record_id,
            "field_name": self.field_name,
            "value": str(self.value) if self.value is not None else None,
            "source": {
                "name": self.source_name,
                "document_url": self.source_document_url,
                "page": self.source_document_page,
                "section": self.source_document_section,
                "table_name": self.source_document_table_name,
                "line_item": self.source_document_line_item,
            },
            "extraction": {
                "method": self.extraction_method,
                "extracted_by": self.extracted_by,
                "extracted_at": self.extracted_at.isoformat()
                if self.extracted_at
                else None,
                "notes": self.notes,
            },
            "validation": {
                "validated": self.validated,
                "validated_by": self.validated_by,
                "validated_at": self.validated_at.isoformat()
                if self.validated_at
                else None,
                "validation_notes": self.validation_notes,
            },
            "confidence": {
                "score": self.confidence_score,
                "level": self.confidence_level,
            },
        }


class LineageChain:
    """
    Represents a complete chain of data lineage.

    Traces from a high-level metric (e.g., risk score) down through
    all constituent data points to their source documents.
    """

    def __init__(self, root_node: LineageNode):
        """Initialize lineage chain with root node."""
        self.root = root_node
        self.nodes: List[LineageNode] = [root_node]
        self.dependencies: List[Tuple[LineageNode, LineageNode]] = []

    def add_dependency(self, parent: LineageNode, child: LineageNode):
        """Add a dependency relationship between nodes."""
        if child not in self.nodes:
            self.nodes.append(child)
        self.dependencies.append((parent, child))

    def to_dict(self) -> Dict:
        """Convert chain to dictionary representation."""
        return {
            "root": self.root.to_dict(),
            "nodes": [node.to_dict() for node in self.nodes],
            "dependencies": [
                {
                    "parent": {
                        "table": parent.table_name,
                        "record_id": parent.record_id,
                        "field": parent.field_name,
                    },
                    "child": {
                        "table": child.table_name,
                        "record_id": child.record_id,
                        "field": child.field_name,
                    },
                }
                for parent, child in self.dependencies
            ],
        }


class DataLineageTracer:
    """
    Main lineage tracing engine.

    Provides functions to trace any data point back to its source documents
    with complete forensic accountability.
    """

    def __init__(self, db: Session):
        """Initialize tracer with database session."""
        self.db = db

    def trace_data_point(
        self, table_name: str, record_id: int, field_name: str
    ) -> Optional[LineageNode]:
        """
        Trace a single data point to its lineage.

        Args:
            table_name: Database table name
            record_id: Record ID
            field_name: Field name

        Returns:
            LineageNode with complete provenance, or None if not found
        """
        # Get lineage record
        lineage = (
            self.db.query(DataLineage)
            .filter(
                DataLineage.table_name == table_name,
                DataLineage.record_id == record_id,
                DataLineage.field_name == field_name,
            )
            .first()
        )

        if not lineage:
            logger.warning(
                "no_lineage_found",
                table=table_name,
                record_id=record_id,
                field=field_name,
            )
            return None

        # Get the actual value from the table
        value = self._get_field_value(table_name, record_id, field_name)

        return LineageNode(table_name, record_id, field_name, value, lineage)

    def trace_risk_score(self, fiscal_year_id: int) -> LineageChain:
        """
        Trace a risk score back through all constituent indicators.

        Args:
            fiscal_year_id: Fiscal year ID

        Returns:
            LineageChain showing complete provenance
        """
        # Get risk score
        risk_score = (
            self.db.query(RiskScore)
            .filter(RiskScore.fiscal_year_id == fiscal_year_id)
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )

        if not risk_score:
            logger.error("risk_score_not_found", fiscal_year_id=fiscal_year_id)
            raise ValueError(f"Risk score not found for fiscal year {fiscal_year_id}")

        # Create root node
        root_lineage = self.trace_data_point(
            "risk_scores", risk_score.id, "overall_score"
        )
        if not root_lineage:
            root_lineage = LineageNode(
                "risk_scores",
                risk_score.id,
                "overall_score",
                risk_score.overall_score,
            )

        chain = LineageChain(root_lineage)

        # Trace indicator scores
        indicator_scores = (
            self.db.query(RiskIndicatorScore)
            .filter(RiskIndicatorScore.risk_score_id == risk_score.id)
            .all()
        )

        for indicator_score in indicator_scores:
            # Trace indicator value
            indicator_node = self.trace_data_point(
                "risk_indicator_scores", indicator_score.id, "indicator_value"
            )

            if not indicator_node:
                indicator_node = LineageNode(
                    "risk_indicator_scores",
                    indicator_score.id,
                    "indicator_value",
                    indicator_score.indicator_value,
                )

            chain.add_dependency(root_lineage, indicator_node)

            # Trace underlying financial data
            self._trace_indicator_dependencies(
                indicator_score, indicator_node, chain, fiscal_year_id
            )

        return chain

    def _trace_indicator_dependencies(
        self,
        indicator_score,
        indicator_node: LineageNode,
        chain: LineageChain,
        fiscal_year_id: int,
    ):
        """Trace dependencies of a risk indicator to underlying financial data."""
        # Map indicators to their data sources
        indicator_code = indicator_score.indicator_code

        # Pension indicators
        if indicator_code in ["PENSION_FUNDED", "UAL_RATIO", "PENSION_BURDEN"]:
            self._trace_pension_dependencies(indicator_node, chain, fiscal_year_id)

        # Revenue/expenditure indicators
        elif indicator_code in ["OP_BALANCE", "DEFICIT_TREND"]:
            self._trace_financial_dependencies(indicator_node, chain, fiscal_year_id)

    def _trace_pension_dependencies(
        self, indicator_node: LineageNode, chain: LineageChain, fiscal_year_id: int
    ):
        """Trace pension indicator dependencies."""
        pension_plans = (
            self.db.query(PensionPlan)
            .filter(PensionPlan.fiscal_year_id == fiscal_year_id)
            .all()
        )

        for plan in pension_plans:
            # Trace funded ratio
            funded_ratio_node = self.trace_data_point(
                "pension_plans", plan.id, "funded_ratio"
            )
            if funded_ratio_node:
                chain.add_dependency(indicator_node, funded_ratio_node)

            # Trace unfunded liability
            ual_node = self.trace_data_point(
                "pension_plans", plan.id, "unfunded_liability"
            )
            if ual_node:
                chain.add_dependency(indicator_node, ual_node)

    def _trace_financial_dependencies(
        self, indicator_node: LineageNode, chain: LineageChain, fiscal_year_id: int
    ):
        """Trace financial data dependencies."""
        # Get revenues
        revenues = (
            self.db.query(Revenue)
            .filter(Revenue.fiscal_year_id == fiscal_year_id)
            .limit(5)  # Limit to top 5 for brevity
            .all()
        )

        for revenue in revenues:
            revenue_node = self.trace_data_point("revenues", revenue.id, "amount")
            if revenue_node:
                chain.add_dependency(indicator_node, revenue_node)

        # Get expenditures
        expenditures = (
            self.db.query(Expenditure)
            .filter(Expenditure.fiscal_year_id == fiscal_year_id)
            .limit(5)  # Limit to top 5 for brevity
            .all()
        )

        for expenditure in expenditures:
            exp_node = self.trace_data_point("expenditures", expenditure.id, "amount")
            if exp_node:
                chain.add_dependency(indicator_node, exp_node)

    def _get_field_value(
        self, table_name: str, record_id: int, field_name: str
    ) -> Any:
        """Get the actual field value from a table."""
        # Map table names to models
        model_map = {
            "risk_scores": RiskScore,
            "risk_indicator_scores": RiskIndicatorScore,
            "pension_plans": PensionPlan,
            "revenues": Revenue,
            "expenditures": Expenditure,
            "fiscal_years": FiscalYear,
            "cities": City,
        }

        model = model_map.get(table_name)
        if not model:
            logger.warning("unknown_table", table_name=table_name)
            return None

        record = self.db.query(model).filter(model.id == record_id).first()
        if not record:
            return None

        return getattr(record, field_name, None)

    def generate_evidence_chain_text(self, chain: LineageChain) -> str:
        """
        Generate human-readable evidence chain text.

        Args:
            chain: LineageChain to format

        Returns:
            Formatted text representation
        """
        lines = []
        root = chain.root

        lines.append(f"Data Point: {root.field_name} = {root.value}")
        lines.append(f"Table: {root.table_name}, Record ID: {root.record_id}")
        lines.append("")

        if root.source_document_url:
            lines.append("Source Document:")
            if root.source_name:
                lines.append(f"  Name: {root.source_name}")
            lines.append(f"  URL: {root.source_document_url}")
            if root.source_document_page:
                lines.append(f"  Page: {root.source_document_page}")
            if root.source_document_table_name:
                lines.append(f"  Table: {root.source_document_table_name}")
            lines.append("")

        if root.extracted_by:
            lines.append("Extraction:")
            lines.append(f"  Method: {root.extraction_method}")
            lines.append(f"  Extracted by: {root.extracted_by}")
            if root.extracted_at:
                lines.append(f"  Extracted at: {root.extracted_at.isoformat()}")
            if root.notes:
                lines.append(f"  Notes: {root.notes}")
            lines.append("")

        if root.validated:
            lines.append("Validation:")
            lines.append(f"  Validated: Yes")
            if root.validated_by:
                lines.append(f"  Validated by: {root.validated_by}")
            if root.validated_at:
                lines.append(f"  Validated at: {root.validated_at.isoformat()}")
            if root.validation_notes:
                lines.append(f"  Notes: {root.validation_notes}")
            lines.append("")

        if root.confidence_score is not None:
            lines.append(f"Confidence: {root.confidence_score}% ({root.confidence_level})")
            lines.append("")

        # Show dependencies
        if len(chain.nodes) > 1:
            lines.append("Dependencies:")
            for parent, child in chain.dependencies:
                lines.append(
                    f"  └─ {child.table_name}.{child.field_name} = {child.value}"
                )
                if child.source_document_url:
                    lines.append(f"     Source: {child.source_name or 'Unknown'}")
                    if child.source_document_page:
                        lines.append(f"     Page: {child.source_document_page}")

        return "\n".join(lines)
