# Metabase Dashboard Configuration for IBCo Vallejo Console

## Overview

This directory contains Metabase dashboard configurations for public visualization of Vallejo's fiscal data. The dashboards provide transparent, accessible views of:

1. **Vallejo Fiscal Overview** - High-level fiscal health metrics
2. **Pension Analysis** - Deep dive into pension obligations and trends
3. **Fiscal Projections** - 10-year forward projections and fiscal cliff analysis
4. **Peer Comparison** - Vallejo vs other CA cities (requires multi-city data)

## Architecture

```
src/dashboard/metabase/
├── README.md                           # This file
├── dashboards/                         # Dashboard JSON configurations
│   ├── vallejo_fiscal_overview.json
│   ├── pension_analysis.json
│   ├── fiscal_projections.json
│   └── peer_comparison.json
├── queries/                            # Shared/reusable SQL queries
└── scripts/                            # Setup and import scripts
    ├── setup_metabase.sh
    ├── create_readonly_user.sql
    ├── import_dashboards.py
    └── export_dashboards.py
```

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database with IBCo data
- Metabase (OSS or Enterprise)
- Python 3.11+ (for import/export scripts)

## Quick Start

### 1. Start Metabase via Docker Compose

```bash
# Metabase is included in docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d metabase
```

Metabase will be available at: `http://localhost:3000`

### 2. Create Read-Only Database User

For security, Metabase should connect to PostgreSQL with a read-only user:

```bash
# Run the SQL migration to create metabase_readonly user
psql -h localhost -U ibco_admin -d ibco_production -f scripts/create_readonly_user.sql
```

This creates:
- User: `metabase_readonly`
- Password: (set via environment variable `METABASE_DB_PASSWORD`)
- Permissions: SELECT only on all IBCo tables

### 3. Configure Metabase Database Connection

**Via Metabase UI:**

1. Navigate to `http://localhost:3000` (first-time setup)
2. Create admin account
3. Click "Add a database"
4. Configure PostgreSQL connection:
   - Name: `IBCo Production`
   - Host: `postgres` (Docker internal network) or `localhost`
   - Port: `5432`
   - Database name: `ibco_production`
   - Username: `metabase_readonly`
   - Password: `${METABASE_DB_PASSWORD}`

**Via Environment Variables** (docker-compose):

```yaml
environment:
  MB_DB_TYPE: postgres
  MB_DB_DBNAME: ibco_production
  MB_DB_PORT: 5432
  MB_DB_USER: metabase_readonly
  MB_DB_PASS: ${METABASE_DB_PASSWORD}
  MB_DB_HOST: postgres
```

### 4. Import Dashboards

Use the Python import script to load dashboard configurations:

```bash
python scripts/import_dashboards.py \
  --metabase-url http://localhost:3000 \
  --metabase-user admin@ibco-ca.us \
  --metabase-password ${METABASE_ADMIN_PASSWORD} \
  --dashboard-dir dashboards/
```

This will:
1. Authenticate to Metabase API
2. Create database connection (if not exists)
3. Import all dashboard JSON files
4. Create questions (SQL queries)
5. Create dashboards with layout
6. Configure public access settings

### 5. Enable Public Access

For each dashboard:

1. Open dashboard in Metabase UI
2. Click "Sharing" icon
3. Enable "Public link"
4. Copy public URL for embedding

**Or via API:**

```bash
python scripts/import_dashboards.py --enable-public-access
```

Public URLs will be:
- `https://metabase.ibco-ca.us/public/dashboard/{hash}`

## Dashboard Configurations

### Dashboard JSON Format

Each dashboard JSON file contains:

```json
{
  "name": "Dashboard Name",
  "description": "Dashboard description",
  "parameters": [...],          // Filter parameters
  "questions": [...],           // SQL queries with visualization configs
  "layout": {...},              // Card positioning
  "public_access": {...},       // Public sharing settings
  "metadata": {...}             // Provenance and versioning
}
```

### Questions (SQL Queries)

Each question includes:
- **Query**: Native SQL or Query Builder JSON
- **Visualization**: Chart type and display settings
- **Template Tags**: Parameterized filters
- **Display Settings**: Number formatting, colors, etc.

Example:

```json
{
  "id": "q1",
  "name": "Revenue Trends by Year",
  "query": {
    "type": "native",
    "native": {
      "query": "SELECT fy.year, SUM(r.actual_amount) AS total_revenue FROM...",
      "template-tags": {
        "city_filter": {
          "type": "text",
          "default": "Vallejo"
        }
      }
    }
  },
  "visualization": {
    "type": "line",
    "x_axis": "fiscal_year",
    "y_axis": "total_revenue"
  }
}
```

## Public Access Configuration

### Embedding Dashboards

Metabase supports two embedding modes:

1. **Public Links** (no authentication required)
   - Best for: Public transparency, blog posts, media
   - URL format: `https://metabase.ibco-ca.us/public/dashboard/{hash}`
   - Enable via: Dashboard → Sharing → Public link

2. **Signed Embedding** (token-based authentication)
   - Best for: Controlled access, whitelabeling
   - Requires: Enterprise Metabase license
   - Not used for IBCo (public transparency priority)

### Auto-Refresh Configuration

Set dashboards to auto-refresh data nightly:

```json
{
  "public_access": {
    "auto_refresh_interval": 86400  // 24 hours in seconds
  }
}
```

Or via Metabase UI:
1. Edit dashboard
2. Settings → Cache TTL → 24 hours

## Security Considerations

### Read-Only Access

Metabase connects with `metabase_readonly` user which has:
- ✅ SELECT on all tables
- ❌ No INSERT, UPDATE, DELETE
- ❌ No DROP, CREATE, ALTER
- ❌ No access to system catalogs

### Public Data Exposure

**All dashboards are public by design.** This is intentional for civic transparency:

- ✅ Anyone can view fiscal data
- ✅ No authentication required
- ✅ Complete data lineage visible
- ❌ No PII or sensitive data exposed
- ❌ Admin functions not public

### Rate Limiting

Configure nginx rate limiting for public dashboard URLs:

```nginx
location /public/dashboard/ {
    limit_req zone=dashboard_limit burst=20;
    proxy_pass http://metabase:3000;
}
```

## Maintenance

### Updating Dashboards

1. **Manual updates** (via Metabase UI):
   - Edit dashboard → Make changes → Save
   - Export updated dashboard:
     ```bash
     python scripts/export_dashboards.py --dashboard-id 123 --output dashboards/
     ```

2. **Programmatic updates** (via JSON):
   - Edit JSON file
   - Re-import:
     ```bash
     python scripts/import_dashboards.py --dashboard dashboards/updated_dashboard.json
     ```

### Backup and Version Control

Dashboard configurations are version-controlled in Git:

```bash
# Export current dashboards from Metabase
python scripts/export_dashboards.py --output dashboards/

# Commit changes
git add dashboards/
git commit -m "Update dashboard configurations"
git push
```

### Data Refresh

Dashboards automatically reflect latest database data. No manual refresh needed.

To force cache refresh:
1. Metabase UI → Settings → Admin → Caching
2. Clear cache for specific dashboard
3. Or wait for TTL expiration (24 hours)

## Monitoring

### Dashboard Analytics

Track public dashboard usage:

1. Enable Metabase analytics (Admin → Settings → Analytics)
2. Monitor:
   - Dashboard view counts
   - Query performance
   - Cache hit rates
   - Error rates

### Performance Optimization

**Slow queries:**
- Add database indexes for common filters
- Pre-aggregate data in materialized views
- Increase Metabase cache TTL

**Database indexes needed:**
```sql
CREATE INDEX CONCURRENTLY idx_fiscal_years_city_year ON fiscal_years(city_id, year);
CREATE INDEX CONCURRENTLY idx_revenues_fy_category ON revenues(fiscal_year_id, category_id);
CREATE INDEX CONCURRENTLY idx_expenditures_fy_category ON expenditures(fiscal_year_id, category_id);
CREATE INDEX CONCURRENTLY idx_risk_scores_fy_date ON risk_scores(fiscal_year_id, calculation_date DESC);
```

## Troubleshooting

### Connection Issues

**Error: "Could not connect to database"**

1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Verify read-only user exists:
   ```bash
   psql -h localhost -U metabase_readonly -d ibco_production -c "SELECT 1;"
   ```

3. Check network connectivity:
   ```bash
   docker exec metabase ping postgres
   ```

### Import Errors

**Error: "Dashboard already exists"**

Delete existing dashboard first:
```bash
python scripts/import_dashboards.py --delete-existing --dashboard-name "Vallejo Fiscal Overview"
```

**Error: "Invalid SQL syntax"**

Validate SQL queries:
```bash
psql -h localhost -U metabase_readonly -d ibco_production -f dashboards/vallejo_fiscal_overview.json
```

### Performance Issues

**Dashboard loads slowly:**

1. Check query performance:
   ```sql
   EXPLAIN ANALYZE <query from dashboard>;
   ```

2. Add missing indexes (see Performance Optimization above)

3. Increase Metabase Java heap:
   ```yaml
   environment:
     JAVA_OPTS: "-Xmx2g"  # Increase from default 1g
   ```

## Advanced Configuration

### Custom Themes

Customize dashboard appearance:

1. Admin → Settings → Appearance
2. Upload logo (IBCo logo)
3. Set colors:
   - Primary: `#2196F3` (blue)
   - Accent: `#4CAF50` (green for positive)
   - Danger: `#F44336` (red for negative)

### Email Subscriptions

Enable email reports for stakeholders:

1. Configure SMTP (Admin → Settings → Email)
2. Create subscription (Dashboard → Sharing → Email)
3. Schedule: Daily, Weekly, or Monthly

SMTP config:
```yaml
environment:
  MB_EMAIL_SMTP_HOST: smtp.sendgrid.net
  MB_EMAIL_SMTP_PORT: 587
  MB_EMAIL_SMTP_USERNAME: apikey
  MB_EMAIL_SMTP_PASSWORD: ${SENDGRID_API_KEY}
  MB_EMAIL_FROM_ADDRESS: notifications@ibco-ca.us
```

### API Access

Metabase API for programmatic access:

```bash
# Authenticate
curl -X POST http://localhost:3000/api/session \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@ibco-ca.us","password":"${METABASE_ADMIN_PASSWORD}"}'

# Get session token from response, then:
export MB_SESSION_TOKEN="<token>"

# List dashboards
curl http://localhost:3000/api/dashboard \
  -H "X-Metabase-Session: ${MB_SESSION_TOKEN}"

# Get dashboard data
curl http://localhost:3000/api/dashboard/1 \
  -H "X-Metabase-Session: ${MB_SESSION_TOKEN}"
```

## Integration with IBCo Website

### Embedding in Static Site

```html
<!-- Embed Vallejo Fiscal Overview -->
<iframe
  src="https://metabase.ibco-ca.us/public/dashboard/abc123"
  frameborder="0"
  width="100%"
  height="800"
  allowtransparency
></iframe>
```

### Responsive Embedding

```html
<div class="metabase-embed-container">
  <iframe
    src="https://metabase.ibco-ca.us/public/dashboard/abc123"
    frameborder="0"
    width="100%"
    height="600"
    style="min-height: 600px;"
  ></iframe>
</div>

<style>
.metabase-embed-container {
  position: relative;
  padding-bottom: 75%; /* 4:3 aspect ratio */
  height: 0;
  overflow: hidden;
}

.metabase-embed-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
</style>
```

## Support

For questions or issues:
- **Documentation**: https://www.metabase.com/docs/latest/
- **Community**: https://discourse.metabase.com/
- **IBCo Issues**: https://github.com/yourusername/vallejo-ibco-ca/issues

## License

Dashboard configurations are open source under MIT License. Metabase is licensed under AGPL (Open Source) or Enterprise License.
