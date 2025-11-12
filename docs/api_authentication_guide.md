# API Authentication & Rate Limiting Guide

## Overview

The IBCo Vallejo Console API implements graduated rate limiting and JWT token authentication to ensure fair access while preventing abuse.

## Rate Limiting Tiers

### Public Tier (No Authentication Required)
- **Hourly Limit**: 100 requests/hour
- **Burst Limit**: 20 requests/10 seconds
- **Access**: Read-only endpoints, single fiscal year queries
- **Use Case**: General public exploration, individual researchers

### Researcher Tier (JWT Token Required)
- **Hourly Limit**: 1000 requests/hour
- **Burst Limit**: 20 requests/10 seconds
- **Access**: All read-only endpoints, bulk export endpoints
- **Use Case**: Academic research, data journalism, bulk analysis

## Rate Limit Headers

All API responses include rate limit information:

```
X-RateLimit-Limit: 1000          # Your hourly limit
X-RateLimit-Remaining: 847       # Requests remaining this hour
X-RateLimit-Reset: 1699564800    # Unix timestamp when limit resets
```

## Rate Limit Response (429)

When rate limit is exceeded:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded: hourly (1000 requests/hour for researcher tier)",
  "retry_after": 3542,
  "documentation": "https://docs.ibco-ca.us/api/rate-limits"
}
```

Response headers:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 3542
```

---

## Obtaining a Researcher Tier Token

### For Administrators

Generate tokens using the CLI script:

```bash
# Generate public tier token
poetry run python scripts/admin/generate_api_token.py \
    --user-id "public-user-001" \
    --tier public \
    --purpose "General API exploration" \
    --email "user@example.com"

# Generate researcher tier token
poetry run python scripts/admin/generate_api_token.py \
    --user-id "researcher@university.edu" \
    --tier researcher \
    --purpose "Municipal finance research project" \
    --email "researcher@university.edu" \
    --organization "UC Berkeley"
```

### For Researchers

**To request a researcher tier token:**

1. Email your request to: `api@ibco-ca.us`
2. Include:
   - Your name and affiliation
   - Research purpose (2-3 sentences)
   - Estimated API usage
   - Contact email
3. Tokens are typically issued within 1-2 business days
4. Tokens are valid for 1 year

---

## Using Your Token

### Store Securely

**Never commit tokens to version control!**

Add to `.env` file:
```bash
IBCO_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### HTTP Authorization Header

Include token as Bearer token in `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Examples

#### cURL

```bash
curl -H "Authorization: Bearer $IBCO_API_TOKEN" \
     https://api.ibco-ca.us/v1/fiscal-years/2023
```

#### Python (requests)

```python
import os
import requests

token = os.environ["IBCO_API_TOKEN"]
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "https://api.ibco-ca.us/v1/fiscal-years/2023",
    headers=headers
)

print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(response.json())
```

#### Python (httpx)

```python
import os
import httpx

async def fetch_fiscal_data():
    token = os.environ["IBCO_API_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.ibco-ca.us/v1/fiscal-years/2023",
            headers=headers
        )
        return response.json()
```

#### JavaScript (fetch)

```javascript
const token = process.env.IBCO_API_TOKEN;

fetch('https://api.ibco-ca.us/v1/fiscal-years/2023', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(response => {
    console.log('Rate limit remaining:', response.headers.get('X-RateLimit-Remaining'));
    return response.json();
  })
  .then(data => console.log(data));
```

#### Node.js (axios)

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.ibco-ca.us/v1',
  headers: {
    'Authorization': `Bearer ${process.env.IBCO_API_TOKEN}`
  }
});

api.get('/fiscal-years/2023')
  .then(response => {
    console.log('Rate limit remaining:', response.headers['x-ratelimit-remaining']);
    console.log(response.data);
  });
```

---

## Admin Token Management API

Administrators can manage tokens via API endpoints (requires admin authentication).

### List All Active Tokens

```bash
GET /api/v1/admin/tokens
```

**Query Parameters:**
- `tier`: Filter by tier (public/researcher)
- `user_id`: Filter by user ID

**Response:**
```json
{
  "total": 15,
  "tokens": [
    {
      "token_id": "abc123...",
      "user_id": "researcher@university.edu",
      "tier": "researcher",
      "purpose": "Municipal finance research",
      "contact_email": "researcher@university.edu",
      "organization": "UC Berkeley",
      "issued_at": "2024-01-15T10:30:00Z",
      "expires_at": "2025-01-15T10:30:00Z",
      "revoked": false,
      "revoked_at": null,
      "revoke_reason": null
    }
  ]
}
```

### Get Token Details

```bash
GET /api/v1/admin/tokens/{token_id}
```

### Create Token

```bash
POST /api/v1/admin/tokens
Content-Type: application/json

{
  "user_id": "researcher@university.edu",
  "tier": "researcher",
  "purpose": "Municipal finance research project",
  "contact_email": "researcher@university.edu",
  "organization": "UC Berkeley"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "metadata": {
    "token_id": "abc123...",
    "user_id": "researcher@university.edu",
    "tier": "researcher",
    "issued_at": "2024-01-15T10:30:00Z",
    "expires_at": "2025-01-15T10:30:00Z"
  }
}
```

### Revoke Token

```bash
POST /api/v1/admin/tokens/{token_id}/revoke
Content-Type: application/json

{
  "reason": "User requested revocation"
}
```

### Validate Token Status

```bash
GET /api/v1/admin/tokens/{token_id}/validate
```

**Response (Valid):**
```json
{
  "valid": true,
  "token_id": "abc123...",
  "user_id": "researcher@university.edu",
  "tier": "researcher",
  "expires_at": "2025-01-15T10:30:00Z"
}
```

**Response (Revoked):**
```json
{
  "valid": false,
  "reason": "Token has been revoked",
  "revoked_at": "2024-06-01T14:20:00Z",
  "revoke_reason": "User requested revocation"
}
```

---

## Token Lifecycle

### Token Generation
1. Admin generates token via CLI or API
2. Token metadata stored in Redis
3. Token delivered to user via secure channel (email)

### Token Validation (per request)
1. Extract token from `Authorization: Bearer <token>` header
2. Decode and verify JWT signature
3. Check expiration
4. Check blacklist (revoked tokens)
5. Add user info to request state for rate limiting

### Token Revocation
1. Admin revokes token by ID
2. Token ID added to Redis blacklist (2-year TTL)
3. Token immediately fails validation
4. Metadata updated with revocation info

---

## Best Practices

### For API Users

1. **Store tokens securely**
   - Use environment variables
   - Never commit to git
   - Rotate tokens periodically

2. **Handle rate limits gracefully**
   - Check `X-RateLimit-Remaining` header
   - Respect `Retry-After` header on 429 responses
   - Implement exponential backoff

3. **Monitor token expiration**
   - Tokens expire after 1 year
   - Request renewal 30 days before expiration
   - Handle 401 responses (expired/revoked tokens)

4. **Optimize requests**
   - Use bulk endpoints when available
   - Cache responses when appropriate
   - Batch requests to stay under burst limit

### For Administrators

1. **Token issuance**
   - Verify requestor identity and purpose
   - Document all issued tokens
   - Set appropriate tier based on use case

2. **Token monitoring**
   - Review active tokens quarterly
   - Revoke unused tokens
   - Monitor for abuse patterns

3. **Rate limit tuning**
   - Adjust limits based on usage patterns
   - Consider special allocations for high-value research
   - Document limit changes

---

## Rate Limiting Implementation Details

### Sliding Window Algorithm

Rate limiting uses Redis-backed sliding windows:

**Hourly Limit:**
- Redis key: `ratelimit:hourly:<client_id>:<current_hour>`
- Counter incremented per request
- TTL: 2 hours (allows cleanup)
- Resets every clock hour

**Burst Limit:**
- Redis key: `ratelimit:burst:<client_id>`
- Sorted set of request timestamps
- Window: 10 seconds
- Old timestamps pruned automatically

### Client Identification

Clients identified by:
1. **Authenticated**: JWT `sub` claim (user ID)
2. **Unauthenticated**: IP address (from `X-Forwarded-For` or `client.host`)

### Fail-Open Behavior

If Redis is unavailable:
- Rate limiting skipped (fail open)
- Logged as error
- Allows service continuity

---

## Security Considerations

### Token Security

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Secret Key**: 256-bit random key (from `SECRET_KEY` env var)
- **Expiration**: 1 year (configurable)
- **Revocation**: Redis blacklist with 2-year TTL

### Rate Limit Security

- Protects against:
  - Brute force attacks
  - API scraping
  - Denial of service
  - Resource exhaustion

- Does NOT protect against:
  - Distributed attacks (consider Cloudflare/AWS Shield)
  - Credential stuffing (use separate authentication)
  - Data exfiltration (monitor usage patterns)

### Admin Endpoint Security

⚠️ **IMPORTANT**: Admin token endpoints require authentication.

In production:
- Implement admin authentication middleware
- Use separate admin API keys
- Restrict to internal network or VPN
- Enable audit logging

---

## Troubleshooting

### "Rate limit exceeded" (429)

**Problem**: Exceeded hourly or burst limit

**Solutions**:
- Wait for `Retry-After` seconds
- Check `X-RateLimit-Reset` header for limit reset time
- Request researcher tier token for higher limits
- Optimize request patterns (use bulk endpoints, caching)

### "Unauthorized" / Invalid token

**Problem**: Token validation failed

**Possible causes**:
- Token expired (check expiration date)
- Token revoked (check with admin)
- Invalid token format
- Wrong secret key (server misconfiguration)

**Solutions**:
- Verify token is correctly copied (no extra spaces/newlines)
- Check token hasn't expired
- Request new token from admin

### "Connection to Redis failed"

**Problem**: Rate limiting Redis unavailable

**Impact**: Rate limiting disabled (fail-open mode)

**Admin action**: Check Redis connectivity, restart Redis service

---

## API Reference

### Public Endpoints (No Auth Required)

- `GET /` - API root
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation
- `GET /disclaimer` - Legal disclaimer

### Data Endpoints (Public Tier)

- `GET /api/v1/cities` - List cities
- `GET /api/v1/fiscal-years/{year}` - Single fiscal year
- `GET /api/v1/risk-scores/{year}` - Risk score for year
- `GET /api/v1/projections/{year}` - Projections from year

### Bulk Endpoints (Researcher Tier Recommended)

- `GET /api/v1/fiscal-years` - All fiscal years
- `GET /api/v1/revenues` - All revenue data
- `GET /api/v1/expenditures` - All expenditure data
- `GET /api/v1/risk-scores` - All risk scores

### Admin Endpoints (Admin Auth Required)

- `GET /api/v1/admin/tokens` - List tokens
- `POST /api/v1/admin/tokens` - Create token
- `GET /api/v1/admin/tokens/{id}` - Get token details
- `POST /api/v1/admin/tokens/{id}/revoke` - Revoke token
- `GET /api/v1/admin/quality/status` - Data quality status

---

## Contact & Support

**API Access Requests**: api@ibco-ca.us
**Technical Support**: support@ibco-ca.us
**Bug Reports**: https://github.com/ibco-ca/vallejo-ibco-ca/issues
**Documentation**: https://docs.ibco-ca.us/api

---

## Appendix: Token Metadata Schema

```python
{
  "token_id": str,           # Unique token identifier (jti claim)
  "user_id": str,            # User identifier (sub claim)
  "tier": str,               # "public" or "researcher"
  "purpose": str,            # Purpose of token
  "contact_email": str,      # Contact email
  "organization": str,       # Optional organization
  "issued_at": datetime,     # Token issue time (iat claim)
  "expires_at": datetime,    # Token expiration (exp claim)
  "revoked": bool,           # Revocation status
  "revoked_at": datetime,    # Revocation time (if revoked)
  "revoke_reason": str       # Revocation reason (if revoked)
}
```

## Appendix: JWT Claims

```json
{
  "jti": "abc123...",                 // Token ID
  "sub": "researcher@university.edu", // User identifier (subject)
  "tier": "researcher",               // Rate limit tier
  "iat": 1705315800,                  // Issued at (Unix timestamp)
  "exp": 1736851800,                  // Expires at (Unix timestamp)
  "purpose": "Municipal finance research"
}
```
