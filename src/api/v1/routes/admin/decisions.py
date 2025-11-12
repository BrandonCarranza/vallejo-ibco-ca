"""
Admin API routes for logging and managing city council decisions.

Requires authentication. Used to:
- Log new council decisions and ballot measures
- Record predicted fiscal impacts
- Update decision status
- Add votes and outcomes
"""
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from src.api.dependencies import get_db
from src.api.v1.schemas.civic import (
    DecisionCreate,
    DecisionDetailResponse,
    DecisionListResponse,
    DecisionSummaryResponse,
    DecisionUpdate,
    OutcomeCreate,
    OutcomeResponse,
    VoteCreate,
    VoteResponse,
)
from src.database.models.civic import Decision, DecisionCategory, DecisionStatus, Outcome, Vote
from src.database.models.core import City

router = APIRouter(prefix="/admin/decisions", tags=["Admin", "Decisions"])


# ============================================================================
# Decision Management
# ============================================================================


@router.post("", response_model=DecisionDetailResponse, status_code=201)
async def create_decision(
    decision: DecisionCreate,
    db: Session = Depends(get_db)
):
    """
    Log a new city council decision or ballot measure.

    **Requires authentication.**

    Use this endpoint to manually log decisions from city council meetings,
    ballot measures, and other government actions with fiscal impact.

    Example use cases:
    - City council approves new labor contract
    - Voters approve sales tax increase (Measure V)
    - Council authorizes bond issuance
    - Emergency spending authorization
    """
    # Verify city exists
    city = db.query(City).filter(City.id == decision.city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Create decision
    db_decision = Decision(**decision.model_dump())
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)

    return db_decision


@router.get("/{decision_id}", response_model=DecisionDetailResponse)
async def get_decision(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific decision.

    **Requires authentication.**

    Includes:
    - Decision details
    - All votes
    - All outcome tracking records
    - Prediction accuracy (if outcomes available)
    """
    decision = db.query(Decision).options(
        joinedload(Decision.votes),
        joinedload(Decision.outcomes)
    ).filter(Decision.id == decision_id).first()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@router.patch("/{decision_id}", response_model=DecisionDetailResponse)
async def update_decision(
    decision_id: int,
    update: DecisionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a decision record.

    **Requires authentication.**

    Use this to:
    - Update status (proposed → approved)
    - Add missing information
    - Correct errors
    - Link to source documents
    """
    decision = db.query(Decision).filter(Decision.id == decision_id).first()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(decision, field, value)

    db.commit()
    db.refresh(decision)

    return decision


@router.delete("/{decision_id}", status_code=204)
async def delete_decision(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a decision.

    **Requires authentication.**

    Marks decision as deleted but preserves data for audit trail.
    """
    decision = db.query(Decision).filter(Decision.id == decision_id).first()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision.soft_delete()
    db.commit()

    return None


# ============================================================================
# Vote Management
# ============================================================================


@router.post("/{decision_id}/votes", response_model=VoteResponse, status_code=201)
async def add_vote(
    decision_id: int,
    vote: VoteCreate,
    db: Session = Depends(get_db)
):
    """
    Add a vote to a decision.

    **Requires authentication.**

    Records how individual council members voted, enabling analysis
    of voting patterns and political dynamics.
    """
    # Verify decision exists
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Create vote
    db_vote = Vote(decision_id=decision_id, **vote.model_dump())
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)

    return db_vote


@router.get("/{decision_id}/votes", response_model=List[VoteResponse])
async def get_votes(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all votes for a decision.

    **Requires authentication.**
    """
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    votes = db.query(Vote).filter(Vote.decision_id == decision_id).all()
    return votes


# ============================================================================
# Outcome Management
# ============================================================================


@router.post("/{decision_id}/outcomes", response_model=OutcomeResponse, status_code=201)
async def add_outcome(
    decision_id: int,
    outcome: OutcomeCreate,
    db: Session = Depends(get_db)
):
    """
    Record actual fiscal impact outcome.

    **Requires authentication.**

    Use this to track actual outcomes over time:
    - 6-month partial results
    - 1-year final results
    - Revised estimates

    The system will automatically calculate prediction accuracy.

    Example workflow:
    1. Decision logged with prediction: +$25M annual revenue
    2. After 6 months: Log partial outcome: +$12.5M (on track)
    3. After 1 year: Log final outcome: +$26M (104% accuracy)
    """
    # Verify decision exists
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Create outcome
    db_outcome = Outcome(decision_id=decision_id, **outcome.model_dump())

    # Calculate accuracy metrics
    db_outcome.calculate_accuracy()

    db.add(db_outcome)
    db.commit()
    db.refresh(db_outcome)

    return db_outcome


@router.get("/{decision_id}/outcomes", response_model=List[OutcomeResponse])
async def get_outcomes(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all outcome tracking records for a decision.

    **Requires authentication.**

    Returns outcomes in reverse chronological order (most recent first).
    """
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    outcomes = db.query(Outcome).filter(
        Outcome.decision_id == decision_id
    ).order_by(desc(Outcome.outcome_date)).all()

    return outcomes


@router.patch("/outcomes/{outcome_id}", response_model=OutcomeResponse)
async def update_outcome(
    outcome_id: int,
    update: OutcomeCreate,
    db: Session = Depends(get_db)
):
    """
    Update an outcome record.

    **Requires authentication.**

    Use this to:
    - Update partial outcomes with final data
    - Correct errors
    - Add variance explanations
    """
    outcome = db.query(Outcome).filter(Outcome.id == outcome_id).first()

    if not outcome:
        raise HTTPException(status_code=404, detail="Outcome not found")

    # Update fields
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(outcome, field, value)

    # Recalculate accuracy
    outcome.calculate_accuracy()

    db.commit()
    db.refresh(outcome)

    return outcome


# ============================================================================
# Bulk Operations
# ============================================================================


@router.get("", response_model=DecisionListResponse)
async def list_decisions(
    city_id: Optional[int] = Query(None, description="Filter by city"),
    category: Optional[DecisionCategory] = Query(None, description="Filter by category"),
    status: Optional[DecisionStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter by decision date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by decision date (to)"),
    min_impact: Optional[float] = Query(None, description="Minimum predicted impact (absolute value)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    List decisions with filtering and pagination.

    **Requires authentication.**

    Supports filtering by:
    - City
    - Category (budget, tax, bond, labor, etc.)
    - Status (proposed, approved, rejected, etc.)
    - Date range
    - Minimum fiscal impact

    Returns summary information. Use GET /{decision_id} for full details.
    """
    query = db.query(Decision).filter(Decision.is_deleted == False)

    # Apply filters
    if city_id is not None:
        query = query.filter(Decision.city_id == city_id)

    if category is not None:
        query = query.filter(Decision.category == category)

    if status is not None:
        query = query.filter(Decision.status == status)

    if start_date is not None:
        query = query.filter(Decision.decision_date >= start_date)

    if end_date is not None:
        query = query.filter(Decision.decision_date <= end_date)

    if min_impact is not None:
        query = query.filter(
            func.abs(Decision.predicted_annual_impact) >= min_impact
        )

    # Get total count
    total = query.count()

    # Apply pagination
    decisions = query.order_by(desc(Decision.decision_date)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return DecisionListResponse(
        decisions=decisions,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )
