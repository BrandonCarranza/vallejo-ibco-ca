# Dashboard Configuration

This directory contains configuration for the Metabase business intelligence dashboard.

## Overview

We use [Metabase](https://www.metabase.com/) as our primary dashboarding and visualization tool because:

- **User-friendly**: Non-technical users can create queries
- **Open source**: No licensing costs
- **Self-hosted**: Complete data control
- **SQL-native**: Direct database queries
- **Embeddable**: Can embed visualizations in other sites
- **API-driven**: Can programmatically manage dashboards

## Directory Structure

```
dashboard/
├── metabase/
│   ├── dashboards/      # Dashboard definitions (JSON)
│   └── queries/         # Saved SQL queries
└── README.md           # This file
```

## Metabase Setup

### Initial Configuration

Metabase is included in `docker-compose.yml`:

```bash
# Start Metabase
docker-compose up -d metabase

# Access Metabase
# Open browser to http://localhost:3000
```

### First-Time Setup

1. **Create admin account**
   - Email: Your email
   - Password: Secure password

2. **Connect to database**
   - Type: PostgreSQL
   - Host: `postgres` (Docker network name)
   - Port: 5432
   - Database: `ibco_vallejo`
   - Username: From `.env`
   - Password: From `.env`

3. **Test connection** and save

### Database Connection Details

Connection details are in `.env`:

```env
POSTGRES_USER=ibco
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ibco_vallejo
```

## Dashboard Structure

### Planned Dashboards

1. **Executive Summary**
   - High-level fiscal health indicators
   - Current risk score
   - Key metrics at a glance
   - Trend charts

2. **Financial Overview**
   - Revenue trends
   - Expenditure breakdown
   - Fund balance history
   - Budget vs. actual

3. **Pension Deep Dive**
   - Pension funded ratio
   - Unfunded liability trend
   - Contribution burden
   - Projection scenarios

4. **Risk Analysis**
   - Risk score components
   - Individual indicator scores
   - Peer comparison
   - Historical risk trends

5. **Data Quality**
   - Data completeness metrics
   - Validation status
   - Recent updates
   - Data age indicators

### Dashboard Best Practices

- **Keep it simple**: Each dashboard has a clear purpose
- **Show trends**: Include time-series where relevant
- **Provide context**: Use benchmarks and comparisons
- **Enable drill-down**: Allow users to explore details
- **Document assumptions**: Add descriptions to charts

## Queries

### Saved Queries

SQL queries are stored in `metabase/queries/` for:
- Version control
- Documentation
- Sharing
- Backup

### Query Naming Convention

```
{category}_{description}.sql

Examples:
financial_revenue_trends.sql
risk_composite_score_calculation.sql
pension_funded_ratio_history.sql
```

### Query Best Practices

- **Comment your SQL**: Explain complex logic
- **Parameterize**: Use Metabase parameters for filters
- **Optimize**: Add indexes for frequently queried fields
- **Test**: Verify query results against source data
- **Document**: Include expected results in comments

## Exporting Dashboards

### Export Dashboard Configuration

Export dashboard definitions for version control:

```bash
# Export all dashboards
# (Requires Metabase API access)
curl -X GET \
  http://localhost:3000/api/dashboard \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN" \
  > metabase/dashboards/export.json
```

### Backup Dashboards

Dashboards are backed up:
1. Via JSON exports (version controlled)
2. Via Metabase database backup
3. Periodically to cloud storage

## Embedding Dashboards

### Public Sharing

Dashboards can be shared publicly:

1. **Enable public sharing** in Metabase
2. **Get public URL** from dashboard settings
3. **Embed in website** using iframe

### Signed Embedding

For authenticated embedding:

1. **Enable signed embedding** in Metabase settings
2. **Generate signed URL** from API
3. **Embed with authentication** in your application

See [Metabase embedding docs](https://www.metabase.com/docs/latest/embedding/introduction)

## Custom Visualizations

### Adding Custom Viz

Metabase supports custom visualizations:

1. Build custom viz following [Metabase guide](https://www.metabase.com/docs/latest/developers-guide/custom-visualizations)
2. Add to `custom-visualizations/` directory
3. Load into Metabase

### Recommended Viz Types

- **Line charts**: Trends over time
- **Bar charts**: Comparisons across categories
- **Gauge charts**: Single metric with thresholds
- **Tables**: Detailed data display
- **Maps**: Geographic visualization (future)

## Alerts & Subscriptions

### Email Subscriptions

Set up scheduled email reports:

1. **Create dashboard or question**
2. **Click "Subscribe"**
3. **Set schedule** (daily, weekly, monthly)
4. **Add recipients**
5. **Configure format** (attachment or link)

### Alerts

Create alerts for threshold breaches:

1. **Create question** with metric
2. **Set up alert** for condition
3. **Configure notification** (email, Slack)

Example alerts:
- Fund balance drops below 10%
- Risk score increases by 10+ points
- Data validation fails

## Maintenance

### Regular Tasks

- **Weekly**: Review dashboard usage analytics
- **Monthly**: Update dashboard descriptions
- **Quarterly**: Review and optimize slow queries
- **Annually**: Archive unused dashboards

### Performance Optimization

If dashboards load slowly:

1. **Add database indexes**
2. **Materialize complex queries** (create views)
3. **Reduce data range** (use date filters)
4. **Enable caching** in Metabase
5. **Consider aggregation tables**

### Troubleshooting

**Dashboard not loading**
- Check database connection
- Review query for errors
- Check Metabase logs

**Slow query performance**
- Review query execution plan
- Add appropriate indexes
- Consider pre-aggregation

**Data not updating**
- Check ETL pipeline status
- Verify database updates
- Clear Metabase cache

## Development Workflow

### Creating New Dashboard

1. **Design on paper**: Sketch layout first
2. **Create queries**: Build and test SQL
3. **Build in Metabase**: Create visualizations
4. **Export JSON**: Save to version control
5. **Document**: Add README entry
6. **Review**: Get feedback from users

### Updating Existing Dashboard

1. **Make changes** in Metabase
2. **Test thoroughly**
3. **Export updated JSON**
4. **Commit to git**
5. **Update documentation**

## API Integration

### Metabase API

Access dashboards programmatically:

```python
import requests

# Authenticate
response = requests.post(
    "http://localhost:3000/api/session",
    json={"username": "user", "password": "pass"}
)
session_token = response.json()["id"]

# Query dashboard
response = requests.get(
    "http://localhost:3000/api/dashboard/1",
    headers={"X-Metabase-Session": session_token}
)
```

See [Metabase API docs](https://www.metabase.com/docs/latest/api-documentation)

## Resources

### Documentation

- [Metabase Documentation](https://www.metabase.com/docs/latest/)
- [Metabase Learn](https://www.metabase.com/learn/)
- [Metabase Community](https://discourse.metabase.com/)

### Tutorials

- [Getting Started Guide](https://www.metabase.com/docs/latest/getting-started)
- [SQL Tutorial](https://www.metabase.com/learn/sql-questions/)
- [Dashboard Best Practices](https://www.metabase.com/learn/dashboards/)

## Questions?

- **Metabase issues**: Open GitHub issue with "dashboard" label
- **Dashboard requests**: Email dashboards@ibco-ca.us
- **General questions**: See project documentation

---

**Last Updated**: 2025-01-10
