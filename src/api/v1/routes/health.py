"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api.dependencies import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check.

    Returns API status without database check.
    """
    return {
        "status": "healthy",
        "service": "ibco-api",
        "version": "1.0.0"
    }


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """
    Health check with database connection test.

    Verifies database connectivity.
    """
    try:
        # Execute simple query to test connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        return {
            "status": "healthy",
            "service": "ibco-api",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ibco-api",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }
