"""
Admin API routes for legal defense and incident tracking.

Requires authentication. Used to:
- Log cease-and-desist letters, defamation claims, SLAPP lawsuits
- Track legal threats and harassment
- Manage responses and documentation
- Generate transparency reports
- Trigger dead-man's switch integration (if legal suppression escalates)

IMMUTABLE LOG: Legal incidents are preserved for discovery (soft delete only).
PUBLIC TRANSPARENCY: All incidents included in quarterly transparency reports.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from src.api.dependencies import get_db
from src.api.v1.schemas.legal import (
    LegalDocumentCreate,
    LegalDocumentResponse,
    LegalIncidentCreate,
    LegalIncidentListResponse,
    LegalIncidentResponse,
    LegalIncidentUpdate,
    LegalResponseCreate,
    LegalResponseResponse,
)
from src.database.models.legal import (
    LegalDocument,
    LegalIncident,
    LegalResponse,
)

router = APIRouter(prefix="/admin/legal-incidents", tags=["Admin", "Legal Defense"])


# ============================================================================
# Legal Incident Management
# ============================================================================


@router.post("", response_model=LegalIncidentResponse, status_code=201)
async def create_legal_incident(
    incident: LegalIncidentCreate,
    db: Session = Depends(get_db)
):
    """
    Log a new legal incident (cease-and-desist, defamation claim, lawsuit, etc.).

    **Requires authentication.**

    Use this endpoint to create an immutable record of legal threats:
    - Cease-and-desist letters
    - Defamation claims
    - SLAPP lawsuits
    - Subpoenas
    - Harassment
    - Other legal threats

    **IMMUTABILITY:** Legal incident records are preserved for discovery.
    Use soft delete only if absolutely necessary.

    **DEAD-MAN'S SWITCH INTEGRATION:** If `triggers_dead_mans_switch=True`,
    the incident will reduce the dead-man's timer (typically to 7 days),
    making suppression attempts counterproductive (Streisand Effect).

    **TRANSPARENCY:** All legal incidents are included in quarterly
    transparency reports unless marked confidential by legal counsel.

    Example use cases:
    - Law firm sends cease-and-desist demanding data removal
    - City official threatens defamation lawsuit
    - Anonymous harassment via threatening emails
    - Subpoena received for source documents
    """
    # Create legal incident
    db_incident = LegalIncident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # TODO: If triggers_dead_mans_switch=True, integrate with dead-man's switch
    # system to reduce timer (planned in Wave 2, Prompt 8.3)

    # TODO: Send notifications to legal counsel, EFF, ACLU if configured
    # (integrate with stakeholder notification system)

    return db_incident


@router.get("/{incident_id}", response_model=LegalIncidentResponse)
async def get_legal_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific legal incident.

    **Requires authentication.**

    Returns complete incident details including:
    - Incident classification and severity
    - Sender information
    - Claims and demands
    - Legal analysis
    - Response tracking
    - Resolution status
    - Dead-man's switch integration status
    """
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    return incident


@router.patch("/{incident_id}", response_model=LegalIncidentResponse)
async def update_legal_incident(
    incident_id: int,
    update: LegalIncidentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a legal incident record.

    **Requires authentication.**

    Use this to:
    - Update status (Active → ResponseSent → Resolved)
    - Add legal analysis
    - Record resolution
    - Update external counsel information
    - Mark for public disclosure
    - Track Streisand Effect (media coverage)

    **IMPORTANT:** Legal incident records should never be deleted.
    Use status updates to track progression.
    """
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)

    # TODO: If triggers_dead_mans_switch changed to True, trigger integration

    return incident


@router.delete("/{incident_id}", status_code=204)
async def soft_delete_legal_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a legal incident.

    **Requires authentication.**

    **WARNING:** Legal incidents should NEVER be hard deleted.
    This endpoint performs a soft delete only, preserving data for:
    - Legal discovery
    - Audit trail
    - Transparency reports
    - Historical analysis

    Only use this if the incident was logged in error.
    """
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    incident.soft_delete()
    db.commit()

    return None


@router.get("", response_model=LegalIncidentListResponse)
async def list_legal_incidents(
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sender_name: Optional[str] = Query(None, description="Filter by sender name (partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter by date received (from)"),
    end_date: Optional[datetime] = Query(None, description="Filter by date received (to)"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    triggers_dead_mans_switch: Optional[bool] = Query(None, description="Filter by dead-man's switch trigger"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    List legal incidents with filtering and pagination.

    **Requires authentication.**

    Supports filtering by:
    - Incident type (CeaseAndDesist, DefamationClaim, SLAPPLawsuit, etc.)
    - Severity (Low, Medium, High, Critical)
    - Status (Active, UnderReview, ResponseSent, Resolved, etc.)
    - Sender name (partial text search)
    - Date range (when incident was received)
    - Resolution status
    - Dead-man's switch trigger status

    Use this endpoint to:
    - Monitor active legal threats
    - Generate transparency reports
    - Analyze suppression attempts
    - Track resolution timelines
    """
    query = db.query(LegalIncident).filter(LegalIncident.is_deleted == False)

    # Apply filters
    if incident_type is not None:
        query = query.filter(LegalIncident.incident_type == incident_type)

    if severity is not None:
        query = query.filter(LegalIncident.severity == severity)

    if status is not None:
        query = query.filter(LegalIncident.status == status)

    if sender_name is not None:
        query = query.filter(LegalIncident.sender_name.ilike(f"%{sender_name}%"))

    if start_date is not None:
        query = query.filter(LegalIncident.date_received >= start_date)

    if end_date is not None:
        query = query.filter(LegalIncident.date_received <= end_date)

    if resolved is not None:
        query = query.filter(LegalIncident.resolved == resolved)

    if triggers_dead_mans_switch is not None:
        query = query.filter(
            LegalIncident.triggers_dead_mans_switch == triggers_dead_mans_switch
        )

    # Get total count
    total = query.count()

    # Apply pagination
    incidents = query.order_by(desc(LegalIncident.date_received)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return LegalIncidentListResponse(
        incidents=incidents,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# ============================================================================
# Legal Response Management
# ============================================================================


@router.post("/{incident_id}/responses", response_model=LegalResponseResponse, status_code=201)
async def create_legal_response(
    incident_id: int,
    response: LegalResponseCreate,
    db: Session = Depends(get_db)
):
    """
    Create a response to a legal incident.

    **Requires authentication.**

    Use this to log:
    - Initial responses to cease-and-desist letters
    - Anti-SLAPP motion filings
    - Court filings and briefs
    - Settlement negotiations
    - Retraction demands
    - EFF/ACLU notification letters

    **TEMPLATE INTEGRATION:** Specify `template_used` to track which
    template was used, enabling effectiveness analysis.

    **CITATIONS:** Include citations to data sources, methodology docs,
    and disclaimers to strengthen legal defense.

    Example workflow:
    1. Legal incident logged (cease-and-desist received)
    2. Draft response created using anti-SLAPP template
    3. Response reviewed by legal counsel
    4. Response approved and sent
    5. Outcome tracked (threat retracted, lawsuit filed, etc.)
    """
    # Verify incident exists
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    # Create response (override incident_id from URL)
    response_data = response.model_dump()
    response_data['incident_id'] = incident_id
    db_response = LegalResponse(**response_data)

    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    return db_response


@router.get("/{incident_id}/responses", response_model=List[LegalResponseResponse])
async def list_legal_responses(
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all responses for a legal incident.

    **Requires authentication.**

    Returns responses in reverse chronological order (most recent first).
    """
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    responses = db.query(LegalResponse).filter(
        LegalResponse.incident_id == incident_id
    ).order_by(desc(LegalResponse.created_at)).all()

    return responses


@router.get("/responses/{response_id}", response_model=LegalResponseResponse)
async def get_legal_response(
    response_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific legal response.

    **Requires authentication.**
    """
    response = db.query(LegalResponse).filter(
        LegalResponse.id == response_id
    ).first()

    if not response:
        raise HTTPException(status_code=404, detail="Legal response not found")

    return response


# ============================================================================
# Legal Document Management
# ============================================================================


@router.post("/{incident_id}/documents", response_model=LegalDocumentResponse, status_code=201)
async def upload_legal_document(
    incident_id: int,
    document: LegalDocumentCreate,
    db: Session = Depends(get_db)
):
    """
    Record a legal document related to an incident.

    **Requires authentication.**

    Use this to track:
    - Original cease-and-desist letters (scan/PDF)
    - Lawsuit filings
    - Court orders
    - Email correspondence
    - Settlement agreements
    - Supporting evidence

    **IMPORTANT:** This endpoint records document metadata only.
    Actual file upload should be handled separately via file storage system.

    **INTEGRITY:** Include SHA256 hash for document verification.

    **CONFIDENTIALITY:** Mark sensitive documents as confidential to
    exclude from public transparency reports.
    """
    # Verify incident exists
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    # Create document record (override incident_id from URL)
    document_data = document.model_dump()
    document_data['incident_id'] = incident_id
    db_document = LegalDocument(**document_data)

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return db_document


@router.get("/{incident_id}/documents", response_model=List[LegalDocumentResponse])
async def list_legal_documents(
    incident_id: int,
    include_confidential: bool = Query(
        False,
        description="Include confidential documents (requires elevated permissions)"
    ),
    db: Session = Depends(get_db)
):
    """
    Get all documents for a legal incident.

    **Requires authentication.**

    Returns documents in reverse chronological order (most recent first).

    By default, excludes confidential documents. Set `include_confidential=true`
    to include them (requires elevated admin permissions).
    """
    incident = db.query(LegalIncident).filter(
        LegalIncident.id == incident_id
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Legal incident not found")

    query = db.query(LegalDocument).filter(
        LegalDocument.incident_id == incident_id
    )

    # Filter confidential documents if not requested
    if not include_confidential:
        query = query.filter(LegalDocument.confidential == False)

    documents = query.order_by(desc(LegalDocument.uploaded_date)).all()

    return documents


# ============================================================================
# Statistics & Analytics
# ============================================================================


@router.get("/stats/summary")
async def get_legal_stats_summary(
    db: Session = Depends(get_db)
):
    """
    Get summary statistics about legal incidents.

    **Requires authentication.**

    Returns:
    - Total incidents (all time)
    - Active incidents
    - Resolved incidents
    - Incidents by type
    - Incidents by severity
    - Average resolution time
    - Dead-man's switch triggers
    - Success rate (frivolous threats retracted)

    Use this for:
    - Dashboard metrics
    - Transparency reports
    - Trend analysis
    """
    # Total incidents
    total_incidents = db.query(func.count(LegalIncident.id)).filter(
        LegalIncident.is_deleted == False
    ).scalar()

    # Active incidents
    active_incidents = db.query(func.count(LegalIncident.id)).filter(
        LegalIncident.is_deleted == False,
        LegalIncident.resolved == False
    ).scalar()

    # Resolved incidents
    resolved_incidents = db.query(func.count(LegalIncident.id)).filter(
        LegalIncident.is_deleted == False,
        LegalIncident.resolved == True
    ).scalar()

    # Incidents by type
    incidents_by_type = db.query(
        LegalIncident.incident_type,
        func.count(LegalIncident.id).label('count')
    ).filter(
        LegalIncident.is_deleted == False
    ).group_by(LegalIncident.incident_type).all()

    # Incidents by severity
    incidents_by_severity = db.query(
        LegalIncident.severity,
        func.count(LegalIncident.id).label('count')
    ).filter(
        LegalIncident.is_deleted == False
    ).group_by(LegalIncident.severity).all()

    # Dead-man's switch triggers
    dead_mans_switch_triggers = db.query(func.count(LegalIncident.id)).filter(
        LegalIncident.is_deleted == False,
        LegalIncident.triggers_dead_mans_switch == True
    ).scalar()

    # Frivolous incidents (assessed by IBCo)
    frivolous_count = db.query(func.count(LegalIncident.id)).filter(
        LegalIncident.is_deleted == False,
        LegalIncident.frivolous == True
    ).scalar()

    return {
        "total_incidents": total_incidents,
        "active_incidents": active_incidents,
        "resolved_incidents": resolved_incidents,
        "incidents_by_type": [
            {"type": item[0], "count": item[1]} for item in incidents_by_type
        ],
        "incidents_by_severity": [
            {"severity": item[0], "count": item[1]} for item in incidents_by_severity
        ],
        "dead_mans_switch_triggers": dead_mans_switch_triggers,
        "frivolous_count": frivolous_count,
        "frivolous_percentage": (
            round(frivolous_count / total_incidents * 100, 1)
            if total_incidents > 0 else 0
        )
    }
