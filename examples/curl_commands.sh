#!/bin/bash
# IBCo API Curl Examples
#
# This script demonstrates how to use the IBCo API with curl.
# All endpoints are public and do not require authentication.
#
# Usage:
#   ./curl_commands.sh
#
# Or run individual commands:
#   curl "https://api.ibco-ca.us/api/v1/cities?state=CA"

set -e

# Configuration
BASE_URL="${IBCO_API_URL:-https://api.ibco-ca.us/api/v1}"
CITY_ID="${CITY_ID:-1}"  # Default to Vallejo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print section headers
print_header() {
    echo ""
    echo "============================================================"
    echo -e "${BLUE}$1${NC}"
    echo "============================================================"
}

# Helper function to print request info
print_request() {
    echo -e "${YELLOW}Request:${NC} $1"
}

# Helper function to pretty print JSON
pretty_json() {
    if command -v jq &> /dev/null; then
        jq '.'
    else
        cat
    fi
}

# ==============================================================================
# 1. Cities
# ==============================================================================

print_header "1. Get All Cities in California"
print_request "GET ${BASE_URL}/cities?state=CA"
curl -s "${BASE_URL}/cities?state=CA" | pretty_json

print_header "2. Search Cities by Name"
print_request "GET ${BASE_URL}/cities?search=vallejo"
curl -s "${BASE_URL}/cities?search=vallejo" | pretty_json

print_header "3. Get Paginated Cities"
print_request "GET ${BASE_URL}/cities?page=1&page_size=5"
curl -s "${BASE_URL}/cities?page=1&page_size=5" | pretty_json

# ==============================================================================
# 2. Risk Scores
# ==============================================================================

print_header "4. Get Current Risk Score for City"
print_request "GET ${BASE_URL}/risk/cities/${CITY_ID}/current"
curl -s "${BASE_URL}/risk/cities/${CITY_ID}/current" | pretty_json

print_header "5. Get Risk Score History"
print_request "GET ${BASE_URL}/risk/cities/${CITY_ID}/history?start_year=2020&end_year=2024"
curl -s "${BASE_URL}/risk/cities/${CITY_ID}/history?start_year=2020&end_year=2024" | pretty_json

print_header "6. Get Risk Score Breakdown by Category"
print_request "GET ${BASE_URL}/risk/cities/${CITY_ID}/current"
curl -s "${BASE_URL}/risk/cities/${CITY_ID}/current" \
    | jq '{
        city: .city_name,
        overall_score: .overall_score,
        risk_level: .risk_level,
        categories: .category_scores
    }' 2>/dev/null || echo "(Install jq for formatted output)"

# ==============================================================================
# 3. Fiscal Projections
# ==============================================================================

print_header "7. Get Fiscal Cliff Analysis (Base Scenario)"
print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=base"
curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=base" | pretty_json

print_header "8. Get Fiscal Cliff Analysis (Pessimistic Scenario)"
print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=pessimistic"
curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=pessimistic" | pretty_json

print_header "9. Get All Projection Scenarios"
print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/scenarios"
curl -s "${BASE_URL}/projections/cities/${CITY_ID}/scenarios" | pretty_json

print_header "10. Get 10-Year Revenue Projections"
print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/revenue?years=10&scenario=base"
curl -s "${BASE_URL}/projections/cities/${CITY_ID}/revenue?years=10&scenario=base" | pretty_json

print_header "11. Get 10-Year Expenditure Projections"
print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/expenditures?years=10&scenario=base"
curl -s "${BASE_URL}/projections/cities/${CITY_ID}/expenditures?years=10&scenario=base" | pretty_json

# ==============================================================================
# 4. Financial Data
# ==============================================================================

print_header "12. Get Revenue by Year"
print_request "GET ${BASE_URL}/financial/cities/${CITY_ID}/revenue?fiscal_year=2024"
curl -s "${BASE_URL}/financial/cities/${CITY_ID}/revenue?fiscal_year=2024" | pretty_json

print_header "13. Get Expenditures by Year"
print_request "GET ${BASE_URL}/financial/cities/${CITY_ID}/expenditures?fiscal_year=2024"
curl -s "${BASE_URL}/financial/cities/${CITY_ID}/expenditures?fiscal_year=2024" | pretty_json

print_header "14. Get Fund Balances"
print_request "GET ${BASE_URL}/financial/cities/${CITY_ID}/fund-balances?fiscal_year=2024"
curl -s "${BASE_URL}/financial/cities/${CITY_ID}/fund-balances?fiscal_year=2024" | pretty_json

print_header "15. Get Multi-Year Revenue Trends"
print_request "GET ${BASE_URL}/financial/cities/${CITY_ID}/revenue?start_year=2020&end_year=2024"
curl -s "${BASE_URL}/financial/cities/${CITY_ID}/revenue?start_year=2020&end_year=2024" | pretty_json

# ==============================================================================
# 5. Pension Data
# ==============================================================================

print_header "16. Get Pension Status"
print_request "GET ${BASE_URL}/pensions/cities/${CITY_ID}/status?fiscal_year=2024"
curl -s "${BASE_URL}/pensions/cities/${CITY_ID}/status?fiscal_year=2024" | pretty_json

print_header "17. Get Unfunded Liability Trends"
print_request "GET ${BASE_URL}/pensions/cities/${CITY_ID}/ual-trends?start_year=2019&end_year=2024"
curl -s "${BASE_URL}/pensions/cities/${CITY_ID}/ual-trends?start_year=2019&end_year=2024" | pretty_json

print_header "18. Get Pension Contribution Burden"
print_request "GET ${BASE_URL}/pensions/cities/${CITY_ID}/contribution-burden?fiscal_year=2024"
curl -s "${BASE_URL}/pensions/cities/${CITY_ID}/contribution-burden?fiscal_year=2024" | pretty_json

print_header "19. Get All Pension Plans for City"
print_request "GET ${BASE_URL}/pensions/cities/${CITY_ID}/plans"
curl -s "${BASE_URL}/pensions/cities/${CITY_ID}/plans" | pretty_json

# ==============================================================================
# 6. Data Lineage & Audit Trail
# ==============================================================================

print_header "20. Get Data Lineage for Risk Score"
print_request "GET ${BASE_URL}/lineage/risk-scores/${CITY_ID}/2024"
curl -s "${BASE_URL}/lineage/risk-scores/${CITY_ID}/2024" | pretty_json

print_header "21. Get Source Documents"
print_request "GET ${BASE_URL}/lineage/cities/${CITY_ID}/sources?fiscal_year=2024"
curl -s "${BASE_URL}/lineage/cities/${CITY_ID}/sources?fiscal_year=2024" | pretty_json

print_header "22. Get Audit Trail for Data Point"
print_request "GET ${BASE_URL}/lineage/audit-trail?entity_type=revenue&entity_id=1"
curl -s "${BASE_URL}/lineage/audit-trail?entity_type=revenue&entity_id=1" | pretty_json

# ==============================================================================
# 7. Advanced Queries with jq Processing
# ==============================================================================

if command -v jq &> /dev/null; then
    print_header "23. Extract Just Risk Level and Score"
    print_request "GET ${BASE_URL}/risk/cities/${CITY_ID}/current | jq"
    curl -s "${BASE_URL}/risk/cities/${CITY_ID}/current" \
        | jq '{
            city: .city_name,
            risk_level: .risk_level,
            overall_score: .overall_score,
            fiscal_year: .fiscal_year
        }'

    print_header "24. Get Top 3 Risk Categories"
    print_request "GET ${BASE_URL}/risk/cities/${CITY_ID}/current | jq"
    curl -s "${BASE_URL}/risk/cities/${CITY_ID}/current" \
        | jq '.category_scores | to_entries | sort_by(.value) | reverse | .[0:3] | map({category: .key, score: .value})'

    print_header "25. Check if Fiscal Cliff Exists"
    print_request "GET ${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=base | jq"
    curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=base" \
        | jq 'if .has_fiscal_cliff then "⚠ FISCAL CLIFF in FY\(.fiscal_cliff_year) (\(.years_until_cliff) years)" else "✓ No fiscal cliff projected" end' -r

    print_header "26. Calculate Average Funded Ratio"
    print_request "GET ${BASE_URL}/pensions/cities/${CITY_ID}/status?fiscal_year=2024 | jq"
    curl -s "${BASE_URL}/pensions/cities/${CITY_ID}/status?fiscal_year=2024" \
        | jq '{
            city: .city_name,
            avg_funded_ratio: (.avg_funded_ratio * 100 | round / 100),
            total_ual_millions: (.total_ual / 1000000 | round),
            plan_count: (.plans | length)
        }'

    print_header "27. Compare Scenarios Side-by-Side"
    print_request "Multiple scenario requests combined"
    echo "{"
    echo "  \"base\": $(curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=base" | jq -c '{has_cliff: .has_fiscal_cliff, cliff_year: .fiscal_cliff_year}'),"
    echo "  \"optimistic\": $(curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=optimistic" | jq -c '{has_cliff: .has_fiscal_cliff, cliff_year: .fiscal_cliff_year}'),"
    echo "  \"pessimistic\": $(curl -s "${BASE_URL}/projections/cities/${CITY_ID}/fiscal-cliff?scenario=pessimistic" | jq -c '{has_cliff: .has_fiscal_cliff, cliff_year: .fiscal_cliff_year}')"
    echo "}" | jq '.'
else
    echo ""
    echo -e "${YELLOW}Note: Install 'jq' for advanced JSON processing examples${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    echo "  RHEL/CentOS: sudo yum install jq"
fi

# ==============================================================================
# 8. Error Handling Examples
# ==============================================================================

print_header "28. Handle 404 - City Not Found"
print_request "GET ${BASE_URL}/risk/cities/99999/current"
RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/risk/cities/99999/current")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "HTTP Status: $HTTP_CODE"
echo "$BODY" | pretty_json

print_header "29. Handle Rate Limiting (429)"
echo "Making rapid requests to trigger rate limit..."
for i in {1..105}; do
    curl -s -w "\n%{http_code}" "${BASE_URL}/cities?page=$i&page_size=1" -o /dev/null &
done
wait
echo "Check for 429 responses (rate limit exceeded)"

print_header "30. Check API Health"
print_request "GET ${BASE_URL}/health"
curl -s "${BASE_URL}/health" | pretty_json

# ==============================================================================
# Summary
# ==============================================================================

print_header "Examples Complete!"
echo ""
echo "Tips:"
echo "  1. Set custom base URL: export IBCO_API_URL=http://localhost:8000/api/v1"
echo "  2. Query different city: export CITY_ID=2"
echo "  3. Save response to file: curl ... > output.json"
echo "  4. Add verbose output: curl -v ..."
echo "  5. Show only headers: curl -I ..."
echo "  6. Follow redirects: curl -L ..."
echo ""
echo "For more examples, see: docs/API_USAGE_GUIDE.md"
echo ""
