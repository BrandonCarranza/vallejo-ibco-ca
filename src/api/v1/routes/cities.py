"""
City endpoints.

Retrieve city information and associated fiscal years.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.city import CityResponse, CityDetailResponse, FiscalYearSummaryResponse
from src.database.models.core import City, FiscalYear

router = APIRouter(prefix="/cities")


@router.get("", response_model=List[CityResponse])
async def list_cities(
    state: Optional[str] = Query(None, description="Filter by state (e.g., CA)"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List all cities in the database.

    Query Parameters:
    - state: Filter by state code
    - is_active: Only show active cities (default: true)
    """
    query = db.query(City)

    if state:
        query = query.filter(City.state == state.upper())

    if is_active:
        query = query.filter(City.is_active == True)

    cities = query.order_by(City.name).all()

    return cities


@router.get("/{city_id}", response_model=CityDetailResponse)
async def get_city(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific city.

    Includes:
    - Basic city information
    - Demographics
    - Bankruptcy history (if applicable)
    - Available fiscal years
    """
    city = db.query(City).filter(City.id == city_id).first()

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    return city


@router.get("/{city_id}/fiscal-years", response_model=List[FiscalYearSummaryResponse])
async def get_city_fiscal_years(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all fiscal years for a city.

    Returns summary information for each year including data availability.
    """
    city = db.query(City).filter(City.id == city_id).first()

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    fiscal_years = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id
    ).order_by(desc(FiscalYear.year)).all()

    return fiscal_years


@router.get("/name/{city_name}", response_model=CityDetailResponse)
async def get_city_by_name(
    city_name: str,
    state: str = Query("CA", description="State code"),
    db: Session = Depends(get_db)
):
    """
    Get city by name.

    Useful for human-readable URLs like /cities/name/Vallejo
    """
    city = db.query(City).filter(
        City.name.ilike(city_name),  # Case-insensitive
        City.state == state.upper()
    ).first()

    if not city:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_name}' not found in {state}"
        )

    return city
