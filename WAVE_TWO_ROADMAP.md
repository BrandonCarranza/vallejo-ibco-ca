# IBCo Wave Two Implementation Roadmap
## Data Reality → Production Hardening → Community Infrastructure

**Wave One Status:** ✅ Complete (15/15 prompts, infrastructure ready)
- Database schema: 5 model domains, Alembic configured
- API: 25+ endpoints, middleware, health checks
- Analytics: Transparent risk scoring, multi-scenario projections
- Tests: 50+ unit + integration tests
- Deployment: Docker, nginx, automation scripts
- **Manual data entry tools: CAFR & CalPERS CSV importers ready**

**Wave Two Objective:** Transform infrastructure into living civic accountability system
- Load real Vallejo data (manual entry workflow) and validate end-to-end
- Harden for production use under adversarial conditions
- Build operational workflows for data quality assurance
- Create public-facing interface (dashboard, reports, narratives)
- Implement community features (decision logging, stakeholder communication)
- Prepare legal defense infrastructure

**Philosophy:** Manual data entry is FAST, ACCURATE, and DEFENSIBLE. Automation is optional enhancement, not requirement.

---

## PHASE 7: DATA REALITY & VALIDATION

### Prompt 7.1: Initialize Database & Load Vallejo Data (Manual Entry)

```
Execute Alembic migration to create live schema, then manually enter Vallejo fiscal data using existing CSV import tools.

CONTEXT: Infrastructure is ready but empty. Wave One built robust manual data entry tools
(scripts/data_entry/import_cafr_manual.py and import_calpers_manual.py). This prompt:
1. Creates actual database schema (Alembic migration)
2. Uses MANUAL transcription workflow to load historical data
3. Validates end-to-end system functionality

WHY MANUAL ENTRY:
- FASTER than building extraction automation (1-2 hours per fiscal year)
- 100% ACCURATE (human-verified at source)
- DEFENSIBLE (complete data lineage to source document & transcriber)
- PROVEN workflow (scripts already built and tested)

DELIVERABLES:
1. Alembic initial migration (auto-generated from models)
   ```bash
   poetry run alembic revision --autogenerate -m "Initial schema"
   poetry run alembic upgrade head
   ```

2. Manual data entry for Vallejo FY2020-2024 (5 most recent years):
   - Transcribe from Vallejo CAFRs (revenues, expenditures, fund balance)
   - Transcribe from CalPERS valuations (pension data, UAL, contribution rates)
   - Use existing CSV import scripts (scripts/data_entry/)
   - Estimated effort: 1-2 hours per year = 5-10 hours total

3. Data validation & reconciliation:
   - Create `scripts/validation/validate_data_integrity.py`
   - Verify totals match CAFR summaries
   - Check fund balance formula: beginning + revenues - expenditures = ending
   - Flag any transcription errors for correction

4. Calculate historical risk scores:
   - Create `scripts/analysis/calculate_historical_risk_scores.py`
   - Run risk scoring engine on all loaded fiscal years
   - Generate risk score progression report

5. Generate 10-year projections:
   - Run projection engine with base/optimistic/pessimistic scenarios
   - Identify fiscal cliff year
   - Validate projection outputs are sensible

VERIFICATION:
- `psql ibco_dev -c "\dt"` shows all 15+ tables
- Manual entry completes without errors (CSV import validation works)
- Data integrity checks pass (reconciliation to source documents)
- Risk scores show logical progression over time
- Fiscal cliff analysis identifies likely crisis year
- API endpoints return valid data for all years

EFFORT ESTIMATE:
- Alembic setup: 30 minutes
- Manual transcription (5 years): 5-10 hours
- Validation scripts: 2-3 hours
- Risk score calculation: 1 hour
- Total: ~10-15 hours of focused work

EXPANSION PATH:
- Start with FY2020-2024 (5 years, most recent)
- Later: Add FY2015-2019 if historical comparison needed
- Quality over quantity: nail 5 years perfectly before expanding
```

### Prompt 7.2: Build CAFR PDF Extraction Pipeline (OPTIONAL FUTURE ENHANCEMENT)

```
⚠️ OPTIONAL - NOT REQUIRED FOR WAVE TWO MVP ⚠️

Manual entry is FASTER for MVP. Build this later if scaling to 50+ cities.

CONTEXT: Manual transcription works great for 1-2 cities. If expanding to state network,
automated extraction becomes valuable. But for Vallejo alone, manual entry is superior:
- Manual: 1-2 hours per year, 100% accurate
- Automated: 40+ hours to build extractor, 85-95% accuracy, requires review workflow

This prompt describes future automation if/when needed.

DELIVERABLES (if building later):
1. `src/data_pipeline/extractors/cafr_extractor.py`
   - PDFPlumber integration for table extraction
   - CAFR structure recognition (balance sheet, revenue/expenditure detail)
   - Confidence scoring (flag low-confidence extractions for manual review)

2. `src/data_pipeline/transformers/cafr_validator.py`
   - Validate extracted totals vs. reported totals
   - Year-over-year anomaly detection
   - Reconciliation with manual entry (if available)

KEY CHALLENGES:
- CAFR format varies year-to-year (different auditors, layouts)
- Table structures inconsistent across pages
- OCR errors require manual review anyway
- Building extractor is 20-40 hours of work

RECOMMENDATION: Skip for now. Manual entry is proven and fast.
```

### Prompt 7.3: Implement CalPERS Pension Data Scraper (OPTIONAL FUTURE ENHANCEMENT)

```
⚠️ OPTIONAL - NOT REQUIRED FOR WAVE TWO MVP ⚠️

Manual entry from CalPERS PDFs is straightforward and accurate.

CONTEXT: CalPERS publishes annual valuation reports (PDFs). Key pension metrics
(funded ratio, UAL, contribution rates) are in summary tables. Manual transcription
takes ~15 minutes per year. Building a scraper takes 20+ hours and still requires
validation. For Vallejo alone, manual entry is superior.

This prompt describes future automation if/when scaling to many cities.

DELIVERABLES (if building later):
1. `src/data_pipeline/extractors/calpers_scraper.py`
   - CalPERS public data portal integration
   - Identify Vallejo pension plans (MISCV, PEPRA, etc.)
   - Extract funded status, UAL, contribution schedules

2. `src/data_pipeline/transformers/calpers_validator.py`
   - Reasonableness checks (funded ratio 0-150%, UAL positive)
   - Reconciliation with CAFR pension notes

KEY CHALLENGES:
- CalPERS data has 3-6 month publication lag
- Plan structure complex (multiple plans per city)
- Historical data not always available online
- Building scraper is 20+ hours of work

RECOMMENDATION: Skip for now. Manual entry works great.
```

### Prompt 7.4: Create Data Quality Dashboard & Validation Framework

```
Build validation framework for manually-entered data to ensure integrity before public release.

CONTEXT: Manual entry is fast and accurate, but human error happens. Need validation
framework to catch:
- Transcription typos (revenues in millions entered as billions)
- Math errors (fund balance doesn't reconcile)
- Year-over-year anomalies (20% revenue drop unexplained)
- Missing data (forgot to enter pension plan)

DELIVERABLES:
1. `src/data_quality/validators.py` (300+ lines)
   - Data quality rules (type checks, range checks, relationship constraints)
   - Cross-table reconciliation (revenues - expenditures = fund balance change)
   - Year-over-year anomaly detection (flag >25% changes)
   - Temporal consistency (newer data can't contradict older data)

2. `src/data_quality/quality_metrics.py`
   - Calculate completeness: % of fields populated
   - Calculate consistency: cross-table reconciliation score
   - Track validation status: pending → validated → published
   - Generate quality scorecards by fiscal year

3. `src/api/v1/routes/admin/quality_dashboard.py`
   - Internal endpoint: `/api/v1/admin/quality-status`
   - Shows: data completeness matrix, validation alerts, reconciliation issues
   - Sortable by severity (critical/warning/info)

4. `scripts/validation/generate_quality_report.py`
   - Comprehensive quality report (HTML + JSON)
   - Year-by-year breakdown
   - Anomaly summary with explanations
   - Recommendations for follow-up

VALIDATION RULES (for manual entry):
- Financial: revenues > 0, expenditures > 0, fund balance can be negative
- Pension: funded ratio 0-150%, UAL ≥ 0, contribution rate < 50% of payroll
- Reconciliation: fund balance change = revenues - expenditures ± transfers (within 2%)
- Temporal: each year's values reasonable vs. prior year (flag >25% unexplained changes)

ALERTS:
- Critical: Missing core data (no revenues/expenditures for a year)
- Critical: Reconciliation failure (fund balance doesn't match formula)
- Warning: Anomalous change (>25% vs. prior year, no annotation)
- Info: Data entered but not yet reviewed

WORKFLOW:
1. Operator manually enters data via CSV import
2. Validation runs automatically
3. Quality dashboard shows any issues
4. Operator reviews flagged items
5. Corrections made, re-validate
6. When quality score >95%, mark as "validated" and publish

OUTPUT:
- Dashboard URL: `http://localhost:8000/api/v1/admin/quality-dashboard`
- Shows real-time validation status before public API release
```

---

## PHASE 8: PRODUCTION HARDENING

### Prompt 8.1: Implement Observability & Monitoring

```
Add structured logging, metrics, and alerting for production resilience.

DELIVERABLES:
1. `src/config/observability.py` (structured logging, metrics)
   - Structured JSON logging (request ID, duration, status, user agent)
   - Prometheus metrics export (response times, database queries, errors)
   - Alert thresholds (API latency >1s, error rate >1%, database errors)

2. `infrastructure/monitoring/prometheus.yml`
   - Scrape metrics from API /metrics endpoint
   - Database connection pool monitoring
   - Request latency histograms (p50, p95, p99)

3. `infrastructure/monitoring/alerting_rules.yml`
   - Alert: API latency spike (p95 >1s for 5 minutes)
   - Alert: database connection exhaustion (pool >90% full)
   - Alert: data staleness (last data update >6 months ago)

4. `infrastructure/grafana-dashboards/`
   - System health: uptime, response times, error rates
   - Data freshness: last CAFR entry, last CalPERS entry
   - Risk score trends: Vallejo score progression over time
   - API usage: endpoints called, unique visitors, response sizes

INTEGRATION:
- Add Prometheus + Grafana to docker-compose.prod.yml
- Export metrics to external monitoring (optional: DataDog, Honeycomb)
- Set up email/SMS alerts for critical issues
```

### Prompt 8.2: Add API Rate Limiting & Request Authentication

```
Implement rate limiting and optional token authentication for API protection.

DELIVERABLES:
1. `src/api/middleware/rate_limiting.py`
   - Redis-backed rate limiting
   - Public tier: 100 requests/hour (no auth required)
   - Researcher tier: 1000 requests/hour (JWT token)
   - Burst allowance: 20 requests/10 seconds

2. `src/api/auth/tokens.py`
   - JWT token generation for researchers, journalists, civil society
   - Token types: public (read-only), researcher (bulk export endpoints)
   - Expiration: 1 year (long-lived for accessibility)
   - Revocation support (blacklist)

3. `scripts/admin/generate_api_tokens.py`
   - CLI tool to issue tokens to known requesters
   - Track: who has token, issue date, purpose, contact info
   - Output token + usage instructions

4. `src/api/v1/routes/admin/tokens.py`
   - Admin endpoint to revoke/regenerate tokens
   - View active tokens and usage statistics

RATIONALE:
- Rate limiting protects infrastructure from abuse
- Authentication enables graduated access tiers
- Public API remains fully accessible (no auth required for basic queries)
- Researcher tier supports bulk analysis without hitting limits
```

### Prompt 8.3: Implement Dead-Man's Switch & Data Persistence

```
Build automated backup, archival, and dead-man's switch system.

DELIVERABLES:
1. `scripts/maintenance/backup_strategy.py`
   - Daily database snapshots to S3/Backblaze B2
   - Weekly full backups (database + data files)
   - Quarterly archival to Glacier/cold storage
   - 7-year retention for legal discovery
   - Backup verification (restore test monthly)

2. `scripts/maintenance/dead_mans_switch.py`
   - Weekly operator check-in requirement
   - If no check-in for 30 days: auto-publish dataset to GitHub
   - Publish: database dump + source documents + methodology docs
   - Ensures data survives if operator silenced/incapacitated

3. `src/api/v1/routes/admin/health_checkin.py`
   - POST /api/v1/admin/checkin: operator pings system
   - Resets 30-day dead-man's timer
   - Returns: days until auto-publish, last check-in date

4. Infrastructure automation:
   - S3/B2 bucket setup with lifecycle policies
   - GitHub Actions workflow for auto-publication
   - Email notifications at 7 days / 3 days / 1 day before trigger

RATIONALE:
- Dead-man's switch is insurance against suppression
- If legal action silences operator, data auto-publishes
- Ensures civic transparency outlasts any individual
- "Streisand Effect" baked into infrastructure
```

---

## PHASE 9: OPERATIONAL WORKFLOWS

### Prompt 9.1: Implement Data Refresh Orchestration (Manual Entry Workflow)

```
Build workflow for periodic data refresh via manual entry.

CONTEXT: Manual entry is ongoing process. When new CAFR/CalPERS reports publish,
need workflow to:
1. Notify operator that new data available
2. Guide manual entry process
3. Run validation automatically
4. Recalculate risk scores and projections
5. Generate "what changed" report

DELIVERABLES:
1. `src/data_pipeline/orchestration/refresh_workflows.py`
   - Quarterly check: Is new CAFR available? (scrape Vallejo finance website for new PDFs)
   - Annual check: Is new CalPERS valuation available?
   - Generate notification: "FY2025 CAFR published - ready for manual entry"
   - After manual entry: auto-run validation, risk scoring, projections

2. `scripts/maintenance/schedule_refresh.py`
   - Scheduled check (quarterly): Are new source documents available?
   - Email operator: "New data available, please transcribe"
   - After entry: trigger validation + analytics pipeline
   - APScheduler integration (or cron job)

3. `scripts/maintenance/refresh_report.py`
   - Generate "what changed" report after new data entered
   - Compare: new risk score vs. prior year
   - Compare: fiscal cliff year (did it move?)
   - Highlight: biggest changes (revenue/expenditure categories)
   - Output: HTML report + email to stakeholders

4. `src/api/v1/routes/admin/refresh_status.py`
   - Endpoint: GET /api/v1/admin/refresh-status
   - Shows: last data entry date, next expected CAFR, data completeness

WORKFLOW:
```
Quarterly (Jan, Apr, Jul, Oct):
  1. Check if new Vallejo CAFR published
  2. If yes: email operator with PDF link
  3. Operator manually enters data (1-2 hours)
  4. System auto-validates data
  5. If validation passes: recalculate risk scores, regenerate projections
  6. Generate "what changed" report
  7. Publish report to dashboard

Annual (each July after CalPERS publishes):
  1. Check for new CalPERS valuation
  2. Email operator with valuation PDF link
  3. Operator manually enters pension data (15 minutes)
  4. System validates + recalculates pension stress indicators
  5. Update projections with new pension assumptions
```
```

### Prompt 9.2: Build Data Lineage & Audit Trail System

```
Implement comprehensive data lineage tracking for forensic accountability.

CONTEXT: Manual entry requires provenance tracking. Every data point must trace to:
- Source document (CAFR page 34, CalPERS valuation page 12)
- Transcriber (who entered it, when)
- Reviewer (who validated it, notes)
- Confidence score (100% for manual entry with validation)

This is CRITICAL for legal defense. Any claim must show complete chain of custody.

DELIVERABLES:
1. Enhanced data models (extend existing DataLineage table):
   - Track: source document URL/path, page number, table name
   - Track: transcriber name, entry timestamp, notes
   - Track: reviewer name, validation timestamp, approval notes
   - Immutable audit log (no deletes, only appends)

2. `src/analytics/lineage_tracer.py`
   - Function: trace any data point back to source
   - Example: Risk score → pension funded ratio → CalPERS valuation page 12
   - Generate complete evidence chain with timestamps

3. `scripts/reports/generate_lineage_report.py`
   - For any data point: show complete provenance
   - Include: source document, page, transcriber, reviewer, confidence
   - Output: HTML report with clickable source links

4. Public endpoint: `/api/v1/metadata/lineage/{data_point_id}`
   - Returns complete chain of custody for any metric
   - Public transparency: anyone can audit data provenance

EXAMPLE OUTPUT:
```
Risk Score FY2024: 68 (High)
└─ Pension Funded Ratio: 62%
   └─ Source: CalPERS Actuarial Valuation, June 30, 2024
      URL: https://www.calpers.ca.gov/.../vallejo_2024.pdf
      Page: 12, Table 5
      ├─ Market Value Assets: $4.2B (transcribed by: Jane Doe, 2024-08-01 10:30 UTC)
      ├─ Total Pension Liability: $6.8B (transcribed by: Jane Doe, 2024-08-01 10:35 UTC)
      └─ Calculation: 4.2 / 6.8 = 0.62 (62% funded)
   └─ Validation: Approved by John Smith, 2024-08-02 14:20 UTC
      Notes: "Cross-checked with CAFR pension note, values match"
      Confidence: 100% (manual entry, validated)

└─ Structural Deficit: $45M
   └─ Source: Vallejo CAFR FY2024, Basic Financial Statements
      URL: https://www.cityofvallejo.net/.../CAFR_2024.pdf
      Page: 34, Statement of Activities
      ├─ Total Revenues: $298M (transcribed by: Jane Doe, 2024-07-15 09:00 UTC)
      ├─ Total Expenditures: $343M (transcribed by: Jane Doe, 2024-07-15 09:15 UTC)
      └─ Calculation: 298 - 343 = -45 (deficit)
   └─ Validation: Approved by Jane Doe, 2024-07-15 11:00 UTC
      Notes: "Matches CAFR summary totals, fund balance reconciles"
      Confidence: 100% (manual entry, reconciled)
```

RATIONALE:
- Forensic accountability: every claim traceable to source
- Legal defense: complete evidence chain
- Public trust: full transparency of methodology
- Manual entry advantage: 100% confidence scores (vs. 85-95% for automation)
```

### Prompt 9.3: Create Manual Review & Validation Workflow

```
Build human-in-the-loop validation workflow for manually-entered data.

CONTEXT: Manual entry is accurate but not perfect. Need workflow for:
1. Peer review (second person validates first person's entry)
2. Anomaly flagging (system alerts to unusual values)
3. Correction workflow (fix errors, document changes)

DELIVERABLES:
1. `src/api/v1/routes/admin/review_queue.py`
   - GET /api/v1/admin/review-queue: returns items pending validation
   - Items: newly entered data, flagged anomalies, reconciliation issues
   - Sortable by: severity (critical/warning), fiscal year, data type

2. `src/api/v1/routes/admin/validation_endpoint.py`
   - POST /api/v1/admin/validate/{item_id}: approve/reject data
   - Fields: validator name, approval status, notes, confidence adjustment
   - Stores immutable validation record

3. `scripts/reports/review_report.py`
   - Daily/weekly report of items pending validation
   - By severity: critical (reconciliation failures), warning (anomalies), info (new entry)
   - Email to validator: "3 items need review"

4. Validation workflow states:
   - ENTERED: data manually entered, not yet reviewed
   - FLAGGED: validation rules detected anomaly
   - APPROVED: reviewer confirmed data correct
   - CORRECTED: reviewer fixed error, documented change
   - PUBLISHED: approved data made public via API

WORKFLOW:
```
Manual entry completes → Validation check:
  - Run automated validation rules
  - If all pass: mark APPROVED (auto-approve if reconciliation perfect)
  - If anomalies: mark FLAGGED, add to review queue

Reviewer sees:
  - Flagged item with context (entered value, prior year value, validation rule violated)
  - Source document reference (CAFR page image, CalPERS table)
  - Suggested action (approve as-is, correct value, investigate further)

Reviewer action:
  - APPROVE: value correct despite anomaly (add note explaining why)
  - CORRECT: fix transcription error, document change
  - INVESTIGATE: escalate for deeper review

After approval:
  - Item marked PUBLISHED
  - Data available via public API
  - Lineage includes validation timestamp + reviewer notes
```

RATIONALE:
- Peer review catches transcription errors
- Anomaly detection finds unusual values (typos, formula errors)
- Documented validation builds institutional credibility
```

---

## PHASE 10: PUBLIC INTERFACE

### Prompt 10.1: Build Metabase Dashboard Configuration

```
Create production Metabase dashboards for public visualization of Vallejo fiscal data.

DELIVERABLES:
1. `src/dashboard/metabase/dashboards/vallejo_fiscal_overview.json`
   - Revenue trends (available historical years)
   - Expenditure trends (by category: public safety, pensions, etc.)
   - Fund balance trajectory (shows reserve depletion or accumulation)
   - Risk score progression (shows improving/deteriorating fiscal health)

2. `src/dashboard/metabase/dashboards/pension_analysis.json`
   - Pension funded ratio trend (track toward/away from full funding)
   - UAL growth vs. city revenues (shows burden magnitude)
   - Employer contribution burden (% of payroll)
   - Projection: pension costs as % of budget (shows crowding out other services)

3. `src/dashboard/metabase/dashboards/fiscal_projections.json`
   - 10-year projection: base vs. optimistic vs. pessimistic scenarios
   - Fiscal cliff identification: when do reserves run out?
   - Sensitivity analysis: what % revenue increase avoids cliff?
   - Key driver visualization: what's causing the crisis? (pensions, revenue decline, etc.)

4. `src/dashboard/metabase/dashboards/peer_comparison.json` (if multi-city data available)
   - Vallejo vs. other CA cities: risk scores, funded ratios, fiscal health
   - Ranking: which CA cities in worst shape?

5. Public access configuration:
   - URL: `https://ibco-ca.us/dashboard/` (or embedded in ibco-ca.us)
   - Read-only Metabase embeds (no login required)
   - Auto-refresh nightly after data updates

INTEGRATION:
- Connect Metabase to PostgreSQL (docker-compose already includes it)
- Create read-only database user for Metabase
- Import dashboard configurations via Metabase API
- Set refresh schedule (nightly at 2am UTC)
```

### Prompt 10.2: Generate Public Reports & Narratives

```
Create automated report generation system for public communication.

DELIVERABLES:
1. `src/reports/generators/fiscal_summary_report.py`
   - Generate HTML + PDF: "Vallejo Fiscal Status Report"
   - Sections:
     * Executive summary (1-paragraph fiscal health assessment)
     * Revenues (trends, sources, volatility)
     * Expenditures (trends, major categories, pension burden)
     * Pension obligations (funded status, UAL, long-term outlook)
     * Risk score (composite score, category breakdown, top concerns)
     * Projections (10-year outlook, fiscal cliff analysis)
   - Updated quarterly after new data entered
   - Include all charts from Metabase dashboards

2. `src/reports/generators/risk_narrative.py`
   - Generate human-readable narrative from risk score components
   - Example: "Vallejo's fiscal stress score of 68/100 (High) reflects significant challenges.
     Primary driver: pensions only 62% funded with $2.3B unfunded liability. At current trends,
     general fund reserves will be exhausted by FY2029, creating immediate budget crisis.
     Key risk indicators: structural deficit of $45M (15% of revenues), pension contributions
     consuming 38% of payroll, and fund balance below recommended 10% threshold."

3. `src/reports/generators/projection_scenario_report.py`
   - Compare scenarios side-by-side
   - Base case: current trends continue
   - Optimistic: pension reform + revenue growth
   - Pessimistic: pension costs accelerate + revenue decline
   - For each: fiscal cliff year, cumulative deficit, policy implications

4. `scripts/reports/publish_quarterly_report.py`
   - Generate all reports (fiscal summary, risk narrative, projections)
   - Publish to static website: ibco-ca.us/reports/FY2024_Q3.html
   - Archive all prior reports: ibco-ca.us/reports/archive/
   - Generate press release template (for media distribution)
   - Send email notifications to stakeholder list

DELIVERY FORMATS:
- HTML (web-optimized, responsive)
- PDF (printable, archival)
- JSON (machine-readable for researchers)

PUBLIC ACCESS:
- No authentication required
- Permalinks for each report (for citation)
- RSS feed for new reports
```

### Prompt 10.3: Build Public API Documentation & Examples

```
Create comprehensive API documentation for researchers and developers.

DELIVERABLES:
1. `docs/API_USAGE_GUIDE.md` (detailed guide with examples)
   - Getting started: no auth required for basic queries
   - Rate limiting: 100 req/hour public, 1000 req/hour with token
   - Endpoint reference with curl examples:
     * GET /api/v1/cities - List all cities
     * GET /api/v1/risk/cities/1/current - Latest Vallejo risk score
     * GET /api/v1/projections/cities/1/fiscal-cliff - Fiscal cliff analysis
   - Response format examples (JSON)
   - Error handling (4xx/5xx codes)

2. `docs/DEVELOPER_GUIDE.md` (for extending system)
   - How to add new risk indicators
   - How to add new projection scenarios
   - How to contribute data (manual entry workflow)
   - Database schema documentation
   - Code contribution guidelines

3. `src/api/v1/routes/__init__.py` (OpenAPI enhancements)
   - Complete OpenAPI tags & descriptions
   - Example requests/responses for each endpoint
   - Auto-generate interactive Swagger docs at /docs

4. `scripts/docs/generate_api_reference.py`
   - Auto-generate API reference from OpenAPI spec
   - Include: all endpoints, parameters, response schemas
   - Update on each deployment

5. Code examples:
   - `examples/python_client.py` - Python requests usage
   - `examples/fetch_risk_scores.js` - JavaScript fetch() usage
   - `examples/curl_commands.sh` - Curl examples for common queries
   - `examples/data_analysis.ipynb` - Jupyter notebook for researchers

DISTRIBUTION:
- Host at: docs.ibco-ca.us (GitHub Pages or ReadTheDocs)
- Link from main site and API responses
- Include in researcher token emails
```

---

## PHASE 11: COMMUNITY INFRASTRUCTURE

### Prompt 11.1: Implement Decision Logging & City Council Integration

```
Build system to log city council decisions and track fiscal impact predictions vs. outcomes.

DELIVERABLES:
1. `src/database/models/civic.py` (Decision, Vote, Outcome models)
   - Track: city council votes on budget, tax measures, bonds, labor contracts
   - Store: decision date, description, fiscal impact prediction, actual outcome
   - Link: to affected fiscal years (future impact tracking)

2. `src/api/v1/routes/admin/decisions.py`
   - POST /api/v1/admin/decisions: manually log new council decision
   - Fields: date, title, description, predicted fiscal impact (± $M/year)
   - GET /api/v1/decisions: public query by date/category/impact

3. `src/analytics/decision_impact.py`
   - Predict fiscal impact of proposed decision
   - Example: "Sales tax increase → +$25M annual recurring revenue"
   - Example: "Labor contract → +$5M annual personnel costs"
   - Track actual impact 6-12 months later
   - Calculate prediction accuracy (builds institutional credibility)

4. `scripts/reports/decision_impact_report.py`
   - Quarterly: show all logged decisions
   - Compare predictions to actual outcomes
   - Highlight: accurate predictions (builds trust)
   - Acknowledge: inaccurate predictions (transparent about errors)

EXAMPLE WORKFLOW:
```
Decision logged (Nov 2024): Vallejo voters approve Measure V (sales tax increase)
Prediction: +$25M annual recurring revenue (entered manually by analyst)
Status: Pending outcome (will track FY2025 actual revenues)

Update (Jun 2025): First 6 months actuals available
Actual: +$12.5M (on track for full-year estimate)
Comment: "Some collection delays from new businesses, but trending as predicted"

Final update (Dec 2025): Full-year actuals available
Actual: +$26M annual revenue
Accuracy: 104% of prediction (within 4%)
Comment: "Better than predicted due to strong economic growth and high compliance"
```

RATIONALE:
- Tracking predictions vs. outcomes builds institutional credibility
- Transparent about both successes and failures
- Demonstrates analytical rigor
- Informs future decision analysis
```

### Prompt 11.2: Create Stakeholder Communication Framework

```
Build system for transparent communication with media, council, civil society.

DELIVERABLES:
1. `src/api/v1/routes/public/notifications.py`
   - Automated alerts when key metrics change:
     * Risk score increases (e.g., 65 → 70)
     * Fiscal cliff year moves closer (e.g., FY2031 → FY2029)
     * Pension funded ratio drops below threshold
   - Alert format: brief summary + link to details

2. `scripts/communications/email_alerts.py`
   - Quarterly email to subscriber list
   - Summary: risk score trend, new data entered, projection updates
   - Links: latest reports, dashboards, source documents
   - Unsubscribe option (respect privacy)

3. `scripts/communications/press_release_template.py`
   - Auto-generate press release from quarterly data
   - Template: "IBCo Vallejo Fiscal Analysis: Q3 2024 Update"
   - Include: risk score, key findings, fiscal cliff analysis, quote from methodology
   - Ready for media distribution

4. `src/api/v1/routes/admin/stakeholder_list.py`
   - Manage email subscriber list
   - Categories: media, council, civil society, researchers
   - One-way notification (no replies to system email)
   - Privacy-respecting (GDPR compliant, easy unsubscribe)

COMMUNICATION PHILOSOPHY:
- Strictly non-partisan: data only, no policy advocacy
- Let data speak for itself
- Separate facts (risk scores) from interpretation (implications)
- Transparent about methodology and limitations
- Responsive to questions but not prescriptive about solutions
```

### Prompt 11.3: Build SLAPP Defense & Legal Infrastructure

```
Implement legal defense automation for cease-and-desist, defamation claims, and harassment.

DELIVERABLES:
1. `docs/LEGAL_DEFENSE_PLAYBOOK.md` integration
   - Anti-SLAPP motion templates (already exist in docs/legal/)
   - Integrate into system: auto-generate responses
   - EFF/ACLU contact protocols
   - Media liability insurance documentation

2. `src/api/v1/routes/admin/legal_incidents.py`
   - POST /api/v1/admin/legal-incident: log cease-and-desist, threat, lawsuit
   - Track: incident type, sender, date received, response sent, resolution
   - Immutable log (preserved for discovery)

3. `scripts/legal/generate_anti_slapp_response.py`
   - Template-based cease-and-desist response generator
   - Auto-cite: data sources (CAFR page X, CalPERS document Y)
   - Auto-cite: methodology (transparent risk scoring, open source code)
   - Auto-cite: disclaimers (independent analysis, not predictions)
   - Output: draft response ready for legal counsel review

4. `src/database/models/legal.py` (LegalIncident, LegalResponse models)
   - Track all legal threats
   - Link to affected data points (show provenance)
   - Store response templates and outcomes
   - Public log (transparency about suppression attempts)

5. `scripts/reports/legal_incident_report.py`
   - Public transparency report: all legal incidents
   - Show: threat type, IBCo response, outcome
   - Demonstrate: suppression attempts fail

INTEGRATION WITH DEAD-MAN'S SWITCH:
- If legal incident logged: reduce dead-man's timer to 7 days
- If lawsuit filed: immediately publish full dataset + legal documents
- Ensures: suppression attempts backfire (Streisand Effect)
- Message: "Threatening IBCo triggers immediate data publication"

RATIONALE:
- Proactive legal defense infrastructure
- Automated response generation saves legal fees
- Public transparency about suppression attempts
- Dead-man's switch integration makes suppression counterproductive
```

---

## PHASE 12: EXPANSION & SUSTAINABILITY

### Prompt 12.1: Multi-City Architecture & Data Federation

```
Prepare infrastructure for expansion from Vallejo to additional CA cities.

CONTEXT: Database schema already supports multiple cities. Phase 12 activates multi-city
features and creates onboarding workflow.

DELIVERABLES:
1. `scripts/setup/onboard_new_city.py`
   - Wizard: add new city to system
   - Prompts: city name, county, population, fiscal year end, CAFR source, pension plans
   - Creates: City record, first FiscalYear, data source placeholders
   - Generates: CSV templates for manual entry

2. `src/data_pipeline/city_configs/`
   - `vallejo.yaml` - Vallejo configuration (CAFR URL, pension plans, etc.)
   - `stockton.yaml` - Template for Stockton (second city)
   - `oakland.yaml` - Template for Oakland (optional)
   - Used by: import scripts, validation, reporting

3. `src/api/v1/routes/cities.py` enhancements
   - GET /api/v1/cities: list all tracked cities
   - GET /api/v1/cities/{city_id}/... (all endpoints work for any city)
   - Comparative endpoints: GET /api/v1/cities/compare?city_ids=1,2,3

4. `src/dashboard/metabase/dashboards/state_overview.json`
   - Compare all tracked CA cities
   - State-wide risk trends
   - Identify: which cities approaching fiscal crisis?
   - Ranking: worst to best fiscal health

EXPANSION SEQUENCING:
- Wave Two: Perfect Vallejo (nail one city completely)
- Future: Add Stockton as second city (validates multi-city logic)
- Future: Expand to 3-5 cities (Riverside, San Bernardino, Oakland)
- Future: CA state network (ibco-ca.us covers all at-risk CA cities)
- Future: Other states (IBDo federal system)

MANUAL ENTRY SCALING:
- Vallejo alone: 5-10 hours/year
- 5 cities: 25-50 hours/year (feasible for one dedicated volunteer)
- 20 cities: 100-200 hours/year (requires team or automation)
```

### Prompt 12.2: Research Partner Integration

```
Build secure data sharing for university researchers and fiscal policy organizations.

DELIVERABLES:
1. `src/api/v1/routes/research/data_exports.py`
   - POST /api/v1/research/export-request: researcher requests dataset
   - Formats: CSV, JSON, Excel
   - Track: who downloaded what, when, for what research purpose

2. `src/api/auth/research_tokens.py`
   - Special researcher token tier
   - Rate limit: 10,000 requests/hour (vs. 1000 for standard tier)
   - Access: bulk export endpoints, historical raw data
   - Requires: institutional affiliation, research purpose, data use agreement

3. `scripts/research/manage_research_partnerships.py`
   - Track: partner institutions, Principal Investigators, active projects
   - Generate: data sharing agreements (template)
   - Monitor: token usage, citation compliance

4. `docs/RESEARCH_COLLABORATION.md`
   - How to request research access
   - Data sharing policies (open data, attribution required)
   - Citation requirements (how to cite IBCo data)
   - Example use cases (published research using IBCo data)

TARGET RESEARCH PARTNERS:
- UC Berkeley Institute of Government Studies
- SF State Urban Analysis Institute
- Stanford Hoover Institution
- Lincoln Institute of Land Policy
- Mercatus Center
- Community Initiatives (fiscal sponsorship)
```

### Prompt 12.3: Funding & Governance Model

```
Implement fiscal sustainability and governance structure.

DELIVERABLES:
1. `docs/GOVERNANCE_MODEL.md`
   - Decision-making structure: non-partisan board
   - Advisory council: civic leaders, researchers, civil society
   - Public comment periods for major methodology changes
   - Conflict of interest policies

2. `src/api/v1/routes/admin/funding_tracker.py`
   - Public endpoint: GET /api/v1/funding
   - Disclose: all funding sources, amounts, any restrictions
   - Transparency: who supports IBCo financially?
   - Updated annually

3. `scripts/reports/annual_transparency_report.py`
   - Annual report: funding sources and allocation
   - Impact metrics: cities tracked, decisions informed, media coverage
   - Financial sustainability: current funding vs. operating costs
   - Future plan: fundraising targets, growth strategy

4. `docs/SUSTAINABILITY_PLAN.md`
   - Operating costs: hosting ($50-100/month), development (volunteer + occasional contract)
   - Revenue model: philanthropic grants (fiscal sponsorship via Community Initiatives)
   - Growth plan: when can system self-sustain?
   - Endowment goal: $500K-$1M for perpetual operation

FUNDING STRATEGY:
- Initial: Volunteer-run, minimal costs (hosting only)
- Early stage: Small grants (local foundations, civic tech funds)
- Growth: Larger grants (Open Philanthropy, Arnold Ventures, etc.)
- Sustainable: Municipal subscriptions (cities pay sliding scale for access)
- Endowment: Major donor or foundation creates permanent fund
```

---

## EXECUTION PRIORITY

**CRITICAL PATH (do these first):**
1. **Prompt 7.1: Database + Manual Entry** - UNBLOCKS EVERYTHING ELSE
   - Run Alembic migration
   - Manually enter Vallejo FY2020-2024 (5 years)
   - Calculate risk scores, generate projections
   - Verify end-to-end system works

2. **Prompt 9.2: Data Lineage** - Legal defense backbone
   - Track every data point to source document
   - Forensic accountability for all claims
   - Essential for legal defense

3. **Prompt 7.4: Data Quality Dashboard** - Validate before public release
   - Ensure manual entry is error-free
   - Build confidence in data accuracy

4. **Prompt 10.1: Metabase Dashboards** - Public interface
   - Visualize Vallejo fiscal data
   - Make complex data accessible

**HIGH PRIORITY (do these next):**
5. **Prompt 8.3: Dead-Man's Switch** - Insurance against suppression
6. **Prompt 10.2: Public Reports** - Narrative communication
7. **Prompt 10.3: API Documentation** - Enable researcher access
8. **Prompt 8.1: Monitoring** - Production reliability
9. **Prompt 9.3: Manual Review Workflow** - Quality assurance

**MEDIUM PRIORITY (valuable but not urgent):**
10. Prompt 8.2: Rate Limiting & Auth
11. Prompt 11.2: Stakeholder Communications
12. Prompt 11.3: Legal Defense Infrastructure
13. Prompt 11.1: Decision Logging

**LOWER PRIORITY (nice-to-have):**
14. Prompt 9.1: Refresh Orchestration (until routine updates needed)
15. Prompt 12.1: Multi-City Architecture (until ready to expand)
16. Prompt 12.2: Research Partnerships (once data proven valuable)
17. Prompt 12.3: Funding & Governance (once operational)

**SKIP FOR NOW (optional future enhancements):**
- Prompt 7.2: CAFR PDF Extraction (manual entry works great)
- Prompt 7.3: CalPERS Scraping (manual entry works great)

---

## SUCCESS METRICS

Wave Two is successful when:
- ✅ Vallejo data loaded (FY2020-2024 minimum, all manually entered and validated)
- ✅ Risk scores calculated for all loaded years
- ✅ 10-year projections generated (base/optimistic/pessimistic scenarios)
- ✅ Fiscal cliff year identified with confidence intervals
- ✅ Dashboard live showing fiscal trends and risk progression
- ✅ API documented and publicly accessible
- ✅ Data lineage complete (every metric traceable to source document)
- ✅ Dead-man's switch configured and tested
- ✅ Legal defense infrastructure in place (response templates, incident logging)
- ✅ Public reports published (fiscal summary, risk narrative)

**Outcome:** Vallejo has transparent, defensible fiscal accountability system that:
- Survives legal challenges (complete data provenance)
- Survives operator suppression (dead-man's switch)
- Informs public discourse with non-partisan data
- Outlasts any political cycle or individual operator

---

## PHILOSOPHY: MANUAL ENTRY ADVANTAGE

**Why manual entry beats automation for Wave Two:**

1. **Speed**: 1-2 hours per year vs. 40+ hours to build extractor
2. **Accuracy**: 100% accurate (human-verified) vs. 85-95% (requires review)
3. **Defensibility**: Complete provenance (transcriber + reviewer + source page)
4. **Simplicity**: CSV import tools already built and tested
5. **Reliability**: No OCR errors, format changes, or scraper breakage
6. **Flexibility**: Can handle any format (old CAFRs, scanned PDFs, etc.)

**When to build automation:**
- Scaling to 20+ cities (manual entry becomes bottleneck)
- Routine monthly updates (automation saves recurring effort)
- Historical backfill (extracting 10+ years per city)

**For Vallejo alone:** Manual entry is superior in every way.

---

**Ready to begin Wave Two?** Start with Prompt 7.1 (Database + Manual Entry).
