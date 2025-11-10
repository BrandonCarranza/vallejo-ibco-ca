"""
Data metadata and provenance endpoints.

Transparency about data sources and quality.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.common import DataSourceResponse, DataLineageResponse
from src.database.models.core import DataSource, DataLineage

router = APIRouter(prefix="/metadata")


@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all data sources.

    Provides transparency about where our data comes from.

    Query Parameters:
    - source_type: Filter by type (CAFR, CalPERS, StateController, Manual)
    """
    query = db.query(DataSource)

    if source_type:
        query = query.filter(DataSource.source_type == source_type)

    sources = query.order_by(DataSource.name).all()

    return sources


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details about a specific data source.
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return source


@router.get("/lineage", response_model=List[DataLineageResponse])
async def get_data_lineage(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Get data lineage for a specific record.

    Shows where a piece of data came from, how it was extracted, and validation status.

    Query Parameters:
    - table_name: The table name (e.g., "revenues", "pension_plans")
    - record_id: The record ID

    This endpoint enables full transparency and traceability.
    """
    lineage = db.query(DataLineage).filter(
        DataLineage.table_name == table_name,
        DataLineage.record_id == record_id
    ).order_by(desc(DataLineage.extracted_at)).all()

    if not lineage:
        raise HTTPException(
            status_code=404,
            detail=f"No lineage found for {table_name} record {record_id}"
        )

    return lineage


@router.get("/data-quality")
async def get_data_quality_summary(
    db: Session = Depends(get_db)
):
    """
    Overall data quality summary.

    Reports on:
    - Data completeness
    - Validation status
    - Last update times
    - Known issues
    """
    from src.database.models.core import FiscalYear

    # Get fiscal years with completeness flags
    fiscal_years = db.query(FiscalYear).order_by(desc(FiscalYear.year)).limit(10).all()

    summary = {
        "last_updated": datetime.utcnow().isoformat(),
        "fiscal_years_available": len(fiscal_years),
        "recent_years": []
    }

    for fy in fiscal_years:
        summary["recent_years"].append({
            "year": fy.year,
            "city": fy.city.name,
            "data_completeness": {
                "revenues": fy.revenues_complete,
                "expenditures": fy.expenditures_complete,
                "pensions": fy.pension_data_complete,
            },
            "data_quality_score": fy.data_quality_score,
            "cafr_available": fy.cafr_available,
            "cafr_url": fy.cafr_url,
        })

    return summary
