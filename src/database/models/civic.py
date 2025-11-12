"""
Civic engagement and decision tracking models.

Tracks city council decisions, votes, and fiscal impact outcomes.
Enables prediction accuracy tracking and institutional credibility building.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from src.database.base import AuditMixin, Base

if TYPE_CHECKING:
    from src.database.models.core import City, FiscalYear


class DecisionCategory(str, Enum):
    """Categories of city council decisions."""

    BUDGET = "budget"  # Annual budget approval, amendments
    TAX = "tax"  # Tax rate changes, new taxes
    BOND = "bond"  # Bond issuances for infrastructure
    LABOR = "labor"  # Labor contracts, employee benefits
    SERVICE = "service"  # Service level changes
    INFRASTRUCTURE = "infrastructure"  # Capital projects
    PENSION = "pension"  # Pension obligation bonds, reforms
    POLICY = "policy"  # Other policy decisions with fiscal impact
    EMERGENCY = "emergency"  # Emergency spending authorizations
    OTHER = "other"  # Other decisions


class DecisionStatus(str, Enum):
    """Status of decision tracking."""

    PROPOSED = "proposed"  # Decision proposed, not yet voted
    APPROVED = "approved"  # Approved by council/voters
    REJECTED = "rejected"  # Rejected by council/voters
    PENDING_OUTCOME = "pending_outcome"  # Approved, waiting for actual impact data
    OUTCOME_TRACKED = "outcome_tracked"  # Actual outcome recorded
    CANCELLED = "cancelled"  # Decision cancelled or rescinded


class VoteType(str, Enum):
    """Type of vote."""

    COUNCIL = "council"  # City council vote
    BALLOT = "ballot"  # Voter ballot measure
    REFERENDUM = "referendum"  # Referendum
    EMERGENCY = "emergency"  # Emergency vote


class OutcomeStatus(str, Enum):
    """Status of outcome tracking."""

    PENDING = "pending"  # Waiting for data
    PARTIAL = "partial"  # Some data available (e.g., 6-month actuals)
    FINAL = "final"  # Complete outcome data available
    REVISED = "revised"  # Outcome revised based on new data


class Decision(Base, AuditMixin):
    """
    City council or voter decisions with fiscal impact.

    Tracks decisions from proposal through outcome, enabling prediction
    accuracy analysis and institutional credibility building.

    Examples:
    - Sales tax increase ballot measure
    - Labor contract approval
    - Bond issuance for infrastructure
    - Budget amendments
    """

    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_city_date", "city_id", "decision_date"),
        Index("ix_decisions_category", "category"),
        Index("ix_decisions_status", "status"),
    )

    id = Column(Integer, primary_key=True)

    # Core Information
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    decision_date = Column(Date, nullable=False)  # Date of decision/vote

    title = Column(String(500), nullable=False)  # Short title
    description = Column(Text, nullable=False)  # Detailed description

    category = Column(SQLEnum(DecisionCategory), nullable=False)
    status = Column(SQLEnum(DecisionStatus), nullable=False, default=DecisionStatus.PROPOSED)

    # Vote Information
    vote_type = Column(SQLEnum(VoteType), nullable=True)
    vote_count_yes = Column(Integer, nullable=True)
    vote_count_no = Column(Integer, nullable=True)
    vote_count_abstain = Column(Integer, nullable=True)

    # Ballot measure details (if applicable)
    ballot_measure_id = Column(String(50), nullable=True)  # e.g., "Measure V"
    ballot_measure_text = Column(Text, nullable=True)

    # Fiscal Impact Prediction
    predicted_annual_impact = Column(Numeric(15, 2), nullable=True)  # ± dollars/year
    predicted_one_time_impact = Column(Numeric(15, 2), nullable=True)  # One-time cost/revenue
    predicted_impact_start_year = Column(Integer, nullable=True)  # FY when impact begins
    predicted_impact_duration_years = Column(Integer, nullable=True)  # Duration of impact

    prediction_notes = Column(Text, nullable=True)  # Assumptions, methodology
    prediction_confidence = Column(String(20), nullable=True)  # "high", "medium", "low"
    predicted_by = Column(String(255), nullable=True)  # Analyst name/team
    prediction_date = Column(Date, nullable=True)

    # Links to affected fiscal years
    primary_fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)

    # Source Documentation
    source_document_url = Column(String(500), nullable=True)  # Link to agenda/minutes
    source_document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=True)

    # External References
    external_reference_url = Column(String(500), nullable=True)  # News article, etc.
    council_meeting_date = Column(Date, nullable=True)

    # Relationships
    city = relationship("City", foreign_keys=[city_id])
    primary_fiscal_year = relationship("FiscalYear", foreign_keys=[primary_fiscal_year_id])
    source_document = relationship("SourceDocument", foreign_keys=[source_document_id])

    votes = relationship("Vote", back_populates="decision", lazy="dynamic")
    outcomes = relationship("Outcome", back_populates="decision", lazy="dynamic",
                          order_by="Outcome.outcome_date.desc()")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Decision(id={self.id}, city_id={self.city_id}, "
            f"title='{self.title[:50]}...', date={self.decision_date})>"
        )

    @property
    def latest_outcome(self) -> Optional["Outcome"]:
        """Get the most recent outcome for this decision."""
        return self.outcomes.first()

    @property
    def prediction_accuracy_percent(self) -> Optional[float]:
        """
        Calculate prediction accuracy percentage.

        Returns accuracy as percentage (0-100+).
        100% = perfect prediction
        >100% = actual exceeded prediction
        <100% = actual less than prediction

        Returns None if no final outcome available.
        """
        latest = self.latest_outcome
        if not latest or latest.status != OutcomeStatus.FINAL:
            return None

        if not self.predicted_annual_impact or self.predicted_annual_impact == 0:
            return None

        if not latest.actual_annual_impact:
            return None

        # Calculate accuracy
        accuracy = (float(latest.actual_annual_impact) /
                   float(self.predicted_annual_impact)) * 100
        return accuracy


class Vote(Base, AuditMixin):
    """
    Individual votes on a decision.

    Tracks how individual council members voted, enabling analysis
    of voting patterns and political dynamics.
    """

    __tablename__ = "votes"
    __table_args__ = (
        Index("ix_votes_decision", "decision_id"),
        Index("ix_votes_voter", "voter_name"),
    )

    id = Column(Integer, primary_key=True)

    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=False)

    # Voter Information
    voter_name = Column(String(255), nullable=False)  # Council member or "Voters"
    voter_title = Column(String(100), nullable=True)  # e.g., "Mayor", "Council Member"
    voter_district = Column(String(50), nullable=True)  # District/ward if applicable

    # Vote
    vote = Column(String(20), nullable=False)  # "yes", "no", "abstain", "absent"
    vote_date = Column(Date, nullable=False)

    # Context
    vote_notes = Column(Text, nullable=True)  # Explanation of vote, if recorded

    # Relationships
    decision = relationship("Decision", back_populates="votes")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Vote(id={self.id}, decision_id={self.decision_id}, "
            f"voter='{self.voter_name}', vote='{self.vote}')>"
        )


class Outcome(Base, AuditMixin):
    """
    Actual fiscal impact outcomes of decisions.

    Tracks actual financial impact over time, enabling comparison with
    predictions and accuracy analysis. Multiple outcomes can be tracked
    for a single decision (e.g., 6-month partial, 1-year final).
    """

    __tablename__ = "outcomes"
    __table_args__ = (
        Index("ix_outcomes_decision", "decision_id"),
        Index("ix_outcomes_date", "outcome_date"),
        Index("ix_outcomes_status", "status"),
    )

    id = Column(Integer, primary_key=True)

    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=False)

    # Outcome Information
    outcome_date = Column(Date, nullable=False)  # Date of outcome measurement
    status = Column(SQLEnum(OutcomeStatus), nullable=False, default=OutcomeStatus.PENDING)

    # Actual Impact
    actual_annual_impact = Column(Numeric(15, 2), nullable=True)  # Actual ± dollars/year
    actual_one_time_impact = Column(Numeric(15, 2), nullable=True)  # Actual one-time impact

    # Linked Fiscal Year (for verification)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=True)

    # Analysis
    outcome_notes = Column(Text, nullable=True)  # Explanation of outcome
    variance_explanation = Column(Text, nullable=True)  # Why did prediction differ?

    # Accuracy Metrics (calculated)
    accuracy_percent = Column(Numeric(6, 2), nullable=True)  # % accuracy
    absolute_variance = Column(Numeric(15, 2), nullable=True)  # Absolute difference

    # Data Source
    data_source = Column(String(255), nullable=True)  # Where did actual data come from?
    source_document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=True)

    # Tracking
    measured_by = Column(String(255), nullable=True)  # Analyst who measured outcome
    measurement_date = Column(Date, nullable=True)  # When outcome was measured

    # Relationships
    decision = relationship("Decision", back_populates="outcomes")
    fiscal_year = relationship("FiscalYear", foreign_keys=[fiscal_year_id])
    source_document = relationship("SourceDocument", foreign_keys=[source_document_id])

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Outcome(id={self.id}, decision_id={self.decision_id}, "
            f"status='{self.status}', date={self.outcome_date})>"
        )

    def calculate_accuracy(self) -> None:
        """
        Calculate accuracy metrics based on decision prediction.

        Updates accuracy_percent and absolute_variance fields.
        """
        if not self.decision:
            return

        predicted = self.decision.predicted_annual_impact
        actual = self.actual_annual_impact

        if predicted is None or actual is None or predicted == 0:
            return

        # Calculate accuracy percentage
        self.accuracy_percent = (float(actual) / float(predicted)) * 100

        # Calculate absolute variance
        self.absolute_variance = abs(float(actual) - float(predicted))
