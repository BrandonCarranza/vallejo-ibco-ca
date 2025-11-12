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
from src.api.v1.routes import health, cities, financial, risk, projections, metadata, lineage, decisions
from src.api.v1.routes.admin import quality_dashboard, tokens, refresh_status, validation_workflow, decisions as admin_decisions
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


# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "Root",
        "description": "API root endpoints including health checks and disclaimer information.",
    },
    {
        "name": "Health",
        "description": "System health monitoring endpoints for checking API availability and database connectivity.",
    },
    {
        "name": "Cities",
        "description": "Browse and search California municipalities. Returns city information including population, location, and data availability.",
    },
    {
        "name": "Risk Scores",
        "description": (
            "Fiscal risk indicators composite scores (0-100) calculated from multiple financial ratios. "
            "Higher scores indicate greater fiscal stress. Categories: Pension Stress, Structural Balance, "
            "Liquidity & Reserves, Revenue Sustainability, and Debt Burden. "
            "**Note:** These are stress indicators, not bankruptcy predictions."
        ),
    },
    {
        "name": "Financial Data",
        "description": (
            "Municipal financial data from Comprehensive Annual Financial Reports (CAFRs). "
            "Includes revenues, expenditures, fund balances, and debt obligations. "
            "All data manually entered with complete audit trail."
        ),
    },
    {
        "name": "Projections",
        "description": (
            "10-year fiscal projections under multiple scenarios (base, optimistic, pessimistic). "
            "Includes fiscal cliff analysis showing when reserves may be exhausted. "
            "Projections use trend-based models with configurable assumptions."
        ),
    },
    {
        "name": "Metadata",
        "description": "API metadata including available indicators, scenarios, data coverage, and system information.",
    },
    {
        "name": "Data Lineage",
        "description": (
            "Complete data provenance tracking. Every data point links back to source documents "
            "(CAFR, actuarial reports, etc.) with page numbers, upload timestamps, and change history. "
            "Enables full transparency and reproducibility."
        ),
    },
    {
        "name": "Decisions",
        "description": (
            "City council decisions and ballot measures with fiscal impact tracking. "
            "Includes predicted fiscal impacts and actual outcomes, enabling prediction accuracy analysis. "
            "Tracks decisions like tax increases, bond issuances, labor contracts, and budget amendments. "
            "Transparent tracking of predictions vs. actuals builds institutional credibility."
        ),
    },
    {
        "name": "Admin",
        "description": "**Internal use only.** Administrative endpoints for data management, validation workflows, and token management. Requires authentication.",
        "externalDocs": {
            "description": "Admin Guide",
            "url": "https://docs.ibco-ca.us/admin-guide"
        }
    },
    {
        "name": "Data Quality",
        "description": "**Internal use only.** Data quality monitoring dashboards and validation status. Requires authentication.",
    },
    {
        "name": "Token Management",
        "description": "**Internal use only.** API token generation and management for authenticated access. Requires authentication.",
    },
    {
        "name": "Data Refresh",
        "description": "**Internal use only.** Data refresh orchestration status and controls. Requires authentication.",
    },
    {
        "name": "Validation",
        "description": "**Internal use only.** Manual review and validation workflow for data entry. Requires authentication.",
    },
]

# Create FastAPI app
app = FastAPI(
    title="IBCo Vallejo Console API",
    description=(
        "# Independent Budget & Oversight Console\n\n"
        "Municipal fiscal transparency API providing access to California city financial data, "
        "pension obligations, risk scores, and fiscal projections.\n\n"
        "## Key Features\n\n"
        "- **Complete Transparency**: All data manually entered from official documents with full audit trail\n"
        "- **Risk Indicators**: Composite fiscal stress scores across 5 categories\n"
        "- **10-Year Projections**: Multi-scenario forecasts with fiscal cliff analysis\n"
        "- **Data Lineage**: Every data point links to source document with page number\n"
        "- **Public Access**: No authentication required for public endpoints (rate limited)\n\n"
        "## Getting Started\n\n"
        "1. Browse available cities: `GET /api/v1/cities?state=CA`\n"
        "2. Get current risk score: `GET /api/v1/risk/cities/{city_id}/current`\n"
        "3. View fiscal projections: `GET /api/v1/projections/cities/{city_id}/fiscal-cliff`\n\n"
        "## Rate Limits\n\n"
        "- **Public tier**: 100 requests/hour (no authentication)\n"
        "- **Researcher tier**: 1000 requests/hour (API token required)\n"
        "- Contact data@ibco-ca.us for API token\n\n"
        "## Important Notice\n\n"
        "This is **independent civic analysis**, not official government data. "
        "Risk scores are stress indicators, not bankruptcy predictions. "
        "See `/disclaimer` for full legal disclaimer.\n\n"
        "## Documentation\n\n"
        "- **API Usage Guide**: [API_USAGE_GUIDE.md](https://github.com/your-org/vallejo-ibco-ca/blob/main/docs/API_USAGE_GUIDE.md)\n"
        "- **Developer Guide**: [DEVELOPER_GUIDE.md](https://github.com/your-org/vallejo-ibco-ca/blob/main/docs/DEVELOPER_GUIDE.md)\n"
        "- **Code Examples**: [examples/](https://github.com/your-org/vallejo-ibco-ca/tree/main/examples)\n"
    ),
    version="1.0.0",
    contact={
        "name": "IBCo Data Team",
        "email": "data@ibco-ca.us",
        "url": "https://ibco-ca.us",
    },
    license_info={
        "name": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    terms_of_service="https://docs.ibco-ca.us/legal/terms-of-service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
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
app.include_router(decisions.router, prefix=settings.api_prefix, tags=["Decisions"])

# Admin routers (internal use only)
app.include_router(quality_dashboard.router, prefix=settings.api_prefix, tags=["Admin", "Data Quality"])
app.include_router(tokens.router, prefix=f"{settings.api_prefix}/admin", tags=["Admin", "Token Management"])
app.include_router(refresh_status.router, prefix=settings.api_prefix, tags=["Admin", "Data Refresh"])
app.include_router(validation_workflow.router, prefix=settings.api_prefix, tags=["Admin", "Validation"])
app.include_router(admin_decisions.router, prefix=settings.api_prefix, tags=["Admin", "Decisions"])


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
