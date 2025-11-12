"""
Pydantic schemas for legal defense and incident tracking API.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Legal Incident Schemas
# ============================================================================


class LegalIncidentBase(BaseModel):
    """Base legal incident schema."""

    incident_type: str = Field(
        ...,
        max_length=50,
        description="CeaseAndDesist, DefamationClaim, SLAPPLawsuit, Subpoena, Harassment, Other"
    )
    severity: str = Field(
        "Medium",
        max_length=20,
        description="Low, Medium, High, Critical"
    )
    status: str = Field(
        "Active",
        max_length=30,
        description="Active, UnderReview, ResponseSent, Resolved, Escalated, Litigation"
    )

    # Sender Information
    sender_name: str = Field(..., max_length=255, description="Individual or organization")
    sender_organization: Optional[str] = Field(None, max_length=255)
    sender_legal_counsel: Optional[str] = Field(None, max_length=255)
    sender_address: Optional[str] = Field(None)
    sender_email: Optional[str] = Field(None, max_length=255)
    sender_phone: Optional[str] = Field(None, max_length=50)

    # Incident Details
    date_received: datetime = Field(..., description="When IBCo received the threat")
    date_sent_by_sender: Optional[datetime] = Field(None, description="Date on original letter")
    delivery_method: str = Field(
        ...,
        max_length=50,
        description="Email, CertifiedMail, ProcessServer, InPerson"
    )

    subject: str = Field(..., max_length=500, description="Brief description")
    description: str = Field(..., description="Full details of allegations/claims")

    # Claims & Demands
    claims_made: Optional[str] = Field(None, description="Specific claims")
    demands: Optional[str] = Field(None, description="What they're demanding")
    deadline: Optional[datetime] = Field(None, description="Deadline for response")

    # Affected Data
    affected_data_points: Optional[str] = Field(None, description="JSON list of affected records")
    affected_reports: Optional[str] = Field(None, description="Which reports/pages challenged")
    affected_cities: Optional[str] = Field(None, max_length=255)

    # Legal Analysis
    frivolous: bool = Field(False, description="IBCo assessment")
    anti_slapp_applicable: Optional[bool] = Field(None)
    first_amendment_protected: Optional[bool] = Field(None)
    legal_merit_assessment: Optional[str] = Field(None, max_length=20)
    legal_analysis_notes: Optional[str] = Field(None)

    # Response Tracking
    response_required: bool = Field(True)
    response_sent: bool = Field(False)
    response_sent_date: Optional[datetime] = Field(None)
    response_sent_by: Optional[str] = Field(None, max_length=255)

    # Resolution
    resolved: bool = Field(False)
    resolved_date: Optional[datetime] = Field(None)
    resolution_type: Optional[str] = Field(None, max_length=50)
    resolution_notes: Optional[str] = Field(None)

    # Dead-Man's Switch Integration
    triggers_dead_mans_switch: bool = Field(False)
    dead_mans_switch_triggered_date: Optional[datetime] = Field(None)
    dead_mans_switch_reduced_to_days: Optional[int] = Field(None)

    # External Counsel & Insurance
    external_counsel_engaged: bool = Field(False)
    external_counsel_firm: Optional[str] = Field(None, max_length=255)
    external_counsel_attorney: Optional[str] = Field(None, max_length=255)

    insurance_claim_filed: bool = Field(False)
    insurance_carrier: Optional[str] = Field(None, max_length=255)
    insurance_claim_number: Optional[str] = Field(None, max_length=100)

    # Public Disclosure
    publicly_disclosed: bool = Field(False)
    public_disclosure_date: Optional[datetime] = Field(None)
    public_disclosure_url: Optional[str] = Field(None, max_length=500)

    # Streisand Effect Tracking
    media_coverage: bool = Field(False)
    media_coverage_notes: Optional[str] = Field(None)

    # Internal Tracking
    internal_case_number: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=255)
    priority: int = Field(3, ge=1, le=5, description="1=Highest, 5=Lowest")

    # Metadata
    notes: Optional[str] = Field(None)
    tags: Optional[str] = Field(None, description="JSON array of tags")


class LegalIncidentCreate(LegalIncidentBase):
    """Schema for creating a legal incident."""
    pass


class LegalIncidentUpdate(BaseModel):
    """Schema for updating a legal incident (all fields optional)."""

    incident_type: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=30)

    sender_name: Optional[str] = Field(None, max_length=255)
    sender_organization: Optional[str] = Field(None, max_length=255)
    sender_legal_counsel: Optional[str] = Field(None, max_length=255)
    sender_address: Optional[str] = Field(None)
    sender_email: Optional[str] = Field(None, max_length=255)
    sender_phone: Optional[str] = Field(None, max_length=50)

    date_received: Optional[datetime] = Field(None)
    date_sent_by_sender: Optional[datetime] = Field(None)
    delivery_method: Optional[str] = Field(None, max_length=50)

    subject: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None)

    claims_made: Optional[str] = Field(None)
    demands: Optional[str] = Field(None)
    deadline: Optional[datetime] = Field(None)

    affected_data_points: Optional[str] = Field(None)
    affected_reports: Optional[str] = Field(None)
    affected_cities: Optional[str] = Field(None, max_length=255)

    frivolous: Optional[bool] = Field(None)
    anti_slapp_applicable: Optional[bool] = Field(None)
    first_amendment_protected: Optional[bool] = Field(None)
    legal_merit_assessment: Optional[str] = Field(None, max_length=20)
    legal_analysis_notes: Optional[str] = Field(None)

    response_required: Optional[bool] = Field(None)
    response_sent: Optional[bool] = Field(None)
    response_sent_date: Optional[datetime] = Field(None)
    response_sent_by: Optional[str] = Field(None, max_length=255)

    resolved: Optional[bool] = Field(None)
    resolved_date: Optional[datetime] = Field(None)
    resolution_type: Optional[str] = Field(None, max_length=50)
    resolution_notes: Optional[str] = Field(None)

    triggers_dead_mans_switch: Optional[bool] = Field(None)
    dead_mans_switch_triggered_date: Optional[datetime] = Field(None)
    dead_mans_switch_reduced_to_days: Optional[int] = Field(None)

    external_counsel_engaged: Optional[bool] = Field(None)
    external_counsel_firm: Optional[str] = Field(None, max_length=255)
    external_counsel_attorney: Optional[str] = Field(None, max_length=255)

    insurance_claim_filed: Optional[bool] = Field(None)
    insurance_carrier: Optional[str] = Field(None, max_length=255)
    insurance_claim_number: Optional[str] = Field(None, max_length=100)

    publicly_disclosed: Optional[bool] = Field(None)
    public_disclosure_date: Optional[datetime] = Field(None)
    public_disclosure_url: Optional[str] = Field(None, max_length=500)

    media_coverage: Optional[bool] = Field(None)
    media_coverage_notes: Optional[str] = Field(None)

    internal_case_number: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[str] = Field(None, max_length=255)
    priority: Optional[int] = Field(None, ge=1, le=5)

    notes: Optional[str] = Field(None)
    tags: Optional[str] = Field(None)


class LegalIncidentResponse(LegalIncidentBase):
    """Schema for legal incident response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime]


class LegalIncidentListResponse(BaseModel):
    """Paginated list of legal incidents."""

    incidents: List[LegalIncidentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Legal Response Schemas
# ============================================================================


class LegalResponseBase(BaseModel):
    """Base legal response schema."""

    incident_id: int = Field(..., description="Related legal incident ID")

    response_type: str = Field(
        ...,
        max_length=50,
        description="InitialResponse, AntiSLAPPMotion, CourtFiling, Settlement, Retraction, EFFNotification"
    )
    status: str = Field(
        "Draft",
        max_length=30,
        description="Draft, UnderReview, Approved, Sent, Filed"
    )

    subject: str = Field(..., max_length=500)
    content: str = Field(..., description="Full text of response")

    template_used: Optional[str] = Field(None, max_length=255)
    template_version: Optional[str] = Field(None, max_length=50)

    citations: Optional[str] = Field(None, description="JSON array of cited sources")
    evidence_references: Optional[str] = Field(None)
    data_lineage_citations: Optional[str] = Field(None)

    legal_strategy: Optional[str] = Field(None)
    anticipated_outcome: Optional[str] = Field(None, max_length=100)

    sent_date: Optional[datetime] = Field(None)
    sent_by: Optional[str] = Field(None, max_length=255)
    sent_method: Optional[str] = Field(None, max_length=50)

    recipient_name: Optional[str] = Field(None, max_length=255)
    recipient_address: Optional[str] = Field(None)
    recipient_email: Optional[str] = Field(None, max_length=255)

    court_name: Optional[str] = Field(None, max_length=255)
    case_number: Optional[str] = Field(None, max_length=100)
    filing_date: Optional[datetime] = Field(None)
    filing_confirmation: Optional[str] = Field(None, max_length=255)

    reviewed_by: Optional[str] = Field(None, max_length=255)
    reviewed_date: Optional[datetime] = Field(None)
    approved_by: Optional[str] = Field(None, max_length=255)
    approved_date: Optional[datetime] = Field(None)

    response_received: bool = Field(False)
    response_received_date: Optional[datetime] = Field(None)
    response_summary: Optional[str] = Field(None)

    effective: Optional[bool] = Field(None)
    effectiveness_notes: Optional[str] = Field(None)

    notes: Optional[str] = Field(None)


class LegalResponseCreate(LegalResponseBase):
    """Schema for creating a legal response."""
    pass


class LegalResponseResponse(LegalResponseBase):
    """Schema for legal response API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Document Schemas
# ============================================================================


class LegalDocumentBase(BaseModel):
    """Base legal document schema."""

    incident_id: int = Field(..., description="Related legal incident ID")

    document_type: str = Field(
        ...,
        max_length=50,
        description="CeaseAndDesistLetter, Lawsuit, CourtFiling, Email, Letter, Evidence, Other"
    )
    category: Optional[str] = Field(None, max_length=50)

    title: str = Field(..., max_length=500)
    description: Optional[str] = Field(None)

    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size_bytes: Optional[int] = Field(None)
    file_mime_type: Optional[str] = Field(None, max_length=100)
    file_hash_sha256: Optional[str] = Field(None, max_length=64)

    document_date: Optional[datetime] = Field(None)
    uploaded_by: str = Field(..., max_length=255)

    received_from: Optional[str] = Field(None, max_length=255)
    received_method: Optional[str] = Field(None, max_length=50)

    confidential: bool = Field(False)
    confidentiality_reason: Optional[str] = Field(None)

    publicly_available: bool = Field(False)
    public_url: Optional[str] = Field(None, max_length=500)

    court_filed: bool = Field(False)
    court_name: Optional[str] = Field(None, max_length=255)
    case_number: Optional[str] = Field(None, max_length=100)
    filing_date: Optional[datetime] = Field(None)

    page_count: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    tags: Optional[str] = Field(None)


class LegalDocumentCreate(LegalDocumentBase):
    """Schema for creating a legal document record."""
    pass


class LegalDocumentResponse(LegalDocumentBase):
    """Schema for legal document API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uploaded_date: datetime
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Template Schemas
# ============================================================================


class LegalTemplateBase(BaseModel):
    """Base legal template schema."""

    template_name: str = Field(..., max_length=255)
    template_type: str = Field(
        ...,
        max_length=50,
        description="AntiSLAPP, CeaseAndDesistResponse, DefamationResponse, EFFNotification"
    )
    version: str = Field(..., max_length=50)

    subject_template: Optional[str] = Field(None, max_length=500)
    body_template: str = Field(..., description="Template with placeholders")

    description: Optional[str] = Field(None)
    usage_instructions: Optional[str] = Field(None)

    required_variables: Optional[str] = Field(None)
    optional_variables: Optional[str] = Field(None)

    reviewed_by_counsel: bool = Field(False)
    reviewed_by: Optional[str] = Field(None, max_length=255)
    reviewed_date: Optional[datetime] = Field(None)
    review_notes: Optional[str] = Field(None)

    is_active: bool = Field(True)
    is_current_version: bool = Field(True)

    supersedes_template_id: Optional[int] = Field(None)

    created_by: str = Field(..., max_length=255)
    notes: Optional[str] = Field(None)
    tags: Optional[str] = Field(None)


class LegalTemplateCreate(LegalTemplateBase):
    """Schema for creating a legal template."""
    pass


class LegalTemplateResponse(LegalTemplateBase):
    """Schema for legal template API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usage_count: int
    last_used_date: Optional[datetime]
    success_rate: Optional[int]
    average_resolution_days: Optional[int]
    created_at: datetime
    updated_at: datetime
