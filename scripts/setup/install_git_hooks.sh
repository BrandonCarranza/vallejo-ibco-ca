#!/bin/bash
# Install git pre-commit hook for code quality checks
# This script creates a pre-commit hook that runs formatting, linting, and tests

set -e

echo "Installing git pre-commit hook..."

# Create the pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Git pre-commit hook for code quality
# Runs: black, isort, flake8, mypy, and unit tests

set -e

echo "🔍 Running pre-commit checks..."
echo ""

# Check if running in CI (skip hooks in CI)
if [ -n "$CI" ]; then
    echo "Running in CI, skipping pre-commit hooks"
    exit 0
fi

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "⚠️  Poetry not found. Install from: https://python-poetry.org/"
    echo "Skipping pre-commit checks..."
    exit 0
fi

# Track if any checks fail
FAILED=0

# 1. Check code formatting with Black
echo "📝 Checking code formatting (black)..."
if ! poetry run black --check src/ tests/ scripts/ 2>&1; then
    echo "❌ Black formatting check failed"
    echo "   Fix with: poetry run black src/ tests/ scripts/"
    FAILED=1
else
    echo "✅ Black formatting passed"
fi
echo ""

# 2. Check import sorting with isort
echo "📦 Checking import sorting (isort)..."
if ! poetry run isort --check-only src/ tests/ scripts/ 2>&1; then
    echo "❌ isort check failed"
    echo "   Fix with: poetry run isort src/ tests/ scripts/"
    FAILED=1
else
    echo "✅ isort passed"
fi
echo ""

# 3. Run linter with flake8
echo "🔎 Running linter (flake8)..."
if ! poetry run flake8 src/ tests/ 2>&1; then
    echo "❌ flake8 found issues"
    FAILED=1
else
    echo "✅ flake8 passed"
fi
echo ""

# 4. Type checking with mypy
echo "🔍 Type checking (mypy)..."
if ! poetry run mypy src/ 2>&1; then
    echo "❌ mypy found type errors"
    FAILED=1
else
    echo "✅ mypy passed"
fi
echo ""

# 5. Run unit tests (fast tests only)
echo "🧪 Running unit tests..."
if ! poetry run pytest tests/unit -v --tb=short 2>&1; then
    echo "❌ Unit tests failed"
    FAILED=1
else
    echo "✅ Unit tests passed"
fi
echo ""

# Final result
echo "═══════════════════════════════════════"
if [ $FAILED -eq 1 ]; then
    echo "❌ Pre-commit checks FAILED"
    echo ""
    echo "Please fix the issues above before committing."
    echo "To bypass (not recommended): git commit --no-verify"
    exit 1
else
    echo "✅ All pre-commit checks PASSED"
    echo ""
    exit 0
fi
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo "✅ Git pre-commit hook installed successfully!"
echo ""
echo "The hook will run automatically before each commit."
echo "It checks:"
echo "  - Code formatting (black)"
echo "  - Import sorting (isort)"
echo "  - Linting (flake8)"
echo "  - Type checking (mypy)"
echo "  - Unit tests"
echo ""
echo "To bypass the hook (not recommended): git commit --no-verify"
