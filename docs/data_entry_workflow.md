# Manual Data Entry Workflow

## Overview

This document describes the manual data entry workflow for loading historical fiscal data into the IBCo Vallejo Console. The manual approach provides:

- **SPEED**: 1-2 hours per fiscal year (faster than building extraction automation)
- **ACCURACY**: 100% human-verified at source
- **DEFENSIBILITY**: Complete data lineage to source document & transcriber
- **PROVEN WORKFLOW**: Scripts already built and tested

## Prerequisites

1. **Database Setup**
   ```bash
   # Verify database is running and migrations are applied
   poetry run alembic current

   # Should show: ea4a6621450b (head)
   ```

2. **Source Documents**
   - Vallejo CAFRs (Comprehensive Annual Financial Reports) for FY2020-2024
   - CalPERS Actuarial Valuations for Vallejo
   - Available at: `data/raw/vallejo/cafr/` and `data/raw/vallejo/calpers/`

3. **Tools**
   - Spreadsheet software (Excel, Google Sheets, or LibreOffice Calc)
   - PDF reader for source documents
   - Text editor for CSV files

## Workflow Steps

### Step 1: Prepare Source Documents

1. Obtain Vallejo CAFRs for target fiscal years
2. Obtain CalPERS Actuarial Valuations
3. Organize in `data/raw/vallejo/` directory:
   ```
   data/raw/vallejo/
   ├── cafr/
   │   ├── FY2020_CAFR.pdf
   │   ├── FY2021_CAFR.pdf
   │   ├── FY2022_CAFR.pdf
   │   ├── FY2023_CAFR.pdf
   │   └── FY2024_CAFR.pdf
   └── calpers/
       ├── FY2020_ValuationReport.pdf
       ├── FY2021_ValuationReport.pdf
       ├── FY2022_ValuationReport.pdf
       ├── FY2023_ValuationReport.pdf
       └── FY2024_ValuationReport.pdf
   ```

### Step 2: Extract CAFR Data

For each fiscal year, extract the following data from the CAFR:

#### A. General Fund Revenues

Create CSV file: `data/samples/vallejo/cafr/FY{YEAR}_revenues.csv`

**Required columns:**
- `fiscal_year` - Fiscal year (e.g., 2024)
- `category` - Revenue category (see categories below)
- `subcategory` - Subcategory name
- `amount` - Dollar amount
- `source_document` - Document name (e.g., "FY2024 CAFR")
- `source_page` - Page number in source document
- `notes` - Any relevant notes

**Revenue Categories:**
- Property Tax
- Sales Tax
- Other Taxes
- Licenses & Permits
- Intergovernmental
- Charges for Services
- Fines & Forfeitures
- Investment Income
- Other Revenue

**Example CSV:**
```csv
fiscal_year,category,subcategory,amount,source_document,source_page,notes
2024,Property Tax,Secured Property Tax,45678901.00,FY2024 CAFR,42,Table 3
2024,Property Tax,Unsecured Property Tax,2345678.00,FY2024 CAFR,42,Table 3
2024,Sales Tax,General Sales Tax,18900123.00,FY2024 CAFR,42,Table 3
```

**Where to find in CAFR:**
- Look for "Statement of Revenues, Expenditures, and Changes in Fund Balances - Governmental Funds"
- Usually in the "Basic Financial Statements" section
- Verify totals match the summary totals

#### B. General Fund Expenditures

Create CSV file: `data/samples/vallejo/cafr/FY{YEAR}_expenditures.csv`

**Required columns:**
- `fiscal_year`
- `category` - Expenditure category
- `subcategory` - Subcategory name
- `amount` - Dollar amount
- `source_document`
- `source_page`
- `notes`

**Expenditure Categories:**
- General Government
- Public Safety
- Public Works
- Community Development
- Parks & Recreation
- Debt Service
- Capital Outlay

**Example CSV:**
```csv
fiscal_year,category,subcategory,amount,source_document,source_page,notes
2024,Public Safety,Police - Salaries,35678901.00,FY2024 CAFR,45,Table 5
2024,Public Safety,Police - Benefits,18900123.00,FY2024 CAFR,45,Table 5
2024,Public Safety,Fire - Salaries,28456789.00,FY2024 CAFR,45,Table 5
```

**Where to find in CAFR:**
- Same location as revenues
- Look for expenditures by function/program
- Note: Exclude pension contributions from salaries (we'll track those separately)

#### C. Fund Balance

Create CSV file: `data/samples/vallejo/cafr/FY{YEAR}_fund_balance.csv`

**Required columns:**
- `fiscal_year`
- `fund_type` - Fund type (usually "General Fund")
- `beginning_balance` - Balance at start of year
- `ending_balance` - Balance at end of year
- `reserved_balance` - Reserved/Committed portion
- `unreserved_balance` - Unreserved/Unassigned portion
- `source_document`
- `source_page`
- `notes`

**Example CSV:**
```csv
fiscal_year,fund_type,beginning_balance,ending_balance,reserved_balance,unreserved_balance,source_document,source_page,notes
2024,General Fund,25678901.00,28456789.00,15000000.00,13456789.00,FY2024 CAFR,48,Fund Balance Statement
```

**Where to find in CAFR:**
- "Statement of Revenues, Expenditures, and Changes in Fund Balances"
- Look for beginning and ending fund balance
- Check "Fund Balance Classifications" note for reserved/unreserved breakdown

### Step 3: Extract CalPERS Data

For each fiscal year, extract pension data from CalPERS Actuarial Valuation:

Create CSV file: `data/samples/vallejo/calpers/FY{YEAR}_pension.csv`

**Required columns:**
- `fiscal_year`
- `plan_name` - Plan name (e.g., "Miscellaneous", "Safety")
- `actuarial_value_assets` - Actuarial value of assets
- `actuarial_liability` - Total actuarial liability (AAL)
- `unfunded_liability` - Unfunded Actuarial Liability (UAL)
- `funded_ratio` - Funded ratio (percentage)
- `annual_contribution` - Required employer contribution
- `payroll` - Covered payroll
- `discount_rate` - Discount rate assumption
- `source_document`
- `source_page`
- `notes`

**Example CSV:**
```csv
fiscal_year,plan_name,actuarial_value_assets,actuarial_liability,unfunded_liability,funded_ratio,annual_contribution,payroll,discount_rate,source_document,source_page,notes
2024,Miscellaneous,245678901.00,456789012.00,211110111.00,53.8,18900123.00,45678901.00,6.8,FY2024 Valuation,12,Summary Table
2024,Safety,189001234.00,398765432.00,209764198.00,47.4,25678901.00,38900123.00,6.8,FY2024 Valuation,12,Summary Table
```

**Where to find in Valuation Report:**
- "Actuarial Valuation Summary" or first few pages
- Look for "Funded Status" table
- "Contribution Rates" section for required contributions

### Step 4: Import Data Using Scripts

Once CSV files are prepared, use the import scripts to load data into the database.

#### A. Import CAFR Data

```bash
# Import revenues for FY2024
poetry run python scripts/data_entry/import_cafr_manual.py \
    --fiscal-year 2024 \
    --city Vallejo \
    --revenues data/samples/vallejo/cafr/FY2024_revenues.csv \
    --expenditures data/samples/vallejo/cafr/FY2024_expenditures.csv \
    --fund-balance data/samples/vallejo/cafr/FY2024_fund_balance.csv

# Import for all years
for year in 2020 2021 2022 2023 2024; do
    poetry run python scripts/data_entry/import_cafr_manual.py \
        --fiscal-year $year \
        --city Vallejo \
        --revenues data/samples/vallejo/cafr/FY${year}_revenues.csv \
        --expenditures data/samples/vallejo/cafr/FY${year}_expenditures.csv \
        --fund-balance data/samples/vallejo/cafr/FY${year}_fund_balance.csv
done
```

#### B. Import CalPERS Data

```bash
# Import pension data for FY2024
poetry run python scripts/data_entry/import_calpers_manual.py \
    --fiscal-year 2024 \
    --city Vallejo \
    --pension-data data/samples/vallejo/calpers/FY2024_pension.csv

# Import for all years
for year in 2020 2021 2022 2023 2024; do
    poetry run python scripts/data_entry/import_calpers_manual.py \
        --fiscal-year $year \
        --city Vallejo \
        --pension-data data/samples/vallejo/calpers/FY${year}_pension.csv
done
```

### Step 5: Validate Data Integrity

After importing, run validation checks:

```bash
# Validate all years
poetry run python scripts/validation/validate_data_integrity.py

# Validate specific year
poetry run python scripts/validation/validate_data_integrity.py --fiscal-year 2024

# With custom tolerance
poetry run python scripts/validation/validate_data_integrity.py --tolerance 0.001
```

**Expected validation checks:**
- ✓ Fund balance formula: ending = beginning + revenues - expenditures
- ✓ Revenue totals match CAFR summary
- ✓ Expenditure totals match CAFR summary
- ✓ All required data present
- ✓ No missing fiscal years

**If errors found:**
1. Review CSV files for transcription errors
2. Check source documents for correct values
3. Re-import corrected data
4. Re-run validation

### Step 6: Calculate Risk Scores

Once data is validated, calculate historical risk scores:

```bash
# Calculate risk scores for all fiscal years
poetry run python scripts/analysis/calculate_historical_risk_scores.py

# Calculate for specific year
poetry run python scripts/analysis/calculate_historical_risk_scores.py --fiscal-year 2024

# Recalculate existing scores
poetry run python scripts/analysis/calculate_historical_risk_scores.py --recalculate
```

**Output:**
- Risk score progression report
- Category scores (Liquidity, Structural, Pension, Revenue, Debt)
- Top risk factors identified
- Data completeness metrics

### Step 7: Generate Projections

Generate 10-year financial projections:

```bash
# Generate all scenarios (base, optimistic, pessimistic)
poetry run python scripts/analysis/generate_projections.py

# Generate from specific base year
poetry run python scripts/analysis/generate_projections.py --base-year 2024

# Generate specific scenario
poetry run python scripts/analysis/generate_projections.py --scenario base

# Custom horizon
poetry run python scripts/analysis/generate_projections.py --years 15

# With validation
poetry run python scripts/analysis/generate_projections.py --validate
```

**Output:**
- Financial projections for each scenario
- Fiscal cliff analysis
- Years to depletion estimate
- Severity ratings

## Data Quality Checklist

Before marking data entry as complete, verify:

- [ ] All 5 fiscal years have data (FY2020-2024)
- [ ] Revenue totals reconcile to CAFR
- [ ] Expenditure totals reconcile to CAFR
- [ ] Fund balance formula validates
- [ ] Pension data matches CalPERS valuations
- [ ] All CSV files have source_document and source_page filled
- [ ] Data validation script runs without errors
- [ ] Risk scores calculated successfully
- [ ] Projections generated for all scenarios
- [ ] No missing or null values in critical fields

## Troubleshooting

### Common Issues

**Issue: Import script fails with "City not found"**
```bash
# Solution: Create city record first
poetry run python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.config.settings import settings
from src.database.models import City

engine = create_engine(settings.database_url)
with Session(engine) as session:
    city = City(name='Vallejo', state='CA', county='Solano')
    session.add(city)
    session.commit()
    print(f'Created city: {city.name} (ID: {city.id})')
"
```

**Issue: Validation shows fund balance mismatch**
- Check that revenues and expenditures are complete
- Verify beginning and ending balances from CAFR
- Ensure no duplicate entries
- Check for missing categories

**Issue: Risk score calculation fails**
- Verify all required data is present
- Check for negative values where they shouldn't exist
- Ensure pension data is loaded
- Review data completeness metrics

## Time Estimates

Per fiscal year (approximate):

| Task | Time |
|------|------|
| Extract revenues from CAFR | 20-30 min |
| Extract expenditures from CAFR | 20-30 min |
| Extract fund balance from CAFR | 5-10 min |
| Extract pension data from CalPERS | 10-15 min |
| Create CSV files | 10-15 min |
| Import data | 5 min |
| Validate data | 5 min |
| Calculate risk scores | 2 min |
| Generate projections | 2 min |
| **Total per year** | **1-2 hours** |

For 5 years (FY2020-2024): **5-10 hours total**

## Best Practices

1. **Work in chronological order** - Start with oldest year, move to most recent
2. **Double-check totals** - Always verify totals match CAFR summaries
3. **Document sources** - Always record source_document and source_page
4. **Validate frequently** - Run validation after each year's import
5. **Keep originals** - Never modify original PDF source documents
6. **Version control** - Commit CSV files to git after validation passes
7. **Take notes** - Document any unusual items or questions in notes field

## Data Lineage

Every data point must have:
- **Source Document**: Name of CAFR or CalPERS report
- **Source Page**: Page number where data appears
- **Transcriber**: Who entered the data (tracked via git commits)
- **Entry Date**: When data was entered (tracked via git commits)

This provides complete auditability and defensibility of all data.

## Next Steps

After completing manual data entry for FY2020-2024:

1. **Verify API endpoints** - Test that data is accessible via API
2. **Review visualizations** - Check Metabase dashboards
3. **Document findings** - Create summary report of risk trends
4. **Expand history** (optional) - Add FY2015-2019 if needed
5. **Plan automation** (future) - Consider automated extraction for ongoing updates

## Support

For issues or questions:
- Check `scripts/data_entry/README.md` for script documentation
- Review model documentation in `src/database/models/`
- Consult CAFR User Guide in `docs/cafr_user_guide.md`
- Open issue at https://github.com/ibco-ca/vallejo-ibco-ca/issues
