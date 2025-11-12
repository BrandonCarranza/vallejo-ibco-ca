# IBCo Developer Guide

Guide for developers extending the IBCo Vallejo Console system.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Adding New Risk Indicators](#adding-new-risk-indicators)
- [Adding Projection Scenarios](#adding-projection-scenarios)
- [Contributing Data](#contributing-data)
- [Database Schema](#database-schema)
- [Code Contribution Guidelines](#code-contribution-guidelines)

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose
- Poetry (Python dependency management)

### Development Setup

```bash
# Clone repository
git clone https://github.com/ibco-ca/vallejo-ibco-ca.git
cd vallejo-ibco-ca

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d postgres redis

# Run database migrations
poetry run alembic upgrade head

# Start API server
poetry run uvicorn src.api.main:app --reload
```

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/test_risk_scoring.py

# With coverage
poetry run pytest --cov=src --cov-report=html
```

---

## Architecture Overview

```
src/
├── api/                    # FastAPI application
│   ├── v1/routes/         # API endpoints
│   └── middleware/        # Auth, rate limiting, etc.
├── database/              # SQLAlchemy models
│   └── models/
├── analytics/             # Risk scoring, projections
│   ├── risk_scoring.py
│   └── projections.py
├── data_pipeline/         # Data import/refresh
├── reports/              # Report generation
└── utils/                # Shared utilities

scripts/
├── data_entry/           # Manual data entry tools
├── reports/              # Report generation
└── maintenance/          # System maintenance

infrastructure/
├── docker/               # Docker configurations
├── nginx/                # Web server config
└── monitoring/           # Prometheus, Grafana

tests/
├── unit/                 # Unit tests
└── integration/          # Integration tests
```

### Key Technologies

- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL + SQLAlchemy + Alembic
- **Task Queue:** Celery + Redis + APScheduler
- **Data Processing:** Pandas + NumPy
- **Reports:** Jinja2 + WeasyPrint
- **Monitoring:** Prometheus + Grafana
- **Dashboards:** Metabase

---

## Adding New Risk Indicators

Risk indicators are the building blocks of the fiscal risk score.

### Step 1: Define Indicator

Add to `src/database/models/risk.py` or seed data:

```python
# In seed data or migration
indicator = RiskIndicator(
    indicator_code="NEW_INDICATOR",
    indicator_name="New Risk Indicator",
    category="Liquidity",  # or Structural, Pension, Revenue, Debt
    description="Description of what this measures",
    calculation_formula="Formula: metric / baseline",

    # Weight in composite score (should sum to 1.0 within category)
    weight=0.25,

    # Thresholds for scoring
    threshold_healthy=0.15,      # Score 0 (healthy)
    threshold_adequate=0.10,     # Score 25
    threshold_warning=0.05,      # Score 50
    threshold_critical=0.02,     # Score 100

    # Direction
    higher_is_better=True,       # False if lower values are better

    # Metadata
    data_source="Fund Balance / Expenditures",
    unit_of_measure="ratio",
    is_active=True,
)
```

### Step 2: Implement Calculation

Add calculation method in `src/analytics/risk_scoring.py`:

```python
class RiskScorer:
    def calculate_new_indicator(
        self,
        city_id: int,
        fiscal_year: int,
    ) -> Optional[float]:
        """
        Calculate new risk indicator.

        Returns:
            Indicator value (e.g., 0.15 for 15%)
        """
        # Fetch data
        fy = self._get_fiscal_year(city_id, fiscal_year)

        # Calculate metric
        metric = self._calculate_metric(fy)

        # Normalize if needed
        normalized = metric / baseline

        return normalized

    def _calculate_metric(self, fy: FiscalYear) -> float:
        """Calculate the underlying metric."""
        # Implementation here
        pass
```

### Step 3: Integrate into Risk Score

Update `src/analytics/risk_scoring.py` to include new indicator:

```python
def calculate_category_score(
    self,
    category: str,
    city_id: int,
    fiscal_year: int,
) -> Dict[str, Any]:
    """Calculate category score including all indicators."""
    indicators = self._get_category_indicators(category)
    indicator_scores = []

    for indicator in indicators:
        # Calculate indicator value
        if indicator.indicator_code == "NEW_INDICATOR":
            value = self.calculate_new_indicator(city_id, fiscal_year)
        else:
            value = self.calculate_indicator(indicator, city_id, fiscal_year)

        # Score the value
        score = self._score_indicator(value, indicator)
        indicator_scores.append(score)

    # Weight and aggregate
    category_score = self._aggregate_scores(indicator_scores)

    return category_score
```

### Step 4: Create Migration

```bash
# Generate migration
poetry run alembic revision -m "Add new risk indicator"
```

Edit migration file:

```python
def upgrade():
    # Insert new indicator
    op.execute("""
        INSERT INTO risk_indicators
        (indicator_code, indicator_name, category, ...)
        VALUES ('NEW_INDICATOR', 'New Risk Indicator', 'Liquidity', ...)
    """)

def downgrade():
    op.execute("DELETE FROM risk_indicators WHERE indicator_code = 'NEW_INDICATOR'")
```

### Step 5: Test

```python
# tests/test_risk_scoring.py
def test_new_indicator_calculation():
    scorer = RiskScorer(db)
    value = scorer.calculate_new_indicator(city_id=1, fiscal_year=2024)

    assert value is not None
    assert 0 <= value <= 1.0  # Or appropriate range
```

---

## Adding Projection Scenarios

Scenarios enable "what-if" analysis of different fiscal futures.

### Step 1: Define Scenario

```python
# In seed data or admin interface
scenario = ProjectionScenario(
    scenario_name="Pension Reform Package",
    scenario_code="pension_reform",
    description="Assumes PEPRA reforms + increased employee contributions",
    is_baseline=False,
    display_order=4,
    is_active=True,
)
```

### Step 2: Define Assumptions

```python
# Scenario assumptions
assumptions = [
    ScenarioAssumption(
        scenario_id=scenario.id,
        assumption_category="pension",
        assumption_name="employer_contribution_growth",
        assumption_value="2.0% annual",
        assumption_numeric_value=0.02,
        description="Employer contribution growth under reform",
        rationale="PEPRA caps + employee cost sharing",
        source="CalPERS projection model",
    ),
    ScenarioAssumption(
        scenario_id=scenario.id,
        assumption_category="revenue",
        assumption_name="tax_revenue_growth",
        assumption_value="3.5% annual",
        assumption_numeric_value=0.035,
        description="Assumed revenue growth",
        rationale="Historical average + economic recovery",
    ),
]
```

### Step 3: Implement Projection Logic

Update `src/analytics/projections.py`:

```python
class FiscalProjector:
    def project_scenario(
        self,
        city_id: int,
        base_fiscal_year: int,
        scenario_code: str,
        years_ahead: int = 10,
    ) -> List[FinancialProjection]:
        """Generate projections for a scenario."""
        scenario = self._get_scenario(scenario_code)
        assumptions = self._get_assumptions(scenario.id)

        projections = []

        for year_offset in range(1, years_ahead + 1):
            projection_year = base_fiscal_year + year_offset

            # Apply scenario-specific growth rates
            revenues = self._project_revenues(
                city_id,
                base_fiscal_year,
                year_offset,
                assumptions,
            )

            expenditures = self._project_expenditures(
                city_id,
                base_fiscal_year,
                year_offset,
                assumptions,
            )

            # Calculate balances
            projection = FinancialProjection(
                city_id=city_id,
                base_fiscal_year_id=base_fy.id,
                scenario_id=scenario.id,
                projection_year=projection_year,
                years_ahead=year_offset,
                total_revenues_projected=revenues,
                total_expenditures_projected=expenditures,
                # ... calculate other fields
            )

            projections.append(projection)

        return projections

    def _project_revenues(
        self,
        city_id: int,
        base_year: int,
        years_ahead: int,
        assumptions: List[ScenarioAssumption],
    ) -> float:
        """Project revenues under scenario assumptions."""
        # Get base revenue
        base_revenue = self._get_base_revenue(city_id, base_year)

        # Get growth assumption
        growth_rate = self._get_assumption_value(
            assumptions,
            "revenue",
            "tax_revenue_growth",
        )

        # Compound growth
        projected = base_revenue * ((1 + growth_rate) ** years_ahead)

        return projected
```

### Step 4: Run Fiscal Cliff Analysis

```python
# Automatically run for new scenario
cliff_analysis = FiscalCliffAnalysis(
    city_id=city_id,
    base_fiscal_year_id=base_fy.id,
    scenario_id=scenario.id,
    has_fiscal_cliff=True,  # Determined by projections
    fiscal_cliff_year=2031,
    years_until_cliff=7,
    severity="long_term",
    cumulative_deficit_at_cliff=-85000000.0,
    revenue_increase_needed_percent=8.5,
    expenditure_decrease_needed_percent=7.2,
)
```

---

## Contributing Data

IBCo uses **manual data entry** for accuracy and defensibility.

### Manual Entry Workflow

#### 1. Obtain Source Documents

- **CAFR:** City's Comprehensive Annual Financial Report
- **CalPERS:** Actuarial valuation reports
- **Budget:** Adopted budget documents

#### 2. Prepare CSV Template

```bash
# Generate CSV template
poetry run python scripts/data_entry/generate_template.py \\
    --city-id 1 \\
    --fiscal-year 2024 \\
    --output-dir data/entry/
```

This creates:
- `revenues_template_FY2024.csv`
- `expenditures_template_FY2024.csv`
- `pension_template_FY2024.csv`

#### 3. Enter Data

Fill in CSV templates:

**revenues_template_FY2024.csv:**
```csv
category_level1,category_level2,fund_type,actual_amount,source_page,source_line_item
Taxes,Property Taxes,General,98500000,34,Secured Property Taxes
Taxes,Sales Tax,General,42000000,34,Sales and Use Tax
...
```

**pension_template_FY2024.csv:**
```csv
plan_name,valuation_date,total_pension_liability,fiduciary_net_position,funded_ratio,source_page
Miscellaneous,2024-06-30,4200000000,2604000000,0.62,12
Safety,2024-06-30,2800000000,1624000000,0.58,15
```

#### 4. Import Data

```bash
# Import with validation
poetry run python scripts/data_entry/import_cafr_manual.py \\
    --city-id 1 \\
    --fiscal-year 2024 \\
    --revenues-file data/entry/revenues_template_FY2024.csv \\
    --expenditures-file data/entry/expenditures_template_FY2024.csv \\
    --validate

# Import CalPERS data
poetry run python scripts/data_entry/import_calpers_manual.py \\
    --city-id 1 \\
    --fiscal-year 2024 \\
    --pension-file data/entry/pension_template_FY2024.csv
```

#### 5. Validate & Review

```bash
# Run validation checks
poetry run python scripts/validation/validate_data_integrity.py \\
    --city-id 1 \\
    --fiscal-year 2024

# Generate validation report
poetry run python scripts/validation/generate_quality_report.py \\
    --city-id 1 \\
    --fiscal-year 2024 \\
    --output reports/validation/
```

#### 6. Record Lineage

Lineage is automatically recorded during import:

```python
# Example from import script
from src.utils.lineage_helpers import record_cafr_entry

record_cafr_entry(
    db=db,
    table_name="revenues",
    record_id=revenue.id,
    field_name="actual_amount",
    cafr_source_id=cafr_source.id,
    page_number=34,
    section_name="Statement of Activities",
    entered_by="Jane Doe",
)
```

---

## Database Schema

### Core Tables

```sql
-- Cities being tracked
cities (
    id, name, state, county, population,
    has_bankruptcy_history, bankruptcy_filing_date
)

-- Fiscal years
fiscal_years (
    id, city_id, year, start_date, end_date,
    cafr_available, calpers_valuation_available
)

-- Data lineage (complete provenance)
data_lineage (
    id, table_name, record_id, field_name,
    source_document_id, source_page,
    extracted_by, validated_by,
    confidence_score, validation_notes
)
```

### Financial Tables

```sql
-- Revenues
revenues (
    id, fiscal_year_id, category_id,
    fund_type, actual_amount, budget_amount,
    source_document_type, source_page
)

-- Expenditures
expenditures (
    id, fiscal_year_id, category_id,
    fund_type, actual_amount, budget_amount,
    department, source_page
)

-- Fund balances (reserves)
fund_balances (
    id, fiscal_year_id, fund_type,
    total_fund_balance, fund_balance_ratio,
    unassigned, days_of_cash
)
```

### Pension Tables

```sql
-- Pension plans
pension_plans (
    id, fiscal_year_id, plan_name,
    total_pension_liability, fiduciary_net_position,
    unfunded_actuarial_liability, funded_ratio,
    total_employer_contribution, discount_rate
)

-- Pension projections (from CalPERS)
pension_projections (
    id, base_fiscal_year_id, plan_name,
    projection_year, projected_contribution
)
```

### Risk Tables

```sql
-- Risk indicators (definitions)
risk_indicators (
    id, indicator_code, indicator_name,
    category, weight, thresholds, is_active
)

-- Risk scores (calculated)
risk_scores (
    id, fiscal_year_id, calculation_date,
    overall_score, risk_level,
    liquidity_score, pension_stress_score, ...
)

-- Individual indicator scores
risk_indicator_scores (
    id, risk_score_id, indicator_id,
    indicator_value, indicator_score,
    contribution_to_overall
)
```

### Projection Tables

```sql
-- Projection scenarios
projection_scenarios (
    id, scenario_name, scenario_code,
    description, is_baseline, display_order
)

-- Scenario assumptions
scenario_assumptions (
    id, scenario_id, assumption_category,
    assumption_name, assumption_numeric_value,
    description, rationale
)

-- Financial projections
financial_projections (
    id, city_id, base_fiscal_year_id, scenario_id,
    projection_year, years_ahead,
    total_revenues_projected,
    total_expenditures_projected,
    ending_fund_balance, is_fiscal_cliff
)
```

### Schema Diagram

See `docs/schema_diagram.png` (generated via):

```bash
poetry run python scripts/docs/generate_schema_diagram.py
```

---

## Code Contribution Guidelines

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-new-indicator

# Make changes and commit
git add src/analytics/risk_scoring.py
git commit -m "feat: Add liquidity coverage ratio indicator"

# Push and create PR
git push origin feature/add-new-indicator
# Open pull request on GitHub
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(risk-scoring): Add liquidity coverage ratio indicator

Implements new indicator measuring liquid assets vs current liabilities.
Uses 30-day liquidity metric from GASB 54 classifications.

Closes #123
```

### Code Style

```bash
# Format code
poetry run black src/

# Sort imports
poetry run isort src/

# Lint
poetry run flake8 src/
poetry run mypy src/
```

### Testing Requirements

All new features must include tests:

```python
# tests/analytics/test_risk_scoring.py
def test_calculate_new_indicator():
    """Test new indicator calculation."""
    scorer = RiskScorer(db)

    # Setup test data
    city_id = create_test_city()
    fiscal_year = create_test_fiscal_year(city_id)

    # Calculate indicator
    value = scorer.calculate_new_indicator(city_id, fiscal_year.year)

    # Assertions
    assert value is not None
    assert 0 <= value <= 1.0
    assert isinstance(value, float)
```

### Documentation Requirements

- Docstrings for all public functions/classes
- Update relevant markdown docs
- Add examples to usage guide
- Update API documentation

### Pull Request Checklist

- [ ] Tests added/updated and passing
- [ ] Code formatted (black + isort)
- [ ] Linting passing (flake8 + mypy)
- [ ] Documentation updated
- [ ] Database migrations created (if schema changes)
- [ ] CHANGELOG.md updated
- [ ] PR description explains changes

### Review Process

1. Create pull request
2. Automated checks run (tests, linting, coverage)
3. Code review by maintainers
4. Address feedback
5. Approval + merge to main
6. Deployment to staging
7. Deployment to production (after testing)

---

## Additional Resources

- **API Documentation:** https://docs.ibco-ca.us/api-usage-guide
- **Architecture Docs:** https://docs.ibco-ca.us/architecture
- **Data Dictionary:** https://docs.ibco-ca.us/data-dictionary
- **Community Forum:** https://forum.ibco-ca.us

---

**Last Updated:** November 12, 2024
**Version:** 1.0
