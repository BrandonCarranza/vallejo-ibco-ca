#!/bin/bash
#
# Metabase Setup Script for IBCo Vallejo Console
#
# Automates the complete Metabase setup process:
#   1. Starts Metabase container
#   2. Creates read-only database user
#   3. Waits for Metabase to be ready
#   4. Imports dashboard configurations
#   5. Enables public access
#
# Usage:
#   ./setup_metabase.sh
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - PostgreSQL database running with IBCo data
#   - Environment variables set in .env file:
#       - DATABASE_USER
#       - DATABASE_PASSWORD
#       - METABASE_ADMIN_PASSWORD
#       - METABASE_DB_PASSWORD
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo -e "${BLUE}=========================================="
echo -e "IBCo Metabase Setup"
echo -e "==========================================${NC}\n"

# =============================================================================
# 1. Check Prerequisites
# =============================================================================

echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with required variables:${NC}"
    echo "  DATABASE_USER=ibco_admin"
    echo "  DATABASE_PASSWORD=your_password"
    echo "  METABASE_ADMIN_PASSWORD=your_metabase_admin_password"
    echo "  METABASE_DB_PASSWORD=your_metabase_db_password"
    exit 1
fi

# Source .env file
source "$PROJECT_ROOT/.env"

# Check required environment variables
REQUIRED_VARS=(
    "DATABASE_USER"
    "DATABASE_PASSWORD"
    "METABASE_ADMIN_PASSWORD"
    "METABASE_DB_PASSWORD"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗ Missing required environment variable: $var${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ All prerequisites met${NC}\n"

# =============================================================================
# 2. Start Metabase
# =============================================================================

echo -e "${BLUE}[2/6] Starting Metabase container...${NC}"

cd "$PROJECT_ROOT"

# Check if Metabase is already running
if docker-compose -f docker-compose.prod.yml ps metabase | grep -q "Up"; then
    echo -e "${YELLOW}Metabase is already running${NC}"
else
    echo "Starting Metabase..."
    docker-compose -f docker-compose.prod.yml up -d metabase

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Metabase container started${NC}"
    else
        echo -e "${RED}✗ Failed to start Metabase${NC}"
        exit 1
    fi
fi

echo ""

# =============================================================================
# 3. Wait for PostgreSQL to be ready
# =============================================================================

echo -e "${BLUE}[3/6] Waiting for PostgreSQL to be ready...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

until docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "$DATABASE_USER" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}✗ PostgreSQL did not become ready in time${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo -e "\n${GREEN}✓ PostgreSQL is ready${NC}\n"

# =============================================================================
# 4. Create Read-Only Database User
# =============================================================================

echo -e "${BLUE}[4/6] Creating read-only database user for Metabase...${NC}"

# Check if metabase_readonly user already exists
USER_EXISTS=$(docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$DATABASE_USER" -d ibco_production -tAc \
    "SELECT 1 FROM pg_user WHERE usename='metabase_readonly'")

if [ "$USER_EXISTS" = "1" ]; then
    echo -e "${YELLOW}metabase_readonly user already exists${NC}"
    echo -n "Do you want to recreate it? (y/N) "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Skipping user creation"
    else
        # Run SQL script to create user
        docker-compose -f docker-compose.prod.yml exec -T postgres \
            psql -U "$DATABASE_USER" -d ibco_production \
            -v METABASE_DB_PASSWORD="$METABASE_DB_PASSWORD" \
            -f /dev/stdin < "$SCRIPT_DIR/create_readonly_user.sql"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Read-only user created/updated${NC}"
        else
            echo -e "${RED}✗ Failed to create read-only user${NC}"
            exit 1
        fi
    fi
else
    # Run SQL script to create user
    docker-compose -f docker-compose.prod.yml exec -T postgres \
        psql -U "$DATABASE_USER" -d ibco_production \
        -v METABASE_DB_PASSWORD="$METABASE_DB_PASSWORD" \
        -f /dev/stdin < "$SCRIPT_DIR/create_readonly_user.sql"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Read-only user created${NC}"
    else
        echo -e "${RED}✗ Failed to create read-only user${NC}"
        exit 1
    fi
fi

echo ""

# =============================================================================
# 5. Wait for Metabase to be ready
# =============================================================================

echo -e "${BLUE}[5/6] Waiting for Metabase to be ready (this may take 2-3 minutes)...${NC}"

METABASE_URL="http://localhost:3000"
MAX_RETRIES=60
RETRY_COUNT=0

until curl -s -f "$METABASE_URL/api/health" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}✗ Metabase did not become ready in time${NC}"
        echo "Check logs: docker-compose -f docker-compose.prod.yml logs metabase"
        exit 1
    fi
    echo -n "."
    sleep 3
done

echo -e "\n${GREEN}✓ Metabase is ready${NC}\n"

# =============================================================================
# 6. Import Dashboards
# =============================================================================

echo -e "${BLUE}[6/6] Importing dashboard configurations...${NC}"

# Check if Python and required packages are available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not installed${NC}"
    exit 1
fi

# Install required Python packages if not already installed
echo "Installing required Python packages..."
pip3 install -q requests 2>/dev/null || true

# Run import script
METABASE_ADMIN_EMAIL="${METABASE_ADMIN_EMAIL:-admin@ibco-ca.us}"

python3 "$SCRIPT_DIR/import_dashboards.py" \
    --metabase-url "$METABASE_URL" \
    --metabase-user "$METABASE_ADMIN_EMAIL" \
    --metabase-password "$METABASE_ADMIN_PASSWORD" \
    --dashboard-dir "$SCRIPT_DIR/../dashboards" \
    --enable-public-access

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dashboards imported successfully${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard import had some errors (see above)${NC}"
    echo -e "${YELLOW}You can manually import dashboards from the Metabase UI${NC}"
fi

echo ""

# =============================================================================
# Success Summary
# =============================================================================

echo -e "${GREEN}=========================================="
echo -e "Metabase Setup Complete!"
echo -e "==========================================${NC}\n"

echo -e "${BLUE}Access Information:${NC}"
echo -e "  Metabase Admin UI: ${GREEN}$METABASE_URL${NC}"
echo -e "  Admin Email: ${GREEN}$METABASE_ADMIN_EMAIL${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Open Metabase: $METABASE_URL"
echo "  2. Log in with admin credentials"
echo "  3. Verify dashboards imported correctly"
echo "  4. Configure database connection (if not auto-configured)"
echo "  5. Share public dashboard URLs with stakeholders"
echo ""

echo -e "${BLUE}Public Dashboards:${NC}"
echo "  • Vallejo Fiscal Overview"
echo "  • Pension Analysis"
echo "  • Fiscal Projections"
echo "  • Peer Comparison (requires multi-city data)"
echo ""

echo -e "${YELLOW}Important:${NC}"
echo "  - Public dashboards are accessible without authentication"
echo "  - All data is read-only (metabase_readonly user)"
echo "  - Dashboards auto-refresh every 24 hours"
echo "  - Data lineage is fully transparent and auditable"
echo ""

echo -e "${GREEN}Setup script completed successfully!${NC}"
