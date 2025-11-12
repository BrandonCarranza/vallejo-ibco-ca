#!/usr/bin/env python3
"""
Generate data lineage reports for forensic accountability.

Shows complete provenance chain for any data point:
- Source documents with clickable links
- Page numbers, table names, line items
- Transcriber and reviewer information
- Timestamps for all operations
- Confidence scores

Usage:
    # Generate lineage report for a risk score
    python scripts/reports/generate_lineage_report.py --fiscal-year-id 1 --output lineage.html

    # Generate for specific data point
    python scripts/reports/generate_lineage_report.py --table revenues --record-id 42 --field amount

    # Generate and open in browser
    python scripts/reports/generate_lineage_report.py --fiscal-year-id 1 --open
"""

import argparse
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import structlog

from src.analytics.lineage_tracer import DataLineageTracer
from src.config.database import SessionLocal

logger = structlog.get_logger(__name__)


class LineageReportGenerator:
    """Generate HTML lineage reports."""

    def __init__(self, db):
        """Initialize report generator."""
        self.db = db
        self.tracer = DataLineageTracer(db)

    def generate_risk_score_report(self, fiscal_year_id: int) -> str:
        """
        Generate lineage report for a risk score.

        Args:
            fiscal_year_id: Fiscal year ID

        Returns:
            HTML report string
        """
        logger.info("generating_risk_score_lineage", fiscal_year_id=fiscal_year_id)

        try:
            chain = self.tracer.trace_risk_score(fiscal_year_id)
            return self._generate_html_report(chain, f"Risk Score - Fiscal Year ID {fiscal_year_id}")
        except Exception as e:
            logger.error("report_generation_failed", error=str(e))
            raise

    def generate_data_point_report(
        self, table_name: str, record_id: int, field_name: str
    ) -> str:
        """
        Generate lineage report for a specific data point.

        Args:
            table_name: Table name
            record_id: Record ID
            field_name: Field name

        Returns:
            HTML report string
        """
        logger.info(
            "generating_data_point_lineage",
            table=table_name,
            record_id=record_id,
            field=field_name,
        )

        node = self.tracer.trace_data_point(table_name, record_id, field_name)

        if not node:
            raise ValueError(f"No lineage found for {table_name}.{record_id}.{field_name}")

        # Create simple chain with just this node
        from src.analytics.lineage_tracer import LineageChain

        chain = LineageChain(node)

        return self._generate_html_report(
            chain, f"{table_name}.{field_name} (Record {record_id})"
        )

    def _generate_html_report(self, chain, title: str) -> str:
        """Generate HTML report from lineage chain."""
        root = chain.root

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Data Lineage Report - {title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .data-point {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .data-point-header {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin: 15px 0;
        }}
        .metadata-label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .metadata-value {{
            color: #2c3e50;
        }}
        .source-section {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .extraction-section {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .validation-section {{
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .confidence-section {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .confidence-high {{
            background-color: #d4edda;
            border-left-color: #28a745;
        }}
        .dependency {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0 10px 30px;
            border-radius: 5px;
        }}
        .dependency-arrow {{
            color: #3498db;
            font-size: 1.2em;
            margin-right: 10px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.9em;
            font-weight: bold;
            margin-right: 10px;
        }}
        .badge-success {{
            background-color: #28a745;
            color: white;
        }}
        .badge-warning {{
            background-color: #ffc107;
            color: #333;
        }}
        .badge-info {{
            background-color: #17a2b8;
            color: white;
        }}
        .timestamp {{
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Data Lineage Report</h1>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

        <div class="data-point">
            <div class="data-point-header">
                {root.field_name}: {root.value}
            </div>
            <div class="metadata">
                <div class="metadata-label">Table:</div>
                <div class="metadata-value">{root.table_name}</div>
                <div class="metadata-label">Record ID:</div>
                <div class="metadata-value">{root.record_id}</div>
            </div>
        </div>
"""

        # Source document section
        if root.source_document_url:
            html += """
        <div class="source-section">
            <h2>📄 Source Document</h2>
            <div class="metadata">
"""
            if root.source_name:
                html += f"""
                <div class="metadata-label">Document Name:</div>
                <div class="metadata-value">{root.source_name}</div>
"""
            if root.source_document_url:
                html += f"""
                <div class="metadata-label">URL:</div>
                <div class="metadata-value"><a href="{root.source_document_url}" target="_blank">{root.source_document_url}</a></div>
"""
            if root.source_document_page:
                html += f"""
                <div class="metadata-label">Page:</div>
                <div class="metadata-value">Page {root.source_document_page}</div>
"""
            if root.source_document_section:
                html += f"""
                <div class="metadata-label">Section:</div>
                <div class="metadata-value">{root.source_document_section}</div>
"""
            if root.source_document_table_name:
                html += f"""
                <div class="metadata-label">Table:</div>
                <div class="metadata-value">{root.source_document_table_name}</div>
"""
            if root.source_document_line_item:
                html += f"""
                <div class="metadata-label">Line Item:</div>
                <div class="metadata-value">{root.source_document_line_item}</div>
"""
            html += """
            </div>
        </div>
"""

        # Extraction section
        if root.extracted_by:
            html += f"""
        <div class="extraction-section">
            <h2>✏️ Data Extraction</h2>
            <div class="metadata">
                <div class="metadata-label">Method:</div>
                <div class="metadata-value"><span class="badge badge-info">{root.extraction_method}</span></div>
                <div class="metadata-label">Extracted by:</div>
                <div class="metadata-value">{root.extracted_by}</div>
"""
            if root.extracted_at:
                html += f"""
                <div class="metadata-label">Timestamp:</div>
                <div class="metadata-value"><span class="timestamp">{root.extracted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</span></div>
"""
            if root.notes:
                html += f"""
                <div class="metadata-label">Notes:</div>
                <div class="metadata-value">{root.notes}</div>
"""
            html += """
            </div>
        </div>
"""

        # Validation section
        if root.validated:
            html += f"""
        <div class="validation-section">
            <h2>✅ Validation</h2>
            <div class="metadata">
                <div class="metadata-label">Status:</div>
                <div class="metadata-value"><span class="badge badge-success">Validated</span></div>
"""
            if root.validated_by:
                html += f"""
                <div class="metadata-label">Validated by:</div>
                <div class="metadata-value">{root.validated_by}</div>
"""
            if root.validated_at:
                html += f"""
                <div class="metadata-label">Timestamp:</div>
                <div class="metadata-value"><span class="timestamp">{root.validated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</span></div>
"""
            if root.validation_notes:
                html += f"""
                <div class="metadata-label">Validation Notes:</div>
                <div class="metadata-value">{root.validation_notes}</div>
"""
            html += """
            </div>
        </div>
"""

        # Confidence section
        if root.confidence_score is not None:
            confidence_class = "confidence-high" if root.confidence_score >= 90 else ""
            html += f"""
        <div class="confidence-section {confidence_class}">
            <h2>🎯 Confidence</h2>
            <div class="metadata">
                <div class="metadata-label">Confidence Score:</div>
                <div class="metadata-value">{root.confidence_score}% ({root.confidence_level or 'N/A'})</div>
            </div>
        </div>
"""

        # Dependencies section
        if len(chain.nodes) > 1:
            html += """
        <h2>🔗 Dependencies</h2>
        <p>This data point depends on the following underlying data:</p>
"""
            for parent, child in chain.dependencies:
                html += f"""
        <div class="dependency">
            <span class="dependency-arrow">└─</span>
            <strong>{child.field_name}:</strong> {child.value}
            <div class="metadata" style="margin-top: 10px; margin-left: 30px;">
                <div class="metadata-label">Table:</div>
                <div class="metadata-value">{child.table_name} (Record {child.record_id})</div>
"""
                if child.source_name:
                    html += f"""
                <div class="metadata-label">Source:</div>
                <div class="metadata-value">{child.source_name}</div>
"""
                if child.source_document_page:
                    html += f"""
                <div class="metadata-label">Page:</div>
                <div class="metadata-value">Page {child.source_document_page}</div>
"""
                if child.extracted_by:
                    html += f"""
                <div class="metadata-label">Extracted by:</div>
                <div class="metadata-value">{child.extracted_by}</div>
"""
                html += """
            </div>
        </div>
"""

        # Footer
        html += """
        <div class="footer">
            <p><strong>IBCo Vallejo Console</strong> - Independent Budget & Civic Oversight</p>
            <p>Data Lineage Report - Forensic Accountability & Transparency</p>
            <p>Every data point in this report is traceable to its source document with complete chain of custody.</p>
        </div>
    </div>
</body>
</html>
"""

        return html


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate data lineage report")

    # Mutually exclusive group for data point selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fiscal-year-id", type=int, help="Generate report for risk score")
    group.add_argument(
        "--table",
        type=str,
        help="Table name for specific data point (requires --record-id and --field)",
    )

    # Additional arguments for specific data point
    parser.add_argument("--record-id", type=int, help="Record ID")
    parser.add_argument("--field", type=str, help="Field name")

    # Output options
    parser.add_argument("--output", type=str, help="Output HTML file path")
    parser.add_argument("--open", action="store_true", help="Open report in browser")

    args = parser.parse_args()

    # Validate specific data point arguments
    if args.table:
        if not args.record_id or not args.field:
            parser.error("--table requires --record-id and --field")

    db = SessionLocal()
    try:
        generator = LineageReportGenerator(db)

        # Generate report
        if args.fiscal_year_id:
            html_report = generator.generate_risk_score_report(args.fiscal_year_id)
            default_filename = f"lineage_risk_score_fy{args.fiscal_year_id}.html"
        else:
            html_report = generator.generate_data_point_report(
                args.table, args.record_id, args.field
            )
            default_filename = f"lineage_{args.table}_{args.record_id}_{args.field}.html"

        # Save to file
        output_path = args.output or default_filename
        with open(output_path, "w") as f:
            f.write(html_report)

        logger.info("report_generated", output=output_path)
        print(f"✅ Lineage report generated: {output_path}")

        # Open in browser if requested
        if args.open:
            webbrowser.open(f"file://{Path(output_path).absolute()}")
            print(f"🌐 Opened in browser")

    finally:
        db.close()


if __name__ == "__main__":
    main()
