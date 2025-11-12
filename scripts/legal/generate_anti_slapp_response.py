#!/usr/bin/env python3
"""
Generate automated anti-SLAPP responses for legal threats.

This script generates template-based responses to cease-and-desist letters,
defamation claims, and SLAPP lawsuits. Responses include:
- Auto-cited data sources (CAFR page X, CalPERS document Y)
- Auto-cited methodology (transparent risk scoring, open source code)
- Auto-cited disclaimers (independent analysis, not predictions)
- Legal defenses (First Amendment, anti-SLAPP statute, public interest)

Output is a draft response ready for legal counsel review.

IMPORTANT: This script generates DRAFT responses only. All responses
must be reviewed by qualified legal counsel before sending.

Usage:
    python scripts/legal/generate_anti_slapp_response.py \
        --incident-id 42 \
        --template AntiSLAPP \
        --output-file response_draft.md

    python scripts/legal/generate_anti_slapp_response.py \
        --incident-id 42 \
        --template CeaseAndDesistResponse \
        --include-lineage \
        --output-format markdown
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.database.base import Base
from src.database.models.legal import LegalIncident, LegalTemplate
from src.database.models.core import DataLineage, DataSource
from src.config.database import SessionLocal


# ============================================================================
# Template Data Structure
# ============================================================================

TEMPLATE_REGISTRY = {
    "AntiSLAPP": {
        "name": "Anti-SLAPP Motion Response",
        "subject": "Response to {incident_type} - First Amendment Protected Speech",
        "sections": [
            "introduction",
            "factual_background",
            "legal_analysis",
            "data_provenance",
            "methodology_transparency",
            "disclaimers",
            "first_amendment_protection",
            "anti_slapp_statute",
            "public_interest",
            "conclusion",
        ],
    },
    "CeaseAndDesistResponse": {
        "name": "Cease-and-Desist Response",
        "subject": "Response to Cease-and-Desist Letter - {date_received}",
        "sections": [
            "introduction",
            "factual_background",
            "data_provenance",
            "methodology_transparency",
            "disclaimers",
            "first_amendment_protection",
            "no_retraction_warranted",
            "conclusion",
        ],
    },
    "DefamationResponse": {
        "name": "Defamation Claim Response",
        "subject": "Response to Defamation Claim - Truth Defense",
        "sections": [
            "introduction",
            "factual_background",
            "truth_defense",
            "data_provenance",
            "methodology_transparency",
            "disclaimers",
            "first_amendment_protection",
            "no_actual_malice",
            "conclusion",
        ],
    },
    "EFFNotification": {
        "name": "EFF/ACLU Notification Letter",
        "subject": "Legal Threat Notification - Request for Support",
        "sections": [
            "introduction",
            "incident_summary",
            "first_amendment_implications",
            "public_interest",
            "request_for_support",
        ],
    },
}


# ============================================================================
# Section Generators
# ============================================================================


def generate_introduction(incident: LegalIncident, context: Dict) -> str:
    """Generate introduction section."""
    return f"""## Introduction

This letter responds to the {incident.incident_type.lower()} received on {incident.date_received.strftime('%B %d, %Y')} from {incident.sender_name}{f' ({incident.sender_organization})' if incident.sender_organization else ''}.

**IBCo Position:** We respectfully decline to comply with the demands outlined in your {incident.incident_type.lower()}. Our analysis is protected under the First Amendment, based on publicly available government documents, and serves a clear public interest.

This response explains:
1. The factual and legal basis for our analysis
2. The complete provenance of all challenged data points
3. Our transparent methodology and open-source implementation
4. Applicable legal protections (First Amendment, anti-SLAPP statute)
5. The public interest served by fiscal transparency
"""


def generate_factual_background(incident: LegalIncident, context: Dict) -> str:
    """Generate factual background section."""
    return f"""## Factual Background

**IBCo Mission:** Independent Budget & Oversight Console (IBCo) is a civic transparency project that analyzes municipal fiscal health using publicly available government documents. We are not affiliated with any government agency.

**Challenged Content:** Your {incident.incident_type.lower()} challenges the following:

{incident.description}

**Our Analysis:** The challenged content is based on:
- Official city financial reports (CAFRs)
- CalPERS actuarial valuations
- State Controller financial disclosures
- Other publicly available government documents

All data is manually entered with complete audit trail. Every data point links to its source document with page numbers.

**Timeline:**
- Data sourced: {context.get('data_source_dates', 'See Data Provenance section')}
- Analysis published: {context.get('publication_date', 'See incident details')}
- {incident.incident_type} received: {incident.date_received.strftime('%B %d, %Y')}
"""


def generate_data_provenance(
    incident: LegalIncident,
    context: Dict,
    db: Session
) -> str:
    """Generate data provenance section with complete source citations."""
    output = ["## Data Provenance\n"]
    output.append("**COMPLETE SOURCE DOCUMENTATION**\n")
    output.append("Every challenged data point is traceable to official government sources:\n")

    # If affected_data_points is specified, look up lineage
    if incident.affected_data_points:
        try:
            affected_ids = json.loads(incident.affected_data_points)
            output.append("### Challenged Data Points\n")

            for data_ref in affected_ids:
                # Query lineage records
                lineage_records = db.query(DataLineage).filter(
                    DataLineage.table_name == data_ref.get('table'),
                    DataLineage.record_id == data_ref.get('record_id')
                ).all()

                if lineage_records:
                    output.append(f"\n**{data_ref.get('description', 'Data Point')}:**\n")
                    for record in lineage_records:
                        source = db.query(DataSource).filter(
                            DataSource.id == record.source_id
                        ).first()

                        if source:
                            output.append(f"- **Source:** {source.name}\n")
                            output.append(f"  - **Organization:** {source.organization}\n")
                            output.append(f"  - **Type:** {source.source_type}\n")
                            if record.source_document_url:
                                output.append(f"  - **URL:** {record.source_document_url}\n")
                            if record.source_document_page:
                                output.append(f"  - **Page:** {record.source_document_page}\n")
                            if record.source_document_section:
                                output.append(f"  - **Section:** {record.source_document_section}\n")
                            output.append(f"  - **Extraction Method:** {record.extraction_method}\n")
                            output.append(f"  - **Extracted:** {record.extracted_at.strftime('%Y-%m-%d')}\n")
                            if record.validated:
                                output.append(f"  - **Validated:** {record.validated_at.strftime('%Y-%m-%d')} by {record.validated_by}\n")
        except (json.JSONDecodeError, AttributeError):
            pass

    # General source information
    output.append("\n### General Data Sources\n")
    output.append("""
All IBCo data derives from official government sources:

1. **Comprehensive Annual Financial Reports (CAFRs)**
   - Published by city finance departments
   - Audited by independent CPA firms
   - Public records under California Public Records Act

2. **CalPERS Actuarial Valuations**
   - Published by California Public Employees' Retirement System
   - Prepared by independent actuaries
   - Public records available at www.calpers.ca.gov

3. **State Controller Reports**
   - Published by California State Controller's Office
   - Cities & Counties Annual Report
   - Public records under Government Code §12463

4. **City Budget Documents**
   - Published by city finance departments
   - Adopted by city councils in public meetings
   - Public records under Brown Act
""")

    return "".join(output)


def generate_methodology_transparency(incident: LegalIncident, context: Dict) -> str:
    """Generate methodology transparency section."""
    return """## Methodology Transparency

**OPEN SOURCE & REPRODUCIBLE**

IBCo methodology is completely transparent and independently verifiable:

1. **Open Source Code**
   - All calculations: GitHub repository (public)
   - Risk scoring algorithms: Documented in METHODOLOGY.md
   - Projection models: Fully documented with assumptions
   - Anyone can audit our math

2. **Documented Assumptions**
   - Pension discount rates
   - Revenue growth assumptions
   - Expenditure trend projections
   - All assumptions documented and justified

3. **Peer Review**
   - Methodology reviewed by municipal finance experts
   - Risk indicators based on academic research
   - Benchmarking follows standard municipal finance practices

4. **Data Quality Controls**
   - Manual data entry with two-person verification
   - Cross-validation with multiple sources
   - Anomaly detection flags for review
   - Complete audit trail (who entered what, when)

**TRANSPARENT LIMITATIONS:**

We explicitly disclose limitations in our DISCLAIMER.md:
- "Risk scores are stress indicators, NOT bankruptcy predictions"
- "Independent analysis, not affiliated with government"
- "Users should independently verify information"
- "No warranties - provided AS IS"

Our transparency distinguishes us from opaque rating agencies.
"""


def generate_disclaimers(incident: LegalIncident, context: Dict) -> str:
    """Generate disclaimers section."""
    return """## Disclaimers & Limitations

**CONSPICUOUS DISCLAIMERS THROUGHOUT SITE:**

IBCo includes prominent disclaimers at multiple levels:

1. **API Root Endpoint** (`/disclaimer`):
   - "Independent analysis, not government-affiliated"
   - "Risk scores are stress indicators, NOT bankruptcy predictions"
   - "No warranties - provided AS IS"
   - "Not financial advice - consult qualified professionals"

2. **Every API Response:**
   - Risk score responses include methodology explanation
   - Projection responses include assumption documentation
   - All responses link to full disclaimer

3. **Website Homepage:**
   - Disclaimer prominently displayed
   - Links to full methodology documentation
   - "Report errors to: data@ibco-ca.us"

4. **Every Report & Visualization:**
   - "Independent analysis - verify independently"
   - "Stress indicators, not predictions"
   - Links to source documents

**LEGAL EFFECT:**

These disclaimers eliminate any reasonable expectation that:
- IBCo is affiliated with government
- Risk scores predict bankruptcy (they measure fiscal stress)
- Data is warranted error-free (we invite corrections)
- Analysis constitutes professional advice (explicitly disclaimed)

No reasonable person could be misled about the nature of our analysis.
"""


def generate_first_amendment_protection(incident: LegalIncident, context: Dict) -> str:
    """Generate First Amendment protection section."""
    return """## First Amendment Protection

**PROTECTED SPEECH ON MATTERS OF PUBLIC CONCERN**

IBCo's fiscal analysis is quintessential First Amendment protected speech:

1. **Public Concern:**
   - Municipal fiscal health affects all residents
   - Pension obligations impact taxpayers
   - Fiscal transparency enables democratic accountability
   - Public has right to know about government finances

2. **Political Speech:**
   - Commentary on government performance
   - Analysis of public policy decisions
   - Critique of fiscal management
   - Core First Amendment protection (New York Times v. Sullivan)

3. **Truthful Information:**
   - Based on official government documents
   - Mathematically accurate calculations
   - Transparent methodology
   - Factual statements protected (Hustler v. Falwell)

4. **No Prior Restraint:**
   - Demanding content removal = prior restraint
   - Presumptively unconstitutional (Near v. Minnesota)
   - Heavy burden to justify censorship
   - Public interest weighs against suppression

**APPLICABLE CASE LAW:**

- *New York Times v. Sullivan*: Public figures face actual malice standard
- *Hustler v. Falwell*: Parody and opinion protected
- *Gertz v. Robert Welch*: Matters of public concern get heightened protection
- *Citizens United*: Political speech receives maximum protection
"""


def generate_anti_slapp_statute(incident: LegalIncident, context: Dict) -> str:
    """Generate anti-SLAPP statute section."""
    return f"""## California Anti-SLAPP Statute (CCP §425.16)

**STRATEGIC LAWSUIT AGAINST PUBLIC PARTICIPATION**

California's anti-SLAPP statute protects speech on matters of public interest:

1. **Statute Applicability:**
   - Protects speech on "public issue" or "issue of public interest"
   - Municipal fiscal health = quintessential public issue
   - IBCo's analysis directly relates to government performance
   - Statute explicitly protects this type of civic analysis

2. **Burden Shifting:**
   - IBCo easily shows speech relates to public issue
   - Burden shifts to plaintiff to show probability of prevailing
   - Plaintiff must overcome First Amendment protections
   - Extremely difficult burden for matters of public concern

3. **Attorney's Fees:**
   - Prevailing anti-SLAPP defendant recovers attorney's fees
   - Discourages frivolous threats against protected speech
   - Makes SLAPP lawsuits expensive for plaintiffs

4. **Special Motion to Strike:**
   - If sued, IBCo will immediately file anti-SLAPP motion
   - Suspends discovery (limiting plaintiff's leverage)
   - Early resolution protecting First Amendment rights

**PRECEDENT:**

California courts consistently protect fiscal transparency:
- Analysis of government finances = protected speech
- Criticism of public officials = protected speech
- Data journalism on public records = protected speech

**NOTICE:**

{incident.sender_name} should carefully consider the anti-SLAPP statute before filing any lawsuit. IBCo will vigorously defend its First Amendment rights and seek attorney's fees under CCP §425.16(c).
"""


def generate_public_interest(incident: LegalIncident, context: Dict) -> str:
    """Generate public interest section."""
    return """## Public Interest

**CIVIC TRANSPARENCY SERVES THE PUBLIC GOOD**

IBCo's fiscal analysis serves compelling public interests:

1. **Democratic Accountability:**
   - Voters need fiscal information to make informed decisions
   - Pension obligations affect future tax burdens
   - Fiscal transparency enables accountability
   - Sunlight = best disinfectant (Justice Brandeis)

2. **Municipal Bond Market:**
   - Bond investors need independent analysis
   - Credit rating agencies failed in 2008 financial crisis
   - Independent civic analysis fills market gap
   - Protects investors from fiscal surprises

3. **Resident Planning:**
   - Residents make decisions based on city fiscal health
   - Property values affected by fiscal stress
   - Service levels depend on fiscal sustainability
   - Right to know about municipal finances

4. **Academic Research:**
   - Researchers use IBCo data for municipal finance studies
   - API enables reproducible research
   - Contributes to understanding of fiscal sustainability
   - Open data benefits scholarship

5. **Journalism:**
   - Local journalists cite IBCo analysis
   - Media coverage improves civic awareness
   - Fourth estate role in democratic society
   - Protected under First Amendment

**SUPPRESSION HARMS PUBLIC:**

Removing IBCo's analysis would:
- Reduce fiscal transparency
- Harm democratic accountability
- Benefit opaque governance
- Contradict California Public Records Act principles
"""


def generate_conclusion(incident: LegalIncident, context: Dict) -> str:
    """Generate conclusion section."""
    return f"""## Conclusion

**SUMMARY OF RESPONSE:**

1. IBCo's fiscal analysis is based entirely on publicly available government documents
2. All data is traceable to official sources with complete lineage
3. Methodology is transparent, open-source, and independently verifiable
4. Prominent disclaimers clarify nature of analysis
5. Speech is protected under First Amendment and California anti-SLAPP statute
6. Analysis serves compelling public interest in fiscal transparency

**NO RETRACTION WARRANTED:**

We respectfully decline to:
- Remove challenged content
- Issue retraction or correction
- Modify our analysis
- Cease fiscal transparency activities

**INVITATION TO DIALOGUE:**

If {incident.sender_name} believes any specific data point is factually inaccurate, we invite submission of:
- Specific claim of inaccuracy
- Correct data with official source citation
- Evidence contradicting our analysis

We take accuracy seriously and will promptly correct any demonstrable errors. However, we will not remove truthful analysis due to legal threats.

**NEXT STEPS:**

If {incident.sender_name} proceeds with litigation, IBCo will:
1. Immediately file anti-SLAPP special motion to strike (CCP §425.16)
2. Vigorously defend First Amendment rights
3. Seek attorney's fees and costs
4. Publicly disclose legal threats (Streisand Effect)
5. Contact EFF/ACLU for potential amicus support

We hope this response clarifies the legal and factual basis for our analysis.

Respectfully,

**Independent Budget & Oversight Console**
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

**NOTICE:** This is a DRAFT response generated by automated template.
**MUST BE REVIEWED BY QUALIFIED LEGAL COUNSEL BEFORE SENDING.**
"""


# ============================================================================
# Main Generator
# ============================================================================


def generate_response(
    incident_id: int,
    template_name: str,
    include_lineage: bool = False,
    output_format: str = "markdown",
    db: Session = None
) -> str:
    """Generate anti-SLAPP response for legal incident."""

    # Get incident from database
    incident = db.query(LegalIncident).filter(LegalIncident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Legal incident #{incident_id} not found")

    # Get template
    template = TEMPLATE_REGISTRY.get(template_name)
    if not template:
        raise ValueError(
            f"Template '{template_name}' not found. "
            f"Available: {', '.join(TEMPLATE_REGISTRY.keys())}"
        )

    # Build context
    context = {
        "incident_id": incident_id,
        "template_name": template_name,
        "generated_at": datetime.utcnow(),
        "include_lineage": include_lineage,
    }

    # Section generators
    section_generators = {
        "introduction": generate_introduction,
        "factual_background": generate_factual_background,
        "data_provenance": lambda i, c: generate_data_provenance(i, c, db),
        "methodology_transparency": generate_methodology_transparency,
        "disclaimers": generate_disclaimers,
        "first_amendment_protection": generate_first_amendment_protection,
        "anti_slapp_statute": generate_anti_slapp_statute,
        "public_interest": generate_public_interest,
        "conclusion": generate_conclusion,
        # Aliases
        "legal_analysis": lambda i, c: generate_first_amendment_protection(i, c) + "\n\n" + generate_anti_slapp_statute(i, c),
        "truth_defense": lambda i, c: generate_data_provenance(i, c, db),
        "no_actual_malice": lambda i, c: "## No Actual Malice\n\nIBCo had no knowledge of falsity and no reckless disregard for truth. All analysis based on official government documents with transparent methodology.",
        "no_retraction_warranted": lambda i, c: "## No Retraction Warranted\n\nAfter careful review, we find no factual errors warranting retraction. Our analysis is accurate, properly sourced, and serves the public interest.",
        "incident_summary": lambda i, c: f"## Incident Summary\n\n{incident.description}",
        "first_amendment_implications": lambda i, c: generate_first_amendment_protection(i, c),
        "request_for_support": lambda i, c: "## Request for Support\n\nWe request EFF/ACLU support in defending First Amendment rights and fiscal transparency."
    }

    # Generate response
    output = []

    # Header
    subject = template["subject"].format(
        incident_type=incident.incident_type,
        date_received=incident.date_received.strftime('%B %d, %Y')
    )
    output.append(f"# {subject}\n")
    output.append(f"**Template:** {template['name']}\n")
    output.append(f"**Incident ID:** {incident_id}\n")
    output.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
    output.append("\n---\n\n")
    output.append("**⚠️ DRAFT RESPONSE - REQUIRES LEGAL COUNSEL REVIEW ⚠️**\n\n")
    output.append("---\n\n")

    # Generate sections
    for section_name in template["sections"]:
        generator = section_generators.get(section_name)
        if generator:
            try:
                section_content = generator(incident, context)
                output.append(section_content)
                output.append("\n\n")
            except Exception as e:
                output.append(f"## {section_name.replace('_', ' ').title()}\n\n")
                output.append(f"*Error generating section: {e}*\n\n")

    return "".join(output)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate anti-SLAPP response for legal incident",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available Templates:
{chr(10).join(f'  - {name}: {info["name"]}' for name, info in TEMPLATE_REGISTRY.items())}

Examples:
  # Generate anti-SLAPP motion response
  python scripts/legal/generate_anti_slapp_response.py \\
      --incident-id 42 \\
      --template AntiSLAPP \\
      --include-lineage \\
      --output-file response_draft.md

  # Generate cease-and-desist response
  python scripts/legal/generate_anti_slapp_response.py \\
      --incident-id 42 \\
      --template CeaseAndDesistResponse \\
      --output-file response.md

  # Generate EFF notification
  python scripts/legal/generate_anti_slapp_response.py \\
      --incident-id 42 \\
      --template EFFNotification \\
      --output-file eff_notification.md
        """,
    )

    parser.add_argument(
        "--incident-id",
        type=int,
        required=True,
        help="Legal incident ID from database",
    )

    parser.add_argument(
        "--template",
        required=True,
        choices=list(TEMPLATE_REGISTRY.keys()),
        help="Response template to use",
    )

    parser.add_argument(
        "--include-lineage",
        action="store_true",
        help="Include complete data lineage citations (slow, comprehensive)",
    )

    parser.add_argument(
        "--output-format",
        choices=["markdown", "text"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    try:
        # Get database session
        with get_session() as db:
            # Generate response
            print(f"Generating {args.template} response for incident #{args.incident_id}...", file=sys.stderr)

            response = generate_response(
                incident_id=args.incident_id,
                template_name=args.template,
                include_lineage=args.include_lineage,
                output_format=args.output_format,
                db=db
            )

            # Output
            if args.output_file:
                args.output_file.write_text(response)
                print(f"\n✅ Response generated: {args.output_file}", file=sys.stderr)
            else:
                print(response)

            print("\n⚠️  IMPORTANT: This is a DRAFT response.", file=sys.stderr)
            print("Review by qualified legal counsel required before sending.\n", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"\n❌ Error generating response: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
