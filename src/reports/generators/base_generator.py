"""
Base report generator class.

Provides common functionality for all report generators:
- HTML generation via Jinja2 templates
- PDF generation via WeasyPrint
- JSON output for machine-readable data
- Chart embedding and image handling
- Responsive CSS styling
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session


class BaseReportGenerator:
    """Base class for all report generators."""

    def __init__(
        self,
        db: Session,
        template_name: Optional[str] = None,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize report generator.

        Args:
            db: Database session
            template_name: Name of Jinja2 template file (optional)
            template_dir: Directory containing templates (default: src/reports/templates)
        """
        self.db = db
        self.template_name = template_name

        # Set up template environment
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.jinja_env.filters["format_currency"] = self.format_currency
        self.jinja_env.filters["format_percent"] = self.format_percent
        self.jinja_env.filters["format_number"] = self.format_number
        self.jinja_env.filters["format_date"] = self.format_date

    @staticmethod
    def format_currency(value: Optional[float], compact: bool = False) -> str:
        """Format number as currency."""
        if value is None:
            return "N/A"

        if compact and abs(value) >= 1_000_000:
            # Millions
            if abs(value) >= 1_000_000_000:
                return f"${value / 1_000_000_000:.1f}B"
            return f"${value / 1_000_000:.1f}M"

        return f"${value:,.0f}"

    @staticmethod
    def format_percent(value: Optional[float], decimals: int = 1) -> str:
        """Format number as percentage."""
        if value is None:
            return "N/A"

        return f"{value * 100:.{decimals}f}%"

    @staticmethod
    def format_number(value: Optional[float], decimals: int = 0, compact: bool = False) -> str:
        """Format number with thousands separators."""
        if value is None:
            return "N/A"

        if compact and abs(value) >= 1_000_000:
            if abs(value) >= 1_000_000_000:
                return f"{value / 1_000_000_000:.1f}B"
            return f"{value / 1_000_000:.1f}M"

        if decimals == 0:
            return f"{value:,.0f}"
        return f"{value:,.{decimals}f}"

    @staticmethod
    def format_date(value: datetime, format_str: str = "%B %d, %Y") -> str:
        """Format datetime."""
        if value is None:
            return "N/A"

        return value.strftime(format_str)

    def get_report_context(self) -> Dict[str, Any]:
        """
        Get report context data.

        Must be implemented by subclasses.

        Returns:
            Dictionary of context data for template rendering
        """
        raise NotImplementedError("Subclasses must implement get_report_context()")

    def generate_html(
        self,
        context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None,
    ) -> str:
        """
        Generate HTML report.

        Args:
            context: Template context (default: calls get_report_context())
            template_name: Template to use (default: self.template_name)

        Returns:
            HTML string
        """
        if context is None:
            context = self.get_report_context()

        if template_name is None:
            template_name = self.template_name

        if template_name is None:
            raise ValueError("No template name specified")

        # Add generation metadata
        context["generated_at"] = datetime.utcnow()
        context["generator_version"] = "1.0"

        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

    def generate_pdf(
        self,
        output_path: Path,
        context: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate PDF report.

        Args:
            output_path: Where to save PDF
            context: Template context (default: calls get_report_context())

        Returns:
            Path to generated PDF
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )

        # Generate HTML first
        html_content = self.generate_html(context)

        # Convert to PDF
        html = HTML(string=html_content)

        # Custom CSS for PDF
        pdf_css = CSS(
            string="""
            @page {
                size: Letter;
                margin: 1in;
            }
            body {
                font-family: 'Helvetica', 'Arial', sans-serif;
            }
            """
        )

        html.write_pdf(str(output_path), stylesheets=[pdf_css])

        return output_path

    def generate_json(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate JSON report (machine-readable).

        Args:
            context: Report context (default: calls get_report_context())

        Returns:
            JSON string
        """
        if context is None:
            context = self.get_report_context()

        # Add metadata
        output = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "generator_version": "1.0",
                "data_source": "IBCo Vallejo Console",
            },
            "data": context,
        }

        return json.dumps(output, indent=2, default=str)

    def generate_all_formats(
        self,
        output_dir: Path,
        filename_base: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Path]:
        """
        Generate report in all formats.

        Args:
            output_dir: Directory to save files
            filename_base: Base filename (without extension)
            context: Report context (default: calls get_report_context())

        Returns:
            Dictionary mapping format to file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if context is None:
            context = self.get_report_context()

        outputs = {}

        # HTML
        html_path = output_dir / f"{filename_base}.html"
        html_content = self.generate_html(context)
        html_path.write_text(html_content)
        outputs["html"] = html_path

        # PDF
        try:
            pdf_path = output_dir / f"{filename_base}.pdf"
            self.generate_pdf(pdf_path, context)
            outputs["pdf"] = pdf_path
        except ImportError as e:
            print(f"Warning: PDF generation skipped ({e})")

        # JSON
        json_path = output_dir / f"{filename_base}.json"
        json_content = self.generate_json(context)
        json_path.write_text(json_content)
        outputs["json"] = json_path

        return outputs

    def _get_fiscal_year_summary(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """
        Get fiscal year summary data (common across reports).

        Args:
            city_id: City ID
            fiscal_year: Fiscal year

        Returns:
            Dictionary with revenues, expenditures, fund balance, etc.
        """
        from src.database.models.core import City, FiscalYear
        from src.database.models.financial import (
            Expenditure,
            FundBalance,
            Revenue,
        )

        # Get fiscal year record
        fy = (
            self.db.query(FiscalYear)
            .filter(
                FiscalYear.city_id == city_id,
                FiscalYear.year == fiscal_year,
            )
            .first()
        )

        if not fy:
            return {}

        # Get city
        city = self.db.query(City).filter(City.id == city_id).first()

        # Calculate revenue totals
        revenue_total = (
            self.db.query(Revenue)
            .filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.is_deleted == False,
            )
            .with_entities(Revenue.actual_amount)
            .all()
        )
        total_revenues = sum(r[0] for r in revenue_total if r[0])

        # Calculate expenditure totals
        expenditure_total = (
            self.db.query(Expenditure)
            .filter(
                Expenditure.fiscal_year_id == fy.id,
                Expenditure.is_deleted == False,
            )
            .with_entities(Expenditure.actual_amount)
            .all()
        )
        total_expenditures = sum(e[0] for e in expenditure_total if e[0])

        # Get fund balance
        fund_balance = (
            self.db.query(FundBalance)
            .filter(
                FundBalance.fiscal_year_id == fy.id,
                FundBalance.fund_type == "General",
                FundBalance.is_deleted == False,
            )
            .first()
        )

        return {
            "city_name": city.name if city else "Unknown",
            "fiscal_year": fiscal_year,
            "total_revenues": total_revenues,
            "total_expenditures": total_expenditures,
            "operating_balance": total_revenues - total_expenditures if total_revenues and total_expenditures else None,
            "fund_balance": fund_balance.total_fund_balance if fund_balance else None,
            "fund_balance_ratio": fund_balance.fund_balance_ratio if fund_balance else None,
        }

    def _get_risk_score_summary(self, city_id: int, fiscal_year: int) -> Dict[str, Any]:
        """
        Get risk score summary (common across reports).

        Args:
            city_id: City ID
            fiscal_year: Fiscal year

        Returns:
            Dictionary with risk scores and category breakdown
        """
        from src.database.models.core import FiscalYear
        from src.database.models.risk import RiskScore

        # Get fiscal year record
        fy = (
            self.db.query(FiscalYear)
            .filter(
                FiscalYear.city_id == city_id,
                FiscalYear.year == fiscal_year,
            )
            .first()
        )

        if not fy:
            return {}

        # Get latest risk score
        risk_score = (
            self.db.query(RiskScore)
            .filter(
                RiskScore.fiscal_year_id == fy.id,
                RiskScore.is_deleted == False,
            )
            .order_by(RiskScore.calculation_date.desc())
            .first()
        )

        if not risk_score:
            return {}

        return {
            "overall_score": float(risk_score.overall_score),
            "risk_level": risk_score.risk_level,
            "liquidity_score": float(risk_score.liquidity_score),
            "structural_balance_score": float(risk_score.structural_balance_score),
            "pension_stress_score": float(risk_score.pension_stress_score),
            "revenue_sustainability_score": float(risk_score.revenue_sustainability_score),
            "debt_burden_score": float(risk_score.debt_burden_score),
            "calculation_date": risk_score.calculation_date,
            "data_completeness_percent": float(risk_score.data_completeness_percent),
        }
