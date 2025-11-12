"""
Public data lineage endpoints for transparency and accountability.

These endpoints allow anyone to trace any data point back to its source
documents with complete chain of custody. Critical for public trust and
forensic accountability.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.analytics.lineage_tracer import DataLineageTracer
from src.api.dependencies import get_db

router = APIRouter(prefix="/lineage", tags=["lineage"])


# Response models
class SourceDocumentResponse(BaseModel):
    """Source document information."""

    name: Optional[str] = None
    document_url: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    table_name: Optional[str] = None
    line_item: Optional[str] = None


class ExtractionInfoResponse(BaseModel):
    """Data extraction information."""

    method: Optional[str] = None
    extracted_by: Optional[str] = None
    extracted_at: Optional[str] = None
    notes: Optional[str] = None


class ValidationInfoResponse(BaseModel):
    """Data validation information."""

    validated: bool
    validated_by: Optional[str] = None
    validated_at: Optional[str] = None
    validation_notes: Optional[str] = None


class ConfidenceInfoResponse(BaseModel):
    """Confidence score information."""

    score: Optional[int] = None
    level: Optional[str] = None


class LineageNodeResponse(BaseModel):
    """Single node in lineage chain."""

    table_name: str
    record_id: int
    field_name: str
    value: Optional[str] = None
    source: SourceDocumentResponse
    extraction: ExtractionInfoResponse
    validation: ValidationInfoResponse
    confidence: ConfidenceInfoResponse


class DependencyResponse(BaseModel):
    """Dependency relationship between nodes."""

    parent: Dict[str, any]
    child: Dict[str, any]


class LineageChainResponse(BaseModel):
    """Complete lineage chain."""

    root: LineageNodeResponse
    nodes: List[LineageNodeResponse]
    dependencies: List[DependencyResponse]


@router.get("/data-point", response_model=LineageNodeResponse)
async def get_data_point_lineage(
    table: str = Query(..., description="Table name"),
    record_id: int = Query(..., description="Record ID"),
    field: str = Query(..., description="Field name"),
    db: Session = Depends(get_db),
):
    """
    Get complete lineage for a specific data point.

    **Public endpoint** - no authentication required.

    Traces the data point back to its source document with:
    - Source document URL, page number, section, table
    - Who entered the data and when
    - Who validated the data and when
    - Confidence score (0-100)

    This provides complete forensic accountability for every data point
    in the system.

    **Example:**
    ```
    GET /api/v1/lineage/data-point?table=revenues&record_id=42&field=amount
    ```
    """
    tracer = DataLineageTracer(db)

    node = tracer.trace_data_point(table, record_id, field)

    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"No lineage found for {table}.{record_id}.{field}",
        )

    return LineageNodeResponse(**node.to_dict())


@router.get("/risk-score/{fiscal_year_id}", response_model=LineageChainResponse)
async def get_risk_score_lineage(
    fiscal_year_id: int = Path(..., description="Fiscal year ID"),
    db: Session = Depends(get_db),
):
    """
    Get complete lineage chain for a risk score.

    **Public endpoint** - no authentication required.

    Traces the risk score through all constituent indicators down to
    the underlying source data (CAFRs, CalPERS valuations, etc.).

    Shows the complete evidence chain:
    - Risk Score → Indicators → Financial Data → Source Documents

    Each node includes:
    - Source document with clickable URL
    - Page numbers and table references
    - Transcriber and validator information
    - Timestamps for all operations
    - Confidence scores

    **Example:**
    ```
    GET /api/v1/lineage/risk-score/1
    ```
    """
    tracer = DataLineageTracer(db)

    try:
        chain = tracer.trace_risk_score(fiscal_year_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trace lineage: {str(e)}",
        )

    return LineageChainResponse(**chain.to_dict())


@router.get("/evidence-chain/{fiscal_year_id}")
async def get_evidence_chain_text(
    fiscal_year_id: int = Path(..., description="Fiscal year ID"),
    db: Session = Depends(get_db),
):
    """
    Get human-readable evidence chain for a risk score.

    **Public endpoint** - no authentication required.

    Returns a plain text representation of the complete evidence chain,
    suitable for printing or including in reports.

    **Example:**
    ```
    GET /api/v1/lineage/evidence-chain/1
    ```
    """
    tracer = DataLineageTracer(db)

    try:
        chain = tracer.trace_risk_score(fiscal_year_id)
        text = tracer.generate_evidence_chain_text(chain)

        return {
            "fiscal_year_id": fiscal_year_id,
            "evidence_chain": text,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate evidence chain: {str(e)}",
        )


@router.get("/audit-trail")
async def get_audit_trail_summary(
    city_id: int = Query(..., description="City ID"),
    db: Session = Depends(get_db),
):
    """
    Get summary of audit trail completeness for a city.

    **Public endpoint** - no authentication required.

    Shows how much of the city's data has complete lineage tracking:
    - Percentage of data points with source documents
    - Percentage validated
    - Average confidence scores
    - Data completeness by fiscal year

    This provides transparency into the quality and traceability of
    the data in the system.

    **Example:**
    ```
    GET /api/v1/lineage/audit-trail?city_id=1
    ```
    """
    from src.database.models.core import DataLineage, FiscalYear

    # Get all fiscal years for city
    fiscal_years = (
        db.query(FiscalYear)
        .filter(FiscalYear.city_id == city_id)
        .order_by(FiscalYear.year.desc())
        .all()
    )

    summary = {
        "city_id": city_id,
        "fiscal_years": [],
    }

    for fy in fiscal_years:
        # Count lineage records for this fiscal year
        # Note: This is simplified - in production, you'd join with actual data tables
        lineage_count = (
            db.query(DataLineage)
            .filter(DataLineage.table_name == "fiscal_years")
            .filter(DataLineage.record_id == fy.id)
            .count()
        )

        validated_count = (
            db.query(DataLineage)
            .filter(DataLineage.table_name == "fiscal_years")
            .filter(DataLineage.record_id == fy.id)
            .filter(DataLineage.validated == True)
            .count()
        )

        # Get average confidence score
        from sqlalchemy import func

        avg_confidence = (
            db.query(func.avg(DataLineage.confidence_score))
            .filter(DataLineage.table_name == "fiscal_years")
            .filter(DataLineage.record_id == fy.id)
            .filter(DataLineage.confidence_score != None)
            .scalar()
        )

        summary["fiscal_years"].append({
            "year": fy.year,
            "lineage_records": lineage_count,
            "validated_records": validated_count,
            "validation_rate": (
                (validated_count / lineage_count * 100) if lineage_count > 0 else 0
            ),
            "average_confidence": float(avg_confidence) if avg_confidence else None,
            "cafr_available": fy.cafr_available,
            "calpers_available": fy.calpers_valuation_available,
            "data_quality_score": fy.data_quality_score,
        })

    return summary
