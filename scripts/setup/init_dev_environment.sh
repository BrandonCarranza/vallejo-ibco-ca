#!/bin/bash
#
# IBCo Vallejo Console - Development Environment Initialization
#
# This script sets up the complete development environment including:
# - Python dependencies via Poetry
# - Environment configuration
# - Data directories
# - Docker services (PostgreSQL, Redis, Metabase, pgAdmin)
# - Git hooks
#
# Prerequisites:
# - Poetry: https://python-poetry.org/docs/#installation
# - Docker: https://docs.docker.com/get-docker/
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  IBCo Vallejo Console - Development Setup             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Main setup
print_header

# Check if Poetry is installed
print_step "Checking for Poetry..."
if ! command -v poetry &> /dev/null; then
    print_error "Poetry not found!"
    echo "Please install Poetry from: https://python-poetry.org/docs/#installation"
    echo ""
    echo "Quick install:"
    echo "  curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi
print_success "Poetry found: $(poetry --version)"
echo ""

# Check if Docker is installed and running
print_step "Checking for Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker not found!"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker found: $(docker --version)"

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    print_error "Docker daemon is not running!"
    echo "Please start Docker and try again."
    exit 1
fi
print_success "Docker daemon is running"
echo ""

# Check Python version
print_step "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.11 or higher is required (found: Python $PYTHON_VERSION)"
    exit 1
fi
print_success "Python version: $(python3 --version)"
echo ""

# Install Python dependencies
print_step "Installing Python dependencies with Poetry..."
poetry install --no-interaction
print_success "Dependencies installed"
echo ""

# Create .env file if it doesn't exist
print_step "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"
    print_warning "Please review and update .env with your configuration"
else
    print_success ".env file already exists"
fi
echo ""

# Create data directories
print_step "Creating data directories..."
mkdir -p data/raw/cafr
mkdir -p data/raw/calpers
mkdir -p data/raw/state_controller
mkdir -p data/processed
mkdir -p data/archive
mkdir -p data/samples
print_success "Data directories created"
echo ""

# Start Docker services
print_step "Starting Docker services..."
docker compose up -d postgres redis metabase pgadmin
print_success "Docker services started"
echo ""

# Wait for PostgreSQL to be ready
print_step "Waiting for PostgreSQL to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30
until docker compose exec -T postgres pg_isready -U ibco -d ibco_dev > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "PostgreSQL failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo ""
print_success "PostgreSQL is ready"
echo ""

# Wait for Redis to be ready
print_step "Waiting for Redis to be ready..."
RETRY_COUNT=0
until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Redis failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo ""
print_success "Redis is ready"
echo ""

# Install git hooks
print_step "Installing git hooks..."
if [ -f scripts/setup/install_git_hooks.sh ]; then
    bash scripts/setup/install_git_hooks.sh > /dev/null 2>&1
    print_success "Git hooks installed"
else
    print_warning "Git hooks script not found, skipping..."
fi
echo ""

# Setup complete
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Development Environment Setup Complete!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Print next steps
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Review and update configuration:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Verify environment:"
echo "   ${YELLOW}poetry run python scripts/setup/verify_environment.py${NC}"
echo ""
echo "3. Initialize database (when ready):"
echo "   ${YELLOW}poetry run alembic upgrade head${NC}"
echo ""
echo "4. Run tests:"
echo "   ${YELLOW}poetry run pytest${NC}"
echo ""
echo "5. Start development API server:"
echo "   ${YELLOW}poetry run uvicorn src.api.main:app --reload${NC}"
echo ""

# Print service URLs
echo -e "${BLUE}Services Running:${NC}"
echo ""
echo "  PostgreSQL:  localhost:5432"
echo "  Redis:       localhost:6379"
echo "  Metabase:    http://localhost:3000"
echo "  pgAdmin:     http://localhost:5050"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo ""
echo "  Stop services:    ${YELLOW}docker compose down${NC}"
echo "  View logs:        ${YELLOW}docker compose logs -f${NC}"
echo "  Run shell:        ${YELLOW}poetry shell${NC}"
echo "  Format code:      ${YELLOW}poetry run black src/ tests/${NC}"
echo ""

echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
