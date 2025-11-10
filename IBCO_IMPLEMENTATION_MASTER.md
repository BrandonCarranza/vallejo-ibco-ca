# IBCo Vallejo Console - Complete Implementation Guide
## Claude Code Optimized Prompts

**Purpose:** Sequential, comprehensive prompts for building a municipal fiscal transparency platform.

**Philosophy:**
- Build correct, not fast
- Transparency over prediction
- Data preservation as primary goal
- No funding dependencies
- Open by default

**Structure:** Each prompt is standalone and can be executed sequentially by Claude Code.

---

## PHASE 0: PROJECT FOUNDATION & LEGAL FRAMEWORK

### Prompt 0.1: Initialize Project Structure with Legal Framework

```
Create a new IBCo Vallejo Console project with the following comprehensive structure:

PROJECT ROOT: ~/ibco-vallejo-console/

Directory structure:
```
ibco-vallejo-console/
├── README.md
├── LICENSE (CC0 1.0 Universal - Public Domain)
├── DISCLAIMER.md (Legal protection)
├── METHODOLOGY.md (Transparent methodology)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── .gitignore
├── pyproject.toml (Poetry configuration)
├── docker-compose.yml
├── .env.example
├── data/                           # Data storage (gitignored except samples)
│   ├── raw/                        # Unprocessed source documents
│   │   ├── cafr/                   # CAFR PDFs by year
│   │   ├── calpers/                # CalPERS reports
│   │   ├── state_controller/      # State Controller data
│   │   └── README.md               # Data source documentation
│   ├── processed/                  # Cleaned, structured data
│   ├── archive/                    # Historical snapshots (quarterly)
│   └── samples/                    # Sample data (committed to git)
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py             # Environment configuration
│   │   ├── database.py             # Database connection
│   │   └── logging_config.py       # Structured logging
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy base
│   │   ├── models/                 # Database models (split by domain)
│   │   │   ├── __init__.py
│   │   │   ├── core.py             # Cities, fiscal years
│   │   │   ├── financial.py        # Revenues, expenditures
│   │   │   ├── pensions.py         # Pension data
│   │   │   ├── risk.py             # Risk scores
│   │   │   ├── projections.py      # Financial projections
│   │   │   └── metadata.py         # Data lineage, audit logs
│   │   └── migrations/             # Alembic migrations
│   │       ├── alembic.ini
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── extractors/             # Data extraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base extractor interface
│   │   │   ├── manual_entry.py     # Manual data entry utilities
│   │   │   ├── cafr_extractor.py   # CAFR PDF extraction
│   │   │   ├── calpers_scraper.py  # CalPERS data scraper
│   │   │   └── state_controller.py # State Controller API
│   │   ├── transformers/           # Data transformation & validation
│   │   │   ├── __init__.py
│   │   │   ├── validators.py       # Data quality checks
│   │   │   ├── normalizers.py      # Data normalization
│   │   │   └── reconciliation.py   # Cross-source data reconciliation
│   │   ├── loaders/                # Data loading to database
│   │   │   ├── __init__.py
│   │   │   ├── database_loader.py
│   │   │   └── bulk_loader.py
│   │   └── orchestration/          # Pipeline orchestration
│   │       ├── __init__.py
│   │       ├── tasks.py            # Celery tasks
│   │       └── workflows.py        # Task chains
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── risk_scoring/
│   │   │   ├── __init__.py
│   │   │   ├── indicators.py       # Individual risk indicators
│   │   │   ├── scoring_engine.py   # Composite scoring (NOT ML)
│   │   │   ├── thresholds.py       # Risk thresholds & benchmarks
│   │   │   └── explainer.py        # Risk factor explanations
│   │   ├── projections/
│   │   │   ├── __init__.py
│   │   │   ├── revenue_model.py    # Revenue projection
│   │   │   ├── expenditure_model.py # Expenditure projection
│   │   │   ├── pension_model.py    # Pension obligation projection
│   │   │   └── scenarios.py        # Scenario analysis
│   │   ├── trends/
│   │   │   ├── __init__.py
│   │   │   ├── time_series.py      # Trend analysis
│   │   │   └── peer_comparison.py  # Peer city comparison
│   │   └── reports/
│   │       ├── __init__.py
│   │       ├── generator.py        # Report generation
│   │       └── templates/          # Report templates
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── dependencies.py         # Shared dependencies
│   │   ├── middleware.py           # Custom middleware
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py       # Health checks
│   │   │   │   ├── cities.py       # City endpoints
│   │   │   │   ├── financial.py    # Financial data
│   │   │   │   ├── risk.py         # Risk scores
│   │   │   │   ├── projections.py  # Projections
│   │   │   │   └── metadata.py     # Data provenance
│   │   │   └── schemas/            # Pydantic models
│   │   │       ├── __init__.py
│   │   │       ├── city.py
│   │   │       ├── financial.py
│   │   │       ├── risk.py
│   │   │       └── common.py
│   │   └── docs/                   # API documentation customization
│   ├── dashboard/                  # Dashboard configuration
│   │   ├── metabase/
│   │   │   ├── dashboards/         # Dashboard definitions (JSON)
│   │   │   └── queries/            # SQL queries
│   │   └── README.md
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py
│       ├── financial_calcs.py      # Financial calculations
│       └── data_quality.py         # Data quality utilities
├── scripts/
│   ├── setup/
│   │   ├── install_dependencies.sh
│   │   ├── init_database.sh
│   │   └── seed_database.py
│   ├── data_entry/                 # Manual data entry scripts
│   │   ├── import_cafr_manual.py
│   │   ├── import_calpers_manual.py
│   │   └── validation_checks.py
│   ├── maintenance/
│   │   ├── backup_database.sh
│   │   ├── create_snapshot.py      # Create quarterly data snapshot
│   │   └── health_check.py
│   └── analysis/                   # Ad-hoc analysis scripts
│       ├── calculate_risk_scores.py
│       └── generate_projections.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── helpers/
├── docs/
│   ├── README.md
│   ├── architecture/
│   │   ├── SYSTEM_DESIGN.md
│   │   ├── DATABASE_DESIGN.md
│   │   └── API_DESIGN.md
│   ├── data_sources/
│   │   ├── DATA_SOURCES.md         # Comprehensive source catalog
│   │   ├── CAFR_GUIDE.md           # How to read CAFRs
│   │   └── CALPERS_GUIDE.md        # How to interpret CalPERS data
│   ├── methodology/
│   │   ├── RISK_SCORING.md         # Transparent risk methodology
│   │   ├── PROJECTIONS.md          # Projection methodology
│   │   └── VALIDATION.md           # How we validate data
│   ├── operations/
│   │   ├── DEPLOYMENT.md
│   │   ├── RUNBOOK.md
│   │   └── BACKUP_RECOVERY.md
│   ├── user_guides/
│   │   ├── USER_GUIDE.md
│   │   ├── API_GUIDE.md
│   │   └── FAQ.md
│   └── legal/
│       ├── DISCLAIMER_DETAIL.md
│       ├── DATA_LICENSE.md
│       └── PRIVACY_POLICY.md
└── infrastructure/
    ├── docker/
    │   ├── Dockerfile.api
    │   ├── Dockerfile.worker
    │   └── Dockerfile.dev
    ├── terraform/                  # Infrastructure as Code
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── monitoring/
        ├── prometheus.yml
        └── grafana-dashboards/
```

Create these key files with the following content:

**LICENSE**
```
CC0 1.0 Universal (Public Domain Dedication)

The person who associated a work with this deed has dedicated the work to the
public domain by waiving all of his or her rights to the work worldwide under
copyright law, including all related and neighboring rights, to the extent
allowed by law.

You can copy, modify, distribute and perform the work, even for commercial
purposes, all without asking permission.
```

**DISCLAIMER.md**
```
# IBCo Vallejo Console - Legal Disclaimer

## Independent Analysis

IBCo Vallejo Console is an **independent civic transparency project**. We are not affiliated with, endorsed by, or representative of:
- The City of Vallejo
- The State of California
- CalPERS (California Public Employees' Retirement System)
- Any government agency or official body

## Data Accuracy & Limitations

### Sources
All data is derived from publicly available sources:
- City of Vallejo Comprehensive Annual Financial Reports (CAFRs)
- CalPERS actuarial valuation reports
- California State Controller's Office data
- Other public documents

### Known Limitations
1. **Data Freshness**: Financial data is typically 6-18 months old by the time it's published
2. **Extraction Errors**: Data extracted from PDFs may contain errors despite validation
3. **Methodological Choices**: Our analysis methods involve judgment calls and assumptions
4. **Incomplete Picture**: Public financial data doesn't capture everything about municipal fiscal health

### Validation Process
- All data undergoes automated validation checks
- Cross-referenced against multiple sources when available
- Manual review of anomalies
- Corrections published when errors are discovered

## Risk Scores Are Not Predictions

### What Our Risk Scores ARE:
- **Composite indicators** of fiscal stress based on financial ratios
- **Relative assessments** compared to established thresholds
- **Trend analysis** showing trajectory over time
- **Transparent calculations** with documented methodology

### What Our Risk Scores ARE NOT:
- **Probability predictions** of bankruptcy (insufficient data for statistical modeling)
- **Credit ratings** (we are not a rating agency)
- **Investment advice** (do not use for bond purchase decisions)
- **Official assessments** (not endorsed by government or financial authorities)

## Limitation of Liability

### No Warranties
This platform and its data are provided "AS IS" without warranty of any kind, express or implied. We make no guarantees about:
- Accuracy or completeness of data
- Timeliness of updates
- Fitness for any particular purpose
- Availability or uptime of the service

### User Responsibility
Users of this platform are responsible for:
- Independently verifying any information before relying on it
- Consulting official sources for authoritative data
- Seeking professional advice for important decisions
- Understanding the limitations of the analysis

### No Liability
To the fullest extent permitted by law, IBCo and its contributors shall not be liable for any damages arising from use of this platform, including but not limited to:
- Financial losses
- Decisions made based on this information
- Errors or omissions in data
- Service interruptions

## Not Financial or Investment Advice

Nothing on this platform constitutes:
- Financial advice
- Investment recommendations
- Legal advice
- Accounting advice
- Professional services of any kind

For important financial decisions, consult qualified professionals.

## Municipal Securities Disclaimer

This platform publishes analysis of municipal financial health. Under MSRB Rules:
- We are not a municipal securities dealer
- We do not offer investment advice
- We do not engage in municipal securities transactions
- This is educational and informational content only

**If you are considering purchasing municipal bonds, consult a registered financial advisor and review official offering statements.**

## Data Correction Policy

We take data accuracy seriously. If you identify an error:
1. Email: data@ibco-ca.us with details
2. We will investigate within 48 hours
3. Corrections will be published promptly
4. Historical data snapshots preserve original data with correction notes

## Transparency Commitment

To maintain trust and allow verification:
- All source code is open source (MIT License)
- All data is released to the public domain (CC0)
- Methodology is fully documented
- Data lineage is tracked and exposed via API
- Regular data snapshots archived to Archive.org

## Contact

Questions or concerns: info@ibco-ca.us

Last Updated: 2025-01-10
```

**METHODOLOGY.md**
```
# IBCo Vallejo Console - Methodology

## Core Principle: Transparency Over Precision

We prioritize **transparent, understandable analysis** over complex models that cannot be explained or validated.

---

## Data Collection Methodology

### Primary Sources (In Priority Order)

1. **City of Vallejo CAFRs** (Comprehensive Annual Financial Reports)
   - Published annually, typically 6 months after fiscal year end
   - Audited by independent CPA firms
   - Most reliable source for financial data
   - Limitations: Backward-looking, point-in-time

2. **CalPERS Actuarial Valuations**
   - Published annually for each pension plan
   - Contains pension liability and funding data
   - Limitations: Based on actuarial assumptions that may prove incorrect

3. **California State Controller's Office**
   - Cities Annual Report
   - Government Compensation in California
   - Used for validation and gap-filling

4. **City Budget Documents**
   - Proposed and adopted budgets
   - Budget status reports
   - Used for forward-looking context only (not hard data)

### Data Extraction Process

#### Phase 1: Manual Entry (Initial Implementation)
For initial data collection:
1. Download source PDF from official website
2. Manually transcribe data into structured spreadsheet
3. Dual-entry validation (enter twice, compare)
4. Load via script with validation checks
5. Cross-reference against other sources

Why manual first?
- Ensures understanding of data structure
- Catches nuances that automation misses
- Faster than building robust PDF extraction
- Acceptable for 3-5 years of historical data

#### Phase 2: Semi-Automated Extraction (Future)
1. PDF text extraction with manual validation
2. Human review of all extracted values
3. Automated validation against expected ranges
4. Manual correction of flagged issues

We do NOT rely on fully automated extraction due to:
- PDF format inconsistencies
- Critical importance of accuracy
- Liability concerns

### Data Validation Rules

Every data point goes through:

1. **Type Validation**: Correct data type (numeric, date, etc.)
2. **Range Validation**: Within plausible bounds
   - Example: Fund balance cannot be negative without explicit flag
   - Revenue growth >50% year-over-year triggers review
3. **Cross-Source Validation**: Compare to alternate sources when available
4. **Historical Continuity**: Check for unexplained discontinuities
5. **Relationship Validation**: Internal consistency
   - Example: Total revenues = sum of categories
6. **Manual Review**: Human review of all anomalies

### Data Lineage Tracking

Every data point in the database includes:
- Source document (exact URL or file)
- Extraction date
- Extraction method (manual, automated)
- Validator (person or system)
- Validation status (pending, approved, flagged)
- Notes or caveats

This is exposed via API so users can verify provenance.

---

## Risk Scoring Methodology

### Philosophy: Composite Indicators, Not Predictions

We calculate a **Fiscal Stress Score** (0-100) based on established financial indicators.

**This is NOT:**
- A probability of bankruptcy (insufficient data for statistical modeling)
- A credit rating (we are not a rating agency)
- A prediction of future events

**This IS:**
- A relative assessment of fiscal health
- A composite of multiple validated indicators
- A trend tracker over time
- A transparent, replicable calculation

### Risk Indicators (12 Core Metrics)

#### Category 1: Liquidity & Reserves (25% weight)

**1.1 Fund Balance Ratio**
```
Fund Balance Ratio = General Fund Balance / General Fund Expenditures
```
- **Healthy**: >20% (high reserves)
- **Adequate**: 15-20% (recommended minimum)
- **Warning**: 10-15% (low reserves)
- **Critical**: <10% (insufficient buffer)

**1.2 Days of Cash**
```
Days of Cash = (Cash + Investments) / (Annual Expenditures / 365)
```
- **Healthy**: >60 days
- **Adequate**: 45-60 days
- **Warning**: 30-45 days
- **Critical**: <30 days

**1.3 Liquidity Ratio**
```
Liquidity Ratio = Current Assets / Current Liabilities
```
- **Healthy**: >2.0
- **Adequate**: 1.5-2.0
- **Warning**: 1.0-1.5
- **Critical**: <1.0

#### Category 2: Structural Balance (25% weight)

**2.1 Operating Surplus/Deficit**
```
Operating Balance = (Recurring Revenues - Recurring Expenditures) / Revenues
```
- **Healthy**: >5% (surplus)
- **Adequate**: 0-5% (balanced)
- **Warning**: -5% to 0% (deficit)
- **Critical**: <-5% (large deficit)

**2.2 Structural Deficit Trend**
```
Count consecutive years with operating deficit
```
- **Healthy**: 0 years
- **Adequate**: 1 year (one-time issue)
- **Warning**: 2 years
- **Critical**: 3+ years (structural problem)

**2.3 Revenue vs. Expenditure Growth Rate**
```
Compare 3-year CAGR: Revenues vs. Expenditures
```
- **Healthy**: Revenue growth > Expenditure growth
- **Warning**: Rates similar
- **Critical**: Expenditures growing faster than revenues

#### Category 3: Pension Stress (30% weight)

This is the **primary driver** of California municipal fiscal stress.

**3.1 Pension Funded Ratio**
```
Funded Ratio = Pension Assets / Total Pension Liability
```
- **Healthy**: >80%
- **Adequate**: 70-80%
- **Warning**: 60-70%
- **Critical**: <60% (severely underfunded)

**3.2 Unfunded Liability Ratio**
```
UAL Ratio = Unfunded Actuarial Liability / Annual Revenues
```
- **Healthy**: <1.0x (UAL less than annual revenues)
- **Adequate**: 1.0-2.0x
- **Warning**: 2.0-3.0x
- **Critical**: >3.0x (UAL exceeds multiple years of revenue)

**3.3 Pension Contribution Burden**
```
Contribution Burden = Annual Pension Payment / Payroll Costs
```
- **Healthy**: <20%
- **Adequate**: 20-25%
- **Warning**: 25-35%
- **Critical**: >35% (crushing burden)

**3.4 Pension Contribution Growth Rate**
```
3-year CAGR of pension contributions
```
- **Healthy**: <5% annual growth
- **Adequate**: 5-10%
- **Warning**: 10-15%
- **Critical**: >15% (unsustainable growth)

#### Category 4: Revenue Sustainability (10% weight)

**4.1 Revenue Volatility**
```
Standard deviation of year-over-year revenue changes (5 years)
```
- **Healthy**: <5% (stable)
- **Adequate**: 5-10%
- **Warning**: 10-15%
- **Critical**: >15% (highly volatile)

**4.2 Revenue Concentration**
```
Herfindahl Index of revenue sources
```
- **Healthy**: <0.25 (diversified)
- **Adequate**: 0.25-0.35
- **Warning**: 0.35-0.45
- **Critical**: >0.45 (over-reliant on single source)

#### Category 5: Debt Burden (10% weight)

**5.1 Debt Service Ratio**
```
Debt Service Ratio = Annual Debt Payments / Revenues
```
- **Healthy**: <10%
- **Adequate**: 10-15%
- **Warning**: 15-20%
- **Critical**: >20%

**5.2 OPEB Liability Ratio**
```
OPEB Ratio = Unfunded OPEB Liability / Revenues
```
- **Healthy**: <0.5x
- **Adequate**: 0.5-1.0x
- **Warning**: 1.0-2.0x
- **Critical**: >2.0x

### Composite Score Calculation

**Step 1: Score Each Indicator**
- Healthy = 0 points (no stress)
- Adequate = 25 points
- Warning = 50 points
- Critical = 100 points

**Step 2: Calculate Category Scores**
```
Category Score = Average of indicators in category
```

**Step 3: Calculate Overall Score**
```
Overall Score = (Liquidity * 0.25) +
                (Structural Balance * 0.25) +
                (Pension Stress * 0.30) +
                (Revenue Sustainability * 0.10) +
                (Debt Burden * 0.10)
```

**Step 4: Classify Risk Level**
- **Low Risk**: 0-25 (healthy finances)
- **Moderate Risk**: 26-50 (watch carefully)
- **High Risk**: 51-75 (corrective action needed)
- **Severe Risk**: 76-100 (fiscal crisis)

### Risk Score Interpretation

**Important:** These scores indicate **fiscal stress**, not bankruptcy probability.

- A score of 75 does NOT mean "75% chance of bankruptcy"
- It means "severe fiscal stress across multiple indicators"
- Bankruptcy is a political decision as much as a financial one

**Historical Context:**
- Vallejo (2008 bankruptcy): Would have scored ~80-85
- Stockton (2012 bankruptcy): Would have scored ~85-90
- San Bernardino (2012): Would have scored ~75-80

### Why NOT Machine Learning?

We explicitly chose NOT to use machine learning because:

1. **Insufficient Data**: Only 3 CA municipal bankruptcies in history
   - Cannot train meaningful model on 3 examples
   - Cross-validation is meaningless with n=3

2. **False Precision**: ML models imply predictive accuracy we cannot support
   - "65% probability" suggests precision we don't have
   - Users may over-trust numerical predictions

3. **Lack of Transparency**:
   - Complex models are black boxes
   - Cannot explain to lay users
   - Cannot be validated by external experts

4. **Liability**:
   - Predictions could be challenged legally
   - "Forecasts" could affect bond markets
   - Indicators are defensible, predictions are not

5. **Alternative Approaches Work Better**:
   - Financial ratio analysis has 100+ years of validation
   - Used by rating agencies, auditors, researchers
   - Transparent and replicable

### Confidence & Uncertainty

For each risk score, we report:

1. **Data Quality Score** (0-100%)
   - Based on: source reliability, data completeness, validation results
   - Example: "85% data quality - 3 minor data gaps filled via estimation"

2. **Indicator Availability** (X/12 indicators)
   - Some cities may lack certain data points
   - Score adjusted for missing indicators

3. **Temporal Currency**
   - "Based on FY 2023 data (as of June 30, 2023)"
   - "Data is 18 months old"

4. **Key Assumptions**
   - Example: "Assumes CalPERS 6.8% discount rate"
   - "Excludes potential state/federal aid"

### Validation Against Reality

We test our methodology by:
1. **Backtesting**: Calculate scores for cities that later experienced distress
2. **Peer Review**: Methodology reviewed by municipal finance experts
3. **Comparison**: Check against Moody's, S&P approaches
4. **User Feedback**: Incorporate feedback from municipal officials, residents

---

## Projection Methodology

### Purpose: Illustrative Scenarios, Not Forecasts

Our projections are **scenario analysis** tools, not predictions.

**Goal:** Answer "If current trends continue, what happens?"

### Revenue Projection

**Base Case: Trend Extrapolation**
```
Future Revenue = Current Revenue * (1 + Historical CAGR)^Years
```

**Adjustments:**
- Known policy changes (e.g., approved tax measures)
- Economic cycle adjustments (recession scenarios)
- Population trends

**Scenarios:**
1. **Optimistic**: 75th percentile historical growth rate
2. **Base**: 50th percentile (median)
3. **Pessimistic**: 25th percentile

### Expenditure Projection

**Base Case: Baseline Growth + Pension Growth**
```
Base Expenditures = Current * (1 + Inflation)^Years
Pension Costs = Per CalPERS contribution schedule
Total = Base + (Pension - Current Pension)
```

**Key Driver:** Pension contribution increases
- CalPERS publishes 20-year amortization schedule
- This is the most predictable (and alarming) trend

**Scenarios:**
1. **Optimistic**: Pension reform reduces contributions
2. **Base**: CalPERS schedule as-published
3. **Pessimistic**: CalPERS lowers discount rate → higher contributions

### Fiscal Cliff Identification

**Definition:** Year when projected revenues < projected expenditures + required reserve replenishment

**Calculation:**
```
For each year 1-10:
  If (Revenues < Expenditures) AND (Fund Balance < 10%):
    Fiscal Cliff = This Year
```

**Interpretation:**
"Without corrective action, Vallejo will exhaust reserves by 2029"

NOT: "Vallejo will go bankrupt in 2029"

### Projection Limitations

**What can change (and invalidate projections):**
- Policy changes (tax increases, service cuts)
- Economic shocks (recession, boom)
- State/federal aid
- Pension reform
- Bankruptcy (restarts the clock)

**Therefore:**
- Update projections annually
- Report as "If trends continue from [date]"
- Do not present as predictions

---

## Peer Comparison Methodology

### Selection of Peer Cities

**Criteria for peer selection:**
1. California cities (same state legal/pension framework)
2. Population 50,000-250,000 (similar scale)
3. Similar pension funded status (±10%)
4. Available data (published CAFRs)

**Vallejo Peer Set:**
- Richmond (similar distress profile)
- Fairfield (same county)
- Pittsburg
- Antioch
- Vacaville

### Comparison Metrics

- Rank cities on each of 12 indicators
- Show Vallejo's percentile ranking
- Identify best and worst performers
- Show trend over time

**NOT used for:** "Better" or "worse" labels - just context

---

## Data Quality Standards

### Accuracy Targets

- **Critical Fields** (revenues, expenditures, pension UAL): 99.9% accuracy target
- **Secondary Fields**: 99% accuracy target
- **Metadata**: 95% completeness target

### Validation Process

1. **Automated Checks**: Run on every data load
2. **Manual Review**: Human review of anomalies
3. **Cross-Source Validation**: Compare to alternate sources
4. **External Review**: Annual audit by independent expert
5. **Public Correction**: Transparent correction process

### Data Freshness

- Update financial data annually (within 30 days of CAFR release)
- Update pension data quarterly (CalPERS reports)
- Show "Data as of [date]" prominently
- Archive historical snapshots

---

## Methodology Evolution

This methodology will evolve as:
- New data sources become available
- We learn from user feedback
- Expert review suggests improvements
- New research emerges

**All changes will be:**
- Documented in CHANGELOG.md
- Explained in methodology updates
- Applied retroactively to historical data
- Versioned for reproducibility

---

**Version:** 1.0
**Last Updated:** 2025-01-10
**Next Review:** 2026-01-10
```

Create README.md with comprehensive project overview including:
- Purpose and goals
- Quick start guide
- Link to methodology and disclaimer
- Data sources
- How to contribute
- License information
- Contact information

Create pyproject.toml for Poetry with dependencies:
- fastapi
- uvicorn
- sqlalchemy
- alembic
- psycopg2-binary
- redis
- celery
- pandas
- numpy
- pydantic
- pydantic-settings
- python-dotenv
- requests
- beautifulsoup4
- pdfplumber
- tabula-py
- pytest
- pytest-asyncio
- black
- isort
- mypy
- flake8

Create docker-compose.yml with services:
- postgres (with PostGIS)
- redis
- metabase
- pgadmin (for database management)

Create .env.example with all required environment variables documented.

Create CONTRIBUTING.md explaining:
- How to contribute data corrections
- How to contribute code
- Development setup
- Testing requirements
- Code style guidelines

Create .gitignore appropriate for Python, excluding:
- data/ directory (except samples)
- .env
- Virtual environments
- IDE configs
- __pycache__
- Build artifacts
```

**This is the foundation. Execute this prompt first, then confirm completion before moving to next prompt.**
```

---

### Prompt 0.2: Configure Development Environment

```
Set up the complete development environment for the IBCo project.

**Context:** We've created the project structure. Now configure all development tooling.

**Tasks:**

1. **Initialize Poetry Project**
```bash
cd ~/ibco-vallejo-console
poetry init --name ibco-vallejo-console \
            --description "Municipal fiscal transparency platform for Vallejo, CA" \
            --author "Your Name <your@email.com>" \
            --license "MIT" \
            --python "^3.11"
```

2. **Add Core Dependencies**
```bash
# Web framework
poetry add fastapi uvicorn[standard] python-multipart

# Database
poetry add sqlalchemy alembic psycopg2-binary asyncpg

# Data processing
poetry add pandas numpy pyarrow

# Validation & settings
poetry add pydantic pydantic-settings python-dotenv

# Task queue
poetry add celery redis

# HTTP & scraping
poetry add requests httpx beautifulsoup4 lxml

# PDF processing
poetry add pdfplumber tabula-py pymupdf pillow

# Utilities
poetry add python-dateutil pytz

# Development dependencies
poetry add --group dev pytest pytest-asyncio pytest-cov pytest-mock
poetry add --group dev black isort mypy flake8 pylint
poetry add --group dev ipython jupyter
poetry add --group dev faker factory-boy
```

3. **Configure Black (Code Formatting)**

Create `pyproject.toml` section:
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | migrations
)/
'''
```

4. **Configure isort (Import Sorting)**

Add to `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

5. **Configure mypy (Type Checking)**

Create `mypy.ini`:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_any_unimported = False
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
check_untyped_defs = True
strict_equality = True

# Per-module options for third-party libraries without stubs
[mypy-celery.*]
ignore_missing_imports = True

[mypy-pdfplumber.*]
ignore_missing_imports = True

[mypy-tabula.*]
ignore_missing_imports = True
```

6. **Configure flake8 (Linting)**

Create `.flake8`:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, E266, E501, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    migrations
max-complexity = 10
```

7. **Configure pytest**

Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database required)
    slow: Slow-running tests
    manual: Tests requiring manual intervention
```

8. **Create Pre-commit Hook Script**

Create `scripts/setup/install_git_hooks.sh`:
```bash
#!/bin/bash
# Install git pre-commit hook for code quality

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "Running pre-commit checks..."

# Run black
echo "Checking code formatting (black)..."
poetry run black --check src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ Black formatting check failed. Run: poetry run black src/ tests/"
    exit 1
fi

# Run isort
echo "Checking import sorting (isort)..."
poetry run isort --check-only src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ isort check failed. Run: poetry run isort src/ tests/"
    exit 1
fi

# Run flake8
echo "Running linter (flake8)..."
poetry run flake8 src/ tests/
if [ $? -ne 0 ]; then
    echo "❌ flake8 found issues"
    exit 1
fi

# Run mypy
echo "Type checking (mypy)..."
poetry run mypy src/
if [ $? -ne 0 ]; then
    echo "❌ mypy found type errors"
    exit 1
fi

# Run tests
echo "Running tests..."
poetry run pytest tests/unit -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "✅ All checks passed!"
exit 0
EOF

chmod +x .git/hooks/pre-commit
echo "Git pre-commit hook installed successfully"
```

9. **Create Environment Configuration**

Create `src/config/settings.py`:
```python
"""
Application settings and configuration.

Loads from environment variables with validation.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "IBCo Vallejo Console"
    app_version: str = "0.1.0"
    environment: str = "development"  # development, staging, production
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # Database
    database_url: str = "postgresql://ibco:ibcopass@localhost:5432/ibco_dev"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Data Storage
    data_directory: str = "./data"
    raw_data_directory: str = "./data/raw"
    processed_data_directory: str = "./data/processed"
    archive_directory: str = "./data/archive"

    # External APIs (if any)
    calpers_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # Security
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"

    # Monitoring
    sentry_dsn: Optional[str] = None

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


# Global settings instance
settings = Settings()
```

Create corresponding `.env.example`:
```bash
# Application
APP_NAME="IBCo Vallejo Console"
APP_VERSION="0.1.0"
ENVIRONMENT="development"
DEBUG="true"

# API
API_HOST="0.0.0.0"
API_PORT="8000"
API_PREFIX="/api/v1"
CORS_ORIGINS='["*"]'

# Database
DATABASE_URL="postgresql://ibco:ibcopass@localhost:5432/ibco_dev"
DATABASE_POOL_SIZE="5"
DATABASE_MAX_OVERFLOW="10"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Celery
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"

# Data Storage
DATA_DIRECTORY="./data"
RAW_DATA_DIRECTORY="./data/raw"
PROCESSED_DATA_DIRECTORY="./data/processed"
ARCHIVE_DIRECTORY="./data/archive"

# External APIs
CALPERS_API_KEY=""

# Logging
LOG_LEVEL="INFO"
LOG_FORMAT="json"

# Security
SECRET_KEY="your-secret-key-change-in-production"

# Monitoring
SENTRY_DSN=""
```

10. **Create Logging Configuration**

Create `src/config/logging_config.py`:
```python
"""
Centralized logging configuration.
"""
import logging
import sys
from typing import Any

from src.config.settings import settings


def setup_logging() -> None:
    """Configure application logging."""

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Format
    if settings.log_format == "json":
        # JSON structured logging
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human-readable format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Set third-party logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
```

11. **Create Docker Compose Configuration**

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.4
    container_name: ibco-postgres
    environment:
      POSTGRES_DB: ibco_dev
      POSTGRES_USER: ibco
      POSTGRES_PASSWORD: ibcopass
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ibco -d ibco_dev"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ibco-network

  redis:
    image: redis:7-alpine
    container_name: ibco-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ibco-network

  metabase:
    image: metabase/metabase:latest
    container_name: ibco-metabase
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase
      MB_DB_PORT: 5432
      MB_DB_USER: ibco
      MB_DB_PASS: ibcopass
      MB_DB_HOST: postgres
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - metabase_data:/metabase-data
    networks:
      - ibco-network

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: ibco-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@ibco.local
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    depends_on:
      - postgres
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - ibco-network

volumes:
  postgres_data:
  redis_data:
  metabase_data:
  pgadmin_data:

networks:
  ibco-network:
    driver: bridge
```

12. **Create Initialization Script**

Create `scripts/setup/init_dev_environment.sh`:
```bash
#!/bin/bash
set -e

echo "=== IBCo Development Environment Setup ==="
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Install from: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "✅ Poetry found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install Docker Desktop or Docker Engine"
    exit 1
fi

echo "✅ Docker found"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
poetry install

# Create .env from example if doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Remember to update .env with your actual values"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw/cafr
mkdir -p data/raw/calpers
mkdir -p data/raw/state_controller
mkdir -p data/processed
mkdir -p data/archive
mkdir -p data/samples

# Start Docker services
echo ""
echo "Starting Docker services..."
docker compose up -d

# Wait for PostgreSQL
echo "Waiting for PostgreSQL to be ready..."
until docker compose exec -T postgres pg_isready -U ibco -d ibco_dev > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Wait for Redis
echo "Waiting for Redis to be ready..."
until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready"

# Install git hooks
echo ""
echo "Installing git hooks..."
bash scripts/setup/install_git_hooks.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review and update .env file"
echo "2. Initialize database: poetry run alembic upgrade head"
echo "3. Run tests: poetry run pytest"
echo "4. Start API: poetry run uvicorn src.api.main:app --reload"
echo ""
echo "Services running:"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo "- Metabase: http://localhost:3000"
echo "- PgAdmin: http://localhost:5050"
```

Make script executable:
```bash
chmod +x scripts/setup/init_dev_environment.sh
chmod +x scripts/setup/install_git_hooks.sh
```

13. **Verify Installation**

Create `scripts/setup/verify_environment.py`:
```python
"""
Verify that the development environment is properly configured.
"""
import sys
from pathlib import Path


def verify_environment() -> bool:
    """Run all verification checks."""
    checks = [
        check_python_version,
        check_poetry_installation,
        check_docker_running,
        check_env_file,
        check_data_directories,
    ]

    all_passed = True
    for check in checks:
        try:
            check()
            print(f"✅ {check.__name__}")
        except Exception as e:
            print(f"❌ {check.__name__}: {e}")
            all_passed = False

    return all_passed


def check_python_version() -> None:
    """Verify Python version is 3.11+."""
    if sys.version_info < (3, 11):
        raise RuntimeError(f"Python 3.11+ required, found {sys.version}")


def check_poetry_installation() -> None:
    """Verify Poetry is installed."""
    import subprocess
    result = subprocess.run(["poetry", "--version"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("Poetry not installed")


def check_docker_running() -> None:
    """Verify Docker is running."""
    import subprocess
    result = subprocess.run(["docker", "ps"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("Docker not running")


def check_env_file() -> None:
    """Verify .env file exists."""
    if not Path(".env").exists():
        raise RuntimeError(".env file not found")


def check_data_directories() -> None:
    """Verify data directories exist."""
    required_dirs = [
        "data/raw/cafr",
        "data/raw/calpers",
        "data/processed",
        "data/archive",
    ]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            raise RuntimeError(f"Directory {dir_path} not found")


if __name__ == "__main__":
    print("=== Environment Verification ===\n")
    success = verify_environment()
    print("\n" + ("="*30))
    if success:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed")
        sys.exit(1)
```

**Execute this prompt, run the init script, and verify everything works before proceeding.**
```

---

## PHASE 1: DATABASE DESIGN & IMPLEMENTATION

### Prompt 1.1: Design Core Database Schema

```
Design and implement the complete database schema for the IBCo Vallejo Console.

**Context:** This is the foundation of the entire system. The schema must be:
- Normalized appropriately (3NF for most tables)
- Flexible for future expansion
- Optimized for the queries we'll run
- Comprehensive in tracking data lineage

**Principles:**
1. **Data Lineage**: Every fact must be traceable to its source
2. **Temporal Tracking**: Track when data was true, not just when we loaded it
3. **Audit Trail**: Who changed what when
4. **Soft Deletes**: Never actually delete data, mark as deleted
5. **Validation Status**: Track whether data has been validated

Create `src/database/base.py`:
```python
"""
SQLAlchemy base configuration and utilities.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Boolean, Integer, MetaData
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.ext.declarative import declared_attr


# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class TimestampMixin:
    """Mixin to add created/updated timestamps to models."""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)


class AuditMixin(TimestampMixin, SoftDeleteMixin):
    """Combines timestamp and soft delete for full audit trail."""
    pass
```

Create `src/database/models/core.py`:
```python
"""
Core models: Cities, Fiscal Years, and foundational entities.
"""
from datetime import date
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Date, Text, Numeric,
    Boolean, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class City(Base, AuditMixin):
    """
    Cities being tracked.

    Initially focused on Vallejo, but designed for multi-city support.
    """
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)

    # Basic Information
    name = Column(String(100), nullable=False, unique=True)
    state = Column(String(2), nullable=False)  # CA
    county = Column(String(100), nullable=False)

    # Demographics
    population = Column(Integer, nullable=True)  # Latest estimate
    population_year = Column(Integer, nullable=True)
    incorporation_date = Column(Date, nullable=True)

    # Geographic
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)

    # Government Structure
    government_type = Column(String(50), nullable=True)  # e.g., "City Council-Manager"
    fiscal_year_end_month = Column(Integer, nullable=False, default=6)  # Most CA cities: June
    fiscal_year_end_day = Column(Integer, nullable=False, default=30)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_charter_city = Column(Boolean, nullable=True)

    # Bankruptcy History (if applicable)
    has_bankruptcy_history = Column(Boolean, nullable=False, default=False)
    bankruptcy_filing_date = Column(Date, nullable=True)
    bankruptcy_exit_date = Column(Date, nullable=True)
    bankruptcy_chapter = Column(String(20), nullable=True)  # "Chapter 9"
    bankruptcy_notes = Column(Text, nullable=True)

    # Official Website & Contact
    website_url = Column(String(255), nullable=True)
    finance_department_url = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Relationships
    fiscal_years = relationship("FiscalYear", back_populates="city")

    def __repr__(self) -> str:
        return f"<City(id={self.id}, name='{self.name}', state='{self.state}')>"


class FiscalYear(Base, AuditMixin):
    """
    A single fiscal year for a city.

    Each row represents one year of financial activity.
    """
    __tablename__ = "fiscal_years"
    __table_args__ = (
        UniqueConstraint('city_id', 'year', name='uq_fiscal_year_city_year'),
        Index('ix_fiscal_year_city_year', 'city_id', 'year'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Fiscal Year Identification
    year = Column(Integer, nullable=False)  # Ending year (e.g., 2024 for FY 2023-24)
    start_date = Column(Date, nullable=False)  # Usually July 1
    end_date = Column(Date, nullable=False)  # Usually June 30

    # Data Availability
    cafr_available = Column(Boolean, nullable=False, default=False)
    cafr_url = Column(String(500), nullable=True)
    cafr_publish_date = Column(Date, nullable=True)
    cafr_audit_firm = Column(String(255), nullable=True)
    cafr_audit_opinion = Column(String(50), nullable=True)  # Unqualified, Qualified, etc.

    budget_available = Column(Boolean, nullable=False, default=False)
    budget_url = Column(String(500), nullable=True)
    budget_adopted_date = Column(Date, nullable=True)

    # CalPERS Data
    calpers_valuation_available = Column(Boolean, nullable=False, default=False)
    calpers_valuation_url = Column(String(500), nullable=True)
    calpers_valuation_date = Column(Date, nullable=True)

    # Data Completeness Flags
    revenues_complete = Column(Boolean, nullable=False, default=False)
    expenditures_complete = Column(Boolean, nullable=False, default=False)
    pension_data_complete = Column(Boolean, nullable=False, default=False)

    # Data Quality Score (0-100)
    data_quality_score = Column(Integer, nullable=True)
    data_quality_notes = Column(Text, nullable=True)

    # Validation
    validated_by = Column(String(255), nullable=True)  # Person or system
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    city = relationship("City", back_populates="fiscal_years")
    revenues = relationship("Revenue", back_populates="fiscal_year")
    expenditures = relationship("Expenditure", back_populates="fiscal_year")
    fund_balances = relationship("FundBalance", back_populates="fiscal_year")
    pension_plans = relationship("PensionPlan", back_populates="fiscal_year")
    risk_scores = relationship("RiskScore", back_populates="fiscal_year")

    def __repr__(self) -> str:
        return f"<FiscalYear(id={self.id}, city_id={self.city_id}, year={self.year})>"


class DataSource(Base, AuditMixin):
    """
    Catalog of all data sources.

    Tracks where our data comes from for lineage and citation purposes.
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)

    # Source Identification
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # CAFR, CalPERS, StateController, Manual
    url = Column(String(500), nullable=True)

    # Source Details
    organization = Column(String(255), nullable=False)  # e.g., "City of Vallejo"
    description = Column(Text, nullable=True)

    # Reliability Assessment
    reliability_rating = Column(String(20), nullable=True)  # High, Medium, Low
    reliability_notes = Column(Text, nullable=True)

    # Access Information
    access_method = Column(String(50), nullable=False)  # Download, API, Scrape, Manual
    requires_authentication = Column(Boolean, nullable=False, default=False)

    # Update Frequency
    expected_update_frequency = Column(String(50), nullable=True)  # Annual, Quarterly, etc.
    last_checked_date = Column(Date, nullable=True)
    last_available_date = Column(Date, nullable=True)

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class DataLineage(Base, AuditMixin):
    """
    Tracks the provenance of every data point.

    Links data back to original source documents.
    """
    __tablename__ = "data_lineage"

    id = Column(Integer, primary_key=True)

    # What data is this about?
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=False)

    # Where did it come from?
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    source_document_url = Column(String(500), nullable=True)
    source_document_page = Column(Integer, nullable=True)
    source_document_section = Column(String(255), nullable=True)

    # How was it extracted?
    extraction_method = Column(String(50), nullable=False)  # Manual, Automated, API
    extracted_by = Column(String(255), nullable=True)  # Person or system
    extracted_at = Column(DateTime, nullable=False)

    # Validation
    validated = Column(Boolean, nullable=False, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    # Cross-validation
    cross_validated_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    matches_cross_validation = Column(Boolean, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    confidence_level = Column(String(20), nullable=True)  # High, Medium, Low

    # Relationships
    source = relationship("DataSource", foreign_keys=[source_id])
    cross_validation_source = relationship("DataSource", foreign_keys=[cross_validated_source_id])

    __table_args__ = (
        Index('ix_data_lineage_record', 'table_name', 'record_id'),
    )

    def __repr__(self) -> str:
        return f"<DataLineage(table={self.table_name}, record_id={self.record_id})>"
```

Now create financial models in `src/database/models/financial.py`:

```python
"""
Financial data models: Revenues, Expenditures, Fund Balances.
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, ForeignKey,
    Text, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class RevenueCategory(Base, AuditMixin):
    """
    Standardized revenue categories for cross-year comparison.
    """
    __tablename__ = "revenue_categories"

    id = Column(Integer, primary_key=True)

    # Category Hierarchy (3 levels)
    category_level1 = Column(String(100), nullable=False)  # e.g., "Taxes"
    category_level2 = Column(String(100), nullable=True)   # e.g., "Property Taxes"
    category_level3 = Column(String(100), nullable=True)   # e.g., "Secured Property Taxes"

    # Standardized name for reporting
    standard_name = Column(String(255), nullable=False, unique=True)

    # Classification
    is_recurring = Column(Boolean, nullable=False, default=True)
    is_discretionary = Column(Boolean, nullable=True)

    # Description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RevenueCategory(id={self.id}, name='{self.standard_name}')>"


class Revenue(Base, AuditMixin):
    """
    Revenue data for a fiscal year.

    Tracks both budgeted and actual revenues.
    """
    __tablename__ = "revenues"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'category_id', 'fund_type',
                        name='uq_revenue_year_category_fund'),
        CheckConstraint('actual_amount >= 0', name='ck_revenue_actual_non_negative'),
        Index('ix_revenue_fiscal_year', 'fiscal_year_id'),
        Index('ix_revenue_category', 'category_id'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=False)

    # Fund Classification
    fund_type = Column(String(50), nullable=False, default="General")  # General, Special, Enterprise
    fund_name = Column(String(255), nullable=True)

    # Amounts (in dollars)
    budget_amount = Column(Numeric(15, 2), nullable=True)
    actual_amount = Column(Numeric(15, 2), nullable=False)

    # Variance Analysis
    variance_amount = Column(Numeric(15, 2), nullable=True)  # Actual - Budget
    variance_percent = Column(Numeric(6, 2), nullable=True)  # (Actual - Budget) / Budget * 100

    # Source Information
    source_document_type = Column(String(50), nullable=False)  # CAFR, Budget, etc.
    source_page = Column(Integer, nullable=True)
    source_line_item = Column(String(255), nullable=True)

    # Data Quality
    is_estimated = Column(Boolean, nullable=False, default=False)
    estimation_method = Column(String(255), nullable=True)
    confidence_level = Column(String(20), nullable=True)  # High, Medium, Low

    # Notes
    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="revenues")
    category = relationship("RevenueCategory")

    def __repr__(self) -> str:
        return f"<Revenue(id={self.id}, fy_id={self.fiscal_year_id}, amount=${self.actual_amount})>"


class ExpenditureCategory(Base, AuditMixin):
    """
    Standardized expenditure categories.
    """
    __tablename__ = "expenditure_categories"

    id = Column(Integer, primary_key=True)

    # Category Hierarchy
    category_level1 = Column(String(100), nullable=False)  # e.g., "Public Safety"
    category_level2 = Column(String(100), nullable=True)   # e.g., "Police"
    category_level3 = Column(String(100), nullable=True)   # e.g., "Police Salaries"

    standard_name = Column(String(255), nullable=False, unique=True)

    # Classification
    is_personnel_cost = Column(Boolean, nullable=False, default=False)
    is_pension_cost = Column(Boolean, nullable=False, default=False)
    is_debt_service = Column(Boolean, nullable=False, default=False)
    is_capital = Column(Boolean, nullable=False, default=False)

    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ExpenditureCategory(id={self.id}, name='{self.standard_name}')>"


class Expenditure(Base, AuditMixin):
    """
    Expenditure data for a fiscal year.
    """
    __tablename__ = "expenditures"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'category_id', 'fund_type',
                        name='uq_expenditure_year_category_fund'),
        CheckConstraint('actual_amount >= 0', name='ck_expenditure_actual_non_negative'),
        Index('ix_expenditure_fiscal_year', 'fiscal_year_id'),
        Index('ix_expenditure_category', 'category_id'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("expenditure_categories.id"), nullable=False)

    # Fund Classification
    fund_type = Column(String(50), nullable=False, default="General")
    fund_name = Column(String(255), nullable=True)

    # Department (if available)
    department = Column(String(255), nullable=True)

    # Amounts
    budget_amount = Column(Numeric(15, 2), nullable=True)
    actual_amount = Column(Numeric(15, 2), nullable=False)

    # Variance
    variance_amount = Column(Numeric(15, 2), nullable=True)
    variance_percent = Column(Numeric(6, 2), nullable=True)

    # Source
    source_document_type = Column(String(50), nullable=False)
    source_page = Column(Integer, nullable=True)
    source_line_item = Column(String(255), nullable=True)

    # Data Quality
    is_estimated = Column(Boolean, nullable=False, default=False)
    estimation_method = Column(String(255), nullable=True)
    confidence_level = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="expenditures")
    category = relationship("ExpenditureCategory")

    def __repr__(self) -> str:
        return f"<Expenditure(id={self.id}, fy_id={self.fiscal_year_id}, amount=${self.actual_amount})>"


class FundBalance(Base, AuditMixin):
    """
    Fund balance data (city's reserves/savings).

    Critical indicator of fiscal health.
    """
    __tablename__ = "fund_balances"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'fund_type', name='uq_fund_balance_year_fund'),
        Index('ix_fund_balance_fiscal_year', 'fiscal_year_id'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Fund Classification
    fund_type = Column(String(50), nullable=False, default="General")
    fund_name = Column(String(255), nullable=True)

    # Fund Balance Components (per GASB 54)
    nonspendable = Column(Numeric(15, 2), nullable=True, default=0)
    restricted = Column(Numeric(15, 2), nullable=True, default=0)
    committed = Column(Numeric(15, 2), nullable=True, default=0)
    assigned = Column(Numeric(15, 2), nullable=True, default=0)
    unassigned = Column(Numeric(15, 2), nullable=True, default=0)

    # Total
    total_fund_balance = Column(Numeric(15, 2), nullable=False)

    # Key Ratios
    fund_balance_ratio = Column(Numeric(6, 4), nullable=True)  # Fund Balance / Expenditures
    days_of_cash = Column(Numeric(8, 2), nullable=True)  # Days city can operate

    # Year-over-year Change
    yoy_change_amount = Column(Numeric(15, 2), nullable=True)
    yoy_change_percent = Column(Numeric(6, 2), nullable=True)

    # Source
    source_document_type = Column(String(50), nullable=False)
    source_page = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="fund_balances")

    def __repr__(self) -> str:
        return f"<FundBalance(id={self.id}, fy_id={self.fiscal_year_id}, balance=${self.total_fund_balance})>"
```

Continue in next part...
```

**This prompt creates the foundational schema. Execute it first, then proceed to Prompt 1.2 for pension models.**
```

---

### Prompt 1.2: Create Pension Data Models

```
Create comprehensive pension data models for tracking CalPERS pension obligations.

**Context:** Pension underfunding is THE primary fiscal crisis driver for California cities. This data must be:
- Extremely detailed and accurate
- Track both actuarial assumptions and actual results
- Support scenario analysis (what if discount rate changes?)
- Link to individual fiscal years

Create `src/database/models/pensions.py`:

```python
"""
Pension data models.

Tracks pension plans, liabilities, contributions, and actuarial assumptions.
This is the CORE of California municipal fiscal crisis analysis.
"""
from datetime import date
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Numeric, Date, Boolean,
    ForeignKey, Text, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class PensionPlan(Base, AuditMixin):
    """
    A pension plan for a fiscal year.

    Most cities have multiple plans (Safety, Miscellaneous, etc.)
    """
    __tablename__ = "pension_plans"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'plan_name', name='uq_pension_plan_year_name'),
        Index('ix_pension_plan_fiscal_year', 'fiscal_year_id'),
        CheckConstraint('funded_ratio >= 0 AND funded_ratio <= 2.0',
                       name='ck_pension_funded_ratio_reasonable'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Plan Identification
    plan_name = Column(String(100), nullable=False)  # "Miscellaneous", "Safety", etc.
    plan_id = Column(String(50), nullable=True)  # CalPERS plan ID if available

    # Member Information
    active_members = Column(Integer, nullable=True)
    retired_members = Column(Integer, nullable=True)
    total_members = Column(Integer, nullable=True)

    # Actuarial Valuation Date
    valuation_date = Column(Date, nullable=False)

    # LIABILITY SIDE (What the city owes)

    # Total Pension Liability (TPL) - the BIG number
    total_pension_liability = Column(Numeric(15, 2), nullable=False)

    # Service Cost (new benefits earned this year)
    service_cost = Column(Numeric(15, 2), nullable=True)

    # Interest on TPL
    interest_cost = Column(Numeric(15, 2), nullable=True)

    # ASSET SIDE (What the city has saved)

    # Fiduciary Net Position (plan assets)
    fiduciary_net_position = Column(Numeric(15, 2), nullable=False)

    # Investment Return (actual)
    actual_investment_return = Column(Numeric(15, 2), nullable=True)
    actual_investment_return_percent = Column(Numeric(6, 4), nullable=True)  # As decimal

    # UNFUNDED LIABILITY (The crisis)

    # Net Pension Liability = TPL - Assets
    net_pension_liability = Column(Numeric(15, 2), nullable=False)

    # Unfunded Actuarial Liability (UAL) - same as NPL in most contexts
    unfunded_actuarial_liability = Column(Numeric(15, 2), nullable=False)

    # KEY RATIO
    funded_ratio = Column(Numeric(6, 4), nullable=False)  # Assets / TPL (as decimal)

    # CONTRIBUTIONS (What the city pays annually)

    # Employer Normal Cost (cost of benefits earned this year)
    employer_normal_cost = Column(Numeric(15, 2), nullable=True)
    employer_normal_cost_percent = Column(Numeric(6, 4), nullable=True)  # % of payroll

    # UAL Payment (paying down the unfunded liability)
    ual_payment = Column(Numeric(15, 2), nullable=True)

    # Total Employer Contribution
    total_employer_contribution = Column(Numeric(15, 2), nullable=True)
    total_employer_contribution_percent = Column(Numeric(6, 4), nullable=True)  # % of payroll

    # Employee Contributions
    employee_contribution = Column(Numeric(15, 2), nullable=True)

    # Payroll
    covered_payroll = Column(Numeric(15, 2), nullable=True)

    # ACTUARIAL ASSUMPTIONS (Critical - small changes = huge impact)

    # Discount Rate (assumed investment return)
    discount_rate = Column(Numeric(5, 4), nullable=True)  # e.g., 0.0680 for 6.8%

    # Inflation assumption
    inflation_rate = Column(Numeric(5, 4), nullable=True)

    # Payroll growth assumption
    payroll_growth_rate = Column(Numeric(5, 4), nullable=True)

    # Mortality table
    mortality_table = Column(String(100), nullable=True)

    # Amortization period (years to pay off UAL)
    amortization_period_years = Column(Integer, nullable=True)

    # Amortization method
    amortization_method = Column(String(50), nullable=True)  # "Level Percent", "Level Dollar"

    # PROJECTIONS (From CalPERS)

    # Projected contribution next year
    projected_contribution_next_year = Column(Numeric(15, 2), nullable=True)
    projected_contribution_rate_next_year = Column(Numeric(6, 4), nullable=True)

    # SOURCE INFORMATION
    source_document = Column(String(255), nullable=False)  # "CalPERS Valuation Report"
    source_url = Column(String(500), nullable=True)
    source_page = Column(Integer, nullable=True)

    # DATA QUALITY
    is_preliminary = Column(Boolean, nullable=False, default=False)
    confidence_level = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="pension_plans")

    def __repr__(self) -> str:
        return (f"<PensionPlan(id={self.id}, fy_id={self.fiscal_year_id}, "
                f"plan='{self.plan_name}', funded={self.funded_ratio:.1%})>")


class PensionContribution(Base, AuditMixin):
    """
    Historical pension contributions (what city actually paid).

    Separate from projections - this is cash out the door.
    """
    __tablename__ = "pension_contributions"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'plan_name', name='uq_pension_contribution'),
        Index('ix_pension_contribution_fiscal_year', 'fiscal_year_id'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    plan_name = Column(String(100), nullable=False)

    # Budgeted amounts
    budgeted_contribution = Column(Numeric(15, 2), nullable=True)

    # Actual amounts paid
    actual_contribution = Column(Numeric(15, 2), nullable=False)

    # Variance
    variance = Column(Numeric(15, 2), nullable=True)

    # Breakdown (if available)
    normal_cost_paid = Column(Numeric(15, 2), nullable=True)
    ual_payment_paid = Column(Numeric(15, 2), nullable=True)

    # Source
    source_document = Column(String(255), nullable=False)
    source_page = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        return (f"<PensionContribution(fy_id={self.fiscal_year_id}, "
                f"plan='{self.plan_name}', paid=${self.actual_contribution})>")


class PensionProjection(Base, AuditMixin):
    """
    CalPERS-published contribution projections.

    CalPERS publishes 20-year amortization schedules showing required contributions.
    This is THE most predictable (and alarming) trend.
    """
    __tablename__ = "pension_projections"
    __table_args__ = (
        UniqueConstraint('base_fiscal_year_id', 'plan_name', 'projection_year',
                        name='uq_pension_projection'),
        Index('ix_pension_projection_base_year', 'base_fiscal_year_id'),
        Index('ix_pension_projection_year', 'projection_year'),
    )

    id = Column(Integer, primary_key=True)

    # Which valuation is this projection from?
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    plan_name = Column(String(100), nullable=False)

    # Which future year is being projected?
    projection_year = Column(Integer, nullable=False)

    # Projected contribution
    projected_contribution = Column(Numeric(15, 2), nullable=False)
    projected_contribution_rate = Column(Numeric(6, 4), nullable=True)  # % of payroll

    # Projected payroll (assumption)
    projected_payroll = Column(Numeric(15, 2), nullable=True)

    # Components
    projected_normal_cost = Column(Numeric(15, 2), nullable=True)
    projected_ual_payment = Column(Numeric(15, 2), nullable=True)

    # Scenario label (for what-if analysis)
    scenario = Column(String(50), nullable=False, default="Base")  # Base, Optimistic, Pessimistic

    # Assumptions for this scenario
    assumed_discount_rate = Column(Numeric(5, 4), nullable=True)
    assumed_investment_return = Column(Numeric(5, 4), nullable=True)
    assumed_payroll_growth = Column(Numeric(5, 4), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    base_fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        return (f"<PensionProjection(base_fy={self.base_fiscal_year_id}, "
                f"proj_year={self.projection_year}, amount=${self.projected_contribution})>")


class OPEBLiability(Base, AuditMixin):
    """
    Other Post-Employment Benefits (retiree healthcare).

    Often overlooked but can be massive. Not pre-funded like pensions.
    """
    __tablename__ = "opeb_liabilities"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', name='uq_opeb_fiscal_year'),
        Index('ix_opeb_fiscal_year', 'fiscal_year_id'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Actuarial valuation date
    valuation_date = Column(Date, nullable=False)

    # Total OPEB Liability
    total_opeb_liability = Column(Numeric(15, 2), nullable=False)

    # Plan assets (if any - most cities have $0)
    plan_fiduciary_net_position = Column(Numeric(15, 2), nullable=False, default=0)

    # Net OPEB Liability
    net_opeb_liability = Column(Numeric(15, 2), nullable=False)

    # Funded ratio (usually 0% for unfunded plans)
    funded_ratio = Column(Numeric(6, 4), nullable=False, default=0)

    # Annual cost
    opeb_expense = Column(Numeric(15, 2), nullable=True)
    actual_contributions = Column(Numeric(15, 2), nullable=True)  # Usually pay-as-you-go

    # Actuarial assumptions
    discount_rate = Column(Numeric(5, 4), nullable=True)
    healthcare_cost_trend = Column(Numeric(5, 4), nullable=True)

    # Source
    source_document = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        return f"<OPEBLiability(fy_id={self.fiscal_year_id}, liability=${self.net_opeb_liability})>"


class PensionAssumptionChange(Base, AuditMixin):
    """
    Track changes in actuarial assumptions over time.

    When CalPERS lowers the discount rate, UAL explodes. Track these changes.
    """
    __tablename__ = "pension_assumption_changes"

    id = Column(Integer, primary_key=True)

    # Which fiscal year did the change take effect?
    effective_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Which plan?
    plan_name = Column(String(100), nullable=False)

    # What changed?
    assumption_type = Column(String(50), nullable=False)  # "discount_rate", "mortality", etc.

    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=False)

    # Impact on liability
    impact_on_liability = Column(Numeric(15, 2), nullable=True)
    impact_on_funded_ratio = Column(Numeric(6, 4), nullable=True)

    # Why did it change?
    reason = Column(Text, nullable=True)

    # Source
    source_document = Column(String(255), nullable=True)
    announced_date = Column(Date, nullable=True)

    # Relationships
    effective_fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        return (f"<PensionAssumptionChange(type='{self.assumption_type}', "
                f"old={self.old_value}, new={self.new_value})>")
```

**Additional requirement:** Create seed data for pension plan names.

Create `scripts/seed_data/seed_pension_categories.py`:
```python
"""
Seed standardized pension plan categories.
"""
from src.database.base import Base
from src.database.models.pensions import PensionPlan
from src.config.database import SessionLocal


def seed_pension_plan_categories():
    """Create standardized pension plan name categories."""

    # Standard CalPERS plan types
    plan_descriptions = {
        "Miscellaneous": "Non-safety employees (general admin, public works, etc.)",
        "Safety - Police": "Police officers and public safety personnel",
        "Safety - Fire": "Firefighters and fire department personnel",
        "Safety - Other": "Other safety personnel",
        "PEPRA Miscellaneous": "Miscellaneous employees hired after 1/1/2013 (PEPRA)",
        "PEPRA Safety": "Safety employees hired after 1/1/2013 (PEPRA)",
    }

    print("Standard CalPERS Plan Types:")
    for plan_name, description in plan_descriptions.items():
        print(f"  - {plan_name}: {description}")

    print("\nThese will be used when importing pension data.")


if __name__ == "__main__":
    seed_pension_plan_categories()
```

Execute this prompt to create pension models, then proceed to risk scoring models.
```

---

### Prompt 1.3: Create Risk Scoring Models

```
Create models for storing risk scores and risk factor explanations.

**Context:** Risk scores are the PRIMARY OUTPUT of this platform. These models must:
- Store composite scores and individual indicator scores
- Track which factors contribute most to risk
- Support historical comparison (is risk increasing?)
- Link back to underlying data for transparency

Create `src/database/models/risk.py`:

```python
"""
Risk scoring models.

Stores fiscal stress indicators and composite risk scores.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean,
    ForeignKey, Text, JSON, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class RiskIndicator(Base, AuditMixin):
    """
    Definition of a risk indicator.

    Each indicator has thresholds and weights.
    """
    __tablename__ = "risk_indicators"

    id = Column(Integer, primary_key=True)

    # Indicator Identity
    indicator_code = Column(String(50), nullable=False, unique=True)  # e.g., "FB_RATIO"
    indicator_name = Column(String(255), nullable=False)  # "Fund Balance Ratio"

    # Category
    category = Column(String(50), nullable=False)  # Liquidity, Structural, Pension, etc.

    # Description
    description = Column(Text, nullable=False)
    calculation_formula = Column(Text, nullable=True)

    # Weight in composite score (0-1, should sum to 1.0 within category)
    weight = Column(Numeric(5, 4), nullable=False)

    # Thresholds (for scoring)
    threshold_healthy = Column(Numeric(15, 4), nullable=True)    # Score 0
    threshold_adequate = Column(Numeric(15, 4), nullable=True)   # Score 25
    threshold_warning = Column(Numeric(15, 4), nullable=True)    # Score 50
    threshold_critical = Column(Numeric(15, 4), nullable=True)   # Score 100

    # Direction (is higher better or worse?)
    higher_is_better = Column(Boolean, nullable=False, default=True)

    # Metadata
    data_source = Column(String(255), nullable=True)
    unit_of_measure = Column(String(50), nullable=True)  # "ratio", "percent", "dollars"

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)

    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RiskIndicator(code='{self.indicator_code}', name='{self.indicator_name}')>"


class RiskScore(Base, AuditMixin):
    """
    Complete risk assessment for a fiscal year.

    This is THE KEY OUTPUT of the platform.
    """
    __tablename__ = "risk_scores"
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'calculation_date', name='uq_risk_score_fy_date'),
        Index('ix_risk_score_fiscal_year', 'fiscal_year_id'),
        Index('ix_risk_score_date', 'calculation_date'),
        CheckConstraint('overall_score >= 0 AND overall_score <= 100',
                       name='ck_risk_overall_score_valid'),
    )

    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # When was this calculated?
    calculation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    model_version = Column(String(20), nullable=False)  # e.g., "1.0", "1.1"

    # OVERALL COMPOSITE SCORE (0-100)
    overall_score = Column(Numeric(5, 2), nullable=False)

    # Risk Level Classification
    risk_level = Column(String(20), nullable=False)  # "low", "moderate", "high", "severe"

    # CATEGORY SCORES (0-100 each)
    liquidity_score = Column(Numeric(5, 2), nullable=False)
    structural_balance_score = Column(Numeric(5, 2), nullable=False)
    pension_stress_score = Column(Numeric(5, 2), nullable=False)
    revenue_sustainability_score = Column(Numeric(5, 2), nullable=False)
    debt_burden_score = Column(Numeric(5, 2), nullable=False)

    # DATA QUALITY & CONFIDENCE
    data_completeness_percent = Column(Numeric(5, 2), nullable=False)  # 0-100
    indicators_available = Column(Integer, nullable=False)  # How many of 12 indicators had data
    indicators_missing = Column(Integer, nullable=False)

    # DATA FRESHNESS
    data_as_of_date = Column(DateTime, nullable=False)  # When the underlying data was current
    data_age_months = Column(Integer, nullable=True)  # How old is the data?

    # TOP RISK FACTORS (JSON array of top 5)
    # Format: [{"indicator": "pension_funded_ratio", "score": 85, "contribution": 15.3}, ...]
    top_risk_factors = Column(JSON, nullable=True)

    # NARRATIVE SUMMARY
    summary = Column(Text, nullable=True)  # Auto-generated summary

    # VALIDATION
    validated = Column(Boolean, nullable=False, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="risk_scores")
    indicator_scores = relationship("RiskIndicatorScore", back_populates="risk_score")

    def __repr__(self) -> str:
        return (f"<RiskScore(fy_id={self.fiscal_year_id}, score={self.overall_score}, "
                f"level='{self.risk_level}')>")


class RiskIndicatorScore(Base, AuditMixin):
    """
    Individual indicator scores that roll up to composite risk score.

    Stores the value and score for each of the 12 indicators.
    """
    __tablename__ = "risk_indicator_scores"
    __table_args__ = (
        UniqueConstraint('risk_score_id', 'indicator_id', name='uq_risk_indicator_score'),
        Index('ix_risk_indicator_score_risk_score', 'risk_score_id'),
        Index('ix_risk_indicator_score_indicator', 'indicator_id'),
    )

    id = Column(Integer, primary_key=True)
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("risk_indicators.id"), nullable=False)

    # The actual measured value
    indicator_value = Column(Numeric(15, 4), nullable=False)

    # The scored value (0-100)
    indicator_score = Column(Numeric(5, 2), nullable=False)

    # Which threshold bucket?
    threshold_category = Column(String(20), nullable=False)  # healthy, adequate, warning, critical

    # How much does this contribute to overall score?
    weight = Column(Numeric(5, 4), nullable=False)
    contribution_to_overall = Column(Numeric(5, 2), nullable=False)  # score * weight

    # Data source for this indicator value
    data_source_table = Column(String(100), nullable=True)
    data_source_record_id = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    risk_score = relationship("RiskScore", back_populates="indicator_scores")
    indicator = relationship("RiskIndicator")

    def __repr__(self) -> str:
        return (f"<RiskIndicatorScore(risk_score_id={self.risk_score_id}, "
                f"value={self.indicator_value}, score={self.indicator_score})>")


class RiskTrend(Base, AuditMixin):
    """
    Risk trend analysis over time.

    Tracks how risk is changing: improving, stable, or deteriorating.
    """
    __tablename__ = "risk_trends"
    __table_args__ = (
        UniqueConstraint('city_id', 'indicator_code', 'analysis_date',
                        name='uq_risk_trend'),
        Index('ix_risk_trend_city', 'city_id'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Which indicator or overall?
    indicator_code = Column(String(50), nullable=False)  # "OVERALL" or specific indicator

    # Analysis date
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Time period analyzed
    years_analyzed = Column(Integer, nullable=False)  # e.g., 5 years
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)

    # Trend analysis
    trend_direction = Column(String(20), nullable=False)  # "improving", "stable", "deteriorating"
    trend_slope = Column(Numeric(8, 4), nullable=True)  # Change per year
    trend_significance = Column(String(20), nullable=True)  # "significant", "moderate", "minor"

    # Statistics
    average_score = Column(Numeric(5, 2), nullable=True)
    min_score = Column(Numeric(5, 2), nullable=True)
    max_score = Column(Numeric(5, 2), nullable=True)
    volatility = Column(Numeric(5, 2), nullable=True)  # Standard deviation

    # Narrative
    narrative = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")

    def __repr__(self) -> str:
        return (f"<RiskTrend(city_id={self.city_id}, indicator='{self.indicator_code}', "
                f"direction='{self.trend_direction}')>")


class BenchmarkComparison(Base, AuditMixin):
    """
    Compare city's indicators to peer cities or benchmarks.

    Context is critical: is Vallejo worse than similar cities?
    """
    __tablename__ = "benchmark_comparisons"
    __table_args__ = (
        Index('ix_benchmark_comparison_city', 'city_id'),
        Index('ix_benchmark_comparison_fiscal_year', 'fiscal_year_id'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Which indicator?
    indicator_code = Column(String(50), nullable=False)

    # This city's value
    city_value = Column(Numeric(15, 4), nullable=False)

    # Benchmark statistics
    peer_group_name = Column(String(100), nullable=False)  # e.g., "CA Cities 50K-250K pop"
    peer_group_size = Column(Integer, nullable=True)  # How many cities in peer group

    peer_average = Column(Numeric(15, 4), nullable=True)
    peer_median = Column(Numeric(15, 4), nullable=True)
    peer_25th_percentile = Column(Numeric(15, 4), nullable=True)
    peer_75th_percentile = Column(Numeric(15, 4), nullable=True)
    peer_best = Column(Numeric(15, 4), nullable=True)
    peer_worst = Column(Numeric(15, 4), nullable=True)

    # This city's percentile rank (0-100)
    city_percentile = Column(Numeric(5, 2), nullable=True)

    # Interpretation
    comparison_category = Column(String(20), nullable=True)  # "much_worse", "worse", "similar", "better", "much_better"

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    fiscal_year = relationship("FiscalYear")

    def __repr__(self) -> str:
        return (f"<BenchmarkComparison(city_id={self.city_id}, indicator='{self.indicator_code}', "
                f"percentile={self.city_percentile})>")
```

Execute this prompt to create risk models, then proceed to projection models.
```

---

### Prompt 1.4: Create Projection Models

```
Create models for storing financial projections and scenarios.

**Context:** Projections answer "What happens if current trends continue?" Must support:
- Multiple scenarios (base, optimistic, pessimistic)
- What-if analysis (what if pension discount rate changes?)
- Identification of "fiscal cliff" year

Create `src/database/models/projections.py`:

```python
"""
Financial projection models.

Store forward-looking projections and scenario analysis.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean,
    ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from src.database.base import Base, AuditMixin


class ProjectionScenario(Base, AuditMixin):
    """
    A projection scenario with assumptions.

    Multiple scenarios can be compared: base, optimistic, pessimistic.
    """
    __tablename__ = "projection_scenarios"

    id = Column(Integer, primary_key=True)

    # Scenario Identity
    scenario_name = Column(String(100), nullable=False)  # "Base Case", "Pension Reform", etc.
    scenario_code = Column(String(50), nullable=False)   # "base", "optimistic", "pessimistic"

    # Description
    description = Column(Text, nullable=False)

    # Is this the default/baseline scenario?
    is_baseline = Column(Boolean, nullable=False, default=False)

    # Display order
    display_order = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    projections = relationship("FinancialProjection", back_populates="scenario")

    def __repr__(self) -> str:
        return f"<ProjectionScenario(name='{self.scenario_name}', code='{self.scenario_code}')>"


class FinancialProjection(Base, AuditMixin):
    """
    Projected financial data for a future year.

    Based on current trends + assumptions.
    """
    __tablename__ = "financial_projections"
    __table_args__ = (
        UniqueConstraint('city_id', 'base_fiscal_year_id', 'projection_year', 'scenario_id',
                        name='uq_financial_projection'),
        Index('ix_financial_projection_city', 'city_id'),
        Index('ix_financial_projection_base_year', 'base_fiscal_year_id'),
        Index('ix_financial_projection_year', 'projection_year'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)

    # Which fiscal year is this projection based on?
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)

    # Which scenario?
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Which future year is being projected?
    projection_year = Column(Integer, nullable=False)
    years_ahead = Column(Integer, nullable=False)  # 1, 2, 3, ... 10

    # When was this projection created?
    projection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    projection_model_version = Column(String(20), nullable=False)

    # REVENUE PROJECTIONS
    total_revenues_projected = Column(Numeric(15, 2), nullable=False)
    recurring_revenues_projected = Column(Numeric(15, 2), nullable=True)

    # Revenue growth assumptions
    revenue_growth_rate = Column(Numeric(6, 4), nullable=True)  # As decimal

    # EXPENDITURE PROJECTIONS
    total_expenditures_projected = Column(Numeric(15, 2), nullable=False)

    # Expenditure components
    personnel_costs_projected = Column(Numeric(15, 2), nullable=True)
    pension_costs_projected = Column(Numeric(15, 2), nullable=True)  # THE BIG ONE
    opeb_costs_projected = Column(Numeric(15, 2), nullable=True)
    other_costs_projected = Column(Numeric(15, 2), nullable=True)

    # Expenditure growth assumptions
    base_expenditure_growth_rate = Column(Numeric(6, 4), nullable=True)
    pension_growth_rate = Column(Numeric(6, 4), nullable=True)

    # STRUCTURAL BALANCE
    operating_surplus_deficit = Column(Numeric(15, 2), nullable=False)  # Revenues - Expenditures
    operating_margin_percent = Column(Numeric(6, 2), nullable=True)  # As percent

    # FUND BALANCE PROJECTION
    beginning_fund_balance = Column(Numeric(15, 2), nullable=False)
    ending_fund_balance = Column(Numeric(15, 2), nullable=False)
    fund_balance_ratio = Column(Numeric(6, 4), nullable=True)  # Fund Balance / Expenditures

    # FISCAL HEALTH FLAGS
    is_deficit = Column(Boolean, nullable=False)
    is_depleting_reserves = Column(Boolean, nullable=False)
    reserves_below_minimum = Column(Boolean, nullable=False)  # Below 10%

    # Is this the "fiscal cliff" year? (when reserves run out)
    is_fiscal_cliff = Column(Boolean, nullable=False, default=False)

    # PENSION SPECIFIC PROJECTIONS
    pension_funded_ratio_projected = Column(Numeric(6, 4), nullable=True)
    pension_ual_projected = Column(Numeric(15, 2), nullable=True)

    # ASSUMPTIONS (stored as JSON for flexibility)
    # Format: {"discount_rate": 0.068, "inflation": 0.025, "payroll_growth": 0.03, ...}
    assumptions = Column(JSON, nullable=True)

    # CONFIDENCE
    confidence_level = Column(String(20), nullable=True)  # "high", "medium", "low"

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    base_fiscal_year = relationship("FiscalYear")
    scenario = relationship("ProjectionScenario", back_populates="projections")

    def __repr__(self) -> str:
        return (f"<FinancialProjection(city_id={self.city_id}, year={self.projection_year}, "
                f"deficit={self.operating_surplus_deficit})>")


class ScenarioAssumption(Base, AuditMixin):
    """
    Detailed assumptions for a projection scenario.

    Documents what-if assumptions clearly.
    """
    __tablename__ = "scenario_assumptions"
    __table_args__ = (
        UniqueConstraint('scenario_id', 'assumption_category', 'assumption_name',
                        name='uq_scenario_assumption'),
    )

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Assumption Identity
    assumption_category = Column(String(50), nullable=False)  # "revenue", "expenditure", "pension"
    assumption_name = Column(String(100), nullable=False)  # "property_tax_growth_rate"

    # Value
    assumption_value = Column(String(100), nullable=False)
    assumption_numeric_value = Column(Numeric(10, 6), nullable=True)  # If numeric

    # Description
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)  # Why this assumption?

    # Source
    source = Column(String(255), nullable=True)  # Where did this assumption come from?

    is_custom = Column(Boolean, nullable=False, default=False)  # User-modified assumption?

    # Relationships
    scenario = relationship("ProjectionScenario")

    def __repr__(self) -> str:
        return (f"<ScenarioAssumption(scenario_id={self.scenario_id}, "
                f"name='{self.assumption_name}', value='{self.assumption_value}')>")


class FiscalCliffAnalysis(Base, AuditMixin):
    """
    Analysis of when/if a city hits fiscal crisis.

    "Fiscal Cliff" = year when revenues < expenditures AND reserves exhausted.
    """
    __tablename__ = "fiscal_cliff_analyses"
    __table_args__ = (
        UniqueConstraint('city_id', 'base_fiscal_year_id', 'scenario_id',
                        name='uq_fiscal_cliff_analysis'),
    )

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    base_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("projection_scenarios.id"), nullable=False)

    # Analysis date
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Results
    has_fiscal_cliff = Column(Boolean, nullable=False)
    fiscal_cliff_year = Column(Integer, nullable=True)  # Which year does crisis hit?
    years_until_cliff = Column(Integer, nullable=True)  # How many years away?

    # Details
    reserves_exhausted_year = Column(Integer, nullable=True)
    cumulative_deficit_at_cliff = Column(Numeric(15, 2), nullable=True)

    # Severity
    severity = Column(String(20), nullable=True)  # "immediate", "near_term", "long_term", "none"

    # Narrative
    summary = Column(Text, nullable=True)

    # Sensitivity analysis
    # How much would revenues need to increase to avoid cliff?
    revenue_increase_needed_percent = Column(Numeric(6, 2), nullable=True)

    # How much would expenditures need to decrease?
    expenditure_decrease_needed_percent = Column(Numeric(6, 2), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    city = relationship("City")
    base_fiscal_year = relationship("FiscalYear")
    scenario = relationship("ProjectionScenario")

    def __repr__(self) -> str:
        return (f"<FiscalCliffAnalysis(city_id={self.city_id}, "
                f"has_cliff={self.has_fiscal_cliff}, year={self.fiscal_cliff_year})>")
```

Execute this prompt to create projection models.

Now initialize database with Alembic.

Create `src/database/migrations/env.py`:
```python
"""
Alembic environment configuration.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from src.config.settings import settings
from src.database.base import Base

# Import all models so Alembic can see them
from src.database.models.core import *
from src.database.models.financial import *
from src.database.models.pensions import *
from src.database.models.risk import *
from src.database.models.projections import *

# this is the Alembic Config object
config = context.config

# Set the database URL from our settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Create initial migration:
```bash
# From project root
poetry run alembic init src/database/migrations
poetry run alembic revision --autogenerate -m "Initial schema"
poetry run alembic upgrade head
```

**Database schema is now complete. Proceed to API design.**
```

---

## PHASE 2: API DESIGN & IMPLEMENTATION

### Prompt 2.1: Create Core API Structure

```
Build the FastAPI application structure with health checks, middleware, and base configuration.

**Context:** The API is how external users (dashboard, researchers, public) access data. Must be:
- Well-documented (OpenAPI/Swagger)
- Fast (<500ms response time for simple queries)
- Secure (rate limiting, input validation)
- Versioned (API v1, v2, etc.)

Create `src/api/main.py`:

```python
"""
FastAPI application main entry point.

This is the public interface to IBCo data.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from src.config.settings import settings
from src.config.logging_config import setup_logging, get_logger
from src.api.v1.routes import health, cities, financial, risk, projections, metadata

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info("IBCo API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    yield

    # Shutdown
    logger.info("IBCo API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="IBCo Vallejo Console API",
    description=(
        "Independent Budget & Oversight Console - Municipal fiscal transparency API.\n\n"
        "Provides access to municipal financial data, pension obligations, risk scores, "
        "and financial projections.\n\n"
        "**Important:** This is independent civic analysis, not official city data. "
        "See /disclaimer for full disclaimer."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        }
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(cities.router, prefix=settings.api_prefix, tags=["Cities"])
app.include_router(financial.router, prefix=settings.api_prefix, tags=["Financial Data"])
app.include_router(risk.router, prefix=settings.api_prefix, tags=["Risk Scores"])
app.include_router(projections.router, prefix=settings.api_prefix, tags=["Projections"])
app.include_router(metadata.router, prefix=settings.api_prefix, tags=["Metadata"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": "IBCo Vallejo Console API",
        "version": "1.0.0",
        "description": "Municipal fiscal transparency API",
        "documentation": "/docs",
        "health": "/health",
        "disclaimer": "/disclaimer",
    }


# Disclaimer endpoint
@app.get("/disclaimer", tags=["Root"])
async def disclaimer():
    """
    Legal disclaimer.

    IMPORTANT: Read this before using the API.
    """
    return {
        "title": "IBCo Legal Disclaimer",
        "independent_analysis": (
            "IBCo is an independent civic transparency project. "
            "We are not affiliated with, endorsed by, or representative of any government agency."
        ),
        "no_warranties": (
            "This API and its data are provided 'AS IS' without warranty of any kind. "
            "Users are responsible for independently verifying information."
        ),
        "not_predictions": (
            "Risk scores are composite indicators of fiscal stress, NOT predictions of bankruptcy. "
            "They are relative assessments based on financial ratios, not probability forecasts."
        ),
        "not_financial_advice": (
            "Nothing in this API constitutes financial, investment, legal, or professional advice. "
            "For important decisions, consult qualified professionals."
        ),
        "data_corrections": (
            "We take accuracy seriously. Report errors to: data@ibco-ca.us"
        ),
        "full_disclaimer": "https://docs.ibco-ca.us/legal/disclaimer",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
```

Create database dependency in `src/api/dependencies.py`:
```python
"""
Shared FastAPI dependencies.
"""
from typing import Generator

from sqlalchemy.orm import Session

from src.config.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Create database configuration in `src/config/database.py`:
```python
"""
Database connection configuration.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import settings

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,  # Log SQL in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db_session() -> Session:
    """Get a database session."""
    return SessionLocal()
```

Execute this prompt to create API foundation, then proceed to endpoint implementation.
```

---

### Prompt 2.2: Implement API Endpoints - Health & Metadata

```
Create health check and metadata endpoints.

**Context:** These endpoints allow monitoring, diagnostics, and data provenance tracking.

Create `src/api/v1/routes/health.py`:

```python
"""
Health check endpoints.
"""
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api.dependencies import get_db
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check.

    Returns 200 if service is alive.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "IBCo Vallejo Console API",
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check including dependencies.

    Checks:
    - API service
    - Database connectivity
    - Redis connectivity (if used)
    """
    checks = []
    overall_healthy = True

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks.append({
            "name": "database",
            "status": "healthy",
            "message": "PostgreSQL connection successful"
        })
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks.append({
            "name": "database",
            "status": "unhealthy",
            "message": str(e)
        })
        overall_healthy = False

    # Check Redis (if configured)
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        checks.append({
            "name": "redis",
            "status": "healthy",
            "message": "Redis connection successful"
        })
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks.append({
            "name": "redis",
            "status": "unhealthy",
            "message": str(e)
        })
        # Redis is optional, don't fail overall health

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "IBCo Vallejo Console API",
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": checks,
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness probe for Kubernetes/container orchestration.

    Returns 200 when ready to serve traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/container orchestration.

    Returns 200 if process is alive (doesn't check dependencies).
    """
    return {"status": "alive"}
```

Create `src/api/v1/routes/metadata.py`:

```python
"""
Data metadata and provenance endpoints.

Transparency about data sources and quality.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.common import DataSourceResponse, DataLineageResponse
from src.database.models.core import DataSource, DataLineage

router = APIRouter(prefix="/metadata")


@router.get("/sources", response_model=List[DataSourceResponse])
async def list_data_sources(
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all data sources.

    Provides transparency about where our data comes from.

    Query Parameters:
    - source_type: Filter by type (CAFR, CalPERS, StateController, Manual)
    """
    query = db.query(DataSource)

    if source_type:
        query = query.filter(DataSource.source_type == source_type)

    sources = query.order_by(DataSource.name).all()

    return sources


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details about a specific data source.
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    return source


@router.get("/lineage", response_model=List[DataLineageResponse])
async def get_data_lineage(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Get data lineage for a specific record.

    Shows where a piece of data came from, how it was extracted, and validation status.

    Query Parameters:
    - table_name: The table name (e.g., "revenues", "pension_plans")
    - record_id: The record ID

    This endpoint enables full transparency and traceability.
    """
    lineage = db.query(DataLineage).filter(
        DataLineage.table_name == table_name,
        DataLineage.record_id == record_id
    ).order_by(desc(DataLineage.extracted_at)).all()

    if not lineage:
        raise HTTPException(
            status_code=404,
            detail=f"No lineage found for {table_name} record {record_id}"
        )

    return lineage


@router.get("/data-quality")
async def get_data_quality_summary(
    db: Session = Depends(get_db)
):
    """
    Overall data quality summary.

    Reports on:
    - Data completeness
    - Validation status
    - Last update times
    - Known issues
    """
    from src.database.models.core import FiscalYear

    # Get fiscal years with completeness flags
    fiscal_years = db.query(FiscalYear).order_by(desc(FiscalYear.year)).limit(10).all()

    summary = {
        "last_updated": datetime.utcnow().isoformat(),
        "fiscal_years_available": len(fiscal_years),
        "recent_years": []
    }

    for fy in fiscal_years:
        summary["recent_years"].append({
            "year": fy.year,
            "city": fy.city.name,
            "data_completeness": {
                "revenues": fy.revenues_complete,
                "expenditures": fy.expenditures_complete,
                "pensions": fy.pension_data_complete,
            },
            "data_quality_score": fy.data_quality_score,
            "cafr_available": fy.cafr_available,
            "cafr_url": fy.cafr_url,
        })

    return summary
```

Create common schema models in `src/api/v1/schemas/common.py`:

```python
"""
Common Pydantic schemas used across multiple endpoints.
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DataSourceResponse(BaseModel):
    """Data source information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: str
    organization: str
    url: Optional[str] = None
    description: Optional[str] = None
    reliability_rating: Optional[str] = None
    access_method: str
    expected_update_frequency: Optional[str] = None
    last_checked_date: Optional[datetime] = None


class DataLineageResponse(BaseModel):
    """Data lineage information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_name: str
    record_id: int
    field_name: str
    source_document_url: Optional[str] = None
    source_document_page: Optional[int] = None
    extraction_method: str
    extracted_by: Optional[str] = None
    extracted_at: datetime
    validated: bool
    validated_by: Optional[str] = None
    confidence_level: Optional[str] = None
    notes: Optional[str] = None


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page")
    per_page: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
```

Execute this prompt to create health checks and metadata endpoints.
```

---

### Prompt 2.3: Implement API Endpoints - Cities & Financial Data

```
Create endpoints for city information and financial data retrieval.

**Context:** These are the core data access endpoints. Must support:
- Efficient querying (pagination, filtering)
- Multiple output formats
- Rich metadata about data provenance

Create `src/api/v1/routes/cities.py`:

```python
"""
City endpoints.

Retrieve city information and associated fiscal years.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.city import CityResponse, CityDetailResponse, FiscalYearSummaryResponse
from src.database.models.core import City, FiscalYear

router = APIRouter(prefix="/cities")


@router.get("", response_model=List[CityResponse])
async def list_cities(
    state: Optional[str] = Query(None, description="Filter by state (e.g., CA)"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List all cities in the database.

    Query Parameters:
    - state: Filter by state code
    - is_active: Only show active cities (default: true)
    """
    query = db.query(City)

    if state:
        query = query.filter(City.state == state.upper())

    if is_active:
        query = query.filter(City.is_active == True)

    cities = query.order_by(City.name).all()

    return cities


@router.get("/{city_id}", response_model=CityDetailResponse)
async def get_city(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific city.

    Includes:
    - Basic city information
    - Demographics
    - Bankruptcy history (if applicable)
    - Available fiscal years
    """
    city = db.query(City).filter(City.id == city_id).first()

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    return city


@router.get("/{city_id}/fiscal-years", response_model=List[FiscalYearSummaryResponse])
async def get_city_fiscal_years(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all fiscal years for a city.

    Returns summary information for each year including data availability.
    """
    city = db.query(City).filter(City.id == city_id).first()

    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    fiscal_years = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id
    ).order_by(desc(FiscalYear.year)).all()

    return fiscal_years


@router.get("/name/{city_name}", response_model=CityDetailResponse)
async def get_city_by_name(
    city_name: str,
    state: str = Query("CA", description="State code"),
    db: Session = Depends(get_db)
):
    """
    Get city by name.

    Useful for human-readable URLs like /cities/name/Vallejo
    """
    city = db.query(City).filter(
        City.name.ilike(city_name),  # Case-insensitive
        City.state == state.upper()
    ).first()

    if not city:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_name}' not found in {state}"
        )

    return city
```

Create schemas in `src/api/v1/schemas/city.py`:

```python
"""
City-related Pydantic schemas.
"""
from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, ConfigDict


class CityResponse(BaseModel):
    """Basic city information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    county: str
    population: Optional[int] = None
    government_type: Optional[str] = None
    is_active: bool
    has_bankruptcy_history: bool


class CityDetailResponse(BaseModel):
    """Detailed city information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    state: str
    county: str

    # Demographics
    population: Optional[int] = None
    population_year: Optional[int] = None
    incorporation_date: Optional[date] = None

    # Geographic
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Government
    government_type: Optional[str] = None
    fiscal_year_end_month: int
    fiscal_year_end_day: int
    is_charter_city: Optional[bool] = None

    # Status
    is_active: bool

    # Bankruptcy history
    has_bankruptcy_history: bool
    bankruptcy_filing_date: Optional[date] = None
    bankruptcy_exit_date: Optional[date] = None
    bankruptcy_chapter: Optional[str] = None
    bankruptcy_notes: Optional[str] = None

    # Contact
    website_url: Optional[str] = None
    finance_department_url: Optional[str] = None


class FiscalYearSummaryResponse(BaseModel):
    """Summary of a fiscal year's data availability."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    start_date: date
    end_date: date

    # Data availability
    cafr_available: bool
    cafr_url: Optional[str] = None
    cafr_publish_date: Optional[date] = None

    budget_available: bool

    calpers_valuation_available: bool

    # Completeness
    revenues_complete: bool
    expenditures_complete: bool
    pension_data_complete: bool

    data_quality_score: Optional[int] = None
```

Create `src/api/v1/routes/financial.py`:

```python
"""
Financial data endpoints.

Retrieve revenues, expenditures, fund balances, and pension data.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.financial import (
    RevenueResponse,
    ExpenditureResponse,
    FundBalanceResponse,
    PensionPlanResponse,
    FinancialSummaryResponse
)
from src.database.models.core import City, FiscalYear
from src.database.models.financial import Revenue, Expenditure, FundBalance
from src.database.models.pensions import PensionPlan

router = APIRouter(prefix="/financial")


@router.get("/cities/{city_id}/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get financial summary for a city and year.

    Returns high-level overview:
    - Total revenues and expenditures
    - Fund balance
    - Pension summary
    - Operating surplus/deficit
    """
    # Get fiscal year
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(
            status_code=404,
            detail=f"Fiscal year {year} not found for city {city_id}"
        )

    # Calculate totals
    total_revenues = db.query(Revenue).filter(
        Revenue.fiscal_year_id == fiscal_year.id
    ).with_entities(func.sum(Revenue.actual_amount)).scalar() or 0

    total_expenditures = db.query(Expenditure).filter(
        Expenditure.fiscal_year_id == fiscal_year.id
    ).with_entities(func.sum(Expenditure.actual_amount)).scalar() or 0

    fund_balance = db.query(FundBalance).filter(
        FundBalance.fiscal_year_id == fiscal_year.id,
        FundBalance.fund_type == "General"
    ).first()

    pension_plans = db.query(PensionPlan).filter(
        PensionPlan.fiscal_year_id == fiscal_year.id
    ).all()

    total_pension_ual = sum(
        (p.unfunded_actuarial_liability or 0) for p in pension_plans
    )

    return {
        "city_id": city_id,
        "city_name": fiscal_year.city.name,
        "fiscal_year": year,
        "total_revenues": float(total_revenues),
        "total_expenditures": float(total_expenditures),
        "operating_balance": float(total_revenues - total_expenditures),
        "fund_balance": float(fund_balance.total_fund_balance) if fund_balance else None,
        "fund_balance_ratio": float(fund_balance.fund_balance_ratio) if fund_balance else None,
        "total_pension_ual": float(total_pension_ual),
        "data_quality_score": fiscal_year.data_quality_score,
    }


@router.get("/cities/{city_id}/revenues", response_model=List[RevenueResponse])
async def get_revenues(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    db: Session = Depends(get_db)
):
    """
    Get detailed revenue data for a city and year.

    Query Parameters:
    - year: Fiscal year (required)
    - fund_type: Filter by fund type (General, Special, Enterprise)
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    query = db.query(Revenue).filter(Revenue.fiscal_year_id == fiscal_year.id)

    if fund_type:
        query = query.filter(Revenue.fund_type == fund_type)

    revenues = query.all()

    return revenues


@router.get("/cities/{city_id}/expenditures", response_model=List[ExpenditureResponse])
async def get_expenditures(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    db: Session = Depends(get_db)
):
    """
    Get detailed expenditure data for a city and year.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    query = db.query(Expenditure).filter(Expenditure.fiscal_year_id == fiscal_year.id)

    if fund_type:
        query = query.filter(Expenditure.fund_type == fund_type)

    expenditures = query.all()

    return expenditures


@router.get("/cities/{city_id}/pensions", response_model=List[PensionPlanResponse])
async def get_pension_plans(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get pension plan data for a city and year.

    Returns CalPERS pension liabilities, funded ratios, and contribution data.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    pension_plans = db.query(PensionPlan).filter(
        PensionPlan.fiscal_year_id == fiscal_year.id
    ).all()

    return pension_plans
```

Create financial schemas in `src/api/v1/schemas/financial.py`:

```python
"""
Financial data Pydantic schemas.
"""
from typing import Optional
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class FinancialSummaryResponse(BaseModel):
    """High-level financial summary."""
    city_id: int
    city_name: str
    fiscal_year: int
    total_revenues: float
    total_expenditures: float
    operating_balance: float
    fund_balance: Optional[float] = None
    fund_balance_ratio: Optional[float] = None
    total_pension_ual: float
    data_quality_score: Optional[int] = None


class RevenueResponse(BaseModel):
    """Revenue data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    budget_amount: Optional[Decimal] = None
    actual_amount: Decimal
    variance_amount: Optional[Decimal] = None
    variance_percent: Optional[Decimal] = None
    is_estimated: bool
    confidence_level: Optional[str] = None


class ExpenditureResponse(BaseModel):
    """Expenditure data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    department: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    actual_amount: Decimal
    variance_amount: Optional[Decimal] = None
    is_estimated: bool


class FundBalanceResponse(BaseModel):
    """Fund balance data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    fund_type: str
    total_fund_balance: Decimal
    fund_balance_ratio: Optional[Decimal] = None
    days_of_cash: Optional[Decimal] = None
    yoy_change_amount: Optional[Decimal] = None
    yoy_change_percent: Optional[Decimal] = None


class PensionPlanResponse(BaseModel):
    """Pension plan data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_year_id: int
    plan_name: str
    valuation_date: date

    # Liabilities
    total_pension_liability: Decimal
    fiduciary_net_position: Decimal
    unfunded_actuarial_liability: Decimal
    funded_ratio: Decimal

    # Contributions
    total_employer_contribution: Optional[Decimal] = None
    total_employer_contribution_percent: Optional[Decimal] = None

    # Assumptions
    discount_rate: Optional[Decimal] = None

    is_preliminary: bool
```

Execute this prompt to create city and financial data endpoints.
```

---

## PHASE 3: DATA PIPELINE IMPLEMENTATION

### Prompt 3.1: Create Manual Data Entry Tools

```
Build tools for manual data entry of financial information.

**Context:** For MVP, manual data entry is FASTER and MORE RELIABLE than PDF extraction.
These tools must:
- Make entry easy (spreadsheet-like interface via scripts)
- Validate data thoroughly
- Track data lineage
- Support bulk import from CSV

Create `scripts/data_entry/import_cafr_manual.py`:

```python
"""
Manual CAFR data import script.

For MVP: manually transcribe CAFR data into CSV, then import.
This is faster and more reliable than building PDF extraction.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from src.config.database import SessionLocal
from src.database.models.core import City, FiscalYear, DataSource, DataLineage
from src.database.models.financial import (
    Revenue, Expenditure, FundBalance,
    RevenueCategory, ExpenditureCategory
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class CAFRImporter:
    """Import manually transcribed CAFR data."""

    def __init__(self, db: Session):
        self.db = db
        self.validation_errors: List[str] = []
        self.warnings: List[str] = []

    def import_from_csv(
        self,
        city_name: str,
        fiscal_year: int,
        revenues_csv: Path,
        expenditures_csv: Path,
        fund_balance_csv: Path,
        cafr_url: str,
        transcribed_by: str
    ) -> bool:
        """
        Import CAFR data from CSV files.

        CSV Format:

        revenues.csv:
        category,fund_type,budget_amount,actual_amount,notes

        expenditures.csv:
        category,department,fund_type,budget_amount,actual_amount,notes

        fund_balance.csv:
        fund_type,nonspendable,restricted,committed,assigned,unassigned,total
        """
        logger.info(f"Starting CAFR import for {city_name} FY {fiscal_year}")

        # Get or create city
        city = self.get_or_create_city(city_name)

        # Get or create fiscal year
        fy = self.get_or_create_fiscal_year(city.id, fiscal_year, cafr_url)

        # Create data source record
        data_source = self.create_data_source(city_name, fiscal_year, cafr_url)

        # Import revenues
        if revenues_csv.exists():
            logger.info(f"Importing revenues from {revenues_csv}")
            revenue_count = self.import_revenues(fy.id, revenues_csv, data_source.id, transcribed_by)
            logger.info(f"Imported {revenue_count} revenue records")
        else:
            self.warnings.append(f"Revenue file not found: {revenues_csv}")

        # Import expenditures
        if expenditures_csv.exists():
            logger.info(f"Importing expenditures from {expenditures_csv}")
            exp_count = self.import_expenditures(fy.id, expenditures_csv, data_source.id, transcribed_by)
            logger.info(f"Imported {exp_count} expenditure records")
        else:
            self.warnings.append(f"Expenditure file not found: {expenditures_csv}")

        # Import fund balance
        if fund_balance_csv.exists():
            logger.info(f"Importing fund balance from {fund_balance_csv}")
            self.import_fund_balance(fy.id, fund_balance_csv, data_source.id, transcribed_by)
            logger.info("Imported fund balance")
        else:
            self.warnings.append(f"Fund balance file not found: {fund_balance_csv}")

        # Validate imported data
        self.validate_fiscal_year_data(fy.id)

        if self.validation_errors:
            logger.error("Validation errors found:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
            return False

        if self.warnings:
            logger.warning("Warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        # Mark fiscal year as complete
        fy.revenues_complete = True
        fy.expenditures_complete = True
        self.db.commit()

        logger.info("Import completed successfully")
        return True

    def get_or_create_city(self, city_name: str) -> City:
        """Get existing city or create new one."""
        city = self.db.query(City).filter(City.name == city_name).first()

        if not city:
            logger.info(f"Creating new city: {city_name}")
            city = City(
                name=city_name,
                state="CA",
                county="Unknown",  # TODO: Add county info
                fiscal_year_end_month=6,
                fiscal_year_end_day=30,
            )
            self.db.add(city)
            self.db.commit()
            self.db.refresh(city)

        return city

    def get_or_create_fiscal_year(
        self,
        city_id: int,
        year: int,
        cafr_url: str
    ) -> FiscalYear:
        """Get existing fiscal year or create new one."""
        fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id,
            FiscalYear.year == year
        ).first()

        if not fy:
            logger.info(f"Creating fiscal year {year}")
            fy = FiscalYear(
                city_id=city_id,
                year=year,
                start_date=date(year - 1, 7, 1),
                end_date=date(year, 6, 30),
                cafr_available=True,
                cafr_url=cafr_url,
            )
            self.db.add(fy)
            self.db.commit()
            self.db.refresh(fy)

        return fy

    def create_data_source(
        self,
        city_name: str,
        fiscal_year: int,
        cafr_url: str
    ) -> DataSource:
        """Create data source record for this CAFR."""
        source = DataSource(
            name=f"{city_name} CAFR FY{fiscal_year}",
            source_type="CAFR",
            organization=f"City of {city_name}",
            url=cafr_url,
            description=f"Comprehensive Annual Financial Report for {city_name} fiscal year {fiscal_year}",
            reliability_rating="High",
            access_method="Manual",
            expected_update_frequency="Annual",
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def import_revenues(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> int:
        """Import revenue data from CSV."""
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Get or create category
                    category = self.get_or_create_revenue_category(row['category'])

                    # Create revenue record
                    revenue = Revenue(
                        fiscal_year_id=fiscal_year_id,
                        category_id=category.id,
                        fund_type=row.get('fund_type', 'General'),
                        budget_amount=self.parse_decimal(row.get('budget_amount')),
                        actual_amount=self.parse_decimal(row['actual_amount']),
                        source_document_type="CAFR",
                        is_estimated=False,
                        confidence_level="High",
                        notes=row.get('notes'),
                    )

                    # Calculate variance if budget provided
                    if revenue.budget_amount:
                        revenue.variance_amount = revenue.actual_amount - revenue.budget_amount
                        if revenue.budget_amount > 0:
                            revenue.variance_percent = (
                                (revenue.variance_amount / revenue.budget_amount) * 100
                            )

                    self.db.add(revenue)
                    self.db.flush()  # Get ID

                    # Create lineage record
                    self.create_lineage_record(
                        "revenues",
                        revenue.id,
                        "actual_amount",
                        source_id,
                        transcribed_by
                    )

                    count += 1

                except Exception as e:
                    self.validation_errors.append(
                        f"Error importing revenue '{row.get('category')}': {e}"
                    )

        self.db.commit()
        return count

    def import_expenditures(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> int:
        """Import expenditure data from CSV."""
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    category = self.get_or_create_expenditure_category(row['category'])

                    expenditure = Expenditure(
                        fiscal_year_id=fiscal_year_id,
                        category_id=category.id,
                        fund_type=row.get('fund_type', 'General'),
                        department=row.get('department'),
                        budget_amount=self.parse_decimal(row.get('budget_amount')),
                        actual_amount=self.parse_decimal(row['actual_amount']),
                        source_document_type="CAFR",
                        is_estimated=False,
                        confidence_level="High",
                        notes=row.get('notes'),
                    )

                    if expenditure.budget_amount:
                        expenditure.variance_amount = expenditure.actual_amount - expenditure.budget_amount
                        if expenditure.budget_amount > 0:
                            expenditure.variance_percent = (
                                (expenditure.variance_amount / expenditure.budget_amount) * 100
                            )

                    self.db.add(expenditure)
                    self.db.flush()

                    self.create_lineage_record(
                        "expenditures",
                        expenditure.id,
                        "actual_amount",
                        source_id,
                        transcribed_by
                    )

                    count += 1

                except Exception as e:
                    self.validation_errors.append(
                        f"Error importing expenditure '{row.get('category')}': {e}"
                    )

        self.db.commit()
        return count

    def import_fund_balance(
        self,
        fiscal_year_id: int,
        csv_path: Path,
        source_id: int,
        transcribed_by: str
    ) -> None:
        """Import fund balance from CSV."""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fund_balance = FundBalance(
                    fiscal_year_id=fiscal_year_id,
                    fund_type=row.get('fund_type', 'General'),
                    nonspendable=self.parse_decimal(row.get('nonspendable', 0)),
                    restricted=self.parse_decimal(row.get('restricted', 0)),
                    committed=self.parse_decimal(row.get('committed', 0)),
                    assigned=self.parse_decimal(row.get('assigned', 0)),
                    unassigned=self.parse_decimal(row.get('unassigned', 0)),
                    total_fund_balance=self.parse_decimal(row['total']),
                    source_document_type="CAFR",
                )

                self.db.add(fund_balance)
                self.db.flush()

                self.create_lineage_record(
                    "fund_balances",
                    fund_balance.id,
                    "total_fund_balance",
                    source_id,
                    transcribed_by
                )

        self.db.commit()

    def get_or_create_revenue_category(self, category_name: str) -> RevenueCategory:
        """Get or create revenue category."""
        category = self.db.query(RevenueCategory).filter(
            RevenueCategory.standard_name == category_name
        ).first()

        if not category:
            # Simple categorization - can be enhanced later
            level1 = category_name.split(" - ")[0] if " - " in category_name else category_name

            category = RevenueCategory(
                category_level1=level1,
                standard_name=category_name,
                is_recurring=True,
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        return category

    def get_or_create_expenditure_category(self, category_name: str) -> ExpenditureCategory:
        """Get or create expenditure category."""
        category = self.db.query(ExpenditureCategory).filter(
            ExpenditureCategory.standard_name == category_name
        ).first()

        if not category:
            level1 = category_name.split(" - ")[0] if " - " in category_name else category_name

            category = ExpenditureCategory(
                category_level1=level1,
                standard_name=category_name,
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        return category

    def create_lineage_record(
        self,
        table_name: str,
        record_id: int,
        field_name: str,
        source_id: int,
        transcribed_by: str
    ) -> None:
        """Create data lineage record."""
        lineage = DataLineage(
            table_name=table_name,
            record_id=record_id,
            field_name=field_name,
            source_id=source_id,
            extraction_method="Manual",
            extracted_by=transcribed_by,
            extracted_at=datetime.utcnow(),
            validated=True,  # Assume manual entry is validated
            confidence_level="High",
        )
        self.db.add(lineage)

    def validate_fiscal_year_data(self, fiscal_year_id: int) -> None:
        """Validate imported data for internal consistency."""
        from sqlalchemy import func

        # Check that revenues sum correctly
        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == fiscal_year_id
        ).scalar() or 0

        if total_revenues == 0:
            self.validation_errors.append("Total revenues is zero")

        # Check that expenditures sum correctly
        total_expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == fiscal_year_id
        ).scalar() or 0

        if total_expenditures == 0:
            self.validation_errors.append("Total expenditures is zero")

        # Check for negative values (should be rare)
        negative_revenues = self.db.query(Revenue).filter(
            Revenue.fiscal_year_id == fiscal_year_id,
            Revenue.actual_amount < 0
        ).count()

        if negative_revenues > 0:
            self.warnings.append(f"{negative_revenues} negative revenue values found")

        logger.info(f"Validation: Total revenues = ${total_revenues:,.2f}")
        logger.info(f"Validation: Total expenditures = ${total_expenditures:,.2f}")
        logger.info(f"Validation: Operating balance = ${total_revenues - total_expenditures:,.2f}")

    @staticmethod
    def parse_decimal(value: Any) -> Decimal:
        """Parse string to Decimal, handling currency formatting."""
        if value is None or value == '':
            return Decimal(0)

        # Remove currency symbols, commas, parentheses
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
            # Handle parentheses as negative
            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]

        return Decimal(value)


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 7:
        print("Usage: python import_cafr_manual.py CITY_NAME YEAR REVENUES_CSV EXPENDITURES_CSV FUND_BALANCE_CSV CAFR_URL [TRANSCRIBED_BY]")
        print()
        print("Example:")
        print("  python import_cafr_manual.py Vallejo 2024 revenues_2024.csv expenditures_2024.csv fund_balance_2024.csv https://example.com/cafr.pdf 'John Doe'")
        sys.exit(1)

    city_name = sys.argv[1]
    year = int(sys.argv[2])
    revenues_csv = Path(sys.argv[3])
    expenditures_csv = Path(sys.argv[4])
    fund_balance_csv = Path(sys.argv[5])
    cafr_url = sys.argv[6]
    transcribed_by = sys.argv[7] if len(sys.argv) > 7 else "Unknown"

    db = SessionLocal()
    try:
        importer = CAFRImporter(db)
        success = importer.import_from_csv(
            city_name=city_name,
            fiscal_year=year,
            revenues_csv=revenues_csv,
            expenditures_csv=expenditures_csv,
            fund_balance_csv=fund_balance_csv,
            cafr_url=cafr_url,
            transcribed_by=transcribed_by
        )

        if success:
            print("✅ Import completed successfully!")
            sys.exit(0)
        else:
            print("❌ Import completed with errors")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
```

Create similar script for pension data in `scripts/data_entry/import_calpers_manual.py`:

```python
"""
Manual CalPERS pension data import.

Import pension data transcribed from CalPERS valuation reports.
"""
import csv
from pathlib import Path
from datetime import date
from decimal import Decimal

from src.config.database import SessionLocal
from src.database.models.core import FiscalYear, DataSource, DataLineage
from src.database.models.pensions import PensionPlan
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class CalPERSImporter:
    """Import CalPERS pension data."""

    def __init__(self, db):
        self.db = db

    def import_from_csv(
        self,
        city_name: str,
        fiscal_year: int,
        pensions_csv: Path,
        valuation_url: str,
        transcribed_by: str
    ) -> bool:
        """
        Import CalPERS data from CSV.

        CSV Format:
        plan_name,valuation_date,total_pension_liability,fiduciary_net_position,
        unfunded_actuarial_liability,funded_ratio,total_employer_contribution,
        discount_rate,notes
        """
        logger.info(f"Importing CalPERS data for {city_name} FY {fiscal_year}")

        # Get fiscal year
        fy = self.db.query(FiscalYear).join(FiscalYear.city).filter(
            City.name == city_name,
            FiscalYear.year == fiscal_year
        ).first()

        if not fy:
            logger.error(f"Fiscal year not found: {city_name} {fiscal_year}")
            return False

        # Create data source
        source = DataSource(
            name=f"{city_name} CalPERS Valuation FY{fiscal_year}",
            source_type="CalPERS",
            organization="CalPERS",
            url=valuation_url,
            reliability_rating="High",
            access_method="Manual",
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        # Import pension plans
        with open(pensions_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pension_plan = PensionPlan(
                    fiscal_year_id=fy.id,
                    plan_name=row['plan_name'],
                    valuation_date=date.fromisoformat(row['valuation_date']),
                    total_pension_liability=Decimal(row['total_pension_liability']),
                    fiduciary_net_position=Decimal(row['fiduciary_net_position']),
                    net_pension_liability=Decimal(row['unfunded_actuarial_liability']),
                    unfunded_actuarial_liability=Decimal(row['unfunded_actuarial_liability']),
                    funded_ratio=Decimal(row['funded_ratio']),
                    total_employer_contribution=Decimal(row.get('total_employer_contribution', 0)),
                    discount_rate=Decimal(row.get('discount_rate', 0)),
                    source_document="CalPERS Valuation Report",
                    source_url=valuation_url,
                    is_preliminary=False,
                    confidence_level="High",
                    notes=row.get('notes'),
                )

                self.db.add(pension_plan)
                self.db.flush()

                # Create lineage
                lineage = DataLineage(
                    table_name="pension_plans",
                    record_id=pension_plan.id,
                    field_name="unfunded_actuarial_liability",
                    source_id=source.id,
                    extraction_method="Manual",
                    extracted_by=transcribed_by,
                    validated=True,
                    confidence_level="High",
                )
                self.db.add(lineage)

        self.db.commit()

        # Mark pension data as complete
        fy.pension_data_complete = True
        fy.calpers_valuation_available = True
        fy.calpers_valuation_url = valuation_url
        self.db.commit()

        logger.info("CalPERS import completed successfully")
        return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 6:
        print("Usage: python import_calpers_manual.py CITY_NAME YEAR PENSIONS_CSV VALUATION_URL TRANSCRIBED_BY")
        sys.exit(1)

    city_name = sys.argv[1]
    year = int(sys.argv[2])
    pensions_csv = Path(sys.argv[3])
    valuation_url = sys.argv[4]
    transcribed_by = sys.argv[5]

    db = SessionLocal()
    try:
        importer = CalPERSImporter(db)
        success = importer.import_from_csv(
            city_name,
            year,
            pensions_csv,
            valuation_url,
            transcribed_by
        )
        sys.exit(0 if success else 1)
    finally:
        db.close()
```

Create CSV templates in `data/samples/`:

`revenues_template.csv`:
```
category,fund_type,budget_amount,actual_amount,notes
Property Taxes,General,25000000,26500000,Secured property taxes
Sales Taxes,General,18000000,17200000,Lower than budgeted
Business License Fees,General,1500000,1650000,
```

`expenditures_template.csv`:
```
category,department,fund_type,budget_amount,actual_amount,notes
Police Salaries,Police,General,15000000,14800000,
Fire Salaries,Fire,General,12000000,12100000,
Pension Contributions,General Government,General,20000000,22000000,Higher than budgeted
```

`fund_balance_template.csv`:
```
fund_type,nonspendable,restricted,committed,assigned,unassigned,total,notes
General,500000,2000000,1000000,3000000,8500000,15000000,General Fund reserves
```

`pensions_template.csv`:
```
plan_name,valuation_date,total_pension_liability,fiduciary_net_position,unfunded_actuarial_liability,funded_ratio,total_employer_contribution,discount_rate,notes
Miscellaneous,2024-06-30,250000000,165000000,85000000,0.66,15000000,0.068,Main pension plan
Safety,2024-06-30,180000000,110000000,70000000,0.61,12000000,0.068,Police and Fire
```

Execute this prompt to create manual data entry tools. This is the PRIMARY method for initial data population.
```

---

## PHASE 4: ANALYTICS ENGINE IMPLEMENTATION

### Prompt 4.1: Implement Risk Scoring Engine

```
Build the risk scoring engine that calculates fiscal stress indicators.

**Context:** This is THE core analytical output. Must be:
- Transparent (no black-box ML)
- Reproducible (same inputs = same outputs)
- Explainable (show which factors drive the score)
- Well-documented (methodology visible to users)

Create `src/analytics/risk_scoring/indicators.py`:

```python
"""
Individual risk indicator calculations.

Each indicator is a standalone function that:
1. Takes fiscal year data as input
2. Calculates a specific financial ratio
3. Returns the value and metadata
"""
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Revenue, Expenditure, FundBalance
from src.database.models.pensions import PensionPlan
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RiskIndicatorCalculator:
    """Calculate individual risk indicators."""

    def __init__(self, db: Session, fiscal_year_id: int):
        self.db = db
        self.fiscal_year_id = fiscal_year_id
        self.fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()

        if not self.fiscal_year:
            raise ValueError(f"Fiscal year {fiscal_year_id} not found")

    # ==========================================
    # CATEGORY 1: LIQUIDITY & RESERVES (25% weight)
    # ==========================================

    def calculate_fund_balance_ratio(self) -> Dict[str, Any]:
        """
        Fund Balance Ratio = Fund Balance / Expenditures

        Measures: How many months of reserves does the city have?

        Thresholds:
        - Healthy: >20% (2.4 months)
        - Adequate: 15-20% (1.8-2.4 months)
        - Warning: 10-15% (1.2-1.8 months)
        - Critical: <10% (<1.2 months)
        """
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == self.fiscal_year_id,
            FundBalance.fund_type == "General"
        ).first()

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if not fund_balance or total_expenditures == 0:
            return {
                "indicator_code": "FB_RATIO",
                "value": None,
                "score": None,
                "threshold": None,
                "available": False,
                "notes": "Insufficient data"
            }

        ratio = float(fund_balance.total_fund_balance / total_expenditures)

        # Score based on thresholds
        if ratio >= 0.20:
            score = 0  # Healthy
            threshold = "healthy"
        elif ratio >= 0.15:
            score = 25  # Adequate
            threshold = "adequate"
        elif ratio >= 0.10:
            score = 50  # Warning
            threshold = "warning"
        else:
            score = 100  # Critical
            threshold = "critical"

        return {
            "indicator_code": "FB_RATIO",
            "indicator_name": "Fund Balance Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"{ratio:.1%} of annual expenditures in reserves",
            "notes": None
        }

    def calculate_days_of_cash(self) -> Dict[str, Any]:
        """
        Days of Cash = (Cash + Investments) / (Annual Expenditures / 365)

        Measures: How many days can the city operate with current cash?

        Thresholds:
        - Healthy: >60 days
        - Adequate: 45-60 days
        - Warning: 30-45 days
        - Critical: <30 days
        """
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == self.fiscal_year_id,
            FundBalance.fund_type == "General"
        ).first()

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if not fund_balance or total_expenditures == 0:
            return self._indicator_unavailable("DAYS_CASH", "Days of Cash")

        daily_expenditure = total_expenditures / 365
        days = float(fund_balance.total_fund_balance / daily_expenditure)

        if days >= 60:
            score, threshold = 0, "healthy"
        elif days >= 45:
            score, threshold = 25, "adequate"
        elif days >= 30:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DAYS_CASH",
            "indicator_name": "Days of Cash",
            "value": days,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "days",
            "interpretation": f"Can operate for {days:.0f} days with current reserves",
        }

    def calculate_liquidity_ratio(self) -> Dict[str, Any]:
        """
        Liquidity Ratio = Current Assets / Current Liabilities

        Simplified version (using fund balance as proxy for current assets).

        Thresholds:
        - Healthy: >2.0
        - Adequate: 1.5-2.0
        - Warning: 1.0-1.5
        - Critical: <1.0
        """
        # This requires balance sheet data which may not be available in all CAFRs
        # For MVP, we'll use fund balance ratio as a proxy
        return self._indicator_unavailable(
            "LIQUIDITY_RATIO",
            "Liquidity Ratio",
            notes="Balance sheet data not yet imported"
        )

    # ==========================================
    # CATEGORY 2: STRUCTURAL BALANCE (25% weight)
    # ==========================================

    def calculate_operating_balance(self) -> Dict[str, Any]:
        """
        Operating Balance = (Revenues - Expenditures) / Revenues

        Measures: Structural surplus or deficit?

        Thresholds:
        - Healthy: >5% (surplus)
        - Adequate: 0-5% (balanced)
        - Warning: -5% to 0% (deficit)
        - Critical: <-5% (large deficit)
        """
        total_revenues = self.db.query(
            func.sum(Revenue.actual_amount)
        ).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        total_expenditures = self.db.query(
            func.sum(Expenditure.actual_amount)
        ).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        if total_revenues == 0:
            return self._indicator_unavailable("OP_BALANCE", "Operating Balance")

        balance = float((total_revenues - total_expenditures) / total_revenues)

        if balance >= 0.05:
            score, threshold = 0, "healthy"
        elif balance >= 0:
            score, threshold = 25, "adequate"
        elif balance >= -0.05:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "OP_BALANCE",
            "indicator_name": "Operating Balance",
            "value": balance,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"{'Surplus' if balance >= 0 else 'Deficit'} of {abs(balance):.1%}",
        }

    def calculate_structural_deficit_trend(self) -> Dict[str, Any]:
        """
        Structural Deficit Trend: Count consecutive years with deficit.

        Measures: Is the deficit persistent or one-time?

        Thresholds:
        - Healthy: 0 years
        - Adequate: 1 year
        - Warning: 2 years
        - Critical: 3+ years
        """
        # Get previous fiscal years
        previous_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.fiscal_year.city_id,
            FiscalYear.year < self.fiscal_year.year
        ).order_by(FiscalYear.year.desc()).limit(3).all()

        deficit_years = 0
        for fy in [self.fiscal_year] + previous_years:
            revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)

            expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
                Expenditure.fiscal_year_id == fy.id,
                Expenditure.fund_type == "General"
            ).scalar() or Decimal(0)

            if expenditures > revenues:
                deficit_years += 1
            else:
                break  # Stop counting if not consecutive

        if deficit_years == 0:
            score, threshold = 0, "healthy"
        elif deficit_years == 1:
            score, threshold = 25, "adequate"
        elif deficit_years == 2:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DEFICIT_TREND",
            "indicator_name": "Structural Deficit Trend",
            "value": deficit_years,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "years",
            "interpretation": f"{deficit_years} consecutive years with deficit",
        }

    # ==========================================
    # CATEGORY 3: PENSION STRESS (30% weight)
    # ==========================================

    def calculate_pension_funded_ratio(self) -> Dict[str, Any]:
        """
        Pension Funded Ratio = Assets / Total Pension Liability

        THE KEY PENSION INDICATOR.

        Thresholds:
        - Healthy: >80%
        - Adequate: 70-80%
        - Warning: 60-70%
        - Critical: <60%
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        if not pension_plans:
            return self._indicator_unavailable("PENSION_FUNDED", "Pension Funded Ratio")

        # Weighted average across all plans
        total_liability = sum(p.total_pension_liability for p in pension_plans)
        total_assets = sum(p.fiduciary_net_position for p in pension_plans)

        if total_liability == 0:
            return self._indicator_unavailable("PENSION_FUNDED", "Pension Funded Ratio")

        funded_ratio = float(total_assets / total_liability)

        if funded_ratio >= 0.80:
            score, threshold = 0, "healthy"
        elif funded_ratio >= 0.70:
            score, threshold = 25, "adequate"
        elif funded_ratio >= 0.60:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "PENSION_FUNDED",
            "indicator_name": "Pension Funded Ratio",
            "value": funded_ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"Pensions are {funded_ratio:.1%} funded",
        }

    def calculate_ual_ratio(self) -> Dict[str, Any]:
        """
        UAL Ratio = Unfunded Actuarial Liability / Annual Revenues

        Measures: How large is pension debt relative to revenue?

        Thresholds:
        - Healthy: <1.0x (less than 1 year of revenue)
        - Adequate: 1.0-2.0x
        - Warning: 2.0-3.0x
        - Critical: >3.0x
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        if not pension_plans or total_revenues == 0:
            return self._indicator_unavailable("UAL_RATIO", "UAL Ratio")

        total_ual = sum(p.unfunded_actuarial_liability for p in pension_plans)
        ratio = float(total_ual / total_revenues)

        if ratio < 1.0:
            score, threshold = 0, "healthy"
        elif ratio < 2.0:
            score, threshold = 25, "adequate"
        elif ratio < 3.0:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "UAL_RATIO",
            "indicator_name": "UAL to Revenue Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "ratio",
            "interpretation": f"Unfunded pension debt is {ratio:.1f}x annual revenues",
        }

    def calculate_pension_contribution_burden(self) -> Dict[str, Any]:
        """
        Pension Contribution Burden = Annual Pension Payment / Payroll Costs

        Measures: What percentage of payroll goes to pensions?

        Thresholds:
        - Healthy: <20%
        - Adequate: 20-25%
        - Warning: 25-35%
        - Critical: >35%
        """
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == self.fiscal_year_id
        ).all()

        if not pension_plans:
            return self._indicator_unavailable("PENSION_BURDEN", "Pension Contribution Burden")

        total_contributions = sum(
            (p.total_employer_contribution or 0) for p in pension_plans
        )
        total_payroll = sum((p.covered_payroll or 0) for p in pension_plans)

        if total_payroll == 0:
            return self._indicator_unavailable("PENSION_BURDEN", "Pension Contribution Burden")

        burden = float(total_contributions / total_payroll)

        if burden < 0.20:
            score, threshold = 0, "healthy"
        elif burden < 0.25:
            score, threshold = 25, "adequate"
        elif burden < 0.35:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "PENSION_BURDEN",
            "indicator_name": "Pension Contribution Burden",
            "value": burden,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Pension costs are {burden:.1%} of payroll",
        }

    # ==========================================
    # CATEGORY 4: REVENUE SUSTAINABILITY (10% weight)
    # ==========================================

    def calculate_revenue_volatility(self) -> Dict[str, Any]:
        """
        Revenue Volatility = Standard deviation of year-over-year changes

        Measures: How stable are revenues?

        Thresholds:
        - Healthy: <5% (stable)
        - Adequate: 5-10%
        - Warning: 10-15%
        - Critical: >15% (highly volatile)
        """
        # Get 5 years of revenue data
        previous_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.fiscal_year.city_id,
            FiscalYear.year <= self.fiscal_year.year
        ).order_by(FiscalYear.year.desc()).limit(5).all()

        if len(previous_years) < 3:
            return self._indicator_unavailable(
                "REV_VOLATILITY",
                "Revenue Volatility",
                notes="Need 3+ years of data"
            )

        revenues = []
        for fy in previous_years:
            total = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)
            revenues.append(float(total))

        # Calculate year-over-year changes
        changes = []
        for i in range(len(revenues) - 1):
            if revenues[i+1] > 0:
                change = (revenues[i] - revenues[i+1]) / revenues[i+1]
                changes.append(change)

        if not changes:
            return self._indicator_unavailable("REV_VOLATILITY", "Revenue Volatility")

        # Standard deviation
        import statistics
        volatility = statistics.stdev(changes) if len(changes) > 1 else 0

        if volatility < 0.05:
            score, threshold = 0, "healthy"
        elif volatility < 0.10:
            score, threshold = 25, "adequate"
        elif volatility < 0.15:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "REV_VOLATILITY",
            "indicator_name": "Revenue Volatility",
            "value": volatility,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Revenue volatility of {volatility:.1%}",
        }

    # ==========================================
    # CATEGORY 5: DEBT BURDEN (10% weight)
    # ==========================================

    def calculate_debt_service_ratio(self) -> Dict[str, Any]:
        """
        Debt Service Ratio = Annual Debt Payments / Revenues

        Measures: What percentage of revenue goes to debt?

        Thresholds:
        - Healthy: <10%
        - Adequate: 10-15%
        - Warning: 15-20%
        - Critical: >20%
        """
        # Look for debt service in expenditures
        debt_service = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == self.fiscal_year_id,
            Expenditure.fund_type == "General",
            Expenditure.category.has(ExpenditureCategory.is_debt_service == True)
        ).scalar() or Decimal(0)

        total_revenues = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == self.fiscal_year_id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        if total_revenues == 0:
            return self._indicator_unavailable("DEBT_SERVICE", "Debt Service Ratio")

        ratio = float(debt_service / total_revenues)

        if ratio < 0.10:
            score, threshold = 0, "healthy"
        elif ratio < 0.15:
            score, threshold = 25, "adequate"
        elif ratio < 0.20:
            score, threshold = 50, "warning"
        else:
            score, threshold = 100, "critical"

        return {
            "indicator_code": "DEBT_SERVICE",
            "indicator_name": "Debt Service Ratio",
            "value": ratio,
            "score": score,
            "threshold": threshold,
            "available": True,
            "unit": "percent",
            "interpretation": f"Debt service is {ratio:.1%} of revenues",
        }

    # ==========================================
    # HELPER METHODS
    # ==========================================

    def _indicator_unavailable(
        self,
        code: str,
        name: str,
        notes: str = "Insufficient data"
    ) -> Dict[str, Any]:
        """Return structure for unavailable indicator."""
        return {
            "indicator_code": code,
            "indicator_name": name,
            "value": None,
            "score": None,
            "threshold": None,
            "available": False,
            "notes": notes
        }

    def calculate_all_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Calculate all risk indicators."""
        indicators = {
            # Liquidity
            "FB_RATIO": self.calculate_fund_balance_ratio(),
            "DAYS_CASH": self.calculate_days_of_cash(),

            # Structural Balance
            "OP_BALANCE": self.calculate_operating_balance(),
            "DEFICIT_TREND": self.calculate_structural_deficit_trend(),

            # Pension Stress
            "PENSION_FUNDED": self.calculate_pension_funded_ratio(),
            "UAL_RATIO": self.calculate_ual_ratio(),
            "PENSION_BURDEN": self.calculate_pension_contribution_burden(),

            # Revenue Sustainability
            "REV_VOLATILITY": self.calculate_revenue_volatility(),

            # Debt
            "DEBT_SERVICE": self.calculate_debt_service_ratio(),
        }

        return indicators
```

Create `src/analytics/risk_scoring/scoring_engine.py`:

```python
"""
Risk scoring engine.

Combines individual indicators into composite risk score.
"""
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from src.database.models.risk import RiskScore, RiskIndicatorScore, RiskIndicator
from src.analytics.risk_scoring.indicators import RiskIndicatorCalculator
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RiskScoringEngine:
    """Calculate composite risk scores."""

    # Category weights (must sum to 1.0)
    CATEGORY_WEIGHTS = {
        "Liquidity": 0.25,
        "Structural": 0.25,
        "Pension": 0.30,
        "Revenue": 0.10,
        "Debt": 0.10,
    }

    # Indicator to category mapping
    INDICATOR_CATEGORIES = {
        "FB_RATIO": "Liquidity",
        "DAYS_CASH": "Liquidity",
        "OP_BALANCE": "Structural",
        "DEFICIT_TREND": "Structural",
        "PENSION_FUNDED": "Pension",
        "UAL_RATIO": "Pension",
        "PENSION_BURDEN": "Pension",
        "REV_VOLATILITY": "Revenue",
        "DEBT_SERVICE": "Debt",
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_risk_score(
        self,
        fiscal_year_id: int,
        model_version: str = "1.0"
    ) -> RiskScore:
        """
        Calculate complete risk score for a fiscal year.

        Returns: RiskScore object (not yet committed to database)
        """
        logger.info(f"Calculating risk score for fiscal year {fiscal_year_id}")

        # Calculate all indicators
        calculator = RiskIndicatorCalculator(self.db, fiscal_year_id)
        indicators = calculator.calculate_all_indicators()

        # Calculate category scores
        category_scores = self._calculate_category_scores(indicators)

        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)

        # Calculate data quality
        indicators_available = sum(1 for i in indicators.values() if i["available"])
        indicators_missing = len(indicators) - indicators_available
        data_completeness = (indicators_available / len(indicators)) * 100

        # Identify top risk factors
        top_risk_factors = self._identify_top_risk_factors(indicators)

        # Generate summary
        summary = self._generate_summary(
            overall_score,
            risk_level,
            category_scores,
            top_risk_factors
        )

        # Create RiskScore object
        risk_score = RiskScore(
            fiscal_year_id=fiscal_year_id,
            calculation_date=datetime.utcnow(),
            model_version=model_version,
            overall_score=Decimal(str(overall_score)),
            risk_level=risk_level,
            liquidity_score=Decimal(str(category_scores["Liquidity"])),
            structural_balance_score=Decimal(str(category_scores["Structural"])),
            pension_stress_score=Decimal(str(category_scores["Pension"])),
            revenue_sustainability_score=Decimal(str(category_scores["Revenue"])),
            debt_burden_score=Decimal(str(category_scores["Debt"])),
            data_completeness_percent=Decimal(str(data_completeness)),
            indicators_available=indicators_available,
            indicators_missing=indicators_missing,
            data_as_of_date=datetime.utcnow(),
            top_risk_factors=top_risk_factors,
            summary=summary,
            validated=False,
        )

        # Store individual indicator scores
        for indicator_code, indicator_data in indicators.items():
            if not indicator_data["available"]:
                continue

            indicator_score = RiskIndicatorScore(
                risk_score=risk_score,
                indicator_code=indicator_code,
                indicator_value=Decimal(str(indicator_data["value"])),
                indicator_score=Decimal(str(indicator_data["score"])),
                threshold_category=indicator_data["threshold"],
                weight=Decimal(str(self._get_indicator_weight(indicator_code))),
                contribution_to_overall=Decimal(str(
                    indicator_data["score"] * self._get_indicator_weight(indicator_code)
                )),
            )
            risk_score.indicator_scores.append(indicator_score)

        logger.info(
            f"Risk score calculated: {overall_score:.1f} ({risk_level}), "
            f"data completeness: {data_completeness:.0f}%"
        )

        return risk_score

    def _calculate_category_scores(
        self,
        indicators: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate score for each category."""
        category_scores = {}

        for category in self.CATEGORY_WEIGHTS.keys():
            # Get indicators for this category
            category_indicators = [
                ind for code, ind in indicators.items()
                if self.INDICATOR_CATEGORIES.get(code) == category and ind["available"]
            ]

            if not category_indicators:
                # No data for this category - use neutral score
                category_scores[category] = 50.0
                logger.warning(f"No indicators available for category: {category}")
                continue

            # Average score across available indicators
            scores = [ind["score"] for ind in category_indicators]
            category_scores[category] = sum(scores) / len(scores)

        return category_scores

    def _calculate_overall_score(
        self,
        category_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted overall score."""
        overall = 0.0

        for category, score in category_scores.items():
            weight = self.CATEGORY_WEIGHTS[category]
            overall += score * weight

        return round(overall, 2)

    def _determine_risk_level(self, overall_score: float) -> str:
        """Classify risk level based on score."""
        if overall_score < 25:
            return "low"
        elif overall_score < 50:
            return "moderate"
        elif overall_score < 75:
            return "high"
        else:
            return "severe"

    def _identify_top_risk_factors(
        self,
        indicators: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify top 5 risk factors."""
        # Filter available indicators and sort by score
        available = [
            {
                "indicator": ind["indicator_code"],
                "name": ind["indicator_name"],
                "score": ind["score"],
                "value": ind["value"],
                "threshold": ind["threshold"],
                "interpretation": ind.get("interpretation", ""),
            }
            for ind in indicators.values()
            if ind["available"] and ind["score"] is not None
        ]

        # Sort by score (highest = worst)
        available.sort(key=lambda x: x["score"], reverse=True)

        return available[:5]

    def _generate_summary(
        self,
        overall_score: float,
        risk_level: str,
        category_scores: Dict[str, float],
        top_risk_factors: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary."""
        level_descriptions = {
            "low": "shows healthy fiscal conditions",
            "moderate": "shows some fiscal stress indicators",
            "high": "shows significant fiscal stress",
            "severe": "shows severe fiscal stress"
        }

        summary = f"Fiscal stress score of {overall_score:.0f}/100 {level_descriptions[risk_level]}.\n\n"

        # Worst category
        worst_category = max(category_scores, key=category_scores.get)
        summary += f"Primary concern: {worst_category} (score: {category_scores[worst_category]:.0f}).\n\n"

        # Top risk factors
        if top_risk_factors:
            summary += "Key risk factors:\n"
            for factor in top_risk_factors[:3]:
                summary += f"- {factor['name']}: {factor['interpretation']}\n"

        return summary

    def _get_indicator_weight(self, indicator_code: str) -> float:
        """Get weight for a specific indicator within its category."""
        category = self.INDICATOR_CATEGORIES.get(indicator_code)
        if not category:
            return 0.0

        # Count indicators in this category
        category_indicators = [
            code for code, cat in self.INDICATOR_CATEGORIES.items()
            if cat == category
        ]

        # Equal weight within category
        return self.CATEGORY_WEIGHTS[category] / len(category_indicators)
```

Execute this prompt to create the risk scoring engine.
```

---

### Prompt 4.2: Implement Projection Engine

```
Build the financial projection engine for scenario analysis.

**Context:** Projections show "what if current trends continue?" Must:
- Use CalPERS published schedules for pension projections (most predictable)
- Support multiple scenarios
- Identify "fiscal cliff" year
- Be transparent about assumptions

Create `src/analytics/projections/revenue_model.py`:

```python
"""
Revenue projection model.

Projects future revenues based on historical growth rates.
"""
from typing import List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Revenue
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class RevenueProjector:
    """Project future revenues."""

    def __init__(self, db: Session, city_id: int):
        self.db = db
        self.city_id = city_id

    def project_revenues(
        self,
        base_year: int,
        years_ahead: int,
        scenario: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        Project revenues for multiple future years.

        Args:
            base_year: Starting fiscal year
            years_ahead: Number of years to project
            scenario: "base", "optimistic", or "pessimistic"

        Returns: List of projections, one per year
        """
        # Get historical data (5 years)
        historical_years = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year <= base_year
        ).order_by(FiscalYear.year.desc()).limit(5).all()

        if len(historical_years) < 2:
            raise ValueError("Need at least 2 years of historical data")

        # Calculate historical growth rate
        growth_rate = self._calculate_historical_growth_rate(historical_years)

        # Adjust for scenario
        scenario_growth = self._adjust_for_scenario(growth_rate, scenario)

        # Get base year revenue
        base_fy = [fy for fy in historical_years if fy.year == base_year][0]
        base_revenue = self.db.query(func.sum(Revenue.actual_amount)).filter(
            Revenue.fiscal_year_id == base_fy.id,
            Revenue.fund_type == "General"
        ).scalar() or Decimal(0)

        # Project forward
        projections = []
        current_revenue = float(base_revenue)

        for year in range(1, years_ahead + 1):
            current_revenue *= (1 + scenario_growth)
            projections.append({
                "projection_year": base_year + year,
                "years_ahead": year,
                "projected_revenue": current_revenue,
                "growth_rate_used": scenario_growth,
                "scenario": scenario,
            })

        return projections

    def _calculate_historical_growth_rate(
        self,
        fiscal_years: List[FiscalYear]
    ) -> float:
        """Calculate compound annual growth rate from historical data."""
        revenues = []

        for fy in reversed(fiscal_years):  # Oldest to newest
            total = self.db.query(func.sum(Revenue.actual_amount)).filter(
                Revenue.fiscal_year_id == fy.id,
                Revenue.fund_type == "General"
            ).scalar() or Decimal(0)
            revenues.append(float(total))

        if len(revenues) < 2:
            return 0.0

        # CAGR formula: (End/Start)^(1/years) - 1
        years = len(revenues) - 1
        cagr = (revenues[-1] / revenues[0]) ** (1/years) - 1

        logger.info(f"Historical revenue CAGR: {cagr:.2%}")
        return cagr

    def _adjust_for_scenario(self, base_rate: float, scenario: str) -> float:
        """Adjust growth rate based on scenario."""
        if scenario == "optimistic":
            # Use 75th percentile (assume better performance)
            return base_rate * 1.25
        elif scenario == "pessimistic":
            # Use 25th percentile (assume worse performance)
            return base_rate * 0.75
        else:  # base
            return base_rate
```

Create `src/analytics/projections/expenditure_model.py`:

```python
"""
Expenditure projection model.

Projects expenditures with special focus on pension cost growth.
"""
from typing import List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.models.core import FiscalYear
from src.database.models.financial import Expenditure
from src.database.models.pensions import PensionPlan, PensionProjection
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ExpenditureProjector:
    """Project future expenditures."""

    def __init__(self, db: Session, city_id: int):
        self.db = db
        self.city_id = city_id

    def project_expenditures(
        self,
        base_year: int,
        years_ahead: int,
        scenario: str = "base"
    ) -> List[Dict[str, Any]]:
        """
        Project expenditures for multiple future years.

        Key insight: Pension costs are THE driver of expenditure growth.
        We project base costs separately from pension costs.
        """
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == self.city_id,
            FiscalYear.year == base_year
        ).first()

        if not base_fy:
            raise ValueError(f"Base year {base_year} not found")

        # Separate pension costs from other costs
        total_expenditures = self.db.query(func.sum(Expenditure.actual_amount)).filter(
            Expenditure.fiscal_year_id == base_fy.id,
            Expenditure.fund_type == "General"
        ).scalar() or Decimal(0)

        pension_costs = self._get_current_pension_costs(base_fy.id)
        base_costs = float(total_expenditures - pension_costs)

        # Project base costs (modest growth with inflation)
        inflation_rate = 0.025  # 2.5% assumption
        if scenario == "optimistic":
            base_growth_rate = inflation_rate * 0.8
        elif scenario == "pessimistic":
            base_growth_rate = inflation_rate * 1.2
        else:
            base_growth_rate = inflation_rate

        # Project pension costs (use CalPERS schedule if available)
        pension_projections = self._get_pension_projections(base_fy.id, years_ahead)

        # Combine projections
        projections = []
        current_base = base_costs

        for year in range(1, years_ahead + 1):
            current_base *= (1 + base_growth_rate)

            # Get pension cost for this year
            pension_cost = pension_projections.get(
                base_year + year,
                float(pension_costs) * (1.05 ** year)  # Fallback: 5% growth
            )

            total_projected = current_base + pension_cost

            projections.append({
                "projection_year": base_year + year,
                "years_ahead": year,
                "projected_expenditures": total_projected,
                "base_costs": current_base,
                "pension_costs": pension_cost,
                "base_growth_rate": base_growth_rate,
                "pension_growth_rate": (pension_cost / float(pension_costs)) ** (1/year) - 1,
                "scenario": scenario,
            })

        return projections

    def _get_current_pension_costs(self, fiscal_year_id: int) -> Decimal:
        """Get current year pension contributions."""
        pension_plans = self.db.query(PensionPlan).filter(
            PensionPlan.fiscal_year_id == fiscal_year_id
        ).all()

        total = sum(
            (p.total_employer_contribution or Decimal(0)) for p in pension_plans
        )

        return total

    def _get_pension_projections(
        self,
        base_fiscal_year_id: int,
        years_ahead: int
    ) -> Dict[int, float]:
        """
        Get pension cost projections from CalPERS schedule.

        CalPERS publishes 20-year amortization schedules - use if available.
        """
        projections = {}

        # Check if we have CalPERS projections
        calpers_projections = self.db.query(PensionProjection).filter(
            PensionProjection.base_fiscal_year_id == base_fiscal_year_id
        ).all()

        if calpers_projections:
            for proj in calpers_projections:
                projections[proj.projection_year] = float(proj.projected_contribution)
            logger.info(f"Using CalPERS published projections for {len(calpers_projections)} years")
        else:
            logger.warning("No CalPERS projections found, using fallback growth assumptions")

        return projections
```

Create `src/analytics/projections/scenario_engine.py`:

```python
"""
Scenario analysis engine.

Combines revenue and expenditure projections to identify fiscal outcomes.
"""
from typing import List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session

from src.database.models.core import City, FiscalYear
from src.database.models.financial import FundBalance
from src.database.models.projections import (
    FinancialProjection,
    ProjectionScenario,
    FiscalCliffAnalysis
)
from src.analytics.projections.revenue_model import RevenueProjector
from src.analytics.projections.expenditure_model import ExpenditureProjector
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ScenarioEngine:
    """Run scenario analysis."""

    def __init__(self, db: Session):
        self.db = db

    def run_scenario_analysis(
        self,
        city_id: int,
        base_year: int,
        years_ahead: int = 10,
        scenarios: List[str] = None
    ) -> List[FinancialProjection]:
        """
        Run complete scenario analysis.

        Args:
            city_id: City to analyze
            base_year: Base fiscal year
            years_ahead: How many years to project
            scenarios: List of scenarios (default: ["base", "optimistic", "pessimistic"])

        Returns: List of FinancialProjection objects
        """
        if scenarios is None:
            scenarios = ["base", "optimistic", "pessimistic"]

        logger.info(f"Running scenario analysis for city {city_id}, base year {base_year}")

        # Get or create projection scenarios
        scenario_objs = self._get_or_create_scenarios()

        # Get base year data
        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id,
            FiscalYear.year == base_year
        ).first()

        if not base_fy:
            raise ValueError(f"Base year {base_year} not found")

        # Get starting fund balance
        fund_balance = self.db.query(FundBalance).filter(
            FundBalance.fiscal_year_id == base_fy.id,
            FundBalance.fund_type == "General"
        ).first()

        starting_balance = float(fund_balance.total_fund_balance) if fund_balance else 0.0

        all_projections = []

        for scenario_name in scenarios:
            scenario_obj = scenario_objs[scenario_name]

            # Project revenues
            revenue_projector = RevenueProjector(self.db, city_id)
            revenue_projections = revenue_projector.project_revenues(
                base_year, years_ahead, scenario_name
            )

            # Project expenditures
            expenditure_projector = ExpenditureProjector(self.db, city_id)
            expenditure_projections = expenditure_projector.project_expenditures(
                base_year, years_ahead, scenario_name
            )

            # Combine into financial projections
            current_balance = starting_balance

            for year_idx in range(years_ahead):
                rev_proj = revenue_projections[year_idx]
                exp_proj = expenditure_projections[year_idx]

                projected_year = base_year + year_idx + 1

                revenues = rev_proj["projected_revenue"]
                expenditures = exp_proj["projected_expenditures"]
                operating_balance = revenues - expenditures

                # Update fund balance
                beginning_balance = current_balance
                ending_balance = beginning_balance + operating_balance
                current_balance = ending_balance

                # Calculate ratios
                fund_balance_ratio = ending_balance / expenditures if expenditures > 0 else 0
                operating_margin = (operating_balance / revenues * 100) if revenues > 0 else 0

                # Flags
                is_deficit = operating_balance < 0
                is_depleting_reserves = ending_balance < beginning_balance
                reserves_below_minimum = fund_balance_ratio < 0.10

                # Is this the fiscal cliff year?
                is_fiscal_cliff = reserves_below_minimum and is_deficit

                # Create projection
                projection = FinancialProjection(
                    city_id=city_id,
                    base_fiscal_year_id=base_fy.id,
                    scenario_id=scenario_obj.id,
                    projection_year=projected_year,
                    years_ahead=year_idx + 1,
                    projection_model_version="1.0",

                    # Revenues
                    total_revenues_projected=Decimal(str(revenues)),
                    revenue_growth_rate=Decimal(str(rev_proj["growth_rate_used"])),

                    # Expenditures
                    total_expenditures_projected=Decimal(str(expenditures)),
                    pension_costs_projected=Decimal(str(exp_proj["pension_costs"])),
                    base_expenditure_growth_rate=Decimal(str(exp_proj["base_growth_rate"])),
                    pension_growth_rate=Decimal(str(exp_proj.get("pension_growth_rate", 0))),

                    # Balance
                    operating_surplus_deficit=Decimal(str(operating_balance)),
                    operating_margin_percent=Decimal(str(operating_margin)),

                    # Fund balance
                    beginning_fund_balance=Decimal(str(beginning_balance)),
                    ending_fund_balance=Decimal(str(ending_balance)),
                    fund_balance_ratio=Decimal(str(fund_balance_ratio)),

                    # Flags
                    is_deficit=is_deficit,
                    is_depleting_reserves=is_depleting_reserves,
                    reserves_below_minimum=reserves_below_minimum,
                    is_fiscal_cliff=is_fiscal_cliff,

                    confidence_level="medium",
                )

                all_projections.append(projection)

        logger.info(f"Generated {len(all_projections)} projections across {len(scenarios)} scenarios")

        return all_projections

    def analyze_fiscal_cliff(
        self,
        city_id: int,
        base_year: int,
        scenario_name: str = "base"
    ) -> FiscalCliffAnalysis:
        """
        Identify when/if city hits fiscal cliff.

        Fiscal cliff = year when deficits exhaust reserves.
        """
        # Run projections for this scenario
        projections = self.run_scenario_analysis(
            city_id, base_year, years_ahead=10, scenarios=[scenario_name]
        )

        # Find fiscal cliff year
        fiscal_cliff_year = None
        for proj in projections:
            if proj.is_fiscal_cliff:
                fiscal_cliff_year = proj.projection_year
                break

        # Get scenario
        scenario = self.db.query(ProjectionScenario).filter(
            ProjectionScenario.scenario_code == scenario_name
        ).first()

        base_fy = self.db.query(FiscalYear).filter(
            FiscalYear.city_id == city_id,
            FiscalYear.year == base_year
        ).first()

        # Create analysis
        analysis = FiscalCliffAnalysis(
            city_id=city_id,
            base_fiscal_year_id=base_fy.id,
            scenario_id=scenario.id,
            has_fiscal_cliff=(fiscal_cliff_year is not None),
            fiscal_cliff_year=fiscal_cliff_year,
            years_until_cliff=(fiscal_cliff_year - base_year) if fiscal_cliff_year else None,
            reserves_exhausted_year=fiscal_cliff_year,
            severity=self._determine_severity(fiscal_cliff_year, base_year) if fiscal_cliff_year else "none",
            summary=self._generate_cliff_summary(fiscal_cliff_year, base_year),
        )

        return analysis

    def _get_or_create_scenarios(self) -> Dict[str, ProjectionScenario]:
        """Get or create standard scenarios."""
        scenarios = {
            "base": ("Base Case", "Baseline projection using median historical growth rates"),
            "optimistic": ("Optimistic", "Assumes favorable economic conditions and revenue growth"),
            "pessimistic": ("Pessimistic", "Assumes economic downturn and constrained revenues"),
        }

        result = {}

        for code, (name, description) in scenarios.items():
            scenario = self.db.query(ProjectionScenario).filter(
                ProjectionScenario.scenario_code == code
            ).first()

            if not scenario:
                scenario = ProjectionScenario(
                    scenario_name=name,
                    scenario_code=code,
                    description=description,
                    is_baseline=(code == "base"),
                    display_order={"base": 1, "optimistic": 2, "pessimistic": 3}[code],
                )
                self.db.add(scenario)
                self.db.flush()

            result[code] = scenario

        return result

    def _determine_severity(self, cliff_year: int, base_year: int) -> str:
        """Determine severity of fiscal cliff."""
        years_away = cliff_year - base_year

        if years_away <= 2:
            return "immediate"
        elif years_away <= 5:
            return "near_term"
        else:
            return "long_term"

    def _generate_cliff_summary(self, cliff_year: int, base_year: int) -> str:
        """Generate human-readable summary."""
        if not cliff_year:
            return "No fiscal cliff identified within 10-year projection period."

        years_away = cliff_year - base_year
        return (
            f"Without corrective action, the city is projected to exhaust reserves "
            f"by fiscal year {cliff_year} ({years_away} years from {base_year}). "
            f"This assumes current spending patterns and revenue trends continue."
        )
```

Execute this prompt to create the projection engine.
```

---

### Prompt 4.3: Create API Endpoints for Risk & Projections

```
Create API endpoints to expose risk scores and projections.

Create `src/api/v1/routes/risk.py`:

```python
"""
Risk score endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.dependencies import get_db
from src.api.v1.schemas.risk import RiskScoreResponse, RiskIndicatorDetailResponse
from src.database.models.core import City, FiscalYear
from src.database.models.risk import RiskScore, RiskIndicatorScore
from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine

router = APIRouter(prefix="/risk")


@router.get("/cities/{city_id}/current", response_model=RiskScoreResponse)
async def get_current_risk_score(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the most recent risk score for a city.
    """
    # Get latest fiscal year with risk score
    risk_score = db.query(RiskScore).join(RiskScore.fiscal_year).filter(
        FiscalYear.city_id == city_id
    ).order_by(desc(FiscalYear.year)).first()

    if not risk_score:
        raise HTTPException(
            status_code=404,
            detail="No risk score found for this city"
        )

    return risk_score


@router.get("/cities/{city_id}/history", response_model=List[RiskScoreResponse])
async def get_risk_score_history(
    city_id: int,
    db: Session = Depends(get_db)
):
    """
    Get risk score history for a city.

    Returns all available risk scores in chronological order.
    """
    risk_scores = db.query(RiskScore).join(RiskScore.fiscal_year).filter(
        FiscalYear.city_id == city_id
    ).order_by(FiscalYear.year).all()

    if not risk_scores:
        raise HTTPException(
            status_code=404,
            detail="No risk scores found for this city"
        )

    return risk_scores


@router.get("/cities/{city_id}/year/{year}", response_model=RiskScoreResponse)
async def get_risk_score_for_year(
    city_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Get risk score for a specific year.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    risk_score = db.query(RiskScore).filter(
        RiskScore.fiscal_year_id == fiscal_year.id
    ).first()

    if not risk_score:
        raise HTTPException(
            status_code=404,
            detail=f"No risk score found for {year}"
        )

    return risk_score


@router.post("/cities/{city_id}/calculate")
async def calculate_risk_score(
    city_id: int,
    year: int = Query(..., description="Fiscal year to calculate"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Calculate (or recalculate) risk score for a fiscal year.

    This endpoint triggers risk score calculation.
    Calculation happens in background if background_tasks provided.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    # Check if data is complete enough
    if not (fiscal_year.revenues_complete and fiscal_year.expenditures_complete):
        raise HTTPException(
            status_code=400,
            detail="Cannot calculate risk score: financial data incomplete"
        )

    def calculate():
        engine = RiskScoringEngine(db)
        risk_score = engine.calculate_risk_score(fiscal_year.id)
        db.add(risk_score)
        db.commit()

    if background_tasks:
        background_tasks.add_task(calculate)
        return {
            "status": "calculating",
            "message": "Risk score calculation started"
        }
    else:
        calculate()
        return {
            "status": "completed",
            "message": "Risk score calculated successfully"
        }


@router.get("/cities/{city_id}/indicators", response_model=List[RiskIndicatorDetailResponse])
async def get_risk_indicators(
    city_id: int,
    year: int = Query(..., description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """
    Get detailed breakdown of risk indicators for a year.

    Shows individual indicator values, scores, and thresholds.
    """
    fiscal_year = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == year
    ).first()

    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    risk_score = db.query(RiskScore).filter(
        RiskScore.fiscal_year_id == fiscal_year.id
    ).first()

    if not risk_score:
        raise HTTPException(status_code=404, detail="Risk score not found")

    return risk_score.indicator_scores
```

Create `src/api/v1/routes/projections.py`:

```python
"""
Financial projection endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.v1.schemas.projections import (
    FinancialProjectionResponse,
    FiscalCliffAnalysisResponse,
    ProjectionScenarioResponse
)
from src.database.models.core import City, FiscalYear
from src.database.models.projections import (
    FinancialProjection,
    ProjectionScenario,
    FiscalCliffAnalysis
)
from src.analytics.projections.scenario_engine import ScenarioEngine

router = APIRouter(prefix="/projections")


@router.get("/scenarios", response_model=List[ProjectionScenarioResponse])
async def list_scenarios(db: Session = Depends(get_db)):
    """
    List available projection scenarios.
    """
    scenarios = db.query(ProjectionScenario).filter(
        ProjectionScenario.is_active == True
    ).order_by(ProjectionScenario.display_order).all()

    return scenarios


@router.get("/cities/{city_id}/projections", response_model=List[FinancialProjectionResponse])
async def get_city_projections(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    scenario: Optional[str] = Query("base", description="Scenario code"),
    db: Session = Depends(get_db)
):
    """
    Get financial projections for a city.

    Query Parameters:
    - base_year: The fiscal year to project from (required)
    - scenario: Scenario to use (base, optimistic, pessimistic)
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    scenario_obj = db.query(ProjectionScenario).filter(
        ProjectionScenario.scenario_code == scenario
    ).first()

    if not scenario_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")

    projections = db.query(FinancialProjection).filter(
        FinancialProjection.city_id == city_id,
        FinancialProjection.base_fiscal_year_id == base_fy.id,
        FinancialProjection.scenario_id == scenario_obj.id
    ).order_by(FinancialProjection.projection_year).all()

    if not projections:
        raise HTTPException(
            status_code=404,
            detail="No projections found. Run /calculate first."
        )

    return projections


@router.post("/cities/{city_id}/calculate")
async def calculate_projections(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    years_ahead: int = Query(10, ge=1, le=20, description="Years to project"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Calculate financial projections for a city.

    Generates projections for all scenarios (base, optimistic, pessimistic).
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    def calculate():
        engine = ScenarioEngine(db)
        projections = engine.run_scenario_analysis(
            city_id, base_year, years_ahead
        )
        for proj in projections:
            db.add(proj)
        db.commit()

    if background_tasks:
        background_tasks.add_task(calculate)
        return {
            "status": "calculating",
            "message": f"Generating projections for {years_ahead} years"
        }
    else:
        calculate()
        return {
            "status": "completed",
            "message": "Projections calculated successfully"
        }


@router.get("/cities/{city_id}/fiscal-cliff", response_model=FiscalCliffAnalysisResponse)
async def get_fiscal_cliff_analysis(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    scenario: str = Query("base", description="Scenario code"),
    db: Session = Depends(get_db)
):
    """
    Get fiscal cliff analysis for a city.

    Shows when/if the city will exhaust reserves.
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    scenario_obj = db.query(ProjectionScenario).filter(
        ProjectionScenario.scenario_code == scenario
    ).first()

    if not scenario_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")

    analysis = db.query(FiscalCliffAnalysis).filter(
        FiscalCliffAnalysis.city_id == city_id,
        FiscalCliffAnalysis.base_fiscal_year_id == base_fy.id,
        FiscalCliffAnalysis.scenario_id == scenario_obj.id
    ).first()

    if not analysis:
        # Calculate it
        engine = ScenarioEngine(db)
        analysis = engine.analyze_fiscal_cliff(city_id, base_year, scenario)
        db.add(analysis)
        db.commit()

    return analysis
```

Create schemas in `src/api/v1/schemas/risk.py` and `src/api/v1/schemas/projections.py`.

Execute this prompt to create risk and projection API endpoints.
```

---

## PHASE 5: TESTING FRAMEWORK

### Prompt 5.1: Create Comprehensive Test Suite

```
Build a complete test suite covering all components.

**Context:** Testing is critical for data accuracy and system reliability.

Create `tests/conftest.py`:

```python
"""
Pytest fixtures for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from decimal import Decimal

from src.database.base import Base
from src.database.models.core import City, FiscalYear
from src.database.models.financial import (
    Revenue, Expenditure, FundBalance,
    RevenueCategory, ExpenditureCategory
)
from src.database.models.pensions import PensionPlan


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_city(test_db):
    """Create a sample city for testing."""
    city = City(
        name="TestCity",
        state="CA",
        county="Test County",
        population=100000,
        fiscal_year_end_month=6,
        fiscal_year_end_day=30,
    )
    test_db.add(city)
    test_db.commit()
    test_db.refresh(city)
    return city


@pytest.fixture
def sample_fiscal_year(test_db, sample_city):
    """Create a sample fiscal year."""
    fy = FiscalYear(
        city_id=sample_city.id,
        year=2024,
        start_date=date(2023, 7, 1),
        end_date=date(2024, 6, 30),
        cafr_available=True,
        revenues_complete=True,
        expenditures_complete=True,
        pension_data_complete=True,
    )
    test_db.add(fy)
    test_db.commit()
    test_db.refresh(fy)
    return fy


@pytest.fixture
def sample_financial_data(test_db, sample_fiscal_year):
    """Create sample financial data."""
    # Create categories
    rev_category = RevenueCategory(
        category_level1="Taxes",
        standard_name="Property Taxes",
        is_recurring=True,
    )
    exp_category = ExpenditureCategory(
        category_level1="Public Safety",
        standard_name="Police",
    )
    test_db.add(rev_category)
    test_db.add(exp_category)
    test_db.commit()

    # Create revenues
    revenue = Revenue(
        fiscal_year_id=sample_fiscal_year.id,
        category_id=rev_category.id,
        fund_type="General",
        actual_amount=Decimal("50000000"),
        source_document_type="CAFR",
    )
    test_db.add(revenue)

    # Create expenditures
    expenditure = Expenditure(
        fiscal_year_id=sample_fiscal_year.id,
        category_id=exp_category.id,
        fund_type="General",
        actual_amount=Decimal("48000000"),
        source_document_type="CAFR",
    )
    test_db.add(expenditure)

    # Create fund balance
    fund_balance = FundBalance(
        fiscal_year_id=sample_fiscal_year.id,
        fund_type="General",
        total_fund_balance=Decimal("10000000"),
        source_document_type="CAFR",
    )
    test_db.add(fund_balance)

    # Create pension plan
    pension = PensionPlan(
        fiscal_year_id=sample_fiscal_year.id,
        plan_name="Miscellaneous",
        valuation_date=date(2024, 6, 30),
        total_pension_liability=Decimal("200000000"),
        fiduciary_net_position=Decimal("130000000"),
        net_pension_liability=Decimal("70000000"),
        unfunded_actuarial_liability=Decimal("70000000"),
        funded_ratio=Decimal("0.65"),
        total_employer_contribution=Decimal("10000000"),
        discount_rate=Decimal("0.068"),
        source_document="CalPERS Valuation",
    )
    test_db.add(pension)

    test_db.commit()

    return {
        "revenue": revenue,
        "expenditure": expenditure,
        "fund_balance": fund_balance,
        "pension": pension,
    }
```

Create `tests/unit/test_risk_indicators.py`:

```python
"""
Test risk indicator calculations.
"""
import pytest
from decimal import Decimal

from src.analytics.risk_scoring.indicators import RiskIndicatorCalculator


def test_fund_balance_ratio_healthy(test_db, sample_fiscal_year, sample_financial_data):
    """Test fund balance ratio calculation - healthy scenario."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_fund_balance_ratio()

    assert result["available"] is True
    assert result["threshold"] == "adequate"  # 10M / 48M = 20.8%
    assert result["score"] == 0  # Healthy


def test_pension_funded_ratio_warning(test_db, sample_fiscal_year, sample_financial_data):
    """Test pension funded ratio - warning scenario."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_pension_funded_ratio()

    assert result["available"] is True
    assert result["value"] == pytest.approx(0.65, 0.01)
    assert result["threshold"] == "warning"  # 65% funded
    assert result["score"] == 50


def test_operating_balance_surplus(test_db, sample_fiscal_year, sample_financial_data):
    """Test operating balance with surplus."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_operating_balance()

    assert result["available"] is True
    assert result["value"] > 0  # Surplus
    assert result["threshold"] == "adequate"


def test_indicator_unavailable_when_no_data(test_db, sample_fiscal_year):
    """Test that indicators return unavailable when data missing."""
    calculator = RiskIndicatorCalculator(test_db, sample_fiscal_year.id)
    result = calculator.calculate_fund_balance_ratio()

    assert result["available"] is False
    assert result["value"] is None
```

Create `tests/unit/test_risk_scoring_engine.py`:

```python
"""
Test risk scoring engine."""
import pytest

from src.analytics.risk_scoring.scoring_engine import RiskScoringEngine


def test_calculate_risk_score(test_db, sample_fiscal_year, sample_financial_data):
    """Test complete risk score calculation."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score is not None
    assert risk_score.overall_score >= 0
    assert risk_score.overall_score <= 100
    assert risk_score.risk_level in ["low", "moderate", "high", "severe"]
    assert risk_score.data_completeness_percent > 0


def test_risk_level_classification(test_db):
    """Test risk level classification."""
    engine = RiskScoringEngine(test_db)

    assert engine._determine_risk_level(10) == "low"
    assert engine._determine_risk_level(35) == "moderate"
    assert engine._determine_risk_level(60) == "high"
    assert engine._determine_risk_level(85) == "severe"


def test_top_risk_factors_identified(test_db, sample_fiscal_year, sample_financial_data):
    """Test that top risk factors are identified."""
    engine = RiskScoringEngine(test_db)
    risk_score = engine.calculate_risk_score(sample_fiscal_year.id)

    assert risk_score.top_risk_factors is not None
    assert len(risk_score.top_risk_factors) <= 5

    # Should be sorted by score (highest first)
    if len(risk_score.top_risk_factors) > 1:
        assert risk_score.top_risk_factors[0]["score"] >= risk_score.top_risk_factors[1]["score"]
```

Create `tests/integration/test_data_import.py`:

```python
"""
Test data import scripts.
"""
import pytest
from pathlib import Path
import tempfile
import csv

from scripts.data_entry.import_cafr_manual import CAFRImporter


def test_cafr_import_from_csv(test_db):
    """Test importing CAFR data from CSV files."""
    # Create temporary CSV files
    with tempfile.TemporaryDirectory() as tmpdir:
        revenues_csv = Path(tmpdir) / "revenues.csv"
        expenditures_csv = Path(tmpdir) / "expenditures.csv"
        fund_balance_csv = Path(tmpdir) / "fund_balance.csv"

        # Write test data
        with open(revenues_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Property Taxes',
                'fund_type': 'General',
                'budget_amount': '25000000',
                'actual_amount': '26000000',
                'notes': 'Test data'
            })

        with open(expenditures_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'department', 'fund_type', 'budget_amount', 'actual_amount', 'notes'])
            writer.writeheader()
            writer.writerow({
                'category': 'Police',
                'department': 'Police',
                'fund_type': 'General',
                'budget_amount': '15000000',
                'actual_amount': '14800000',
                'notes': 'Test data'
            })

        with open(fund_balance_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['fund_type', 'nonspendable', 'restricted', 'committed', 'assigned', 'unassigned', 'total'])
            writer.writeheader()
            writer.writerow({
                'fund_type': 'General',
                'nonspendable': '500000',
                'restricted': '2000000',
                'committed': '1000000',
                'assigned': '3000000',
                'unassigned': '8500000',
                'total': '15000000'
            })

        # Import
        importer = CAFRImporter(test_db)
        success = importer.import_from_csv(
            city_name="TestCity",
            fiscal_year=2024,
            revenues_csv=revenues_csv,
            expenditures_csv=expenditures_csv,
            fund_balance_csv=fund_balance_csv,
            cafr_url="https://example.com/cafr.pdf",
            transcribed_by="Test User"
        )

        assert success is True

        # Verify data was imported
        from src.database.models.core import City
        city = test_db.query(City).filter(City.name == "TestCity").first()
        assert city is not None
```

Create `tests/integration/test_api_endpoints.py`:

```python
"""
Test API endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_disclaimer_endpoint():
    """Test disclaimer endpoint."""
    response = client.get("/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert "independent_analysis" in data
    assert "not_predictions" in data


def test_list_cities():
    """Test listing cities."""
    response = client.get("/api/v1/cities")
    assert response.status_code == 200
    # May be empty if no test data


def test_get_nonexistent_city():
    """Test getting nonexistent city returns 404."""
    response = client.get("/api/v1/cities/999999")
    assert response.status_code == 404
```

Create test runner script `scripts/run_tests.sh`:

```bash
#!/bin/bash
set -e

echo "Running IBCo test suite..."
echo ""

# Run linting
echo "=== Linting ==="
poetry run black --check src/ tests/
poetry run isort --check-only src/ tests/
poetry run flake8 src/ tests/
poetry run mypy src/

echo ""
echo "=== Unit Tests ==="
poetry run pytest tests/unit -v --cov=src --cov-report=term-missing

echo ""
echo "=== Integration Tests ==="
poetry run pytest tests/integration -v

echo ""
echo "✅ All tests passed!"
```

Execute this prompt to create the testing framework.
```

---

## PHASE 6: DEPLOYMENT & OPERATIONS

### Prompt 6.1: Create Deployment Configuration

```
Create production deployment configuration using Docker and infrastructure as code.

**Context:** Production deployment must be:
- Reproducible (infrastructure as code)
- Monitored (health checks, logging)
- Backed up (automated backups)
- Secure (secrets management, SSL)

Create `infrastructure/docker/Dockerfile.api`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data/raw /app/data/processed /app/data/archive

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `infrastructure/docker/Dockerfile.worker`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root

# Copy code
COPY src/ ./src/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Run Celery worker
CMD ["celery", "-A", "src.data_pipeline.orchestration.tasks", "worker", "--loglevel=info"]
```

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.api
    environment:
      DATABASE_URL: postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: infrastructure/docker/Dockerfile.worker
    environment:
      DATABASE_URL: postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      CELERY_RESULT_BACKEND: redis://:${REDIS_PASSWORD}@redis:6379/2
      ENVIRONMENT: production
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  metabase:
    image: metabase/metabase:latest
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase
      MB_DB_PORT: 5432
      MB_DB_USER: ${DATABASE_USER}
      MB_DB_PASS: ${DATABASE_PASSWORD}
      MB_DB_HOST: postgres
    depends_on:
      - postgres
    ports:
      - "3000:3000"
    volumes:
      - metabase_data:/metabase-data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  metabase_data:
```

Create `infrastructure/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    upstream metabase {
        server metabase:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name ibco-ca.us www.ibco-ca.us;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name ibco-ca.us www.ibco-ca.us;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (no rate limit)
        location /health {
            proxy_pass http://api;
            access_log off;
        }

        # Metabase dashboard
        location /dashboard/ {
            proxy_pass http://metabase/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Static files
        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

Create deployment script `scripts/deploy/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== IBCo Production Deployment ==="
echo ""

# Check environment
if [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ ENVIRONMENT must be set to 'production'"
    exit 1
fi

# Check required environment variables
required_vars=("DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable not set: $var"
        exit 1
    fi
done

echo "✅ Environment variables validated"
echo ""

# Backup database before deployment
echo "📦 Creating database backup..."
./scripts/maintenance/backup_database.sh

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build Docker images
echo "🔨 Building Docker images..."
docker compose -f docker-compose.prod.yml build

# Stop old containers
echo "🛑 Stopping old containers..."
docker compose -f docker-compose.prod.yml down

# Run database migrations
echo "🔄 Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm api \
    poetry run alembic upgrade head

# Start new containers
echo "🚀 Starting new containers..."
docker compose -f docker-compose.prod.yml up -d

# Wait for health checks
echo "⏳ Waiting for health checks..."
sleep 10

# Smoke test
echo "🧪 Running smoke tests..."
./scripts/deploy/smoke-test.sh

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Services:"
echo "- API: https://ibco-ca.us/api"
echo "- Docs: https://ibco-ca.us/api/docs"
echo "- Dashboard: https://ibco-ca.us/dashboard"
```

Create `scripts/deploy/smoke-test.sh`:

```bash
#!/bin/bash
set -e

echo "Running smoke tests..."

# Test health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$response" != "200" ]; then
    echo "❌ Health check failed (HTTP $response)"
    exit 1
fi
echo "✅ Health check passed"

# Test API endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/cities)
if [ "$response" != "200" ]; then
    echo "❌ API test failed (HTTP $response)"
    exit 1
fi
echo "✅ API test passed"

# Test database connection
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/detailed)
if [ "$response" != "200" ]; then
    echo "❌ Database health check failed (HTTP $response)"
    exit 1
fi
echo "✅ Database connection OK"

echo ""
echo "✅ All smoke tests passed!"
```

Create `scripts/maintenance/backup_database.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ibco_backup_$TIMESTAMP.sql.gz"

echo "Creating database backup..."

mkdir -p $BACKUP_DIR

# Create backup
docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U $DATABASE_USER $DATABASE_NAME | gzip > $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "ibco_backup_*.sql.gz" -mtime +30 -delete

echo "✅ Old backups cleaned up"
```

Execute this prompt to create deployment configuration.
```

---

This completes the comprehensive implementation guide. The file now contains detailed prompts for:

1. ✅ Project foundation with legal framework
2. ✅ Complete database schema
3. ✅ Full API implementation
4. ✅ Manual data entry tools
5. ✅ Analytics engine (risk scoring & projections)
6. ✅ Testing framework
7. ✅ Deployment & operations

The guide fixes all the issues from your original plans and provides actionable, Claude-Code-optimized prompts for building a production-ready civic transparency platform.