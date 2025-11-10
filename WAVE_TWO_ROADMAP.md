# IBCo Wave Two Implementation Roadmap
## Data Reality → Production Hardening → Community Infrastructure

**Wave One Status:** ✅ Complete (15/15 prompts, infrastructure ready)
- Database schema: 5 model domains, Alembic configured
- API: 25+ endpoints, middleware, health checks
- Analytics: Transparent risk scoring, multi-scenario projections
- Tests: 50+ unit + integration tests
- Deployment: Docker, nginx, automation scripts

**Wave Two Objective:** Transform infrastructure into living civic accountability system
- Load real Vallejo data and validate end-to-end
- Harden for production use under adversarial conditions
- Build operational workflows for data refresh & quality assurance
- Create public-facing interface (dashboard, reports, narratives)
- Implement community features (voting, oversight, decision logging)
- Prepare legal defense infrastructure

---

## PHASE 7: DATA REALITY & VALIDATION

### Prompt 7.1: Initialize Database & Load Sample Vallejo Data

```
Execute Alembic migration to create live schema, then seed with real Vallejo fiscal data (FY2015-2024).

CONTEXT: Infrastructure is ready but empty. This prompt creates the actual database schema
and loads 10 years of Vallejo historical data to validate:
- Database schema works end-to-end
- Risk scoring produces sensible outputs
- Projections calculate correctly
- API endpoints return valid JSON

DELIVERABLES:
1. Alembic initial migration (auto-generated from models)
2. Seed script with Vallejo FY2015-2024 data:
   - CAFR-extracted financial data (revenues, expenditures)
   - CalPERS pension data (funded ratios, UAL, contribution rates)
   - Fund balance history
   - Personnel costs, OPEB obligations
3. Data validation checks:
   - Revenue totals match CAFR summaries
   - Expenditure categories reconcile
   - Fund balance calculations are consistent
   - Pension data matches CalPERS reports
4. Risk score calculation on all historical years
5. Projection generation for FY2025-2034 (10-year forecast)
6. Comparison of calculated risk scores vs. external assessments

EXECUTION:
- Create `scripts/data/seed_vallejo_production.py` (Vallejo complete dataset)
- Create `scripts/validation/validate_data_integrity.py` (reconciliation checks)
- Create `scripts/analysis/calculate_historical_risk_scores.py`
- Update `.env.example` with Vallejo-specific database seed instructions

RUN ALEMBIC:
```bash
poetry run alembic revision --autogenerate -m "Initial schema"
poetry run alembic upgrade head
```

VERIFY:
- `psql ibco_dev -c "\dt"` shows all 15+ tables
- Seed script loads without errors
- Validation script confirms data integrity
- Risk scores show progression (improving/deteriorating trend over 10 years)
- Fiscal cliff analysis identifies likely crisis year
```

### Prompt 7.2: Build CAFR PDF Extraction Pipeline

```
Implement automated CAFR PDF extraction to populate Financial, Pension, and Risk models from official documents.

CONTEXT: Vallejo produces annual Comprehensive Annual Financial Reports (CAFRs). These PDFs contain:
- Audited financial statements (revenues, expenditures, fund balance)
- Pension actuarial data (funded ratios, contribution rates)
- Debt schedules
- Management discussion & analysis (MD&A)

This prompt creates extractors that:
1. Download/ingest CAFR PDFs
2. Extract key financial tables (OCR-resistant structured data)
3. Normalize to IBCo schema
4. Validate against prior year data (consistency checks)
5. Flag anomalies for manual review

DELIVERABLES:
1. `src/data_pipeline/extractors/cafr_extractor.py` (300+ lines)
   - PDFPlumber integration for table extraction
   - CAFR document structure recognition
   - Multi-table extraction (balance sheet, revenue detail, expenditure detail)
   - Fiscal year detection from document metadata
2. `src/data_pipeline/transformers/cafr_validator.py`
   - CAFR-to-schema mapping validation
   - Reconciliation: extracted totals vs. reported totals
   - Year-over-year anomaly detection
   - Confidence scoring (high/medium/low based on extraction clarity)
3. `scripts/data/extract_historical_cafrs.py`
   - Batch process: Vallejo CAFRs FY2015-2024
   - Store raw CAFR text extraction in data/raw/cafr/
   - Generate extraction report with confidence scores
4. `scripts/validation/reconcile_cafr_to_database.py`
   - Verify extracted data matches loaded database
   - Flag discrepancies for manual investigation
   - Generate extraction quality report

KEY CHALLENGES:
- CAFR format varies year-to-year (different auditors, formats)
- Table structures are visually consistent but XML inconsistent
- Some tables span multiple pages
- Handle OCR errors gracefully

VALIDATION:
- Extract Vallejo FY2024 CAFR (most recent)
- Verify: total revenues extracted match official total
- Verify: total expenditures match official total
- Verify: fund balance formula (beginning + revenues - expenditures = ending)
- Compare extraction confidence to manual audit
- Handle: malformed tables → manual entry fallback
```

### Prompt 7.3: Implement CalPERS Pension Data Scraper

```
Build CalPERS public data scraper to populate PensionPlan, PensionContribution, and projection models.

CONTEXT: CalPERS publishes:
- Funded status reports (funded ratio, market value of assets, UAL)
- Valuation data (discount rates, mortality assumptions)
- Contribution schedules (employer/employee rates by plan)
- Actuarial assumptions (inflation, payroll growth, life expectancy)

These are scattered across CalPERS website and PDFs. This prompt:
1. Identifies Vallejo's pension plans with CalPERS
2. Scrapes/fetches official pension data
3. Extracts key metrics (funded ratio, UAL, contribution rates)
4. Normalizes to PensionPlan schema
5. Tracks assumption changes (discount rate movements, etc.)

DELIVERABLES:
1. `src/data_pipeline/extractors/calpers_scraper.py` (250+ lines)
   - CalPERS public data portal integration
   - Plan identification: retrieve all Vallejo plans
   - Metrics extraction: funded status, UAL, contribution rates
   - Historical data retrieval (retroactive 5+ years if available)
   - Assumption tracking (rate changes, methodology updates)
2. `src/data_pipeline/transformers/calpers_validator.py`
   - CalPERS-to-schema mapping validation
   - Reasonableness checks (funded ratio 0-150%, UAL positive)
   - Anomaly detection (sudden assumption changes)
   - Reconciliation: CalPERS data vs. Vallejo CAFR pension section
3. `scripts/data/scrape_calpers_vallejo.py`
   - Batch scrape: All Vallejo plans
   - Store raw JSON/CSV in data/raw/calpers/
   - Generate scrape report with timestamps
4. `scripts/validation/reconcile_calpers_to_cafr.py`
   - Compare CalPERS funded ratios to CAFR pension notes
   - Flag discrepancies (usually timing differences)
   - Document assumption changes quarter-by-quarter

KEY CHALLENGES:
- CalPERS publishes data with 3-6 month lag
- Plan structure for Vallejo complex (MISCV, PEPRA, etc.)
- Discount rate changes affect UAL projections significantly
- Some historical data unavailable online

INTEGRATION:
- Create PensionPlan records for each Vallejo CalPERS plan
- Track discount rate history (critical for projection sensitivity)
- Store assumption changes in ScenarioAssumption table
- Link to FinancialProjection.assumptions for scenario modeling
```

### Prompt 7.4: Create Data Quality Dashboard & Validation Framework

```
Build validation framework and internal quality dashboard to ensure data integrity before public release.

CONTEXT: After loading data from multiple sources (CAFR, CalPERS, manual entry), need:
1. Data quality metrics (completeness, accuracy, timeliness)
2. Validation rules (revenues > 0, expenditures > 0, etc.)
3. Reconciliation checks (cross-source consistency)
4. Anomaly alerts (unusual year-over-year changes)
5. Manual review workflow (flag items for human verification)

DELIVERABLES:
1. `src/data_quality/validators.py` (300+ lines)
   - Data quality rules (type, range, relationship constraints)
   - Cross-table reconciliation checks
   - Year-over-year anomaly detection (std dev threshold)
   - Temporal consistency (no backwards-looking data modifications)
2. `src/data_quality/quality_metrics.py`
   - Calculate: % complete, % validated, data freshness, anomaly count
   - Generate quality scorecards by data source
   - Track validation status transitions (pending → validated → published)
3. `src/api/v1/routes/admin/quality_dashboard.py`
   - Internal-only endpoint: `/api/v1/admin/quality-status`
   - Returns: Data completeness matrix, validation alerts, reconciliation issues
   - Sortable by severity (critical/warning/info)
4. `scripts/validation/generate_quality_report.py`
   - Comprehensive data quality report (HTML + JSON)
   - Source-by-source breakdown
   - Anomaly summary with explanations
   - Recommendations for follow-up

VALIDATION RULES:
- Financial: revenues, expenditures, fund balance all positive
- Pension: funded ratio 0-150%, UAL positive, contribution rate <50%
- Reconciliation: CAFR financials ± 2% to source documents
- Temporal: each fiscal year's values reasonable vs. prior years

ALERTS:
- Critical: Missing revenue/expenditure data (>5% of budget)
- Warning: Anomalous change (>25% vs. prior year, unexplained)
- Info: Data not yet validated by human reviewer

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
   - Structured JSON logging (request ID, duration, status)
   - Prometheus metrics export (response times, database queries, errors)
   - Alert thresholds (API latency >1s, error rate >1%)
2. `infrastructure/monitoring/prometheus.yml`
   - Scrape metrics from API /metrics endpoint
   - Database connection pool monitoring
   - Request latency histograms
3. `infrastructure/monitoring/alerting_rules.yml`
   - Alert on API latency spike
   - Alert on database connection exhaustion
   - Alert on data staleness (CAFR not updated in >6 months)
4. `infrastructure/grafana-dashboards/`
   - System health (uptime, response times, error rates)
   - Data freshness (last CAFR import, last CalPERS sync)
   - Risk score trends (Vallejo score progression)
   - API usage (endpoints called, response sizes)

INTEGRATION:
- Wire into Docker compose stack
- Export to external monitoring (DataDog, Honeycomb, or self-hosted)
```

### Prompt 8.2: Add API Rate Limiting & Request Authentication

```
Implement rate limiting and optional token authentication for API protection.

DELIVERABLES:
1. `src/api/middleware/rate_limiting.py`
   - Redis-backed rate limiting
   - Default: 100 requests/hour (public)
   - Higher tier: 1000 requests/hour (authenticated)
   - Burst allowance: 20 requests/10s
2. `src/api/auth/tokens.py`
   - JWT token generation for researchers, journalists, civil society
   - Token types: public (read-only), researcher (advanced endpoints)
   - Expiration: 1 year (long-lived for accessibility)
3. `scripts/admin/generate_api_tokens.py`
   - Tool to issue tokens to known requesters
   - Track: who has token, issue date, purpose
4. `src/api/v1/routes/admin/tokens.py`
   - Internal admin endpoint to revoke, regenerate tokens

RATIONALE: Rate limiting protects infrastructure; authentication enables graduated access without breaking public API
```

### Prompt 8.3: Implement Dead-Man's Switch & Data Persistence

```
Build automated backup, archival, and dead-man's switch system.

DELIVERABLES:
1. `scripts/maintenance/backup_strategy.py`
   - Daily snapshots to S3 (database dump + data files)
   - Quarterly archival to Glacier
   - 7-year retention for legal discovery
2. `scripts/maintenance/dead_mans_switch.py`
   - Scheduled verification: operator pings system weekly
   - If no ping in 30 days: auto-publish latest dataset to GitHub
   - Ensures data lives if operator unavailable
3. `src/api/v1/routes/admin/health_checkin.py`
   - POST /api/v1/admin/checkin (operator pings system)
   - Resets dead-man's timer
4. Infrastructure: automated S3 upload + GitHub release publication

CONTEXT: You've described this. Build it.
```

---

## PHASE 9: OPERATIONAL WORKFLOWS

### Prompt 9.1: Implement Data Refresh Orchestration

```
Build automated monthly/quarterly data refresh workflow.

DELIVERABLES:
1. `src/data_pipeline/orchestration/refresh_workflows.py`
   - Monthly: download latest CAFR (if available), scrape CalPERS
   - Quarterly: full data validation + quality checks
   - Automatic: risk score recalculation on all years
   - Automatic: projection regeneration with updated assumptions
2. `scripts/maintenance/schedule_refresh.py`
   - Celery/APScheduler integration
   - Trigger: 1st of each month at 2am UTC
   - Retry logic: if download fails, retry in 2 days
3. `scripts/maintenance/refresh_report.py`
   - Generate summary: data updated, new risk scores, projection changes
   - Publish to admin dashboard
4. `src/api/v1/routes/admin/refresh_status.py`
   - Endpoint to check data refresh status
   - Shows: last refresh date, next scheduled refresh, any errors

WORKFLOW:
```
Monthly refresh:
  1. Attempt CAFR download from Vallejo finance website
  2. Extract tables, validate against prior year
  3. If extraction confidence >95%: auto-load to database
  4. If <95%: flag for manual review
  5. Scrape CalPERS for Vallejo pension updates
  6. Recalculate risk scores for all fiscal years
  7. Regenerate 10-year projections
  8. Publish refresh report to dashboard
```
```

### Prompt 9.2: Build Data Lineage & Audit Trail System

```
Implement comprehensive data lineage tracking for forensic accountability.

DELIVERABLES:
1. `src/database/models/metadata.py` (DataLineage, AuditLog models)
   - Track: every data point's source document, extraction method, confidence score
   - Track: every modification (who changed what when, why)
   - Immutable audit log (no delete, only append)
2. `src/analytics/lineage_tracer.py`
   - Trace: fiscal year risk score → back to source CAFR → specific page/table
   - Generate: "evidence chain" for any claim
3. `scripts/reports/generate_lineage_report.py`
   - For any data point: show complete provenance
   - Include: document date, extraction method, confidence, reviewer notes
4. Public endpoint: `/api/v1/metadata/lineage/{data_point_id}`
   - Returns complete chain of custody for any metric

EXAMPLE OUTPUT:
```
Risk Score FY2024: 68 (High)
└─ Pension Funded Ratio: 62%
   └─ CalPERS Valuation Report, 2024-06-30
      └─ Market Value Assets: $4.2B
      └─ Total Pension Liability: $6.8B
      └─ Confidence: 99% (official document)
   └─ Manual Review: John Smith, 2024-07-15 (approved)
└─ Structural Deficit: $45M
   └─ Vallejo CAFR FY2024, page 34
      └─ Total Revenues: $298M
      └─ Total Expenditures: $343M
      └─ Confidence: 97% (PDF extraction)
   └─ Manual Review: Jane Doe, 2024-08-01 (approved with note: education costs spike from infrastructure investment)
```
```

### Prompt 9.3: Create Manual Review & Validation Workflow

```
Build human-in-the-loop workflow for data validation before public release.

DELIVERABLES:
1. `src/api/v1/routes/admin/review_queue.py`
   - GET /api/v1/admin/review-queue: returns flagged data items
   - Items: extracted data with confidence <95%, anomalies, reconciliation mismatches
2. `src/api/v1/routes/admin/validation_endpoint.py`
   - POST /api/v1/admin/validate/{item_id}: approve/reject data
   - Stores: validator name, timestamp, notes, confidence adjustment
3. `scripts/reports/review_report.py`
   - Daily report of items pending validation
   - By severity: critical (>$10M impact), warning (>$1M), info
4. UI component (if implementing frontend):
   - Review dashboard: see flagged items, approve/reject, add notes

WORKFLOW:
```
Data extraction completes → validation check:
  - If confidence >95%: auto-approve
  - If 80-95%: flag for review
  - If <80%: manual entry required
  
Reviewer sees:
  - Extracted value + context (page image, nearby text)
  - Prior year value for comparison
  - Suggested correction if applicable
  
Reviewer action:
  - Approve (confidence increases)
  - Reject + suggest correction (confidence resets)
  - Flag anomaly (gets escalated)
```
```

---

## PHASE 10: PUBLIC INTERFACE

### Prompt 10.1: Build Metabase Dashboard Configuration

```
Create production Metabase dashboards for public visualization of Vallejo fiscal data.

DELIVERABLES:
1. `src/dashboard/metabase/dashboards/vallejo_fiscal_overview.json`
   - Revenue trends (10-year history)
   - Expenditure trends (by category)
   - Fund balance trajectory
   - Risk score progression
2. `src/dashboard/metabase/dashboards/pension_analysis.json`
   - Funded ratio trend
   - UAL growth vs. revenues
   - Contribution burden trend
   - Projection: pension as % of payroll
3. `src/dashboard/metabase/dashboards/fiscal_projections.json`
   - 10-year projection comparison (base vs. optimistic vs. pessimistic)
   - Fiscal cliff identification: when does reserves run out?
   - Sensitivity analysis: what % revenue increase avoids cliff?
4. `src/dashboard/metabase/dashboards/peer_comparison.json`
   - Vallejo vs. other CA cities (Oakland, Stockton, San Jose, etc.)
   - Risk score comparison
   - Funded ratio comparison
5. Public URL: `https://ibco-ca.us/dashboard/`
   - Embed read-only Metabase dashboards
   - No login required for public views

INTEGRATION:
- Connect Metabase to PostgreSQL
- Configure read-only database user
- Import dashboards via API
- Set refresh schedule (nightly)
```

### Prompt 10.2: Generate Public Reports & Narratives

```
Create automated report generation system for public communication.

DELIVERABLES:
1. `src/reports/generators/fiscal_summary_report.py`
   - HTML + PDF report: "Vallejo Fiscal Status Report"
   - Sections: revenues, expenditures, pension obligations, risk score
   - Include: historical trends, projections, key risks
   - Updated quarterly
2. `src/reports/generators/risk_narrative.py`
   - Generate human-readable narrative of risk score
   - Example: "Vallejo's fiscal stress score of 68/100 reflects significant challenges. Primary concern: pensions are only 62% funded, with unfunded obligations of $2.3B. At current trends, reserves will be exhausted by FY2029, creating immediate fiscal crisis."
3. `src/reports/generators/projection_scenario_report.py`
   - Compare scenarios: base case vs. pension reform vs. revenue enhancements
   - Show: outcomes under each scenario
   - Include: what would it take to avoid fiscal cliff?
4. `scripts/reports/publish_quarterly_report.py`
   - Generate all reports
   - Publish to ibco-ca.us/reports/
   - Create press release template
   - Email notifications to stakeholders

DELIVERY:
- Reports in: HTML (web), PDF (printable), JSON (machine-readable)
- Public access: no authentication required
- Archive: all reports available in /reports/archive/
```

### Prompt 10.3: Build Public API Documentation & Examples

```
Create comprehensive API documentation for researchers and developers.

DELIVERABLES:
1. `docs/API_USAGE_GUIDE.md` (detailed guide with examples)
   - Authentication (if token-based)
   - Rate limiting (public vs. authenticated tiers)
   - Endpoint reference: query examples in curl, Python, JavaScript
   - Example: "Get Vallejo risk score for FY2024"
   - Example: "Get 10-year projection for scenario='pension_reform'"
   - Example: "Compare Vallejo vs. peer cities"
2. `docs/DEVELOPER_GUIDE.md` (for extending system)
   - How to add new indicators
   - How to add new scenarios
   - How to contribute data sources
3. `src/api/v1/routes/__init__.py` (OpenAPI tags & descriptions)
   - Auto-generate Swagger/OpenAPI documentation
   - Public at: `/api/v1/docs`
4. `scripts/docs/generate_api_reference.py`
   - Auto-generate API reference from code
   - Update on each deploy
5. Code examples repository structure:
   - `examples/python_client.py` - Python API client
   - `examples/fetch_risk_scores.js` - JavaScript example
   - `examples/curl_commands.sh` - Simple curl examples

DISTRIBUTION:
- Publish to ReadTheDocs or GitHub Pages
- Host at: docs.ibco-ca.us or ibco-ca.us/docs
```

---

## PHASE 11: COMMUNITY INFRASTRUCTURE

### Prompt 11.1: Implement Decision Logging & City Council Integration

```
Build system to log city council decisions and track fiscal impact predictions vs. outcomes.

DELIVERABLES:
1. `src/database/models/civic.py` (Decision, Vote, Outcome models)
   - Track: city council votes on budget, bonds, rate increases
   - Store: vote date, description, fiscal impact prediction, actual outcome
2. `src/api/v1/routes/admin/decisions.py`
   - POST /api/v1/admin/decisions: log new council decision
   - GET /api/v1/decisions: public query by date/category
3. `src/analytics/decision_impact.py`
   - Predict: fiscal impact of proposed decision (revenue increase? cost savings?)
   - Track: actual impact 6-12 months later
   - Compare: prediction vs. reality (builds institutional credibility)
4. `scripts/reports/decision_impact_report.py`
   - Quarterly: show all city council decisions logged
   - Compare predictions to actual outcomes
   - Highlight: best/worst prediction accuracy

EXAMPLE:
```
Decision (Nov 2024): Vallejo voters approve Measure V (sales tax increase)
Prediction: +$25M annual recurring revenue
Status: Logged, prediction pending outcome

Outcome (Jun 2025): First 6 months show +$12.5M
Comment: "On track for full-year estimate, some collection delays from new businesses"

Outcome (Dec 2025): Full-year shows +$26M
Comment: "Better than predicted; strong economic growth + higher compliance"
```
```

### Prompt 11.2: Create Stakeholder Communication Framework

```
Build system for transparent communication with media, council, civil society.

DELIVERABLES:
1. `src/api/v1/routes/public/notifications.py`
   - Automated alerts: "Risk score moved from 65 to 70 (High)"
   - Alerts: "Fiscal cliff year now FY2029 (was FY2031)"
   - Alerts: "Pension funded ratio dropped to 60%"
2. `scripts/communications/email_alerts.py`
   - Quarterly email to subscribers
   - Summary: risk score trend, projection updates, data refreshes
3. `scripts/communications/press_release_template.py`
   - Auto-generate press release from quarterly data updates
   - Template: "IBCo Vallejo Fiscal Analysis: Q3 2024 Update"
4. `src/api/v1/routes/admin/stakeholder_list.py`
   - Manage email list (journalists, council members, civil society groups)
   - One-way notification system (no responses to system email)

COMMUNICATION PHILOSOPHY:
- Non-partisan information, not advocacy
- Let data speak for itself
- Separate: facts (risk scores, data) from interpretation (implications)
```

### Prompt 11.3: Build SLAPP Defense & Legal Infrastructure

```
Implement legal defense automation for cease-and-desist, defamation, and harassment.

DELIVERABLES:
1. `docs/LEGAL_DEFENSE_PLAYBOOK.md` (already exists, integrate into system)
   - Anti-SLAPP motion templates by state/threat type
   - EFF/ACLU contact protocols
   - Media liability insurance documentation
2. `src/api/v1/routes/admin/legal_incidents.py`
   - Log: cease-and-desist letters, threats, legal actions
   - Track: response sent, resolution
3. `scripts/legal/generate_anti_slapp_response.py`
   - Template-based cease-and-desist response
   - Auto-cite: data sources, methodology, disclaimers
   - Ready to send to legal counsel
4. `src/database/models/legal.py` (LegalIncident, LegalResponse models)
   - Immutable log of all legal incidents
   - Preserved for potential discovery proceedings
5. `scripts/reports/legal_incident_report.py`
   - Summary: all legal incidents to date
   - Response accuracy, timeline, outcomes

INTEGRATION WITH DEAD-MAN'S SWITCH:
- If legal action detected: automatically publish full dataset + legal documents
- Ensures: suppression attempts backfire
```

---

## PHASE 12: EXPANSION & SUSTAINABILITY

### Prompt 12.1: Multi-City Architecture & Data Federation

```
Extend from Vallejo to 2nd dysfunctional CA city (Stockton or Oakland), then state network.

DELIVERABLES:
1. `src/database/models/multi_city_federation.py`
   - Multi-tenant city support (already in schema, activate it)
   - City configuration: fiscal year end, local CAFR source, pension plans
2. `scripts/setup/onboard_new_city.py`
   - Template: add new city to system
   - Configure: data sources, fiscal year, pension plans, peers
3. `src/data_pipeline/city_configs/`
   - `vallejo.yaml` - Vallejo configuration
   - `stockton.yaml` - Stockton configuration (FY2024+)
   - `oakland.yaml` - Oakland configuration (optional expansion)
4. `src/api/v1/routes/cities.py` (extend)
   - GET /api/v1/cities: returns list of all tracked cities
   - GET /api/v1/cities/{city_id}/... (all endpoints work for any city)
5. `src/dashboard/metabase/dashboards/state_overview.json`
   - Compare all CA cities tracked
   - State-wide risk trends
   - Identify: which cities approaching fiscal crisis?

SEQUENCING (strict validation per tier):
- Wave Two: Perfect Vallejo (nail one city)
- FY2025: Add Stockton (second city validates multi-city logic)
- FY2026: Expand to 3-5 CA cities
- FY2027: Deploy state network (ibco-ca.us covers entire CA)
- FY2028+: Expand to other states (IBDo federal system)
```

### Prompt 12.2: Research Partner Integration

```
Build secure data sharing for university researchers, fiscal policy groups.

DELIVERABLES:
1. `src/api/v1/routes/research/data_exports.py`
   - POST /api/v1/research/export-request: researchers request data
   - Auto-generate: CSV/JSON export of requested dataset
   - Track: who downloaded what, when, for what purpose
2. `src/api/auth/research_tokens.py`
   - Special token tier: "researcher"
   - Higher rate limit (10k requests/hour)
   - Access to: raw extracts, historical comparisons
3. `scripts/research/manage_research_partnerships.py`
   - Track: partner institutions, Principal Investigators, use agreements
   - Generate: research data sharing agreements (template)
4. `docs/RESEARCH_COLLABORATION.md`
   - How to request access
   - Data sharing policies
   - Citation requirements

RESEARCH PARTNERSHIPS:
- UC Berkeley Institute of Government Studies
- SF State Urban Analysis Institute
- Lincoln Institute of Land Policy
- Community Initiatives (fiscal sponsorship partner)
```

### Prompt 12.3: Funding & Governance Model

```
Implement fiscal sustainability model and governance structure.

DELIVERABLES:
1. `docs/GOVERNANCE_MODEL.md`
   - Decision-making structure (non-partisan board)
   - Advisory council: civic leaders, researchers, civil society
   - Public comment periods on major changes
2. `src/api/v1/routes/admin/funding_tracker.py`
   - Public disclosure: funding sources, amounts, restrictions
   - Transparency: who supports IBCo? (philanthropies, municipal grants)
3. `scripts/reports/annual_transparency_report.py`
   - Funding: sources and allocation
   - Impact: cities using system, decisions informed by data
   - Future: sustainability plan, fundraising targets
4. `docs/SUSTAINABILITY_PLAN.md`
   - Revenue model: philanthropic grants (fiscal sponsorship)
   - Cost structure: hosting ($X/month), development, operations
   - Growth plan: when can system self-sustain?

FUNDING STRATEGY:
- FY2024-2025: Grant funding (Gates, Simons, philanthropic)
- FY2025-2026: Municipal contributions (Vallejo, etc.)
- FY2026+: Membership model (cities pay sliding scale based on budget)
- Governance: Nonprofit board, fiscal sponsorship through Community Initiatives
```

---

## WAVE TWO SUMMARY

**Timeline: 6 months**

```
Month 1-2: Data Reality (Phase 7)
  - Load 10 years Vallejo data
  - Validate end-to-end
  - Confirm risk scores make sense

Month 2-3: Production Hardening (Phase 8)
  - Monitoring, alerting, dead-man's switch
  - Rate limiting, backup strategy
  - Security hardening

Month 3-4: Operational Workflows (Phase 9)
  - Automated data refresh
  - Data lineage tracking
  - Manual validation workflow

Month 4-5: Public Interface (Phase 10)
  - Dashboards, reports, narratives
  - API documentation
  - Public communication

Month 5-6: Community & Expansion (Phase 11-12)
  - Decision logging, stakeholder comms
  - Legal defense infrastructure
  - Multi-city architecture readiness

Deliverable: Production-ready civic accountability system deployed at ibco-ca.us
```

---

## EXECUTION PRIORITY

**Critical Path (do first):**
1. ✅ Prompt 7.1: Load test data (unblocks everything)
2. ✅ Prompt 7.2-7.3: CAFR + CalPERS extraction
3. ✅ Prompt 9.2: Data lineage (forensic accountability)
4. ✅ Prompt 10.1: Dashboard (public interface)

**Important (do next):**
5. Prompt 9.1: Data refresh automation
6. Prompt 10.2-10.3: Reports & API docs
7. Prompt 8.1-8.3: Production hardening

**Nice-to-have (if time):**
8. Prompt 11.1-11.3: Community features
9. Prompt 12.1-12.3: Expansion & sustainability

---

## SUCCESS METRICS

By end of Wave Two:
- ✅ Vallejo data loaded, validated, publicly queryable
- ✅ Risk scores calculated for 10 years (FY2015-2024)
- ✅ 10-year projections generated for base/optimistic/pessimistic scenarios
- ✅ Fiscal cliff year identified (likely FY2029-2030 for Vallejo)
- ✅ Dashboard live at ibco-ca.us showing trends
- ✅ API documented and rate-limited
- ✅ Data refresh automated (monthly)
- ✅ Dead-man's switch configured
- ✅ Legal defense infrastructure in place
- ✅ Media + stakeholders briefed on findings

**Outcome:** Vallejo (and California) have transparent fiscal accountability infrastructure that will outlast any political cycle.
