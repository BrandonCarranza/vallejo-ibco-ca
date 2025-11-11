# Grafana Dashboards for IBCo Vallejo Console

This directory contains Grafana dashboard definitions for monitoring the IBCo Vallejo Console application.

## Available Dashboards

### 1. System Health Dashboard (`system-health.json`)

**Overview:** System-level metrics and health indicators

**Panels:**
- **Uptime**: Application uptime percentage (target: 99.9%)
- **Request Rate**: HTTP requests per second
- **Response Times**: p50, p95, p99 latencies
- **Error Rate**: 5xx error percentage
- **Active Requests**: Currently processing requests
- **CPU Usage**: System CPU utilization
- **Memory Usage**: Application and system memory
- **Disk Usage**: Filesystem utilization

**Alerts:**
- API latency > 1s (p95)
- Error rate > 1%
- Memory > 85%
- Disk > 80%

### 2. Data Freshness Dashboard (`data-freshness.json`)

**Overview:** Data update tracking and quality metrics

**Panels:**
- **Last CAFR Entry**: Days since last CAFR data import
- **Last CalPERS Entry**: Days since last pension data import
- **Fiscal Years Available**: Count of years with complete data
- **Data Quality Score**: Average quality score across all years
- **Critical Issues**: Count of critical data quality issues
- **Validation Status**: Fiscal years by validation status
- **Data Completeness**: Percentage by data type (revenues, expenditures, pension)

**Alerts:**
- No data update in > 180 days
- Quality score < 95%
- Critical issues > 0

### 3. Risk Score Trends Dashboard (`risk-scores.json`)

**Overview:** Risk score progression and analysis

**Panels:**
- **Current Risk Score**: Vallejo's latest overall risk score
- **Risk Level**: Current risk level (Low, Moderate, Elevated, High, Critical)
- **Score History**: Time series of overall risk score
- **Category Breakdown**: Liquidity, Structural, Pension, Revenue, Debt scores
- **Score Change**: Month-over-month and year-over-year changes
- **Risk Factors**: Top 5 current risk factors
- **Projection Cliff Year**: Predicted fiscal cliff year
- **Comparison**: Vallejo vs. California city average (future)

**Alerts:**
- Risk score increases > 10 points in one update
- Risk level escalates to "High" or "Critical"

### 4. API Usage Dashboard (`api-usage.json`)

**Overview:** API consumption patterns and user analytics

**Panels:**
- **Request Volume**: Total requests over time
- **Unique Users**: Daily active users (by IP)
- **Top Endpoints**: Most frequently called endpoints
- **Response Sizes**: Average and p95 response sizes
- **Geographic Distribution**: Requests by region (if GeoIP enabled)
- **User Agents**: Browser/client distribution
- **Cache Hit Rate**: Redis cache effectiveness
- **Database Query Count**: Queries per endpoint
- **Slowest Endpoints**: Endpoints with highest p99 latency

**Metrics:**
- Total requests today
- New users this week
- Average response time
- Cache hit rate %

### 5. Database Performance Dashboard (`database.json`)

**Overview:** Database health and performance metrics

**Panels:**
- **Connection Pool**: Active connections vs. pool size
- **Query Rate**: Queries per second by type (SELECT, INSERT, UPDATE, DELETE)
- **Query Latency**: p50, p95, p99 query times
- **Slow Queries**: Queries taking > 1 second
- **Database Size**: Total database size over time
- **Table Sizes**: Largest tables
- **Index Usage**: Index hit ratio
- **Lock Wait Time**: PostgreSQL lock wait duration
- **Replication Lag**: Primary-replica lag (if applicable)

**Alerts:**
- Connection pool > 90% utilized
- Slow queries > 1 second
- Database errors > 5/minute

## Importing Dashboards

### Method 1: Manual Import

1. Open Grafana (http://localhost:3000)
2. Login (default: admin/admin)
3. Click "+" → "Import"
4. Upload JSON file or paste JSON content
5. Select Prometheus datasource
6. Click "Import"

### Method 2: Automated Provisioning

Add to `docker-compose.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  volumes:
    - ./infrastructure/grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
    - ./infrastructure/monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
```

### Method 3: Grafana API

```bash
# Import dashboard via API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @system-health.json
```

## Dashboard Variables

All dashboards support these template variables:

- `$environment`: production, staging, development
- `$city`: Vallejo, (future: other cities)
- `$timerange`: Time range for queries (default: Last 24 hours)
- `$interval`: Aggregation interval (default: 1m)

## Common Prometheus Queries

### API Latency (p95)
```promql
histogram_quantile(0.95,
  sum(rate(ibco_http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)
```

### Error Rate
```promql
(
  sum(rate(ibco_http_requests_total{status=~"5.."}[5m]))
  /
  sum(rate(ibco_http_requests_total[5m]))
) * 100
```

### Request Rate
```promql
sum(rate(ibco_http_requests_total[5m])) by (endpoint)
```

### Database Connection Pool Utilization
```promql
(ibco_database_connections_active / ibco_database_connections_pool_size) * 100
```

### Data Staleness (days)
```promql
(time() - ibco_data_last_update_timestamp) / 86400
```

### Risk Score Current Value
```promql
ibco_risk_score_current{city="Vallejo"}
```

## Alert Integration

Dashboards include alert annotations:

- **Warning (Yellow)**: Performance degradation, but not critical
- **Critical (Red)**: Service disruption, immediate action required
- **Info (Blue)**: Notable events (deployments, data updates)

## Customization

To customize dashboards:

1. Import base dashboard
2. Click "Dashboard settings" (gear icon)
3. Click "JSON Model"
4. Edit JSON
5. Save as new dashboard

## Recommended Layout

**Primary Monitor:**
- System Health Dashboard (auto-refresh: 30s)

**Secondary Monitor:**
- API Usage Dashboard (auto-refresh: 1m)
- Database Performance Dashboard (auto-refresh: 1m)

**Operational Dashboard:**
- Data Freshness Dashboard (auto-refresh: 5m)
- Risk Score Trends Dashboard (auto-refresh: 1h)

## Grafana Alerts

Configure alert notifications in Grafana:

1. Settings → Notification channels
2. Add channel (Email, Slack, PagerDuty, etc.)
3. Test notification
4. Link to dashboard panels

## Best Practices

1. **Set appropriate time ranges**: Use Last 24h for ops, Last 30d for trends
2. **Enable auto-refresh**: 30s for real-time, 5m for historical
3. **Use variables**: Filter by environment, city, endpoint
4. **Share dashboards**: Export as JSON, commit to git
5. **Document changes**: Add version/change notes in dashboard description
6. **Test alerts**: Verify thresholds trigger correctly
7. **Review regularly**: Update queries as metrics evolve

## Troubleshooting

**Dashboard not loading:**
- Check Prometheus is scraping metrics: http://localhost:9090/targets
- Verify datasource: Settings → Data Sources → Prometheus
- Check query syntax in panel edit mode

**Missing metrics:**
- Ensure application is exposing /metrics endpoint
- Check Prometheus scrape config
- Verify metrics are being incremented (check Prometheus query)

**Slow queries:**
- Reduce time range
- Increase aggregation interval
- Use recording rules for complex queries

## References

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [IBCo Observability Guide](https://docs.ibco-ca.us/operations/observability)
