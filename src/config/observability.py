"""
Observability configuration for production monitoring.

Provides:
- Structured JSON logging with request tracking
- Prometheus metrics export
- Alert threshold definitions
- Performance monitoring
"""

import time
from contextvars import ContextVar
from typing import Callable, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    make_asgi_app,
    multiprocess,
    CollectorRegistry,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Context variable for request ID
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


# =============================================================================
# Prometheus Metrics
# =============================================================================

# Application info
app_info = Info("ibco_application", "IBCo application information")
app_info.info(
    {
        "application": "ibco_vallejo_console",
        "version": "1.0.0",
        "environment": "production",
    }
)

# Request metrics
http_requests_total = Counter(
    "ibco_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "ibco_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "ibco_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Database metrics
database_queries_total = Counter(
    "ibco_database_queries_total",
    "Total database queries",
    ["query_type", "status"],
)

database_query_duration_seconds = Histogram(
    "ibco_database_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

database_connections_active = Gauge(
    "ibco_database_connections_active",
    "Number of active database connections",
)

database_connections_pool_size = Gauge(
    "ibco_database_connections_pool_size",
    "Database connection pool size",
)

database_connections_pool_overflow = Gauge(
    "ibco_database_connections_pool_overflow",
    "Database connection pool overflow count",
)

# Data freshness metrics
data_last_update_timestamp = Gauge(
    "ibco_data_last_update_timestamp",
    "Timestamp of last data update",
    ["data_type", "city"],
)

data_fiscal_years_available = Gauge(
    "ibco_data_fiscal_years_available",
    "Number of fiscal years available",
    ["city"],
)

# Risk score metrics
risk_score_current = Gauge(
    "ibco_risk_score_current",
    "Current risk score for city",
    ["city", "risk_level"],
)

risk_score_calculation_duration_seconds = Histogram(
    "ibco_risk_score_calculation_duration_seconds",
    "Risk score calculation duration in seconds",
    ["city"],
)

# Data quality metrics
data_quality_score = Gauge(
    "ibco_data_quality_score",
    "Data quality score (0-100)",
    ["city", "fiscal_year"],
)

data_quality_critical_issues = Gauge(
    "ibco_data_quality_critical_issues",
    "Number of critical data quality issues",
    ["city", "fiscal_year"],
)

# Error metrics
errors_total = Counter(
    "ibco_errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)

# API usage metrics
api_unique_users = Gauge(
    "ibco_api_unique_users_today",
    "Number of unique users today (by IP)",
)

api_response_size_bytes = Histogram(
    "ibco_api_response_size_bytes",
    "API response size in bytes",
    ["endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000),
)


# =============================================================================
# Alert Thresholds
# =============================================================================

ALERT_THRESHOLDS = {
    # API performance alerts
    "api_latency_p95_seconds": 1.0,  # Alert if p95 latency > 1 second
    "api_latency_p99_seconds": 2.5,  # Alert if p99 latency > 2.5 seconds
    "api_error_rate_percent": 1.0,  # Alert if error rate > 1%
    # Database alerts
    "database_connection_pool_percent": 90.0,  # Alert if pool > 90% full
    "database_query_slow_seconds": 1.0,  # Alert if query > 1 second
    "database_errors_per_minute": 5,  # Alert if > 5 DB errors/minute
    # Data freshness alerts
    "data_staleness_days": 180,  # Alert if no update in 6 months
    "data_quality_score_min": 95.0,  # Alert if quality score < 95%
    # System health alerts
    "memory_usage_percent": 85.0,  # Alert if memory > 85%
    "disk_usage_percent": 80.0,  # Alert if disk > 80%
}


# =============================================================================
# Request Tracking Middleware
# =============================================================================


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracking and observability.

    Adds:
    - Request ID to context and logs
    - Request duration tracking
    - Prometheus metrics
    - Structured logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability tracking."""
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request_id_var.set(request_id)

        # Extract request metadata
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("User-Agent", "unknown")
        client_ip = request.client.host if request.client else "unknown"

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=method, endpoint=path, status=response.status_code
            ).inc()

            http_request_duration_seconds.labels(method=method, endpoint=path).observe(
                duration
            )

            # Record response size
            if "content-length" in response.headers:
                size = int(response.headers["content-length"])
                api_response_size_bytes.labels(endpoint=path).observe(size)

            # Structured logging
            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                    "user_agent": user_agent,
                    "client_ip": client_ip,
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Check for slow requests
            if duration > ALERT_THRESHOLDS["api_latency_p95_seconds"]:
                logger.warning(
                    "Slow request detected",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_seconds": round(duration, 3),
                        "threshold_seconds": ALERT_THRESHOLDS["api_latency_p95_seconds"],
                    },
                )

            return response

        except Exception as exc:
            # Record error
            duration = time.time() - start_time
            error_type = type(exc).__name__

            errors_total.labels(error_type=error_type, endpoint=path).inc()

            logger.error(
                "Request failed with exception",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_seconds": round(duration, 3),
                    "error_type": error_type,
                    "user_agent": user_agent,
                    "client_ip": client_ip,
                },
            )

            # Re-raise exception
            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=path).dec()


# =============================================================================
# Database Monitoring
# =============================================================================


def track_database_query(query_type: str, duration: float, success: bool = True) -> None:
    """
    Track database query metrics.

    Args:
        query_type: Type of query (select, insert, update, delete)
        duration: Query duration in seconds
        success: Whether query succeeded
    """
    status = "success" if success else "error"

    database_queries_total.labels(query_type=query_type, status=status).inc()
    database_query_duration_seconds.labels(query_type=query_type).observe(duration)

    # Log slow queries
    if duration > ALERT_THRESHOLDS["database_query_slow_seconds"]:
        logger.warning(
            "Slow database query detected",
            extra={
                "query_type": query_type,
                "duration_seconds": round(duration, 3),
                "threshold_seconds": ALERT_THRESHOLDS["database_query_slow_seconds"],
            },
        )


def update_database_pool_metrics(active: int, pool_size: int, overflow: int) -> None:
    """
    Update database connection pool metrics.

    Args:
        active: Number of active connections
        pool_size: Total pool size
        overflow: Number of overflow connections
    """
    database_connections_active.set(active)
    database_connections_pool_size.set(pool_size)
    database_connections_pool_overflow.set(overflow)

    # Check pool utilization
    if pool_size > 0:
        utilization = (active / pool_size) * 100
        if utilization > ALERT_THRESHOLDS["database_connection_pool_percent"]:
            logger.warning(
                "Database connection pool near capacity",
                extra={
                    "active_connections": active,
                    "pool_size": pool_size,
                    "utilization_percent": round(utilization, 1),
                    "threshold_percent": ALERT_THRESHOLDS[
                        "database_connection_pool_percent"
                    ],
                },
            )


# =============================================================================
# Application Setup
# =============================================================================


def setup_observability(app: FastAPI) -> None:
    """
    Set up observability for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add request tracking middleware
    app.add_middleware(RequestTrackingMiddleware)

    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    logger.info("Observability configured: metrics available at /metrics")


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


# =============================================================================
# Health Check Utilities
# =============================================================================


def check_system_health() -> dict:
    """
    Check system health metrics.

    Returns:
        Dictionary of health check results
    """
    import psutil

    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Disk usage
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent

    # Check thresholds
    alerts = []
    if memory_percent > ALERT_THRESHOLDS["memory_usage_percent"]:
        alerts.append(
            f"High memory usage: {memory_percent:.1f}% (threshold: {ALERT_THRESHOLDS['memory_usage_percent']}%)"
        )

    if disk_percent > ALERT_THRESHOLDS["disk_usage_percent"]:
        alerts.append(
            f"High disk usage: {disk_percent:.1f}% (threshold: {ALERT_THRESHOLDS['disk_usage_percent']}%)"
        )

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "alerts": alerts,
        "healthy": len(alerts) == 0,
    }
