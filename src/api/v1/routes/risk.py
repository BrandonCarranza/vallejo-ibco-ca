"""
Risk score endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.risk import RiskScoreResponse, RiskIndicatorDetailResponse
from src.database.models.core import City, FiscalYear
from src.database.models.risk import RiskScore, RiskIndicatorScore
from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine

router = APIRouter(prefix="/risk")


@router.get("/cities/{city_id}/current", response_model=RiskScoreResponse)
async def get_current_risk_score(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the most recent risk score for a city.
    """
    # Get latest fiscal year with risk score
    risk_score = db.query(RiskScore).join(RiskScore.fiscal_year).filter(
        FiscalYear.city_id == city_id
    ).order_by(desc(FiscalYear.year)).first()

    if not risk_score:
        raise HTTPException(
            status_code=404,
            detail="No risk score found for this city"
        )

    return risk_score


@router.get("/cities/{city_id}/history", response_model=List[RiskScoreResponse])
async def get_risk_score_history(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get risk score history for a city.

    Returns all available risk scores in chronological order.
    """
    risk_scores = db.query(RiskScore).join(RiskScore.fiscal_year).filter(
        FiscalYear.city_id == city_id
    ).order_by(FiscalYear.year).all()

    if not risk_scores:
        raise HTTPException(
            status_code=404,
            detail="No risk scores found for this city"
        )

    return risk_scores


@router.get("/cities/{city_id}/year/{year}", response_model=RiskScoreResponse)
async def get_risk_score_for_year(
    city_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get risk score for a specific year.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    risk_score = db.query(RiskScore).filter(
        RiskScore.fiscal_year_id == fiscal_year.id
    ).first()

    if not risk_score:
        raise HTTPException(
            status_code=404,
            detail=f"No risk score found for {year}"
        )

    return risk_score


@router.post("/cities/{city_id}/calculate")
async def calculate_risk_score(
    city_id: int,
    year: int = Query(..., description="Fiscal year to calculate"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Calculate (or recalculate) risk score for a fiscal year.

    This endpoint triggers risk score calculation.
    Calculation happens in background if background_tasks provided.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    # Check if data is complete enough
    if not (fiscal_year.revenues_complete and fiscal_year.expenditures_complete):
        raise HTTPException(
            status_code=400,
            detail="Cannot calculate risk score: financial data incomplete"
        )

    def calculate():
        engine = RiskScoringEngine(db)
        risk_score = engine.calculate_risk_score(fiscal_year.id)
        db.add(risk_score)
        db.commit()

    if background_tasks:
        background_tasks.add_task(calculate)
        return {
            "status": "calculating",
            "message": "Risk score calculation started"
        }
    else:
        calculate()
        return {
            "status": "completed",
            "message": "Risk score calculated successfully"
        }


@router.get("/cities/{city_id}/indicators", response_model=List[RiskIndicatorDetailResponse])
async def get_risk_indicators(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get detailed breakdown of risk indicators for a year.

    Shows individual indicator values, scores, and thresholds.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    risk_score = db.query(RiskScore).filter(
        RiskScore.fiscal_year_id == fiscal_year.id
    ).first()

    if not risk_score:
        raise HTTPException(status_code=404, detail="Risk score not found")

    return risk_score.indicator_scores
