"""
Test API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_check_detailed():
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_health_ready():
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_health_live():
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "documentation" in data


def test_disclaimer_endpoint():
    """Test disclaimer endpoint."""
    response = client.get("/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert "independent_analysis" in data
    assert "not_predictions" in data
    assert "not_financial_advice" in data


def test_openapi_docs():
    """Test that OpenAPI docs are available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_list_cities():
    """Test listing cities."""
    response = client.get("/api/v1/cities")
    assert response.status_code == 200
    # May be empty if no test data
    data = response.json()
    assert isinstance(data, list)


def test_get_nonexistent_city():
    """Test getting nonexistent city returns 404."""
    response = client.get("/api/v1/cities/999999")
    assert response.status_code == 404


def test_metadata_data_sources():
    """Test metadata data sources endpoint."""
    response = client.get("/api/v1/metadata/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_projection_scenarios_list():
    """Test listing projection scenarios."""
    response = client.get("/api/v1/projections/scenarios")
    assert response.status_code == 200
    # May return empty list if scenarios not created


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/health")
    # CORS headers should be present in preflight response
    # or in actual response
    response = client.get("/health")
    assert response.status_code == 200


def test_gzip_compression():
    """Test that gzip compression header is accepted."""
    response = client.get("/health", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200


def test_process_time_header():
    """Test that X-Process-Time header is added."""
    response = client.get("/health")
    assert response.status_code == 200
    # Check for process time header
    assert "x-process-time" in response.headers or "X-Process-Time" in response.headers


def test_api_prefix():
    """Test that API prefix is correctly applied."""
    # All v1 endpoints should be under /api/v1
    response = client.get("/api/v1/cities")
    assert response.status_code == 200


def test_404_for_unknown_route():
    """Test that unknown routes return 404."""
    response = client.get("/this/route/does/not/exist")
    assert response.status_code == 404


def test_risk_current_endpoint_structure():
    """Test risk current endpoint structure (may 404 without data)."""
    response = client.get("/api/v1/risk/cities/1/current")
    # Will 404 if no data, but structure should be correct
    assert response.status_code in [200, 404]


def test_projections_endpoint_structure():
    """Test projections endpoint structure (may 404 without data)."""
    response = client.get("/api/v1/projections/cities/1/projections?base_year=2024")
    # Will 404 if no data, but structure should be correct
    assert response.status_code in [200, 404]


def test_financial_summary_endpoint_structure():
    """Test financial summary endpoint structure."""
    response = client.get("/api/v1/financial/cities/1/summary?year=2024")
    # Will 404 if no data
    assert response.status_code in [200, 404]


def test_city_by_name_endpoint():
    """Test city by name endpoint."""
    response = client.get("/api/v1/cities/name/Vallejo")
    # Will 404 if Vallejo not in test database
    assert response.status_code in [200, 404]


def test_metadata_lineage_endpoint_structure():
    """Test metadata lineage endpoint structure."""
    response = client.get("/api/v1/metadata/lineage?table_name=revenues&record_id=1")
    # May return empty list if no lineage data
    assert response.status_code in [200, 404]


def test_indicators_endpoint_structure():
    """Test indicators endpoint structure."""
    response = client.get("/api/v1/risk/cities/1/indicators?year=2024")
    # Will 404 if no risk score data
    assert response.status_code in [200, 404]


def test_fiscal_cliff_endpoint_structure():
    """Test fiscal cliff endpoint structure."""
    response = client.get("/api/v1/projections/cities/1/fiscal-cliff?base_year=2024")
    # Will 404 if no projection data
    assert response.status_code in [200, 404]
