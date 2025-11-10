# Data Directory

This directory contains all data for the IBCo Vallejo Console project.

## Directory Structure

```
data/
├── raw/              # Unprocessed source documents (gitignored)
│   ├── cafr/         # CAFR PDFs by fiscal year
│   ├── calpers/      # CalPERS actuarial reports
│   └── state_controller/  # State Controller data files
├── processed/        # Cleaned, structured data (gitignored)
├── archive/          # Historical data snapshots (gitignored)
└── samples/          # Sample data for testing (committed to git)
```

## Important Notes

### Data Storage Policy

- **`raw/`**: Original source documents. NOT committed to git due to size.
- **`processed/`**: Cleaned data ready for database import. NOT committed to git.
- **`archive/`**: Quarterly snapshots for historical preservation. NOT committed to git.
- **`samples/`**: Small sample datasets for development and testing. COMMITTED to git.

### Data Sources

All data comes from public sources:

1. **City of Vallejo CAFRs**
   - Annual financial reports
   - Audited by independent CPAs
   - Source: https://www.cityofvallejo.net/

2. **CalPERS Actuarial Valuations**
   - Annual pension plan reports
   - Contains liability and funding data
   - Source: https://www.calpers.ca.gov/

3. **California State Controller**
   - Cities Annual Report
   - Government Compensation data
   - Source: https://bythenumbers.sco.ca.gov/

### Data Lineage

Every data point includes:
- Source document URL or file reference
- Extraction date and method
- Validation status
- Any transformations applied

See [METHODOLOGY.md](../METHODOLOGY.md) for detailed data collection methodology.

## Working with Data

### Initial Setup

1. Create a `raw/` directory structure:
```bash
mkdir -p data/raw/{cafr,calpers,state_controller}
```

2. Download source documents to appropriate directories

3. Run extraction/import scripts:
```bash
poetry run python scripts/data_entry/import_cafr_manual.py
```

### Sample Data

Sample data in `data/samples/` is used for:
- Automated testing
- Development without full dataset
- Documentation examples

Sample data represents real data patterns but uses:
- Anonymized or synthetic values
- Reduced dataset size
- Simplified structure for clarity

### Data Validation

All imported data goes through validation:

```bash
# Run validation checks
poetry run python scripts/data_entry/validation_checks.py
```

### Creating Snapshots

Quarterly snapshots preserve data state:

```bash
# Create snapshot
poetry run python scripts/maintenance/create_snapshot.py
```

Snapshots are archived to:
1. Local `archive/` directory
2. Archive.org for public preservation
3. Backup storage (if configured)

## Data Format Standards

### File Naming Convention

```
{source}_{jurisdiction}_{fiscal_year}_{document_type}.{ext}

Examples:
cafr_vallejo_2023.pdf
calpers_vallejo_safety_2023.pdf
sco_cities_annual_2023.csv
```

### Fiscal Year Format

- Use ending year: FY 2022-23 = 2023
- Date format: YYYY-MM-DD (ISO 8601)
- Fiscal year end: June 30 for California cities

### Data Quality Standards

- Critical fields: 99.9% accuracy target
- Secondary fields: 99% accuracy target
- All anomalies reviewed manually
- Cross-source validation when possible

## Troubleshooting

### Common Issues

**Issue**: Raw data directory empty
- **Solution**: Download source documents from official sources

**Issue**: Import script fails validation
- **Solution**: Review validation errors, correct data, re-import

**Issue**: Sample data outdated
- **Solution**: Regenerate samples from current processed data

## Privacy & Security

This project uses only **public data**. No personally identifiable information (PII) is collected or stored.

If you accidentally include sensitive data:
1. **Immediately** remove it from all directories
2. Contact project maintainers
3. Ensure it's not committed to git
4. Review .gitignore to prevent recurrence

## Questions?

- Data questions: data@ibco-ca.us
- Documentation: See [docs/data_sources/](../docs/data_sources/)
- Methodology: See [METHODOLOGY.md](../METHODOLOGY.md)
