"""
Financial data endpoints.

Retrieve revenues, expenditures, fund balances, and pension data.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.api.dependencies import get_db
from src.api.v1.schemas.financial import (
    RevenueResponse,
    ExpenditureResponse,
    FundBalanceResponse,
    PensionPlanResponse,
    FinancialSummaryResponse
)
from src.database.models.core import City, FiscalYear
from src.database.models.financial import Revenue, Expenditure, FundBalance
from src.database.models.pensions import PensionPlan

router = APIRouter(prefix="/financial")


@router.get("/cities/{city_id}/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get financial summary for a city and year.

    Returns high-level overview:
    - Total revenues and expenditures
    - Fund balance
    - Pension summary
    - Operating surplus/deficit
    """
    # Get fiscal year
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(
            status_code=404,
            detail=f"Fiscal year {year} not found for city {city_id}"
        )

    # Calculate totals
    total_revenues = db.query(Revenue).filter(
        Revenue.fiscal_year_id == fiscal_year.id
    ).with_entities(func.sum(Revenue.actual_amount)).scalar() or 0

    total_expenditures = db.query(Expenditure).filter(
        Expenditure.fiscal_year_id == fiscal_year.id
    ).with_entities(func.sum(Expenditure.actual_amount)).scalar() or 0

    fund_balance = db.query(FundBalance).filter(
        FundBalance.fiscal_year_id == fiscal_year.id,
        FundBalance.fund_type == "General"
    ).first()

    pension_plans = db.query(PensionPlan).filter(
        PensionPlan.fiscal_year_id == fiscal_year.id
    ).all()

    total_pension_ual = sum(
        (p.net_pension_liability or 0) for p in pension_plans
    )

    return {
        "city_id": city_id,
        "city_name": fiscal_year.city.name,
        "fiscal_year": year,
        "total_revenues": float(total_revenues),
        "total_expenditures": float(total_expenditures),
        "operating_balance": float(total_revenues - total_expenditures),
        "fund_balance": float(fund_balance.total_fund_balance) if fund_balance else None,
        "fund_balance_ratio": float(fund_balance.fund_balance_ratio) if fund_balance else None,
        "total_pension_ual": float(total_pension_ual),
        "data_quality_score": fiscal_year.data_quality_score,
    }


@router.get("/cities/{city_id}/revenues", response_model=List[RevenueResponse])
async def get_revenues(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    db: Session = Depends(get_db)
):
    """
    Get detailed revenue data for a city and year.

    Query Parameters:
    - year: Fiscal year (required)
    - fund_type: Filter by fund type (General, Special, Enterprise)
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    query = db.query(Revenue).filter(Revenue.fiscal_year_id == fiscal_year.id)

    if fund_type:
        query = query.filter(Revenue.fund_type == fund_type)

    revenues = query.all()

    return revenues


@router.get("/cities/{city_id}/expenditures", response_model=List[ExpenditureResponse])
async def get_expenditures(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    db: Session = Depends(get_db)
):
    """
    Get detailed expenditure data for a city and year.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    query = db.query(Expenditure).filter(Expenditure.fiscal_year_id == fiscal_year.id)

    if fund_type:
        query = query.filter(Expenditure.fund_type == fund_type)

    expenditures = query.all()

    return expenditures


@router.get("/cities/{city_id}/pensions", response_model=List[PensionPlanResponse])
async def get_pension_plans(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get pension plan data for a city and year.

    Returns CalPERS pension liabilities, funded ratios, and contribution data.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    pension_plans = db.query(PensionPlan).filter(
        PensionPlan.fiscal_year_id == fiscal_year.id
    ).all()

    return pension_plans
