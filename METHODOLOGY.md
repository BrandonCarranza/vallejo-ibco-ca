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
