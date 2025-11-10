"""
Health check endpoints.
"""
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api.dependencies import get_db
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check.

    Returns 200 if service is alive.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "IBCo Vallejo Console API",
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check including dependencies.

    Checks:
    - API service
    - Database connectivity
    - Redis connectivity (if used)
    """
    checks = []
    overall_healthy = True

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks.append({
            "name": "database",
            "status": "healthy",
            "message": "PostgreSQL connection successful"
        })
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks.append({
            "name": "database",
            "status": "unhealthy",
            "message": str(e)
        })
        overall_healthy = False

    # Check Redis (if configured)
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks.append({
            "name": "redis",
            "status": "healthy",
            "message": "Redis connection successful"
        })
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks.append({
            "name": "redis",
            "status": "unhealthy",
            "message": str(e)
        })
        # Redis is optional, don't fail overall health

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "IBCo Vallejo Console API",
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": checks,
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness probe for Kubernetes/container orchestration.

    Returns 200 when ready to serve traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/container orchestration.

    Returns 200 if process is alive (doesn't check dependencies).
    """
    return {"status": "alive"}
