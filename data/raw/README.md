# Raw Data Directory

This directory stores unprocessed source documents in their original format.

## Directory Structure

```
raw/
├── cafr/                   # Comprehensive Annual Financial Reports
│   ├── vallejo_cafr_2023.pdf
│   ├── vallejo_cafr_2022.pdf
│   └── ...
├── calpers/                # CalPERS Actuarial Reports
│   ├── vallejo_safety_2023.pdf
│   ├── vallejo_misc_2023.pdf
│   └── ...
└── state_controller/       # State Controller Data
    ├── cities_annual_2023.csv
    ├── compensation_2023.csv
    └── ...
```

## Data Source Details

### CAFR (Comprehensive Annual Financial Reports)

**What it is**: Annual audited financial statement from the City of Vallejo

**Where to find**:
- City of Vallejo website: https://www.cityofvallejo.net/city_hall/departments___divisions/finance/reports
- Archive.org (if city removes old reports)

**Key information contained**:
- General Fund revenues and expenditures
- Fund balances
- Long-term debt obligations
- Pension liabilities (GASB 68)
- OPEB liabilities (GASB 75)
- Cash flow statements
- Notes to financial statements

**Typical release**: 6 months after fiscal year end (December-January)

**Fiscal year**: July 1 - June 30

### CalPERS Actuarial Valuations

**What it is**: Annual pension plan valuation report

**Where to find**: https://www.calpers.ca.gov/page/employers/actuarial-services/gasb-68

**Plans to collect**:
- Safety Plan (Police and Fire)
- Miscellaneous Plan (Other city employees)

**Key information contained**:
- Total Pension Liability (TPL)
- Pension Plan Fiduciary Net Position
- Net Pension Liability (NPL)
- Funded ratio
- Contribution rates
- Actuarial assumptions
- Demographic data

**Typical release**: 9-12 months after valuation date

**Valuation date**: June 30

### California State Controller's Office

**What it is**: Statewide database of city financial and employee data

**Where to find**: https://bythenumbers.sco.ca.gov/

**Datasets to collect**:
1. **Cities Annual Report**
   - Summary financial data for all CA cities
   - Useful for peer comparison and validation

2. **Government Compensation in California**
   - Individual employee salaries
   - Total compensation including benefits
   - Useful for payroll cost analysis

**Format**: CSV downloads from website

**Typical release**: Ongoing updates, 6-18 months lag

## Download Instructions

### Manual Download

1. **Navigate to source website**
2. **Locate appropriate report/dataset**
3. **Download to this directory** using naming convention:
   ```
   {source}_{jurisdiction}_{fiscal_year}_{type}.{ext}
   ```

4. **Document the download** in download log:
   ```bash
   echo "$(date)|cafr|2023|https://example.com/cafr2023.pdf" >> download_log.txt
   ```

### Automated Download (Future)

Scripts will be provided to automate downloads:

```bash
# Download latest CAFR
poetry run python scripts/data_entry/download_cafr.py --year 2023

# Download CalPERS reports
poetry run python scripts/data_entry/download_calpers.py --year 2023 --all-plans
```

## Data Integrity

### Verification Steps

After downloading any document:

1. **Verify authenticity**: Check URL is official government site
2. **Check completeness**: Ensure file is not truncated
3. **Verify file type**: Confirm PDF/CSV opens correctly
4. **Document metadata**: Record download date, source URL, file hash

### File Integrity

Generate checksums for verification:

```bash
# Generate SHA256 checksum
sha256sum cafr/vallejo_cafr_2023.pdf > checksums.txt
```

## Data Retention

### Retention Policy

- **Keep all original files**: Never delete source documents
- **Preserve file timestamps**: Indicates when document was obtained
- **Maintain download logs**: Provides audit trail

### Backup

Raw data should be backed up to:
1. Project backup storage
2. Archive.org (for public preservation)
3. Multiple geographic locations

## Data Processing

Raw data in this directory is:
1. **Read-only**: Never modify original files
2. **Input to extraction**: Scripts read from here
3. **Archived**: Periodically moved to long-term storage

Processing workflow:
```
raw/ → extraction → validation → processed/ → database
```

See [../processed/README.md](../processed/README.md) for next steps.

## File Naming Convention

Use consistent naming for easy automation:

```
{source}_{jurisdiction}_{fiscal_year_end}_{plan_type}.{extension}

Examples:
cafr_vallejo_2023.pdf           # CAFR ending June 30, 2023
calpers_vallejo_safety_2023.pdf # Safety plan, June 30, 2023
calpers_vallejo_misc_2023.pdf   # Misc plan, June 30, 2023
sco_cities_annual_2023.csv      # State Controller, 2023 data
```

## Troubleshooting

**Cannot find historical CAFRs**
- Check Archive.org Wayback Machine
- Contact City Clerk's office
- Check with State Controller (they maintain copies)

**CalPERS report not available**
- Reports released 9-12 months after valuation date
- Contact CalPERS actuarial services if missing

**Broken download links**
- Document broken link in issues
- Search for alternative source
- Contact website administrator

## Important Notes

⚠️ **This directory is gitignored** - Files here are NOT committed to version control due to size

⚠️ **Backup raw data** - Store copies in multiple locations

⚠️ **Verify authenticity** - Only download from official government sources

⚠️ **Document everything** - Maintain logs of all downloads and sources

## Questions?

- Data sources: See [../../docs/data_sources/](../../docs/data_sources/)
- Issues: Open GitHub issue or email data@ibco-ca.us
- Methodology: See [../../METHODOLOGY.md](../../METHODOLOGY.md)
