# Three-Tier CAFR Data Structure & Stated vs Restated Tracking

## Overview

The IBCo system implements **critical data provenance tracking** to distinguish between:
1. **Stated data**: Original values reported when data was current (ground truth)
2. **Restated data**: Revised historical values published in later CAFRs (comparison only)

This distinction is **essential for data integrity** and enables detection of accounting restatements, GASB standard changes, and error corrections.

---

## CAFR Structure

Every Comprehensive Annual Financial Report (CAFR) contains three main sections:

```
Vallejo CAFR FY2024
│
├── Tier 1: Financial Section ✅ STATED DATA (PRIMARY FOR ANALYSIS)
│   ├── Government-wide Financial Statements
│   ├── Fund Financial Statements
│   ├── Statement of Revenues, Expenditures (FY2024 actuals)
│   └── Statement of Net Position (FY2024 balances)
│
├── Tier 2: Notes to Financial Statements 📝 CONTEXT & METHODOLOGY
│   ├── Accounting policies
│   ├── Pension assumptions & actuarial methods
│   ├── Debt service schedules
│   ├── Contingent liabilities
│   └── Subsequent events
│
└── Tier 3: Statistical Section 📊 RESTATED HISTORICAL DATA
    ├── Ten-Year Financial Trends (FY2015-2024 restated)
    ├── Revenue by Source (10 years restated)
    ├── Expenditures by Function (10 years restated)
    ├── Fund Balances (10 years restated)
    └── Demographic & Economic Statistics
```

---

## Why This Matters: Real-World Example

### Scenario: FY2020 Revenue Restatements

**FY2020 CAFR (published December 2020)**:
- **Stated** FY2020 General Fund Revenue: **$100,000,000**
- 10-year trend shows FY2011-2019 (all restated per FY2020 methodology)

**FY2021 CAFR (published December 2021)**:
- **Restated** FY2020 General Fund Revenue: **$98,500,000** ⚠️ **-1.5%**
- Reason: GASB 87 implementation (lease accounting change)
- 10-year trend now shows FY2012-2021

**FY2024 CAFR (published December 2024)**:
- **Restated** FY2020 General Fund Revenue: **$97,000,000** ⚠️ **-3.0% vs stated!**
- Reason: Additional pension liability reclassification (GASB 68 amendment)
- 10-year trend shows FY2015-2024

### Critical Questions

1. **Which value is "correct"?**
   - **Stated value ($100M) = ground truth** for FY2020 risk analysis
   - Restated values ($98.5M, $97M) = adjusted for comparability, but NOT used for FY2020 scoring

2. **Why do restatements happen?**
   - **GASB standards**: New accounting rules applied retroactively
   - **Reclassifications**: Revenue/expenditure categories reorganized
   - **Error corrections**: Fixing prior year mistakes
   - **Fund transfers**: Moving items between funds

3. **Which data do we analyze?**
   - **ALWAYS use stated data** (is_primary_version=True)
   - **NEVER use restated data** for risk scores or projections
   - Restated data is for **historical comparison only**

---

## Database Schema: Version Tracking Fields

All financial models (Revenue, Expenditure, FundBalance, PensionContribution) include:

```sql
-- Which CAFR section reported this?
cafr_tier VARCHAR(20) NOT NULL DEFAULT 'tier_1_financial'
  -- Values: 'tier_1_financial', 'tier_2_notes', 'tier_3_statistical'

-- Is this stated (original) or restated (revised)?
data_version_type VARCHAR(20) NOT NULL DEFAULT 'stated'
  -- Values: 'stated', 'restated'

-- Which CAFR year reported this value?
source_cafr_year INTEGER NOT NULL
  -- Example: 2024 (from FY2024 CAFR)

-- Should this be used for analysis?
is_primary_version BOOLEAN NOT NULL DEFAULT TRUE
  -- TRUE = stated data (use for risk scores, projections)
  -- FALSE = restated data (comparison only, DO NOT ANALYZE)

-- Why was this restated?
restatement_reason TEXT
  -- Example: "GASB 87 lease accounting reclassification"

-- Link to previous version
supersedes_version_id INTEGER REFERENCES revenues(id)
  -- Points to stated version if this is a restatement
```

---

## Data Entry Workflow

### Step 1: Import FY2024 CAFR - Tier 1 (Financial Section)

**Source**: FY2024 CAFR, pages 10-50 (financial statements)

**CSV Format**:
```csv
fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes
2024,Property Tax,55000000,tier_1_financial,stated,2024,General,
2024,Sales Tax,12000000,tier_1_financial,stated,2024,General,
2024,Licenses & Permits,3500000,tier_1_financial,stated,2024,General,
```

**Import Command**:
```bash
python scripts/data_entry/import_cafr_three_tier.py \
    --cafr-year 2024 \
    --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv
```

**Result**: FY2024 stated data loaded (is_primary_version=True)

---

### Step 2: Import FY2024 CAFR - Tier 3 (Statistical Section)

**Source**: FY2024 CAFR, pages 200-250 (10-year trend tables)

**CSV Format**:
```csv
fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes
2024,Property Tax,55000000,tier_3_statistical,stated,2024,General,Matches Tier 1
2023,Property Tax,53000000,tier_3_statistical,restated,2024,General,
2022,Property Tax,51000000,tier_3_statistical,restated,2024,General,
2021,Property Tax,49000000,tier_3_statistical,restated,2024,General,
2020,Property Tax,47500000,tier_3_statistical,restated,2024,General,GASB 87 reclass
2019,Property Tax,46000000,tier_3_statistical,restated,2024,General,
```

**Import Command**:
```bash
python scripts/data_entry/import_cafr_three_tier.py \
    --cafr-year 2024 \
    --tier3-csv data/raw/cafr/fy2024_tier3_statistical.csv
```

**Result**: FY2015-2024 restated historical data loaded (is_primary_version=False for restated)

---

### Step 3: Detect Discrepancies

**After importing each CAFR**, run discrepancy detection:

```bash
python scripts/validation/detect_restatement_discrepancies.py --cafr-year 2024
```

**Output**:
```
================================================================================
RESTATEMENT DISCREPANCY REPORT
================================================================================

Total Discrepancies Found: 3
  - Critical (>10%): 0
  - Major (5-10%): 1
  - Moderate (1-5%): 2
  - Minor (<1%): 0

================================================================================
MAJOR DISCREPANCIES (1)
================================================================================

📊 FY2020 Revenues - Property Tax
   Stated (FY2020 CAFR):  $50,000,000.00
   Restated (FY2024 CAFR): $47,500,000.00
   Difference: -$2,500,000.00 (-5.00%)
   Reason: GASB 87 lease accounting reclassification
   ⚠️ Action: REQUIRES MANUAL REVIEW

================================================================================
END REPORT
================================================================================
```

---

## Analytics Query Requirements

### ❌ WRONG: Mixing Stated and Restated Data

```python
# This query would mix stated and restated data - INCORRECT!
total_revenue = db.query(func.sum(Revenue.actual_amount)).filter(
    Revenue.fiscal_year_id == fiscal_year_id
).scalar()
```

**Problem**: This includes BOTH stated and restated versions, double-counting and using wrong values!

---

### ✅ CORRECT: Filter for Primary Versions Only

```python
# CORRECT: Use ONLY stated data (primary versions)
total_revenue = db.query(func.sum(Revenue.actual_amount)).filter(
    Revenue.fiscal_year_id == fiscal_year_id,
    Revenue.is_primary_version == True,  # CRITICAL FILTER
    Revenue.data_version_type == 'stated'
).scalar()
```

**All analytics queries MUST include**:
- `is_primary_version == True`
- `data_version_type == 'stated'`

---

## Code Updates Required

### 1. Risk Scoring Indicators

**File**: `src/analytics/risk_scoring/indicators.py`

**Before** (INCORRECT):
```python
def calculate_fund_balance_ratio(self) -> Dict[str, Any]:
    total_expenditures = self.db.query(
        func.sum(Expenditure.actual_amount)
    ).filter(
        Expenditure.fiscal_year_id == self.fiscal_year_id
    ).scalar()
```

**After** (CORRECT):
```python
def calculate_fund_balance_ratio(self) -> Dict[str, Any]:
    # CRITICAL: Use ONLY stated data (is_primary_version=True)
    total_expenditures = self.db.query(
        func.sum(Expenditure.actual_amount)
    ).filter(
        Expenditure.fiscal_year_id == self.fiscal_year_id,
        Expenditure.is_primary_version == True,
        Expenditure.data_version_type == 'stated'
    ).scalar()
```

### 2. Projection Engine

**File**: `src/analytics/projections/projection_engine.py`

**Add primary version filter** to ALL queries that fetch historical data for trend analysis.

### 3. API Endpoints

**File**: `src/api/v1/routes/financial.py`

**Add filter** to revenue/expenditure endpoints:
```python
@router.get("/revenues/")
def get_revenues(fiscal_year: int):
    revenues = db.query(Revenue).filter(
        Revenue.fiscal_year_id == fiscal_year,
        Revenue.is_primary_version == True,  # Add this
        Revenue.data_version_type == 'stated'  # Add this
    ).all()
```

---

## Validation Rules

### Tier vs Version Type Logic

| Tier | Fiscal Year | Expected Version Type | Rule |
|------|-------------|----------------------|------|
| tier_1_financial | Same as CAFR year | `stated` | Financial section contains ONLY current year stated data |
| tier_3_statistical | Same as CAFR year | `stated` or `restated` | Current year in trend table (usually stated) |
| tier_3_statistical | Prior years | `restated` | Historical years are ALWAYS restated |

### Examples

✅ **VALID**:
```csv
2024,Property Tax,55000000,tier_1_financial,stated,2024,General,
2020,Property Tax,47500000,tier_3_statistical,restated,2024,General,
```

❌ **INVALID**:
```csv
# Error: Tier 1 cannot contain prior years
2020,Property Tax,50000000,tier_1_financial,stated,2024,General,

# Error: Tier 1 cannot be restated
2024,Property Tax,55000000,tier_1_financial,restated,2024,General,

# Error: Tier 3 historical data must be restated
2020,Property Tax,50000000,tier_3_statistical,stated,2024,General,
```

---

## Restatement Categories

Track **why** data was restated using `restatement_category` field:

| Category | Description | Example |
|----------|-------------|---------|
| `GASB_Change` | New accounting standard applied retroactively | GASB 87 (leases), GASB 68 (pensions) |
| `Reclassification` | Revenue/expenditure moved between categories | Transfer from "Other" to "Property Tax" |
| `Error_Correction` | Fixing prior year accounting error | Correcting double-counted revenue |
| `Fund_Transfer` | Moving items between funds | Moving item from Special to General fund |
| `Methodology_Change` | Changed calculation method | Revised depreciation schedule |
| `Other` | Other reason (document in notes) | Various adjustments |

---

## Severity Thresholds

Automatic severity classification for discrepancies:

| Severity | Percent Difference | Action Required |
|----------|-------------------|-----------------|
| **Minor** | < 1% | Log for reference, no review needed |
| **Moderate** | 1% - 5% | Flag for review, document reason |
| **Major** | 5% - 10% | **REQUIRES MANUAL REVIEW** |
| **Critical** | > 10% | **URGENT: Investigate immediately** |

**Major and Critical discrepancies** trigger:
1. Manual review requirement
2. Notification to data quality team
3. Investigation and documentation
4. Public transparency log entry

---

## Data Quality Checks

### Automated Checks

1. **Tier Consistency**: Tier 1 contains only current year stated data
2. **Version Logic**: Historical data in Tier 3 is marked restated
3. **Source Year**: source_cafr_year ≥ fiscal_year
4. **Primary Version**: Only one is_primary_version=True per fiscal year + category
5. **Discrepancy Detection**: Stated values compared to all restated versions

### Manual Review Workflow

When Major/Critical discrepancies detected:

1. **Review Source Documents**:
   - Check stated value in original CAFR
   - Check restated value in later CAFR
   - Verify transcription accuracy

2. **Document Reason**:
   - Identify GASB standard or reason
   - Update `restatement_reason` field
   - Set `restatement_category`

3. **Validate Appropriateness**:
   - Is restatement legitimate?
   - Should original stated value remain primary?
   - Are there additional restatements needed?

4. **Mark Reviewed**:
   ```sql
   UPDATE restatement_discrepancies
   SET reviewed = TRUE,
       reviewed_by = 'your_name',
       reviewed_date = NOW(),
       review_notes = 'GASB 87 lease reclassification - legitimate restatement'
   WHERE id = 123;
   ```

---

## Best Practices

### For Data Entry

1. **Always import Tier 1 first** (stated current year data)
2. **Then import Tier 3** (restated historical trends)
3. **Run discrepancy detection** immediately after each CAFR import
4. **Review and document** Major/Critical discrepancies within 48 hours
5. **Never delete** restated data - it's part of the audit trail

### For Analysis

1. **ALWAYS filter** `is_primary_version=True` and `data_version_type='stated'`
2. **Never use restated data** for risk scores or projections
3. **Use restated data only** for historical comparison/charting
4. **Document methodology** in reports (state which version used)
5. **Archive queries** with version filters for reproducibility

### For Reporting

1. **Clearly label** stated vs restated data in charts
2. **Show restatement history** for transparency
3. **Footnote discrepancies** in public reports
4. **Link to source CAFRs** for verification
5. **Update annually** as new CAFRs published

---

## Migration Guide

### Run Migration

```bash
# Apply migration to add version tracking fields
poetry run alembic upgrade g4c9e1f5j8f6

# Verify migration success
psql ibco_dev -c "\d revenues" | grep cafr_tier
```

### Backfill Existing Data

If you have existing data that needs version tracking:

```sql
-- Mark all existing data as stated, Tier 1
UPDATE revenues
SET cafr_tier = 'tier_1_financial',
    data_version_type = 'stated',
    source_cafr_year = (SELECT year FROM fiscal_years WHERE id = fiscal_year_id),
    is_primary_version = TRUE
WHERE cafr_tier IS NULL;

-- Repeat for expenditures, fund_balances, pension_contributions
```

---

## Troubleshooting

### Issue: Duplicate Key Violation on Import

**Error**: `duplicate key value violates unique constraint "uq_revenue_version"`

**Cause**: Trying to import same fiscal_year + category + tier + version + source_cafr_year twice

**Solution**: Check if data already exists, or update existing record instead of inserting

### Issue: Analytics Returning Inflated Values

**Symptom**: Revenue totals are 2-3x expected values

**Cause**: Query not filtering for `is_primary_version=True`, including both stated and restated

**Solution**: Add primary version filter to all analytics queries

### Issue: Missing Data in Risk Scores

**Symptom**: Risk indicators showing "Insufficient data"

**Cause**: Data imported as Tier 3 restated instead of Tier 1 stated

**Solution**: Re-import as Tier 1 stated, or update existing records:
```sql
UPDATE revenues
SET cafr_tier = 'tier_1_financial',
    data_version_type = 'stated',
    is_primary_version = TRUE
WHERE fiscal_year_id = <id> AND cafr_tier = 'tier_3_statistical';
```

---

## Further Reading

- [GASB Statement No. 87 - Leases](https://www.gasb.org/st/summary/gstsm87.html)
- [GASB Statement No. 68 - Pensions](https://www.gasb.org/st/summary/gstsm68.html)
- CAFR Ten-Year Financial Trends (Statistical Section)
- IBCo Data Entry Workflow (docs/data_entry_workflow.md)
- IBCo Data Lineage Guide (docs/data_lineage_guide.md)

---

**Last Updated**: 2025-11-17
**Migration Version**: g4c9e1f5j8f6
**Status**: ✅ Ready for implementation
