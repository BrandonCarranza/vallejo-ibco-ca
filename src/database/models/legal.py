"""
Legal defense models: Incident tracking, response management, and transparency.

Tracks cease-and-desist letters, defamation claims, SLAPP lawsuits, and all legal threats.
Provides complete provenance linking to affected data points.
Public transparency log demonstrates suppression attempts fail.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base

if TYPE_CHECKING:
    from src.database.models.core import DataLineage


class LegalIncident(Base, AuditMixin):
    """
    Tracks all legal threats, cease-and-desist letters, lawsuits, and harassment.

    IMMUTABILITY: Records are preserved for legal discovery.
    Soft deletes only - never hard delete legal incident records.

    PUBLIC TRANSPARENCY: All incidents logged here will be included in
    quarterly transparency reports to demonstrate suppression attempts.

    DEAD-MAN'S SWITCH INTEGRATION: Legal incidents trigger accelerated
    publication timelines to make suppression counterproductive.
    """

    __tablename__ = "legal_incidents"
    __table_args__ = (
        Index("ix_legal_incident_type", "incident_type"),
        Index("ix_legal_incident_date_received", "date_received"),
        Index("ix_legal_incident_status", "status"),
    )

    id = Column(Integer, primary_key=True)

    # Incident Classification
    incident_type = Column(
        String(50), nullable=False
    )  # CeaseAndDesist, DefamationClaim, SLAPPLawsuit, Subpoena, Harassment, Other

    severity = Column(
        String(20), nullable=False, default="Medium"
    )  # Low, Medium, High, Critical

    status = Column(
        String(30), nullable=False, default="Active"
    )  # Active, UnderReview, ResponseSent, Resolved, Escalated, Litigation

    # Sender Information
    sender_name = Column(String(255), nullable=False)  # Individual or organization
    sender_organization = Column(String(255), nullable=True)  # If applicable
    sender_legal_counsel = Column(String(255), nullable=True)  # Law firm representing sender
    sender_address = Column(Text, nullable=True)
    sender_email = Column(String(255), nullable=True)
    sender_phone = Column(String(50), nullable=True)

    # Incident Details
    date_received = Column(DateTime, nullable=False)
    date_sent_by_sender = Column(DateTime, nullable=True)  # Date on original letter
    delivery_method = Column(
        String(50), nullable=False
    )  # Email, CertifiedMail, ProcessServer, InPerson

    subject = Column(String(500), nullable=False)  # Brief description
    description = Column(Text, nullable=False)  # Full details of allegations/claims

    # Claims & Demands
    claims_made = Column(Text, nullable=True)  # Specific claims (defamation, copyright, etc.)
    demands = Column(Text, nullable=True)  # What they're demanding (retraction, takedown, payment)
    deadline = Column(DateTime, nullable=True)  # Deadline for response

    # Affected Data
    affected_data_points = Column(Text, nullable=True)  # JSON list of affected records
    affected_reports = Column(Text, nullable=True)  # Which reports/pages are being challenged
    affected_cities = Column(String(255), nullable=True)  # Which cities' data is involved

    # Legal Analysis
    frivolous = Column(Boolean, nullable=False, default=False)  # IBCo assessment
    anti_slapp_applicable = Column(Boolean, nullable=True)  # Can we file anti-SLAPP motion?
    first_amendment_protected = Column(Boolean, nullable=True)  # Protected speech?

    legal_merit_assessment = Column(
        String(20), nullable=True
    )  # None, Low, Medium, High
    legal_analysis_notes = Column(Text, nullable=True)

    # Response Tracking
    response_required = Column(Boolean, nullable=False, default=True)
    response_sent = Column(Boolean, nullable=False, default=False)
    response_sent_date = Column(DateTime, nullable=True)
    response_sent_by = Column(String(255), nullable=True)  # Person or system

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_date = Column(DateTime, nullable=True)
    resolution_type = Column(
        String(50), nullable=True
    )  # Dismissed, Retracted, Settled, AntiSLAPPGranted, CourtRuling
    resolution_notes = Column(Text, nullable=True)

    # Dead-Man's Switch Integration
    triggers_dead_mans_switch = Column(
        Boolean, nullable=False, default=False
    )  # Does this incident reduce timer?
    dead_mans_switch_triggered_date = Column(DateTime, nullable=True)
    dead_mans_switch_reduced_to_days = Column(Integer, nullable=True)  # e.g., 7 days

    # External Counsel & Insurance
    external_counsel_engaged = Column(Boolean, nullable=False, default=False)
    external_counsel_firm = Column(String(255), nullable=True)
    external_counsel_attorney = Column(String(255), nullable=True)

    insurance_claim_filed = Column(Boolean, nullable=False, default=False)
    insurance_carrier = Column(String(255), nullable=True)
    insurance_claim_number = Column(String(100), nullable=True)

    # Public Disclosure
    publicly_disclosed = Column(Boolean, nullable=False, default=False)
    public_disclosure_date = Column(DateTime, nullable=True)
    public_disclosure_url = Column(String(500), nullable=True)

    # Streisand Effect Tracking
    media_coverage = Column(Boolean, nullable=False, default=False)
    media_coverage_notes = Column(Text, nullable=True)  # Links to articles, tweets, etc.

    # Internal Tracking
    internal_case_number = Column(String(50), nullable=True, unique=True)
    assigned_to = Column(String(255), nullable=True)  # IBCo team member handling
    priority = Column(Integer, nullable=False, default=3)  # 1=Highest, 5=Lowest

    # Metadata
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array of tags for filtering

    # Relationships
    responses = relationship(
        "LegalResponse",
        back_populates="incident",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    documents = relationship(
        "LegalDocument",
        back_populates="incident",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of LegalIncident."""
        return (
            f"<LegalIncident(id={self.id}, type='{self.incident_type}', "
            f"sender='{self.sender_name}', status='{self.status}')>"
        )


class LegalResponse(Base, AuditMixin):
    """
    Responses to legal incidents (letters, filings, notifications).

    Tracks all outbound communications related to legal defense.
    Links to templates used and final sent versions.
    """

    __tablename__ = "legal_responses"
    __table_args__ = (
        Index("ix_legal_response_incident", "incident_id"),
        Index("ix_legal_response_type", "response_type"),
        Index("ix_legal_response_sent_date", "sent_date"),
    )

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("legal_incidents.id"), nullable=False)

    # Response Classification
    response_type = Column(
        String(50), nullable=False
    )  # InitialResponse, AntiSLAPPMotion, CourtFiling, Settlement, Retraction, EFFNotification

    status = Column(
        String(30), nullable=False, default="Draft"
    )  # Draft, UnderReview, Approved, Sent, Filed

    # Response Details
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Full text of response

    # Template Information
    template_used = Column(String(255), nullable=True)  # Which template was used
    template_version = Column(String(50), nullable=True)  # Template version number

    # Citations & Evidence
    citations = Column(Text, nullable=True)  # JSON array of cited sources
    evidence_references = Column(Text, nullable=True)  # Links to supporting evidence
    data_lineage_citations = Column(Text, nullable=True)  # JSON array of DataLineage IDs

    # Legal Strategy
    legal_strategy = Column(Text, nullable=True)  # Strategic notes
    anticipated_outcome = Column(String(100), nullable=True)

    # Sending & Filing
    sent_date = Column(DateTime, nullable=True)
    sent_by = Column(String(255), nullable=True)  # Person who sent/filed
    sent_method = Column(
        String(50), nullable=True
    )  # Email, CertifiedMail, CourtEFiling, InPerson

    recipient_name = Column(String(255), nullable=True)
    recipient_address = Column(Text, nullable=True)
    recipient_email = Column(String(255), nullable=True)

    # Court Filing Details (if applicable)
    court_name = Column(String(255), nullable=True)
    case_number = Column(String(100), nullable=True)
    filing_date = Column(DateTime, nullable=True)
    filing_confirmation = Column(String(255), nullable=True)  # Confirmation number

    # Review & Approval
    reviewed_by = Column(String(255), nullable=True)  # Legal counsel who reviewed
    reviewed_date = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_date = Column(DateTime, nullable=True)

    # Outcome Tracking
    response_received = Column(Boolean, nullable=False, default=False)
    response_received_date = Column(DateTime, nullable=True)
    response_summary = Column(Text, nullable=True)

    # Effectiveness
    effective = Column(Boolean, nullable=True)  # Did this response achieve goals?
    effectiveness_notes = Column(Text, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)

    # Relationships
    incident = relationship("LegalIncident", back_populates="responses")

    def __repr__(self) -> str:
        """String representation of LegalResponse."""
        return (
            f"<LegalResponse(id={self.id}, incident_id={self.incident_id}, "
            f"type='{self.response_type}', status='{self.status}')>"
        )


class LegalDocument(Base, AuditMixin):
    """
    Stores all legal documents related to incidents.

    Preserves original documents, correspondence, court filings, etc.
    Ensures complete documentation for discovery and transparency.
    """

    __tablename__ = "legal_documents"
    __table_args__ = (
        Index("ix_legal_document_incident", "incident_id"),
        Index("ix_legal_document_type", "document_type"),
        Index("ix_legal_document_uploaded", "uploaded_date"),
    )

    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("legal_incidents.id"), nullable=False)

    # Document Classification
    document_type = Column(
        String(50), nullable=False
    )  # CeaseAndDesistLetter, Lawsuit, CourtFiling, Email, Letter, Evidence, Other

    category = Column(
        String(50), nullable=True
    )  # Incoming, Outgoing, Court, Internal, Evidence

    # Document Details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # File Information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to stored file
    file_size_bytes = Column(Integer, nullable=True)
    file_mime_type = Column(String(100), nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True)  # For integrity verification

    # Document Dates
    document_date = Column(DateTime, nullable=True)  # Date on document
    uploaded_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    uploaded_by = Column(String(255), nullable=False)

    # Source Information
    received_from = Column(String(255), nullable=True)
    received_method = Column(String(50), nullable=True)  # Email, Mail, Court, Other

    # Confidentiality & Public Disclosure
    confidential = Column(Boolean, nullable=False, default=False)
    confidentiality_reason = Column(Text, nullable=True)

    publicly_available = Column(Boolean, nullable=False, default=False)
    public_url = Column(String(500), nullable=True)

    # Court Filing Information (if applicable)
    court_filed = Column(Boolean, nullable=False, default=False)
    court_name = Column(String(255), nullable=True)
    case_number = Column(String(100), nullable=True)
    filing_date = Column(DateTime, nullable=True)

    # Metadata
    page_count = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array

    # Relationships
    incident = relationship("LegalIncident", back_populates="documents")

    def __repr__(self) -> str:
        """String representation of LegalDocument."""
        return (
            f"<LegalDocument(id={self.id}, incident_id={self.incident_id}, "
            f"title='{self.title}', type='{self.document_type}')>"
        )


class LegalTemplate(Base, AuditMixin):
    """
    Reusable legal response templates.

    Templates for common legal situations:
    - Anti-SLAPP motion responses
    - Cease-and-desist replies
    - Defamation claim responses
    - EFF/ACLU notification letters

    Version controlled for compliance and improvement tracking.
    """

    __tablename__ = "legal_templates"
    __table_args__ = (
        UniqueConstraint("template_name", "version", name="uq_legal_template_name_version"),
        Index("ix_legal_template_type", "template_type"),
        Index("ix_legal_template_active", "is_active"),
    )

    id = Column(Integer, primary_key=True)

    # Template Identification
    template_name = Column(String(255), nullable=False)
    template_type = Column(
        String(50), nullable=False
    )  # AntiSLAPP, CeaseAndDesistResponse, DefamationResponse, EFFNotification

    version = Column(String(50), nullable=False)  # Semantic versioning

    # Template Content
    subject_template = Column(String(500), nullable=True)  # Subject line template
    body_template = Column(Text, nullable=False)  # Full template with placeholders

    # Template Metadata
    description = Column(Text, nullable=True)
    usage_instructions = Column(Text, nullable=True)

    # Placeholders & Variables
    required_variables = Column(Text, nullable=True)  # JSON array of required variables
    optional_variables = Column(Text, nullable=True)  # JSON array of optional variables

    # Legal Review
    reviewed_by_counsel = Column(Boolean, nullable=False, default=False)
    reviewed_by = Column(String(255), nullable=True)  # Attorney who reviewed
    reviewed_date = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Status & Versioning
    is_active = Column(Boolean, nullable=False, default=True)
    is_current_version = Column(Boolean, nullable=False, default=True)

    supersedes_template_id = Column(
        Integer, ForeignKey("legal_templates.id"), nullable=True
    )  # Previous version

    # Usage Tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_date = Column(DateTime, nullable=True)

    # Effectiveness Metrics
    success_rate = Column(Integer, nullable=True)  # Percentage of successful outcomes
    average_resolution_days = Column(Integer, nullable=True)

    # Metadata
    created_by = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array

    # Relationships
    supersedes = relationship(
        "LegalTemplate",
        remote_side=[id],
        backref="superseded_by"
    )

    def __repr__(self) -> str:
        """String representation of LegalTemplate."""
        return (
            f"<LegalTemplate(id={self.id}, name='{self.template_name}', "
            f"version='{self.version}', type='{self.template_type}')>"
        )


# Note: These models integrate with:
# - DataLineage (core.py) for linking incidents to affected data points
# - Dead-man's switch system (planned in Wave 2) for automated publication triggers
# - Stakeholder notifications (stakeholders.py) for legal counsel/EFF/ACLU alerts
