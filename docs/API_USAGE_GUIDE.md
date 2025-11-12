# IBCo API Usage Guide

Complete guide to using the IBCo Vallejo Console API for accessing municipal fiscal data.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Endpoints Reference](#endpoints-reference)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)

---

## Getting Started

The IBCo API provides programmatic access to transparent municipal fiscal data including:
- Revenue and expenditure data
- Pension obligations and funded status
- Fiscal risk scores and indicators
- 10-year fiscal projections
- Data lineage and audit trails

**Base URL:** `https://api.ibco-ca.us/api/v1`
**Documentation:** `https://api.ibco-ca.us/docs` (interactive Swagger UI)

### No Authentication Required

Basic queries do not require authentication. You can start making requests immediately:

```bash
curl https://api.ibco-ca.us/api/v1/cities
```

### Quick Start Example

Get the latest risk score for Vallejo:

```bash
curl https://api.ibco-ca.us/api/v1/risk/cities/1/current
```

Response:
```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "fiscal_year": 2024,
  "overall_score": 68.5,
  "risk_level": "high",
  "category_scores": {
    "liquidity": 72.0,
    "structural_balance": 65.0,
    "pension_stress": 85.0,
    "revenue_sustainability": 45.0,
    "debt_burden": 55.0
  },
  "calculation_date": "2024-08-15T10:30:00Z",
  "data_completeness": 95.0
}
```

---

## Authentication

### Public Tier (No Token)

- **Rate Limit:** 100 requests/hour
- **Access:** All read endpoints
- **Use Case:** Basic queries, exploring data

### Researcher Tier (API Token)

- **Rate Limit:** 1,000 requests/hour
- **Access:** All read endpoints + bulk export endpoints
- **Use Case:** Data analysis, research projects

### Requesting an API Token

1. Email: `research@ibco-ca.us`
2. Include: Name, institution, research purpose
3. Receive: API token + usage guidelines

### Using Your Token

Include token in request header:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \\
     https://api.ibco-ca.us/api/v1/cities
```

---

## Rate Limiting

Rate limits are enforced per IP address (public tier) or per token (researcher tier).

### Limits

| Tier | Requests/Hour | Burst Allowance |
|------|---------------|-----------------|
| Public | 100 | 20 requests/10 sec |
| Researcher | 1,000 | 50 requests/10 sec |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

### Handling Rate Limits

If you exceed the rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please wait 45 seconds.",
  "retry_after": 45
}
```

**Best Practice:** Implement exponential backoff and respect the `Retry-After` header.

---

## Endpoints Reference

### Cities

#### List All Cities

```http
GET /api/v1/cities
```

**Description:** Retrieve list of all cities tracked by IBCo.

**Query Parameters:**
- `state` (optional): Filter by state code (e.g., `CA`)
- `active_only` (optional): Only active cities (default: `true`)

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/cities?state=CA&active_only=true"
```

**Response:**

```json
{
  "cities": [
    {
      "id": 1,
      "name": "Vallejo",
      "state": "CA",
      "county": "Solano",
      "population": 121692,
      "fiscal_year_end": "06-30",
      "has_bankruptcy_history": true,
      "bankruptcy_filing_date": "2008-05-23",
      "bankruptcy_exit_date": "2011-11-01"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

#### Get City Details

```http
GET /api/v1/cities/{city_id}
```

**Example:**

```bash
curl https://api.ibco-ca.us/api/v1/cities/1
```

**Response:**

```json
{
  "id": 1,
  "name": "Vallejo",
  "state": "CA",
  "county": "Solano",
  "population": 121692,
  "government_type": "City Council-Manager",
  "fiscal_year_end_month": 6,
  "fiscal_year_end_day": 30,
  "has_bankruptcy_history": true,
  "bankruptcy_filing_date": "2008-05-23",
  "bankruptcy_exit_date": "2011-11-01",
  "website_url": "https://www.cityofvallejo.net",
  "finance_department_url": "https://www.cityofvallejo.net/city_hall/departments___divisions/finance"
}
```

---

### Risk Scores

#### Get Current Risk Score

```http
GET /api/v1/risk/cities/{city_id}/current
```

**Description:** Get the latest risk score for a city.

**Example:**

```bash
curl https://api.ibco-ca.us/api/v1/risk/cities/1/current
```

**Response:**

```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "fiscal_year": 2024,
  "overall_score": 68.5,
  "risk_level": "high",
  "category_scores": {
    "liquidity": 72.0,
    "structural_balance": 65.0,
    "pension_stress": 85.0,
    "revenue_sustainability": 45.0,
    "debt_burden": 55.0
  },
  "top_risk_factors": [
    {
      "indicator": "pension_funded_ratio",
      "score": 85.0,
      "value": 0.62,
      "contribution": 15.3
    },
    {
      "indicator": "fund_balance_ratio",
      "score": 72.0,
      "value": 0.08,
      "contribution": 12.5
    }
  ],
  "calculation_date": "2024-08-15T10:30:00Z",
  "model_version": "1.0",
  "data_completeness": 95.0
}
```

#### Get Risk Score History

```http
GET /api/v1/risk/cities/{city_id}/history
```

**Query Parameters:**
- `start_year` (optional): Start fiscal year
- `end_year` (optional): End fiscal year

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/risk/cities/1/history?start_year=2020&end_year=2024"
```

**Response:**

```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "risk_scores": [
    {
      "fiscal_year": 2020,
      "overall_score": 62.0,
      "risk_level": "high"
    },
    {
      "fiscal_year": 2021,
      "overall_score": 64.5,
      "risk_level": "high"
    },
    {
      "fiscal_year": 2022,
      "overall_score": 66.0,
      "risk_level": "high"
    },
    {
      "fiscal_year": 2023,
      "overall_score": 67.5,
      "risk_level": "high"
    },
    {
      "fiscal_year": 2024,
      "overall_score": 68.5,
      "risk_level": "high"
    }
  ],
  "trend": "deteriorating",
  "trend_slope": 1.625
}
```

---

### Projections

#### Get Fiscal Cliff Analysis

```http
GET /api/v1/projections/cities/{city_id}/fiscal-cliff
```

**Description:** Get fiscal cliff analysis (when reserves will be exhausted).

**Query Parameters:**
- `fiscal_year` (optional): Base fiscal year for projections
- `scenario` (optional): Scenario code (`base`, `optimistic`, `pessimistic`)

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/projections/cities/1/fiscal-cliff?scenario=base"
```

**Response:**

```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "base_fiscal_year": 2024,
  "scenario": "Base Case",
  "has_fiscal_cliff": true,
  "fiscal_cliff_year": 2029,
  "years_until_cliff": 5,
  "severity": "near_term",
  "cumulative_deficit_at_cliff": -125000000.0,
  "revenue_increase_needed_percent": 12.5,
  "expenditure_decrease_needed_percent": 10.8,
  "summary": "At current trends, Vallejo faces reserve depletion by FY2029. Corrective action required."
}
```

#### Get 10-Year Projections

```http
GET /api/v1/projections/cities/{city_id}/forecast
```

**Query Parameters:**
- `base_year` (optional): Base fiscal year
- `scenario` (optional): Scenario code

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/projections/cities/1/forecast?scenario=base"
```

**Response:**

```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "base_fiscal_year": 2024,
  "scenario": "Base Case",
  "projections": [
    {
      "projection_year": 2025,
      "total_revenues": 310000000.0,
      "total_expenditures": 325000000.0,
      "operating_balance": -15000000.0,
      "ending_fund_balance": 55000000.0,
      "fund_balance_ratio": 0.169,
      "is_deficit": true
    },
    {
      "projection_year": 2026,
      "total_revenues": 315000000.0,
      "total_expenditures": 335000000.0,
      "operating_balance": -20000000.0,
      "ending_fund_balance": 35000000.0,
      "fund_balance_ratio": 0.104,
      "is_deficit": true
    }
  ]
}
```

---

### Financial Data

#### Get Revenues

```http
GET /api/v1/financial/cities/{city_id}/revenues
```

**Query Parameters:**
- `fiscal_year` (required): Fiscal year
- `category` (optional): Revenue category

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/financial/cities/1/revenues?fiscal_year=2024"
```

**Response:**

```json
{
  "city_id": 1,
  "fiscal_year": 2024,
  "total_revenues": 298000000.0,
  "by_category": {
    "Taxes": 185000000.0,
    "Intergovernmental": 45000000.0,
    "Charges for Services": 38000000.0,
    "Other": 30000000.0
  },
  "recurring_revenues": 280000000.0,
  "one_time_revenues": 18000000.0
}
```

#### Get Expenditures

```http
GET /api/v1/financial/cities/{city_id}/expenditures
```

**Query Parameters:**
- `fiscal_year` (required): Fiscal year
- `category` (optional): Expenditure category

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/financial/cities/1/expenditures?fiscal_year=2024"
```

**Response:**

```json
{
  "city_id": 1,
  "fiscal_year": 2024,
  "total_expenditures": 343000000.0,
  "by_category": {
    "Public Safety": 145000000.0,
    "Personnel": 98000000.0,
    "Pension Costs": 75000000.0,
    "Capital": 25000000.0
  },
  "pension_share": 0.219
}
```

---

### Pensions

#### Get Pension Status

```http
GET /api/v1/pensions/cities/{city_id}/status
```

**Query Parameters:**
- `fiscal_year` (required): Fiscal year

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/pensions/cities/1/status?fiscal_year=2024"
```

**Response:**

```json
{
  "city_id": 1,
  "fiscal_year": 2024,
  "plans": [
    {
      "plan_name": "Miscellaneous",
      "funded_ratio": 0.62,
      "total_pension_liability": 4200000000.0,
      "fiduciary_net_position": 2604000000.0,
      "unfunded_actuarial_liability": 1596000000.0,
      "total_employer_contribution": 42000000.0,
      "employer_contribution_percent": 0.35
    },
    {
      "plan_name": "Safety",
      "funded_ratio": 0.58,
      "total_pension_liability": 2800000000.0,
      "fiduciary_net_position": 1624000000.0,
      "unfunded_actuarial_liability": 1176000000.0,
      "total_employer_contribution": 33000000.0,
      "employer_contribution_percent": 0.42
    }
  ],
  "total_ual": 2772000000.0,
  "avg_funded_ratio": 0.60,
  "total_contribution": 75000000.0
}
```

---

### Data Lineage

#### Get Data Point Lineage

```http
GET /api/v1/lineage/data-point
```

**Query Parameters:**
- `table` (required): Table name (e.g., `revenues`)
- `record_id` (required): Record ID
- `field` (required): Field name

**Example:**

```bash
curl "https://api.ibco-ca.us/api/v1/lineage/data-point?table=revenues&record_id=123&field=actual_amount"
```

**Response:**

```json
{
  "table_name": "revenues",
  "record_id": 123,
  "field_name": "actual_amount",
  "value": 185000000.0,
  "source": {
    "document_type": "CAFR",
    "document_url": "https://www.cityofvallejo.net/files/cafr_2024.pdf",
    "page_number": 34,
    "table_name": "Statement of Activities",
    "line_item": "Total Tax Revenues"
  },
  "entry": {
    "extracted_by": "Jane Doe",
    "extracted_at": "2024-08-01T10:30:00Z",
    "entry_method": "manual"
  },
  "validation": {
    "validated_by": "John Smith",
    "validated_at": "2024-08-02T14:20:00Z",
    "validation_notes": "Cross-checked with CAFR summary, values match",
    "confidence_score": 100
  }
}
```

---

## Response Formats

### Success Response

All successful responses follow this structure:

```json
{
  "data": { /* response data */ },
  "metadata": {
    "timestamp": "2024-11-12T10:30:00Z",
    "api_version": "1.0",
    "request_id": "abc123"
  }
}
```

### Pagination

List endpoints return paginated results:

```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "links": {
    "self": "/api/v1/cities?page=1",
    "next": "/api/v1/cities?page=2",
    "prev": null,
    "first": "/api/v1/cities?page=1",
    "last": "/api/v1/cities?page=5"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "not_found",
    "message": "City with ID 999 not found",
    "details": {
      "city_id": 999
    }
  },
  "metadata": {
    "timestamp": "2024-11-12T10:30:00Z",
    "request_id": "abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Invalid or missing API token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

- `invalid_parameter`: Invalid query parameter
- `missing_parameter`: Required parameter missing
- `not_found`: Resource not found
- `rate_limit_exceeded`: Rate limit exceeded
- `unauthorized`: Invalid or missing authentication
- `server_error`: Internal server error

---

## Code Examples

See the `examples/` directory for complete code samples:

- **Python:** `examples/python_client.py`
- **JavaScript:** `examples/fetch_risk_scores.js`
- **Bash/curl:** `examples/curl_commands.sh`
- **Jupyter:** `examples/data_analysis.ipynb`

### Quick Example (Python)

```python
import requests

# Get Vallejo's current risk score
response = requests.get("https://api.ibco-ca.us/api/v1/risk/cities/1/current")
data = response.json()

print(f"Risk Score: {data['overall_score']}/100 ({data['risk_level']})")
```

---

## Best Practices

### 1. Cache Responses

Data changes quarterly. Cache responses for at least 1 hour:

```python
import requests
from requests_cache import CachedSession

session = CachedSession(expire_after=3600)
response = session.get("https://api.ibco-ca.us/api/v1/cities")
```

### 2. Handle Rate Limits

Implement exponential backoff:

```python
import time
import requests

def make_request(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### 3. Use Bulk Endpoints

For large datasets, use bulk export endpoints (researcher tier):

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     "https://api.ibco-ca.us/api/v1/bulk/cities/1/export?format=json"
```

### 4. Validate Responses

Always validate response structure:

```python
def validate_risk_score(data):
    required_fields = ['overall_score', 'risk_level', 'fiscal_year']
    return all(field in data for field in required_fields)
```

### 5. Monitor API Status

Check API status before making requests:

```bash
curl https://api.ibco-ca.us/api/health
```

---

## Support

### Resources

- **Interactive API Docs:** https://api.ibco-ca.us/docs
- **Developer Guide:** https://docs.ibco-ca.us/developer-guide
- **Code Examples:** https://github.com/ibco-ca/examples
- **API Status:** https://status.ibco-ca.us

### Contact

- **Email:** api@ibco-ca.us
- **GitHub Issues:** https://github.com/ibco-ca/vallejo-ibco-ca/issues
- **Community Forum:** https://forum.ibco-ca.us

### Report Issues

Found a bug or have a feature request? Please report it:

```bash
# GitHub Issue Template
Title: [API] Brief description
Labels: api, bug (or feature)

Description:
- Endpoint: GET /api/v1/...
- Expected behavior: ...
- Actual behavior: ...
- Steps to reproduce: ...
```

---

## Changelog

### v1.0 (2024-11-12)

- Initial public API release
- All read endpoints available
- Rate limiting implemented
- OpenAPI documentation
- Public data lineage endpoints

---

**Last Updated:** November 12, 2024
**API Version:** 1.0
**Documentation Version:** 1.0
