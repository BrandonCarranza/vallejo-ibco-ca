# Dead Man's Switch Integration with Legal Defense System

**Status:** Planned (Wave 2, Prompt 8.3)
**Integration Points:** Documented for future implementation
**Priority:** High (core suppression-resistance mechanism)

---

## Overview

The legal defense system (Prompt 11.3) is designed to integrate with the dead man's switch system (Prompt 8.3). This integration makes legal suppression attempts counterproductive by triggering accelerated data publication.

---

## Integration Architecture

### Data Flow

```
Legal Incident Logged
    ↓
triggers_dead_mans_switch = True?
    ↓ YES
Reduce Dead Man's Switch Timer
    (30 days → 7 days)
    ↓
Operator Misses Check-in?
    ↓ YES
Auto-Publish Full Dataset + Legal Docs
    ↓
Streisand Effect Activated
```

### Key Principle

**Suppression attempts should trigger immediate transparency escalation.**

- Normal operation: 30-day dead man's switch timer
- Legal threat logged: Reduce to 7-day timer
- SLAPP lawsuit filed: Option for immediate publication
- Operator incapacitated: Auto-publish within reduced timer

---

## Database Integration

### Legal Incident Fields

**Already Implemented in `src/database/models/legal.py`:**

```python
class LegalIncident(Base, AuditMixin):
    # ...

    # Dead-Man's Switch Integration
    triggers_dead_mans_switch = Column(
        Boolean, nullable=False, default=False
    )  # Does this incident reduce timer?

    dead_mans_switch_triggered_date = Column(
        DateTime, nullable=True
    )  # When was timer reduced?

    dead_mans_switch_reduced_to_days = Column(
        Integer, nullable=True
    )  # New timer value (e.g., 7 days)
```

### When to Set `triggers_dead_mans_switch = True`

**Criteria:**
- SLAPP lawsuit filed
- Cease-and-desist from powerful entity (city, pension fund, etc.)
- Pattern of harassment/intimidation
- Subpoena seeking to identify sources
- Criminal charges against operators
- Government shutdown orders

**Criteria for False (don't trigger):**
- Anonymous threats (no credibility)
- Obvious spam/crank letters
- Isolated cease-and-desist from individual (not org)
- Requests for correction (not suppression demands)

---

## API Integration Points

### When Legal Incident Created/Updated

**File:** `src/api/v1/routes/admin/legal_incidents.py`

**Integration Point 1: Create Legal Incident**

```python
@router.post("", response_model=LegalIncidentResponse, status_code=201)
async def create_legal_incident(
    incident: LegalIncidentCreate,
    db: Session = Depends(get_db)
):
    """Log a new legal incident."""

    # Create incident
    db_incident = LegalIncident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # TODO: INTEGRATE WITH DEAD MAN'S SWITCH (Prompt 8.3)
    if db_incident.triggers_dead_mans_switch:
        # Reduce timer to 7 days
        reduce_dead_mans_switch_timer(
            incident_id=db_incident.id,
            reduced_days=7,
            reason=f"Legal incident {db_incident.incident_type} logged by {db_incident.sender_name}"
        )

        # Update incident record with trigger date
        db_incident.dead_mans_switch_triggered_date = datetime.utcnow()
        db_incident.dead_mans_switch_reduced_to_days = 7
        db.commit()

    # TODO: INTEGRATE WITH NOTIFICATIONS (existing stakeholder system)
    # Send alert to legal counsel, EFF/ACLU contacts, board
    send_legal_incident_alert(db_incident)

    return db_incident
```

**Integration Point 2: Update Legal Incident**

```python
@router.patch("/{incident_id}", response_model=LegalIncidentResponse)
async def update_legal_incident(
    incident_id: int,
    update: LegalIncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update legal incident."""

    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    # Check if triggers_dead_mans_switch changed from False → True
    old_trigger_status = incident.triggers_dead_mans_switch

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    # TODO: INTEGRATE WITH DEAD MAN'S SWITCH (Prompt 8.3)
    # If trigger status changed from False to True, reduce timer now
    if not old_trigger_status and incident.triggers_dead_mans_switch:
        reduce_dead_mans_switch_timer(
            incident_id=incident.id,
            reduced_days=7,
            reason=f"Legal incident escalated to dead-man's switch trigger"
        )

        incident.dead_mans_switch_triggered_date = datetime.utcnow()
        incident.dead_mans_switch_reduced_to_days = 7
        db.commit()

    return incident
```

---

## Dead Man's Switch Functions (To Be Implemented)

### Function Signatures

**File:** `src/services/dead_mans_switch.py` (to be created in Prompt 8.3)

```python
from datetime import datetime, timedelta
from typing import Optional

def reduce_dead_mans_switch_timer(
    incident_id: int,
    reduced_days: int,
    reason: str
) -> None:
    """
    Reduce dead-man's switch timer in response to legal incident.

    Args:
        incident_id: Legal incident database ID
        reduced_days: New timer value (e.g., 7 days)
        reason: Explanation for reduction (logged)

    Effects:
        - Updates dead-man's switch configuration
        - Sets new check-in deadline
        - Logs reduction event
        - Sends notification to operators

    Example:
        reduce_dead_mans_switch_timer(
            incident_id=42,
            reduced_days=7,
            reason="SLAPP lawsuit filed by City of Example"
        )
    """
    # TODO: Implement in Prompt 8.3
    pass


def get_dead_mans_switch_status() -> dict:
    """
    Get current dead-man's switch status.

    Returns:
        {
            "active": True/False,
            "timer_days": 30 or 7 (current setting),
            "last_checkin": datetime,
            "next_checkin_due": datetime,
            "countdown_started": True/False,
            "countdown_expires": datetime or None,
            "reduced_due_to_legal_incident": True/False,
            "triggering_incident_id": int or None
        }
    """
    # TODO: Implement in Prompt 8.3
    pass


def prepare_immediate_publication(
    trigger: str,
    publication_scope: str = "full_dataset_with_legal_docs"
) -> None:
    """
    Prepare for immediate data publication (emergency measure).

    Use when: SLAPP lawsuit filed, operator arrested, forced shutdown

    Args:
        trigger: Reason for immediate publication
        publication_scope: What to publish
            - "full_dataset_with_legal_docs": Everything + legal incident log
            - "dataset_only": Data without legal docs
            - "minimal": Essential data only

    Effects:
        - Generates publication package
        - Uploads to multiple destinations
        - Notifies media contacts
        - Sends community takeover instructions
        - Activates Streisand Effect
    """
    # TODO: Implement in Prompt 8.3
    pass


def get_publication_package_contents() -> dict:
    """
    Get list of files that will be published if dead-man's switch activates.

    Returns:
        {
            "dataset": ["municipalities.json", "risk_scores.json", ...],
            "source_documents": ["cafrs/*.pdf", "calpers/*.pdf", ...],
            "methodology": ["METHODOLOGY.md", "src/**/*.py", ...],
            "legal_defense": ["legal_incidents.json", "responses/*.md", ...],
            "operational": ["MIRROR_INSTRUCTIONS.md", "REBUILD_GUIDE.md"]
        }
    """
    # TODO: Implement in Prompt 8.3
    pass
```

---

## Integration Testing

### Test Scenarios

**Scenario 1: Legal Incident Triggers Dead Man's Switch**

```python
def test_legal_incident_triggers_dead_mans_switch():
    """Test that logging legal incident reduces timer."""

    # Create legal incident with trigger = True
    incident = create_legal_incident(
        incident_type="SLAPPLawsuit",
        triggers_dead_mans_switch=True,
        sender_name="City of Example"
    )

    # Verify dead man's switch timer reduced
    dms_status = get_dead_mans_switch_status()
    assert dms_status["timer_days"] == 7  # Reduced from 30
    assert dms_status["reduced_due_to_legal_incident"] == True
    assert dms_status["triggering_incident_id"] == incident.id

    # Verify incident record updated
    assert incident.dead_mans_switch_triggered_date is not None
    assert incident.dead_mans_switch_reduced_to_days == 7
```

**Scenario 2: Update Incident to Trigger Dead Man's Switch**

```python
def test_update_incident_triggers_dead_mans_switch():
    """Test that updating incident to trigger=True reduces timer."""

    # Create incident without trigger
    incident = create_legal_incident(
        incident_type="CeaseAndDesist",
        triggers_dead_mans_switch=False
    )

    # Verify timer not affected
    dms_status = get_dead_mans_switch_status()
    assert dms_status["timer_days"] == 30  # Normal

    # Update incident to trigger dead man's switch
    update_legal_incident(
        incident_id=incident.id,
        update={"triggers_dead_mans_switch": True}
    )

    # Verify timer now reduced
    dms_status = get_dead_mans_switch_status()
    assert dms_status["timer_days"] == 7  # Reduced
```

**Scenario 3: Immediate Publication for Severe Threats**

```python
def test_immediate_publication_for_severe_threat():
    """Test immediate publication option for severe legal threats."""

    # Create high-severity SLAPP lawsuit
    incident = create_legal_incident(
        incident_type="SLAPPLawsuit",
        severity="Critical",
        triggers_dead_mans_switch=True
    )

    # Operator decides to trigger immediate publication
    prepare_immediate_publication(
        trigger=f"SLAPP lawsuit filed by {incident.sender_name}",
        publication_scope="full_dataset_with_legal_docs"
    )

    # Verify publication package prepared
    package = get_publication_package_contents()
    assert "legal_incidents.json" in package["legal_defense"]
    assert incident.id in get_published_legal_incidents()
```

---

## Publication Package Specifications

### What Gets Published

When dead-man's switch activates (due to legal incident or operator absence):

**1. Complete IBCo Dataset**
- `data/export/municipalities.json` - All city data
- `data/export/risk_scores.json` - All risk scores
- `data/export/projections.json` - All fiscal projections
- `data/export/data_lineage.json` - Complete provenance records

**2. Source Documents**
- `source_documents/cafrs/*.pdf` - All CAFRs
- `source_documents/calpers/*.pdf` - All CalPERS reports
- `source_documents/index.json` - Document catalog

**3. Methodology & Code**
- `METHODOLOGY.md` - Full methodology documentation
- `src/**/*.py` - Complete source code (GitHub mirror)
- `calculations/*.xlsx` - Calculation worksheets
- `peer_review/*.pdf` - Peer review documentation

**4. Legal Defense Documentation**
- `legal/incidents.json` - All legal incidents (public record)
- `legal/responses/*.md` - IBCo responses to threats
- `legal/source_citations/*.md` - Data provenance documentation
- `legal/README.md` - Explanation of suppression attempt

**5. Operational Continuity**
- `MIRROR_INSTRUCTIONS.md` - How to mirror IBCo
- `REBUILD_GUIDE.md` - How to rebuild from published data
- `COMMUNITY_TAKEOVER.md` - How community can continue IBCo
- `CONTACTS.md` - List of supporters to notify

### Publication Destinations

**Primary:**
1. **GitHub** - Public repository (instant, widely accessible)
2. **Archive.org** - Permanent archival (cannot be deleted)
3. **Distributed Mirrors** - Civic tech community volunteers

**Secondary:**
4. **Torrents** - Decentralized distribution (censorship-resistant)
5. **IPFS** - Distributed file system (permanent availability)

**Media Notification:**
6. **Journalists** - Send publication links to pre-configured media contacts
7. **Researchers** - Notify academic users of IBCo data
8. **Civic Organizations** - Alert transparency advocates

### Automation

**Publication Scripts** (to be created in Prompt 8.3):

```bash
# Generate publication package
scripts/maintenance/generate_publication_package.py

# Upload to all destinations
scripts/maintenance/publish_dead_mans_switch.py --reason "Legal threat"

# Notify community
scripts/communications/send_dead_mans_switch_alert.py
```

---

## Notification Integration

### Legal Incident Alerts

**Stakeholder Notification System** (already exists from Prompt 11.2)

When legal incident logged, send notifications to:

1. **Legal Counsel** (if retained)
   - Incident details
   - Link to database record
   - Request for review/advice

2. **EFF/ACLU Contacts** (if high severity)
   - Incident summary
   - First Amendment implications
   - Request for potential support

3. **IBCo Board/Advisors**
   - Incident notification
   - Dead-man's switch status
   - Action items

4. **Insurance Carrier** (if applicable)
   - Claims notification
   - Incident documentation
   - Request for defense counsel

**Integration Point:**

```python
def send_legal_incident_alert(incident: LegalIncident) -> None:
    """
    Send notifications about legal incident to stakeholders.

    Uses existing stakeholder notification system (Prompt 11.2).
    """

    # Notify legal counsel
    if incident.severity in ["High", "Critical"]:
        create_notification(
            subscriber_category="LegalCounsel",
            notification_type="LegalThreat",
            severity="High",
            subject=f"Legal Incident: {incident.incident_type}",
            content=f"Legal incident logged: {incident.subject}. Review required.",
            related_url=f"/admin/legal-incidents/{incident.id}"
        )

    # Notify EFF/ACLU if First Amendment implications
    if incident.first_amendment_protected:
        create_notification(
            subscriber_category="LegalAdvocacy",
            notification_type="FirstAmendmentThreat",
            severity="High",
            subject="First Amendment Legal Threat",
            content=f"IBCo facing legal threat with First Amendment implications. Support may be needed.",
            related_url=f"/admin/legal-incidents/{incident.id}"
        )

    # Always notify board
    create_notification(
        subscriber_category="Board",
        notification_type="LegalIncident",
        severity=incident.severity,
        subject=f"Legal Incident Logged: {incident.incident_type}",
        content=incident.description,
        related_url=f"/admin/legal-incidents/{incident.id}"
    )
```

---

## Streisand Effect Coordination

### Activation Triggers

**When to Activate Streisand Effect:**

1. **SLAPP lawsuit filed** → Immediate press release
2. **High-profile cease-and-desist** → Public transparency report
3. **Pattern of harassment** → Media engagement
4. **Dead-man's switch activated** → Full publication + media blitz

### Coordination with Transparency Reports

**Quarterly Transparency Reports** (implemented in Prompt 11.3):

```bash
# Generate report including legal incidents
python scripts/reports/legal_incident_report.py --period Q1-2025
```

**Ad-Hoc Reports for Newsworthy Events:**

```bash
# Special report for SLAPP lawsuit
python scripts/reports/legal_incident_report.py \
    --incident-id 42 \
    --special-report \
    --output-file press_releases/slapp_lawsuit_response.md
```

### Media Engagement Protocol

**Prepared Statements** (templates):
- `docs/legal/press_release_slapp_lawsuit.md`
- `docs/legal/press_release_dead_mans_switch_activated.md`
- `docs/legal/media_statement_legal_threat.md`

**Media Contact List** (maintained in stakeholder system):
- Investigative journalists covering municipal finance
- Tech reporters (civic tech beat)
- First Amendment advocates
- Government transparency specialists

---

## Future Enhancements (Post-Prompt 8.3)

### Advanced Features

1. **Gradual Escalation**
   - Day 0: Legal incident logged → Reduce timer to 7 days
   - Day 3: No operator check-in → Send warnings
   - Day 7: Timer expires → Auto-publish dataset
   - Day 10: Still no check-in → Notify media, trigger Streisand Effect

2. **Multiple Timer Levels**
   - Level 1 (Normal): 30-day timer
   - Level 2 (Legal threat): 7-day timer
   - Level 3 (SLAPP lawsuit): 3-day timer
   - Level 4 (Operator arrest): Immediate publication

3. **Community Verification**
   - Distributed check-in system
   - Multiple operators must all miss check-in
   - Prevents false positives (one operator on vacation)

4. **Selective Publication**
   - Publish only challenged data points initially
   - Full dataset publication only if timer fully expires
   - Graduated response approach

### Integration with Other Systems

- **GitHub Actions**: Automated publication workflows
- **Archive.org**: Permanent archival integration
- **IPFS**: Decentralized storage
- **Email Lists**: Automated community notifications
- **Social Media**: Auto-post to Twitter/Mastodon

---

## Summary

### Current Status (Prompt 11.3 Complete)

✅ Legal incident database models with dead-man's switch fields
✅ API endpoints for logging legal incidents
✅ Integration points documented (this file)
✅ Placeholder functions for dead-man's switch calls

### Next Steps (Prompt 8.3 - Dead Man's Switch Implementation)

1. Implement `reduce_dead_mans_switch_timer()` function
2. Implement `get_dead_mans_switch_status()` function
3. Implement `prepare_immediate_publication()` function
4. Create publication package generation scripts
5. Build automated upload/distribution system
6. Integrate check-in mechanism
7. Test end-to-end workflow
8. Document community takeover procedures

### Integration Checklist for Prompt 8.3

When implementing dead-man's switch (Prompt 8.3), integrate with legal defense:

- [ ] Call `reduce_dead_mans_switch_timer()` when legal incident logged
- [ ] Update legal incident record with trigger date and reduced timer
- [ ] Include legal incident log in publication package
- [ ] Add legal defense docs to publication package
- [ ] Send notifications to legal counsel/EFF/ACLU
- [ ] Coordinate with transparency reporting system
- [ ] Test SLAPP lawsuit scenario end-to-end
- [ ] Document emergency publication procedures
- [ ] Prepare media contact templates
- [ ] Set up distributed mirrors

---

**Document Status:** Integration Specification
**Implementation Status:** Pending (Wave 2, Prompt 8.3)
**Owner:** Dead Man's Switch Implementation Team
**Reviewer:** Legal Defense Team
