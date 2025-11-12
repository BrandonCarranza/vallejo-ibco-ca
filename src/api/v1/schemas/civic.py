"""
Pydantic schemas for civic engagement and decision tracking API.
"""
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.database.models.civic import (
    DecisionCategory,
    DecisionStatus,
    OutcomeStatus,
    VoteType,
)


# ============================================================================
# Vote Schemas
# ============================================================================


class VoteBase(BaseModel):
    """Base vote schema."""

    voter_name: str = Field(..., max_length=255, description="Council member name or 'Voters'")
    voter_title: Optional[str] = Field(None, max_length=100, description="e.g., 'Mayor', 'Council Member'")
    voter_district: Optional[str] = Field(None, max_length=50, description="District/ward if applicable")
    vote: str = Field(..., max_length=20, description="'yes', 'no', 'abstain', 'absent'")
    vote_date: date = Field(..., description="Date of vote")
    vote_notes: Optional[str] = Field(None, description="Explanation of vote")


class VoteCreate(VoteBase):
    """Schema for creating a vote."""

    pass


class VoteResponse(VoteBase):
    """Schema for vote response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    decision_id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Outcome Schemas
# ============================================================================


class OutcomeBase(BaseModel):
    """Base outcome schema."""

    outcome_date: date = Field(..., description="Date of outcome measurement")
    status: OutcomeStatus = Field(..., description="pending, partial, final, or revised")

    actual_annual_impact: Optional[Decimal] = Field(
        None,
        description="Actual annual fiscal impact (positive = revenue, negative = cost)"
    )
    actual_one_time_impact: Optional[Decimal] = Field(
        None,
        description="Actual one-time fiscal impact"
    )

    fiscal_year_id: Optional[int] = Field(None, description="Fiscal year for verification")

    outcome_notes: Optional[str] = Field(None, description="Explanation of outcome")
    variance_explanation: Optional[str] = Field(
        None,
        description="Why did prediction differ from actual?"
    )

    data_source: Optional[str] = Field(
        None,
        max_length=255,
        description="Source of actual data (e.g., 'Q2 2025 Financial Report')"
    )
    source_document_id: Optional[int] = Field(None, description="Source document ID")

    measured_by: Optional[str] = Field(None, max_length=255, description="Analyst who measured outcome")
    measurement_date: Optional[date] = Field(None, description="When outcome was measured")


class OutcomeCreate(OutcomeBase):
    """Schema for creating an outcome."""

    pass


class OutcomeResponse(OutcomeBase):
    """Schema for outcome response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    decision_id: int

    # Calculated fields
    accuracy_percent: Optional[Decimal] = Field(
        None,
        description="Prediction accuracy percentage (100% = perfect)"
    )
    absolute_variance: Optional[Decimal] = Field(
        None,
        description="Absolute difference between predicted and actual"
    )

    created_at: datetime
    updated_at: datetime


# ============================================================================
# Decision Schemas
# ============================================================================


class DecisionBase(BaseModel):
    """Base decision schema."""

    decision_date: date = Field(..., description="Date of decision/vote")
    title: str = Field(..., max_length=500, description="Short title")
    description: str = Field(..., description="Detailed description")

    category: DecisionCategory = Field(..., description="Decision category")
    status: DecisionStatus = Field(
        default=DecisionStatus.PROPOSED,
        description="proposed, approved, rejected, etc."
    )

    # Vote information
    vote_type: Optional[VoteType] = Field(None, description="council, ballot, referendum, emergency")
    vote_count_yes: Optional[int] = Field(None, ge=0, description="Number of yes votes")
    vote_count_no: Optional[int] = Field(None, ge=0, description="Number of no votes")
    vote_count_abstain: Optional[int] = Field(None, ge=0, description="Number of abstain votes")

    # Ballot measure (if applicable)
    ballot_measure_id: Optional[str] = Field(None, max_length=50, description="e.g., 'Measure V'")
    ballot_measure_text: Optional[str] = Field(None, description="Full ballot text")

    # Fiscal impact prediction
    predicted_annual_impact: Optional[Decimal] = Field(
        None,
        description="Predicted annual fiscal impact (± dollars/year). Positive = revenue, negative = cost"
    )
    predicted_one_time_impact: Optional[Decimal] = Field(
        None,
        description="Predicted one-time fiscal impact"
    )
    predicted_impact_start_year: Optional[int] = Field(
        None,
        ge=2000,
        le=2100,
        description="Fiscal year when impact begins"
    )
    predicted_impact_duration_years: Optional[int] = Field(
        None,
        ge=1,
        description="Duration of fiscal impact in years"
    )

    prediction_notes: Optional[str] = Field(None, description="Prediction assumptions and methodology")
    prediction_confidence: Optional[str] = Field(
        None,
        max_length=20,
        description="Confidence level: 'high', 'medium', or 'low'"
    )
    predicted_by: Optional[str] = Field(None, max_length=255, description="Analyst name/team")
    prediction_date: Optional[date] = Field(None, description="Date prediction was made")

    # Links
    primary_fiscal_year_id: Optional[int] = Field(None, description="Primary affected fiscal year")

    # Source documentation
    source_document_url: Optional[str] = Field(None, max_length=500, description="Link to agenda/minutes")
    source_document_id: Optional[int] = Field(None, description="Source document ID")
    external_reference_url: Optional[str] = Field(None, max_length=500, description="News article, etc.")
    council_meeting_date: Optional[date] = Field(None, description="City council meeting date")


class DecisionCreate(DecisionBase):
    """Schema for creating a decision."""

    city_id: int = Field(..., description="City ID")


class DecisionUpdate(BaseModel):
    """Schema for updating a decision."""

    decision_date: Optional[date] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[DecisionCategory] = None
    status: Optional[DecisionStatus] = None

    vote_type: Optional[VoteType] = None
    vote_count_yes: Optional[int] = Field(None, ge=0)
    vote_count_no: Optional[int] = Field(None, ge=0)
    vote_count_abstain: Optional[int] = Field(None, ge=0)

    ballot_measure_id: Optional[str] = Field(None, max_length=50)
    ballot_measure_text: Optional[str] = None

    predicted_annual_impact: Optional[Decimal] = None
    predicted_one_time_impact: Optional[Decimal] = None
    predicted_impact_start_year: Optional[int] = Field(None, ge=2000, le=2100)
    predicted_impact_duration_years: Optional[int] = Field(None, ge=1)

    prediction_notes: Optional[str] = None
    prediction_confidence: Optional[str] = Field(None, max_length=20)
    predicted_by: Optional[str] = Field(None, max_length=255)
    prediction_date: Optional[date] = None

    primary_fiscal_year_id: Optional[int] = None

    source_document_url: Optional[str] = Field(None, max_length=500)
    source_document_id: Optional[int] = None
    external_reference_url: Optional[str] = Field(None, max_length=500)
    council_meeting_date: Optional[date] = None


class DecisionResponse(DecisionBase):
    """Schema for decision response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Calculated fields
    prediction_accuracy_percent: Optional[float] = Field(
        None,
        description="Prediction accuracy (requires final outcome)"
    )


class DecisionDetailResponse(DecisionResponse):
    """Detailed decision response with votes and outcomes."""

    votes: List[VoteResponse] = Field(default_factory=list, description="Individual votes")
    outcomes: List[OutcomeResponse] = Field(default_factory=list, description="Outcome tracking")
    latest_outcome: Optional[OutcomeResponse] = Field(None, description="Most recent outcome")


class DecisionSummaryResponse(BaseModel):
    """Simplified decision summary for listings."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    decision_date: date
    title: str
    category: DecisionCategory
    status: DecisionStatus

    predicted_annual_impact: Optional[Decimal] = None
    prediction_accuracy_percent: Optional[float] = None

    created_at: datetime


class DecisionListResponse(BaseModel):
    """Paginated list of decisions."""

    decisions: List[DecisionSummaryResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# Decision Impact Analysis Schemas
# ============================================================================


class DecisionImpactPredictionRequest(BaseModel):
    """Request schema for predicting fiscal impact of a proposed decision."""

    city_id: int = Field(..., description="City ID")
    category: DecisionCategory = Field(..., description="Decision category")
    description: str = Field(..., description="Description of proposed decision")

    # Optional context for better predictions
    revenue_change_percent: Optional[Decimal] = Field(
        None,
        description="Expected revenue change percentage (for tax/fee changes)"
    )
    expenditure_change_amount: Optional[Decimal] = Field(
        None,
        description="Expected expenditure change amount (for contracts/services)"
    )
    affected_fund_balance: Optional[Decimal] = Field(
        None,
        description="Fund balance affected by decision"
    )


class DecisionImpactPredictionResponse(BaseModel):
    """Response schema for fiscal impact prediction."""

    predicted_annual_impact: Decimal = Field(..., description="Predicted annual impact")
    predicted_one_time_impact: Optional[Decimal] = Field(None, description="One-time impact")

    confidence: str = Field(..., description="Confidence level: high, medium, low")
    methodology: str = Field(..., description="Prediction methodology used")
    assumptions: List[str] = Field(..., description="Key assumptions")
    sensitivity_factors: List[str] = Field(..., description="Factors affecting prediction accuracy")

    recommendation: str = Field(..., description="Analyst recommendation")


class DecisionAccuracyReport(BaseModel):
    """Report on prediction accuracy."""

    total_decisions: int = Field(..., description="Total decisions tracked")
    decisions_with_outcomes: int = Field(..., description="Decisions with final outcomes")

    avg_accuracy_percent: Decimal = Field(..., description="Average prediction accuracy")
    median_accuracy_percent: Decimal = Field(..., description="Median prediction accuracy")

    accurate_predictions: int = Field(..., description="Predictions within 10% of actual")
    inaccurate_predictions: int = Field(..., description="Predictions >25% off from actual")

    best_prediction: Optional[DecisionSummaryResponse] = Field(
        None,
        description="Most accurate prediction"
    )
    worst_prediction: Optional[DecisionSummaryResponse] = Field(
        None,
        description="Least accurate prediction"
    )

    by_category: dict = Field(..., description="Accuracy breakdown by category")

    insights: List[str] = Field(..., description="Key insights from accuracy analysis")
