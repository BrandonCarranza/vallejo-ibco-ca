# Data Lineage & Audit Trail Guide

## Overview

The IBCo Vallejo Console implements **forensic-level data lineage tracking** for every data point in the system. This provides complete accountability and transparency, critical for:

- **Legal defense**: Complete evidence chain for any claim
- **Public trust**: Full transparency of data sources
- **Forensic accountability**: Trace any metric back to source documents
- **Manual entry advantage**: 100% confidence scores vs 85-95% for automation

## Architecture

Every data point tracks:

```
Data Point (e.g., Risk Score = 68)
├── Source Document
│   ├── URL: https://www.calpers.ca.gov/.../vallejo_2024.pdf
│   ├── Page: 12
│   ├── Section: "Actuarial Valuation"
│   ├── Table: "Table 5"
│   └── Line Item: "Line 42"
├── Extraction
│   ├── Method: Manual / Automated / Calculated
│   ├── Extracted by: Jane Doe / System Name
│   ├── Timestamp: 2024-08-01 10:30 UTC
│   └── Notes: "Transcribed from CAFR page 34"
├── Validation
│   ├── Validated: Yes
│   ├── Validated by: John Smith
│   ├── Timestamp: 2024-08-02 14:20 UTC
│   └── Notes: "Cross-checked with budget document"
└── Confidence
    ├── Score: 100 (0-100 scale)
    └── Level: High / Medium / Low
```

## Database Model

The `DataLineage` table tracks complete provenance:

```sql
CREATE TABLE data_lineage (
    id INTEGER PRIMARY KEY,
    -- What data?
    table_name VARCHAR(100),      -- "revenues"
    record_id INTEGER,             -- 42
    field_name VARCHAR(100),       -- "amount"

    -- Where from?
    source_id INTEGER,             -- FK to data_sources
    source_document_url VARCHAR(500),
    source_document_page INTEGER,
    source_document_section VARCHAR(255),
    source_document_table_name VARCHAR(255),  -- "Table 5"
    source_document_line_item VARCHAR(255),    -- "Line 42"

    -- How extracted?
    extraction_method VARCHAR(50), -- Manual / Automated / Calculated
    extracted_by VARCHAR(255),     -- Person or system name
    extracted_at TIMESTAMP,
    notes TEXT,

    -- Validated?
    validated BOOLEAN,
    validated_by VARCHAR(255),
    validated_at TIMESTAMP,
    validation_notes TEXT,

    -- Cross-validation
    cross_validated_source_id INTEGER,  -- FK to second source
    matches_cross_validation BOOLEAN,

    -- Confidence
    confidence_score INTEGER,      -- 0-100
    confidence_level VARCHAR(20),  -- High / Medium / Low

    -- Audit trail (AuditMixin)
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,          -- Soft delete only!
    is_deleted BOOLEAN
);
```

**Important**: Lineage records are **immutable** - no hard deletes, only soft deletes. Complete audit trail is preserved.

## Recording Lineage

### During Manual Entry

Use the `LineageRecorder` helper class:

```python
from src.utils.lineage_helpers import LineageRecorder

recorder = LineageRecorder(db)

# Record CAFR entry
lineage = recorder.record_manual_entry(
    table_name="revenues",
    record_id=revenue.id,
    field_name="amount",
    source_id=cafr_source.id,
    extracted_by="jane.doe@ibco-ca.us",
    source_document_url="https://www.cityofvallejo.net/cafr-2024.pdf",
    source_document_page=34,
    source_document_section="Statement of Activities",
    notes="Total General Fund revenues",
    confidence_score=100,  # Manual entry = 100%
)
```

### Convenience Functions

For common operations, use convenience functions:

```python
from src.utils.lineage_helpers import record_cafr_entry, record_calpers_entry

# CAFR entry
lineage = record_cafr_entry(
    db=db,
    table_name="revenues",
    record_id=revenue.id,
    field_name="amount",
    cafr_source_id=cafr_source.id,
    page_number=34,
    section_name="Statement of Activities",
    entered_by="jane.doe@ibco-ca.us",
    notes="Total revenues"
)

# CalPERS entry
lineage = record_calpers_entry(
    db=db,
    table_name="pension_plans",
    record_id=plan.id,
    field_name="funded_ratio",
    calpers_source_id=calpers_source.id,
    page_number=12,
    table_name_in_doc="Table 5",
    entered_by="jane.doe@ibco-ca.us"
)
```

### Bulk Entry

When entering multiple fields from the same source:

```python
field_mappings = {
    "total_revenues": "Total revenues from Statement of Activities",
    "total_expenditures": "Total expenditures from Statement of Activities",
    "operating_balance": "Calculated: revenues - expenditures"
}

lineage_records = recorder.bulk_record_manual_entry(
    table_name="fiscal_years",
    record_id=fy.id,
    field_mappings=field_mappings,
    source_id=cafr_source.id,
    extracted_by="jane.doe@ibco-ca.us",
    source_document_page=34
)
```

### Validating Data

After data entry, a second person should validate:

```python
validated_lineage = recorder.validate_lineage(
    lineage_id=lineage.id,
    validated_by="john.smith@ibco-ca.us",
    validation_notes="Cross-checked with CAFR summary totals, values match"
)
```

## Tracing Lineage

### Trace a Single Data Point

```python
from src.analytics.lineage_tracer import DataLineageTracer

tracer = DataLineageTracer(db)

# Trace any data point
node = tracer.trace_data_point(
    table_name="revenues",
    record_id=42,
    field_name="amount"
)

print(f"Value: {node.value}")
print(f"Source: {node.source_name}")
print(f"Page: {node.source_document_page}")
print(f"Extracted by: {node.extracted_by}")
print(f"Validated: {node.validated}")
print(f"Confidence: {node.confidence_score}%")
```

### Trace a Risk Score

Trace through complete dependency chain:

```python
# Trace risk score through all indicators
chain = tracer.trace_risk_score(fiscal_year_id=1)

print(f"Root: {chain.root.field_name} = {chain.root.value}")
print(f"Dependencies: {len(chain.dependencies)}")

# Generate human-readable text
text = tracer.generate_evidence_chain_text(chain)
print(text)
```

## Generating Reports

### HTML Report

Generate comprehensive HTML report with clickable links:

```bash
# Risk score lineage
python scripts/reports/generate_lineage_report.py --fiscal-year-id 1 --output report.html

# Specific data point
python scripts/reports/generate_lineage_report.py \
  --table revenues \
  --record-id 42 \
  --field amount \
  --output lineage.html

# Generate and open in browser
python scripts/reports/generate_lineage_report.py --fiscal-year-id 1 --open
```

The HTML report includes:
- Source document with clickable URL
- Page numbers, sections, tables, line items
- Transcriber and validator information
- Complete timestamps
- Confidence scores with visual indicators
- Dependency tree showing all underlying data

## Public API Endpoints

### Get Data Point Lineage

```http
GET /api/v1/lineage/data-point?table=revenues&record_id=42&field=amount
```

**Response:**
```json
{
  "table_name": "revenues",
  "record_id": 42,
  "field_name": "amount",
  "value": "298000000",
  "source": {
    "name": "Vallejo CAFR FY2024",
    "document_url": "https://www.cityofvallejo.net/cafr-2024.pdf",
    "page": 34,
    "section": "Statement of Activities",
    "table_name": null,
    "line_item": null
  },
  "extraction": {
    "method": "Manual",
    "extracted_by": "jane.doe@ibco-ca.us",
    "extracted_at": "2024-08-01T10:30:00Z",
    "notes": "Total General Fund revenues"
  },
  "validation": {
    "validated": true,
    "validated_by": "john.smith@ibco-ca.us",
    "validated_at": "2024-08-02T14:20:00Z",
    "validation_notes": "Cross-checked with CAFR summary totals"
  },
  "confidence": {
    "score": 100,
    "level": "High"
  }
}
```

### Get Risk Score Lineage Chain

```http
GET /api/v1/lineage/risk-score/1
```

Returns complete dependency chain from risk score through indicators to source data.

### Get Evidence Chain (Text)

```http
GET /api/v1/lineage/evidence-chain/1
```

Returns human-readable text representation suitable for reports.

### Get Audit Trail Summary

```http
GET /api/v1/lineage/audit-trail?city_id=1
```

Shows data completeness and validation rates for all fiscal years.

## Confidence Scores

### Manual Entry: 100%

Manual transcription by a human from source documents:
- Extracted by: Person's name/email
- Method: "Manual"
- Confidence: 100%
- Level: "High"

**Rationale**: Human carefully transcribes from official document. When validated by a second person, this is gold-standard data quality.

### Automated Extraction: 85-95%

PDF extraction, OCR, or automated scraping:
- Extracted by: System name (e.g., "PDF_Extractor_v1")
- Method: "Automated"
- Confidence: 85-95% depending on accuracy
- Level: "Medium" or "High"

**Rationale**: Automation can mis-read numbers, tables, formatting. Requires human validation to reach 100%.

### Calculated Fields: 100%

Derived from other fields (e.g., revenues - expenditures):
- Extracted by: "Risk_Scoring_Engine" or person who calculated
- Method: "Calculated"
- Confidence: 100% (assuming input data is 100%)
- Level: "High"

**Rationale**: Math is deterministic. If inputs are trusted, calculation is trusted.

## Best Practices

### For Data Entry Operators

1. **Always record lineage** for every field you enter
2. **Be specific** about page numbers, sections, tables
3. **Include notes** explaining what you transcribed
4. **Use your name/email** so validation can happen
5. **Validate someone else's work** - fresh eyes catch errors

### For Validators

1. **Cross-check** with original source document
2. **Verify calculations** are correct
3. **Document disagreements** if found
4. **Use validation_notes** to explain what you checked
5. **Don't validate your own work** - requires second person

### For Developers

1. **Record lineage immediately** after inserting data
2. **Use helper functions** for consistency
3. **Bulk operations** for efficiency
4. **Never hard delete** lineage records
5. **Always soft delete** (set is_deleted=True)

## Legal Defense Example

If challenged on a claim like "Vallejo's pension funded ratio is 62%":

```
Claim: Pension funded ratio = 62%

Evidence Chain:
1. Risk Score FY2024 = 68 (High)
   Source: src/database/risk_scores table, record 1
   Calculated: 2024-08-15 by Risk_Scoring_Engine

2. Pension Stress Indicator = 72
   Source: src/database/risk_indicator_scores, record 5
   Based on: Pension funded ratio

3. Pension Funded Ratio = 62%
   Source: src/database/pension_plans, record 1
   Document: CalPERS Actuarial Valuation, June 30, 2024
   URL: https://www.calpers.ca.gov/docs/vallejo_2024.pdf
   Page: 12, Table 5
   Line: "Funded Ratio"

   Extracted by: jane.doe@ibco-ca.us
   Date: 2024-08-01 10:35:00 UTC
   Method: Manual transcription

   Validated by: john.smith@ibco-ca.us
   Date: 2024-08-02 14:20:00 UTC
   Validation notes: "Cross-checked with CAFR pension note, values match"

   Confidence: 100% (Manual entry, validated)

4. Calculation:
   Market Value of Assets: $4.2B (CalPERS page 12)
   Total Pension Liability: $6.8B (CalPERS page 12)
   Funded Ratio = $4.2B / $6.8B = 0.62 = 62%
```

**Result**: Complete chain of custody from claim to official source document, with timestamps and personnel. Legally defensible.

## Transparency & Public Trust

All lineage endpoints are **public** - no authentication required. Anyone can:

1. View source documents for any data point
2. See who entered and validated data
3. Check confidence scores
4. Verify calculations
5. Generate their own reports

This radical transparency is core to IBCo's mission: **independent, verifiable, accountable civic data**.

## Related Documentation

- [Manual Data Entry Workflow](./data_entry_workflow.md)
- [Data Refresh Orchestration](./data_refresh_workflow.md)
- [Risk Scoring Methodology](../METHODOLOGY.md)
- [API Documentation](./api_documentation.md)

## Support

For questions or issues:
- **GitHub Issues**: https://github.com/ibco-ca/vallejo-ibco-ca/issues
- **Email**: data@ibco-ca.us
- **Documentation**: https://docs.ibco-ca.us
