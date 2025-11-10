"""
Financial data endpoints.

Endpoints for revenues, expenditures, and fund balances.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/cities/{city_id}/financial/revenues")
async def get_revenues(city_id: int, fiscal_year: int | None = None):
    """
    Get revenue data for a city.

    Args:
        city_id: The ID of the city
        fiscal_year: Optional fiscal year filter

    Returns:
        Revenue data with budget vs actual, categories, etc.
    """
    # TODO: Implement revenue data retrieval
    return {
        "city_id": city_id,
        "fiscal_year": fiscal_year,
        "revenues": [],
        "message": "Endpoint not yet implemented"
    }


@router.get("/cities/{city_id}/financial/expenditures")
async def get_expenditures(city_id: int, fiscal_year: int | None = None):
    """
    Get expenditure data for a city.

    Args:
        city_id: The ID of the city
        fiscal_year: Optional fiscal year filter

    Returns:
        Expenditure data with budget vs actual, categories, departments, etc.
    """
    # TODO: Implement expenditure data retrieval
    return {
        "city_id": city_id,
        "fiscal_year": fiscal_year,
        "expenditures": [],
        "message": "Endpoint not yet implemented"
    }


@router.get("/cities/{city_id}/financial/fund-balance")
async def get_fund_balance(city_id: int, fiscal_year: int | None = None):
    """
    Get fund balance data for a city.

    Args:
        city_id: The ID of the city
        fiscal_year: Optional fiscal year filter

    Returns:
        Fund balance data with GASB 54 classifications and key ratios.
    """
    # TODO: Implement fund balance data retrieval
    return {
        "city_id": city_id,
        "fiscal_year": fiscal_year,
        "fund_balance": None,
        "message": "Endpoint not yet implemented"
    }
