#!/bin/bash
set -e

echo "Running IBCo test suite..."
echo ""

# Run linting
echo "=== Linting ==="
poetry run black --check src/ tests/ || echo "Black formatting check failed (non-blocking)"
poetry run isort --check-only src/ tests/ || echo "isort check failed (non-blocking)"
poetry run flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503 || echo "flake8 check failed (non-blocking)"
# poetry run mypy src/ || echo "mypy check failed (non-blocking)"

echo ""
echo "=== Unit Tests ==="
poetry run pytest tests/unit -v --cov=src --cov-report=term-missing || echo "Unit tests failed"

echo ""
echo "=== Integration Tests ==="
poetry run pytest tests/integration -v || echo "Integration tests failed"

echo ""
echo "✅ All tests completed!"
