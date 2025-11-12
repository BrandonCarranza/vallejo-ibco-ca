# Data Refresh Workflow Guide

## Overview

The IBCo Vallejo Console implements an automated **Data Refresh Orchestration** workflow to manage the periodic updating of municipal fiscal data through manual entry. This system coordinates:

1. **Automated checks** for new source documents (CAFRs, CalPERS valuations)
2. **Email notifications** to operators when new data is available
3. **Post-entry validation** and analytics pipeline
4. **Change reporting** to stakeholders

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Data Refresh Workflow                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Scheduled Checks (APScheduler)                          │
│     ├── Quarterly CAFR checks (Jan, Apr, Jul, Oct)         │
│     └── Annual CalPERS checks (July)                        │
│                                                             │
│  2. Web Scraping (BeautifulSoup)                            │
│     ├── Scrape Vallejo finance website for CAFRs           │
│     └── Check CalPERS website for valuations                │
│                                                             │
│  3. Notification System (SMTP)                              │
│     ├── Email operators when new documents found           │
│     └── Track acknowledgment and completion                 │
│                                                             │
│  4. Manual Data Entry                                       │
│     ├── Operator uses scripts/data_entry/ tools            │
│     └── Data entered into database                          │
│                                                             │
│  5. Post-Entry Pipeline (Automated)                         │
│     ├── Validate entered data                               │
│     ├── Recalculate risk scores                             │
│     ├── Regenerate financial projections                    │
│     └── Generate "what changed" report                      │
│                                                             │
│  6. Stakeholder Reporting                                   │
│     ├── HTML change report generation                       │
│     └── Email to stakeholders                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Database Models

Four new models track the refresh workflow:

- **`RefreshCheck`**: Records of automated checks for new documents
- **`RefreshNotification`**: Email notifications sent to operators
- **`RefreshOperation`**: Complete data refresh operations from entry to analytics
- **`DataRefreshSchedule`**: Configuration for scheduled checks

## Usage

### 1. Running the Scheduler (Production)

The scheduler runs continuously, checking for new documents on a defined schedule:

```bash
# Start the scheduler daemon (runs indefinitely)
python scripts/maintenance/schedule_refresh.py
```

**Schedule:**
- **CAFR checks**: 15th of January, April, July, October at 9:00 AM
- **CalPERS checks**: 15th of July at 10:00 AM

### 2. Manual Testing

For testing, run checks manually:

```bash
# Run all checks once
python scripts/maintenance/schedule_refresh.py --run-once

# Run only CAFR check
python scripts/maintenance/schedule_refresh.py --run-once --cafr-only

# Run only CalPERS check
python scripts/maintenance/schedule_refresh.py --run-once --calpers-only
```

### 3. Manual Entry Process

When an operator receives a notification email:

1. **Download the source document** from the URL provided in the email
2. **Run the appropriate entry script**:
   ```bash
   # For CAFR entry
   python scripts/data_entry/manual_cafr_entry.py

   # For CalPERS entry
   python scripts/data_entry/manual_calpers_entry.py
   ```
3. **Follow the prompts** to enter data
4. **System automatically validates** and runs analytics

### 4. Triggering Post-Entry Pipeline

The post-entry pipeline normally runs automatically after data entry. To manually trigger:

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/admin/refresh/trigger-pipeline/1/2024" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or via Python
from src.config.database import SessionLocal
from src.data_pipeline.orchestration.refresh_workflows import DataRefreshOrchestrator

db = SessionLocal()
orchestrator = DataRefreshOrchestrator(db)
operation = orchestrator.trigger_post_entry_pipeline(
    city_id=1,
    fiscal_year=2024,
    operation_type="cafr_entry"
)
db.close()
```

### 5. Generating Change Reports

After a refresh operation completes:

```bash
# Generate report for most recent operation
python scripts/maintenance/refresh_report.py --city-id 1

# Generate and save as HTML
python scripts/maintenance/refresh_report.py --city-id 1 --output report.html

# Generate and email to stakeholders
python scripts/maintenance/refresh_report.py --city-id 1 --email

# Generate for specific operation
python scripts/maintenance/refresh_report.py --operation-id 42 --output report.html
```

## API Endpoints

### Check Refresh Status

```http
GET /api/v1/admin/refresh/status?city_id=1
```

**Response:**
```json
{
  "city_id": 1,
  "city_name": "Vallejo",
  "last_cafr_check": "2024-01-15T09:00:00Z",
  "last_calpers_check": "2024-07-15T10:00:00Z",
  "pending_notifications": 1,
  "in_progress_operations": 0,
  "recent_checks": [...],
  "recent_operations": [...],
  "data_completeness": [...],
  "next_expected_cafr": "Next quarterly check (Jan/Apr/Jul/Oct 15th)",
  "next_expected_calpers": "Next annual check (July 15th)"
}
```

### Trigger Manual Check

```http
POST /api/v1/admin/refresh/trigger-check/1
Content-Type: application/json

{
  "check_type": "cafr"
}
```

### Get Operation Details

```http
GET /api/v1/admin/refresh/operations/42
```

### Get Notifications

```http
GET /api/v1/admin/refresh/notifications/1?pending_only=true
```

## Workflow Steps in Detail

### Step 1: Scheduled Check

Every quarter (for CAFRs) or annually (for CalPERS), the scheduler:

1. Scrapes the Vallejo finance website
2. Looks for links containing "CAFR" or "Comprehensive Annual Financial Report"
3. Extracts fiscal year from link text (e.g., "FY2024")
4. Checks if this fiscal year already has CAFR recorded in database
5. If new document found, records `RefreshCheck` in database

### Step 2: Notification

If new document found:

1. Creates `RefreshNotification` record
2. Sends HTML email to operators with:
   - Document URL
   - Estimated entry time (60-120 min for CAFR, 10-15 min for CalPERS)
   - Step-by-step instructions
   - Links to entry scripts

### Step 3: Manual Entry

Operator:

1. Downloads PDF from URL
2. Runs appropriate entry script
3. Transcribes data following prompts
4. Marks notification as complete

### Step 4: Post-Entry Pipeline

Automatically runs after entry completes:

#### 4a. Validation
- Validates data completeness
- Checks for logical consistency
- Verifies required fields
- Records validation results in `RefreshOperation`

#### 4b. Risk Score Recalculation
- Fetches previous risk score (if exists)
- Calculates new risk score using updated data
- Records both previous and new scores in operation
- Updates `RiskScore` table

#### 4c. Projection Regeneration
- Fetches previous fiscal cliff year (if exists)
- Regenerates financial projections with new data
- Updates projection scenarios
- Records fiscal cliff changes

#### 4d. Duration Tracking
- Records completion time
- Calculates pipeline duration
- Marks operation as completed/failed

### Step 5: Change Report

After pipeline completes:

1. Compares before/after metrics:
   - Risk score change (e.g., 68 → 72)
   - Risk level change (e.g., Medium → Medium-High)
   - Fiscal cliff year movement (e.g., 2028 → 2027)
   - Revenue/expenditure changes from prior year
   - Pension liability updates
2. Generates HTML report with:
   - Executive summary
   - Detailed comparison tables
   - Visual indicators (improved/worsened/unchanged)
3. Optionally emails report to stakeholders

## Configuration

### Email Settings

Configure in `.env`:

```env
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@ibco-ca.us
ADMIN_EMAILS=["operator@ibco-ca.us", "admin@ibco-ca.us"]
```

### Web Scraping Settings

```env
VALLEJO_CAFR_BASE_URL=https://www.cityofvallejo.net/
USER_AGENT=IBCo-Data-Collector/1.0 (+https://ibco-ca.us)
SCRAPER_RATE_LIMIT=1.0
EXTERNAL_API_TIMEOUT=30
```

### Feature Flags

```env
ENABLE_WEB_SCRAPING=true
ENABLE_AUTO_PROJECTIONS=true
```

## Monitoring

### View Refresh Status

```bash
# Check status via API
curl http://localhost:8000/api/v1/admin/refresh/status?city_id=1 | jq

# Check database directly
psql -d ibco_vallejo -c "SELECT * FROM refresh_checks ORDER BY performed_at DESC LIMIT 10;"
psql -d ibco_vallejo -c "SELECT * FROM refresh_operations WHERE status='in_progress';"
```

### Logs

All refresh operations are logged with structured logging:

```bash
# View refresh-related logs
docker logs ibco-api | grep "refresh"

# View specific operations
docker logs ibco-api | grep "operation_id=42"
```

### Metrics (Prometheus)

The following metrics are available:

- `ibco_refresh_checks_total`: Total number of refresh checks performed
- `ibco_refresh_checks_found`: Number of checks that found new documents
- `ibco_refresh_operations_total`: Total refresh operations
- `ibco_refresh_operations_duration_seconds`: Duration of refresh operations
- `ibco_refresh_validations_failed`: Number of failed validations

## Troubleshooting

### No Email Sent

**Problem**: Check runs successfully but no email notification

**Solutions**:
1. Check `ENABLE_EMAIL_NOTIFICATIONS=true` in `.env`
2. Verify SMTP credentials are correct
3. Check spam folder
4. Review logs: `docker logs ibco-api | grep "email_sent"`

### Scraping Fails

**Problem**: `scraping_success=False` in `RefreshCheck`

**Solutions**:
1. Check website is accessible: `curl https://www.cityofvallejo.net/`
2. Verify `USER_AGENT` is set
3. Website structure may have changed - update scraping logic in `CAFRAvailabilityChecker`
4. Check `scraping_error` field in database for details

### Validation Fails

**Problem**: Post-entry pipeline fails at validation step

**Solutions**:
1. Review `validation_errors` in `RefreshOperation`
2. Check data completeness in `FiscalYear` table
3. Manually re-run validation: `python scripts/validation/validate_fiscal_year.py --city-id 1 --year 2024`
4. Fix data issues and re-trigger pipeline

### Pipeline Stalls

**Problem**: `RefreshOperation` stuck in `in_progress` status

**Solutions**:
1. Check for Python exceptions in logs
2. Verify database connectivity
3. Check if analytics services are running (Celery workers)
4. Manually mark as failed: `UPDATE refresh_operations SET status='failed' WHERE id=42;`
5. Re-trigger pipeline

## Best Practices

### For Operators

1. **Acknowledge notifications promptly** to avoid duplicate checks
2. **Complete data entry in one session** to ensure consistency
3. **Double-check transcribed values** before submitting
4. **Review validation errors** immediately and fix before proceeding
5. **Monitor change reports** to catch anomalies

### For Administrators

1. **Monitor scheduler health**: Ensure `schedule_refresh.py` is running
2. **Review failed operations**: Check `status='failed'` in `refresh_operations`
3. **Update scraping logic**: When city website structure changes
4. **Test before production**: Use `--run-once` to test scheduling
5. **Keep documentation updated**: Document any customizations

### For Developers

1. **Log liberally**: Use structured logging for all operations
2. **Handle exceptions gracefully**: Don't let one city's failure stop others
3. **Make scraping robust**: Handle missing elements, timeouts, redirects
4. **Test with real PDFs**: Don't rely on synthetic data
5. **Version control migrations**: Always create Alembic migrations for model changes

## Future Enhancements

Potential improvements for future waves:

1. **OCR/PDF extraction**: Automate data extraction from CAFRs
2. **RSS feed monitoring**: Subscribe to city finance RSS feeds
3. **Multi-city scaling**: Generalize scraping for all CA cities
4. **Slack notifications**: Alternative to email for operators
5. **Retry logic**: Automatically retry failed scraping attempts
6. **Scheduling UI**: Web interface for configuring schedules
7. **Change detection alerts**: Alert when risk score jumps significantly
8. **Historical comparisons**: Multi-year trend analysis in reports

## Related Documentation

- [Manual Data Entry Workflow](./data_entry_workflow.md)
- [API Authentication Guide](./api_authentication_guide.md)
- [Data Validation Guide](./data_validation.md)
- [Risk Scoring Methodology](../METHODOLOGY.md)

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/ibco-ca/vallejo-ibco-ca/issues
- **Email**: support@ibco-ca.us
- **Documentation**: https://docs.ibco-ca.us
