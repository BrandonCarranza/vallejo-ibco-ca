# Quick Start: Three-Tier CAFR Data Entry Workflow

## TL;DR

**Three-tier structure**:
- **Tier 1**: Financial Section → Stated current year → ✅ **USE FOR ANALYSIS**
- **Tier 2**: Notes → Context only → 📝 **REFERENCE ONLY**
- **Tier 3**: Statistical Section → Restated historical → 📊 **COMPARISON ONLY**

**Critical rule**: ALWAYS filter `is_primary_version=True` in analytics queries!

---

## Prerequisites

1. **Database migrated**:
   ```bash
   poetry run alembic upgrade head
   ```

2. **City exists**:
   ```sql
   INSERT INTO cities (name, state, county, fiscal_year_end_month, fiscal_year_end_day)
   VALUES ('Vallejo', 'CA', 'Solano', 6, 30);
   ```

---

## Workflow: Import FY2024 CAFR

### Step 1: Prepare CSV Files

Create two CSV files from FY2024 CAFR:

#### `fy2024_tier1_financial.csv` (from Financial Section, pages 10-50)
```csv
fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes
2024,Property Tax,55000000,tier_1_financial,stated,2024,General,
2024,Sales Tax,12000000,tier_1_financial,stated,2024,General,
2024,Business License Tax,3500000,tier_1_financial,stated,2024,General,
```

#### `fy2024_tier3_statistical.csv` (from Statistical Section, pages 200-250)
```csv
fiscal_year,category,amount,cafr_tier,data_version_type,source_cafr_year,fund_type,notes
2024,Property Tax,55000000,tier_3_statistical,stated,2024,General,
2023,Property Tax,53000000,tier_3_statistical,restated,2024,General,
2022,Property Tax,51000000,tier_3_statistical,restated,2024,General,
2021,Property Tax,49000000,tier_3_statistical,restated,2024,General,
2020,Property Tax,47500000,tier_3_statistical,restated,2024,General,GASB 87 adjustment
2019,Property Tax,46000000,tier_3_statistical,restated,2024,General,
2018,Property Tax,44500000,tier_3_statistical,restated,2024,General,
2017,Property Tax,43000000,tier_3_statistical,restated,2024,General,
2016,Property Tax,41500000,tier_3_statistical,restated,2024,General,
2015,Property Tax,40000000,tier_3_statistical,restated,2024,General,
```

---

### Step 2: Validate with Dry Run

```bash
# Validate Tier 1 CSV
python scripts/data_entry/import_cafr_three_tier.py \
    --cafr-year 2024 \
    --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv \
    --dry-run

# Check for errors in output
# If validation passes, proceed to import
```

---

### Step 3: Import Tier 1 (Financial Section)

```bash
# Import Tier 1: Stated current year data
python scripts/data_entry/import_cafr_three_tier.py \
    --cafr-year 2024 \
    --tier1-csv data/raw/cafr/fy2024_tier1_financial.csv
```

**Expected output**:
```
✅ Imported 150 revenues from fy2024_tier1_financial.csv
📊 Tier 1 (Financial Section - Stated Data):
   Revenues:     150
   Expenditures: 0
   Fund Balances: 0
Total Records: 150
Errors: 0
✅ Import completed successfully
```

---

### Step 4: Import Tier 3 (Statistical Section)

```bash
# Import Tier 3: Restated 10-year historical trends
python scripts/data_entry/import_cafr_three_tier.py \
    --cafr-year 2024 \
    --tier3-csv data/raw/cafr/fy2024_tier3_statistical.csv
```

**Expected output**:
```
✅ Imported 1500 revenues from fy2024_tier3_statistical.csv
📈 Tier 3 (Statistical Section - Restated Historical Data):
   Revenues:     1500
Total Records: 1500
```

---

### Step 5: Detect Discrepancies

```bash
# Automatically detect restatement discrepancies
python scripts/validation/detect_restatement_discrepancies.py --cafr-year 2024
```

**Expected output**:
```
================================================================================
RESTATEMENT DISCREPANCY REPORT
================================================================================

Total Discrepancies Found: 12
  - Critical (>10%): 0
  - Major (5-10%): 2
  - Moderate (1-5%): 8
  - Minor (<1%): 2

================================================================================
MAJOR DISCREPANCIES (2)
================================================================================

📊 FY2020 Revenues - Property Tax
   Stated (FY2020 CAFR):  $50,000,000.00
   Restated (FY2024 CAFR): $47,500,000.00
   Difference: -$2,500,000.00 (-5.00%)
   Reason: GASB 87 lease accounting reclassification
   ⚠️ Action: REQUIRES MANUAL REVIEW
```

---

### Step 6: Review Discrepancies

```sql
-- Query unreviewed discrepancies
SELECT
    d.fiscal_year_id,
    fy.year AS fiscal_year,
    d.table_name,
    d.stated_value,
    d.restated_value,
    d.percent_difference,
    d.severity,
    d.restatement_reason
FROM restatement_discrepancies d
JOIN fiscal_years fy ON d.fiscal_year_id = fy.id
WHERE d.reviewed = FALSE
  AND d.severity IN ('Major', 'Critical')
ORDER BY d.severity DESC, ABS(d.percent_difference) DESC;
```

**For each discrepancy**:
1. Verify stated value in original CAFR
2. Verify restated value in FY2024 CAFR
3. Identify reason (GASB standard, reclassification, error)
4. Document and mark reviewed:

```sql
UPDATE restatement_discrepancies
SET reviewed = TRUE,
    reviewed_by = 'your_name',
    reviewed_date = NOW(),
    review_notes = 'GASB 87 lease accounting - legitimate restatement per auditor note 15'
WHERE id = 123;
```

---

## Data Validation Checklist

After import, verify:

### ✅ Tier 1 Data Loaded Correctly
```sql
SELECT COUNT(*) FROM revenues
WHERE source_cafr_year = 2024
  AND cafr_tier = 'tier_1_financial'
  AND data_version_type = 'stated'
  AND is_primary_version = TRUE;
-- Expected: ~150-200 revenue line items
```

### ✅ Tier 3 Data Loaded Correctly
```sql
SELECT fiscal_year_id, COUNT(*) as count
FROM revenues
WHERE source_cafr_year = 2024
  AND cafr_tier = 'tier_3_statistical'
  AND data_version_type = 'restated'
GROUP BY fiscal_year_id
ORDER BY fiscal_year_id;
-- Expected: ~150-200 line items per year × 10 years = 1500-2000 records
```

### ✅ Primary Versions Set Correctly
```sql
SELECT
    data_version_type,
    is_primary_version,
    COUNT(*) as count
FROM revenues
WHERE fiscal_year_id = (SELECT id FROM fiscal_years WHERE year = 2024)
GROUP BY data_version_type, is_primary_version;

-- Expected:
-- stated   | TRUE  | 150-200 (Tier 1)
-- restated | FALSE | 150-200 (Tier 3 current year)
```

### ✅ No Duplicate Primary Versions
```sql
SELECT
    fiscal_year_id,
    category_id,
    fund_type,
    COUNT(*) as version_count
FROM revenues
WHERE is_primary_version = TRUE
GROUP BY fiscal_year_id, category_id, fund_type
HAVING COUNT(*) > 1;
-- Expected: 0 rows (no duplicates)
```

---

## Common Errors & Solutions

### Error: "Invalid tier: tier1"
**Cause**: Incorrect tier name in CSV
**Solution**: Use full tier names:
- ✅ `tier_1_financial`
- ✅ `tier_3_statistical`
- ❌ `tier1` or `Tier 1`

### Error: "Tier 1 data must match CAFR year"
**Cause**: Tier 1 CSV contains historical years
**Solution**: Move historical data to Tier 3 CSV

### Error: "Revenue already exists, skipping"
**Cause**: Duplicate import attempt
**Solution**: Delete existing records or skip re-import

### Error: "Tier 3 historical data must be 'restated'"
**Cause**: Historical year marked as 'stated' in Tier 3
**Solution**: Change `data_version_type` to `restated` for years < cafr_year

---

## Analytics Query Template

**ALWAYS use this template** for analytics queries:

```python
# ✅ CORRECT: Filter for primary versions only
query_results = db.query(Revenue).filter(
    Revenue.fiscal_year_id == fiscal_year_id,
    Revenue.is_primary_version == True,  # CRITICAL!
    Revenue.data_version_type == 'stated'
).all()

# Calculate totals
total_revenue = db.query(func.sum(Revenue.actual_amount)).filter(
    Revenue.fiscal_year_id == fiscal_year_id,
    Revenue.is_primary_version == True,  # CRITICAL!
    Revenue.data_version_type == 'stated'
).scalar()
```

**❌ WRONG: Missing primary version filter**
```python
# This will double-count and use wrong values!
query_results = db.query(Revenue).filter(
    Revenue.fiscal_year_id == fiscal_year_id
).all()
```

---

## Repeat for Each CAFR Year

For comprehensive historical data:

1. **Import FY2024 CAFR** (Tier 1 + Tier 3) ✅
2. **Import FY2023 CAFR** (Tier 1 + Tier 3)
3. **Import FY2022 CAFR** (Tier 1 + Tier 3)
4. **Import FY2021 CAFR** (Tier 1 + Tier 3)
5. **Import FY2020 CAFR** (Tier 1 + Tier 3)

**After each import**: Run discrepancy detection

**Result**: Complete stated + restated history with full audit trail

---

## Summary

| Action | Command |
|--------|---------|
| Validate CSV | `python scripts/data_entry/import_cafr_three_tier.py --cafr-year 2024 --tier1-csv ... --dry-run` |
| Import Tier 1 | `python scripts/data_entry/import_cafr_three_tier.py --cafr-year 2024 --tier1-csv ...` |
| Import Tier 3 | `python scripts/data_entry/import_cafr_three_tier.py --cafr-year 2024 --tier3-csv ...` |
| Detect Discrepancies | `python scripts/validation/detect_restatement_discrepancies.py --cafr-year 2024` |
| Review Discrepancies | `SELECT * FROM restatement_discrepancies WHERE reviewed=FALSE AND severity IN ('Major', 'Critical');` |

---

**Ready to start?** Import your first CAFR and let the system automatically detect restatements!

For detailed documentation, see: [docs/three_tier_cafr_data_structure.md](./three_tier_cafr_data_structure.md)
