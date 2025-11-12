"""
FastAPI application main entry point.

This is the public interface to IBCo data.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from src.config.settings import settings
from src.config.logging_config import setup_logging, get_logger
from src.config.observability import setup_observability
from src.api.v1.routes import health, cities, financial, risk, projections, metadata, lineage
from src.api.v1.routes.admin import quality_dashboard, tokens, refresh_status
from src.api.middleware.authentication import AuthenticationMiddleware
from src.api.middleware.rate_limiting import RateLimitMiddleware

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info("IBCo API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("IBCo API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="IBCo Vallejo Console API",
    description=(
        "Independent Budget & Oversight Console - Municipal fiscal transparency API.\n\n"
        "Provides access to municipal financial data, pension obligations, risk scores, "
        "and financial projections.\n\n"
        "**Important:** This is independent civic analysis, not official city data. "
        "See /disclaimer for full disclaimer."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup observability (metrics, logging, monitoring)
setup_observability(app)

# API authentication and rate limiting middleware
# Note: Middleware is executed in reverse order of addition
# So we add rate limiting first (executes last) and authentication second (executes first)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthenticationMiddleware)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(cities.router, prefix=settings.api_prefix, tags=["Cities"])
app.include_router(financial.router, prefix=settings.api_prefix, tags=["Financial Data"])
app.include_router(risk.router, prefix=settings.api_prefix, tags=["Risk Scores"])
app.include_router(projections.router, prefix=settings.api_prefix, tags=["Projections"])
app.include_router(metadata.router, prefix=settings.api_prefix, tags=["Metadata"])
app.include_router(lineage.router, prefix=settings.api_prefix, tags=["Data Lineage"])

# Admin routers (internal use only)
app.include_router(quality_dashboard.router, prefix=settings.api_prefix, tags=["Admin", "Data Quality"])
app.include_router(tokens.router, prefix=f"{settings.api_prefix}/admin", tags=["Admin", "Token Management"])
app.include_router(refresh_status.router, prefix=settings.api_prefix, tags=["Admin", "Data Refresh"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": "IBCo Vallejo Console API",
        "version": "1.0.0",
        "description": "Municipal fiscal transparency API",
        "documentation": "/docs",
        "health": "/health",
        "disclaimer": "/disclaimer",
    }


# Disclaimer endpoint
@app.get("/disclaimer", tags=["Root"])
async def disclaimer():
    """
    Legal disclaimer.

    IMPORTANT: Read this before using the API.
    """
    return {
        "title": "IBCo Legal Disclaimer",
        "independent_analysis": (
            "IBCo is an independent civic transparency project. "
            "We are not affiliated with, endorsed by, or representative of any government agency."
        ),
        "no_warranties": (
            "This API and its data are provided 'AS IS' without warranty of any kind. "
            "Users are responsible for independently verifying information."
        ),
        "not_predictions": (
            "Risk scores are composite indicators of fiscal stress, NOT predictions of bankruptcy. "
            "They are relative assessments based on financial ratios, not probability forecasts."
        ),
        "not_financial_advice": (
            "Nothing in this API constitutes financial, investment, legal, or professional advice. "
            "For important decisions, consult qualified professionals."
        ),
        "data_corrections": (
            "We take accuracy seriously. Report errors to: data@ibco-ca.us"
        ),
        "full_disclaimer": "https://docs.ibco-ca.us/legal/disclaimer",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
