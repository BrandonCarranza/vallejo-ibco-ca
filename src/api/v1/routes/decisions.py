"""
Public API routes for city council decisions.

Provides public access to decision tracking data, enabling transparency
and institutional credibility analysis.
"""
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from src.api.dependencies import get_db
from src.api.v1.schemas.civic import (
    DecisionAccuracyReport,
    DecisionDetailResponse,
    DecisionListResponse,
    DecisionSummaryResponse,
)
from src.database.models.civic import Decision, DecisionCategory, DecisionStatus, Outcome, OutcomeStatus
from src.database.models.core import City

router = APIRouter(prefix="/decisions", tags=["Decisions"])


@router.get("", response_model=DecisionListResponse)
async def get_decisions(
    city_id: Optional[int] = Query(None, description="Filter by city"),
    category: Optional[DecisionCategory] = Query(None, description="Filter by category"),
    status: Optional[DecisionStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter by decision date (from)"),
    end_date: Optional[date] = Query(None, description="Filter by decision date (to)"),
    min_impact: Optional[float] = Query(None, description="Minimum predicted impact (absolute value)"),
    has_outcomes: Optional[bool] = Query(None, description="Filter decisions with outcomes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    Query city council decisions and ballot measures.

    **Public endpoint** - No authentication required.

    Search and filter decisions by:
    - City
    - Category (budget, tax, bond, labor, etc.)
    - Status (proposed, approved, rejected, etc.)
    - Date range
    - Minimum fiscal impact
    - Whether outcomes have been tracked

    Returns summary information. Use GET /{decision_id} for full details
    including votes and outcome tracking.

    **Example queries:**

    - All sales tax measures: `?category=tax`
    - Recent decisions: `?start_date=2024-01-01`
    - Decisions with outcomes: `?has_outcomes=true`
    - High-impact decisions: `?min_impact=10000000` (≥$10M)
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

    if has_outcomes is not None:
        if has_outcomes:
            # Has at least one outcome
            query = query.join(Decision.outcomes).distinct()
        else:
            # No outcomes
            query = query.outerjoin(Decision.outcomes).filter(Outcome.id == None)

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


@router.get("/{decision_id}", response_model=DecisionDetailResponse)
async def get_decision(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific decision.

    **Public endpoint** - No authentication required.

    Includes:
    - Complete decision details
    - Predicted fiscal impact
    - Individual votes (if recorded)
    - Outcome tracking over time
    - Prediction accuracy (if final outcomes available)

    **Example response includes:**
    - Decision description and context
    - Vote breakdown (yes/no/abstain)
    - Initial prediction: +$25M annual revenue
    - 6-month outcome: +$12.5M (on track)
    - Final outcome: +$26M (104% accuracy)
    """
    decision = db.query(Decision).options(
        joinedload(Decision.votes),
        joinedload(Decision.outcomes)
    ).filter(
        Decision.id == decision_id,
        Decision.is_deleted == False
    ).first()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@router.get("/cities/{city_id}/accuracy", response_model=DecisionAccuracyReport)
async def get_decision_accuracy_report(
    city_id: int,
    start_date: Optional[date] = Query(None, description="Report period start"),
    end_date: Optional[date] = Query(None, description="Report period end"),
    db: Session = Depends(get_db)
):
    """
    Get prediction accuracy report for a city.

    **Public endpoint** - No authentication required.

    Analyzes how accurate fiscal impact predictions have been compared
    to actual outcomes. This transparency builds institutional credibility.

    **Metrics included:**
    - Overall accuracy statistics
    - Breakdown by decision category
    - Best and worst predictions
    - Key insights and learnings

    **Use this to:**
    - Demonstrate analytical rigor
    - Build public trust through transparency
    - Identify areas for methodology improvement
    - Show accountability (acknowledging both successes and failures)

    **Example insights:**
    - "Tax revenue predictions 98% accurate on average"
    - "Labor contract costs tend to exceed initial estimates by 15%"
    - "Bond proceeds consistently track within 5% of projections"
    """
    # Verify city exists
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Query decisions with final outcomes
    query = db.query(Decision).join(Decision.outcomes).filter(
        Decision.city_id == city_id,
        Decision.is_deleted == False,
        Outcome.status == OutcomeStatus.FINAL,
        Decision.predicted_annual_impact.isnot(None),
        Outcome.actual_annual_impact.isnot(None)
    )

    if start_date:
        query = query.filter(Decision.decision_date >= start_date)
    if end_date:
        query = query.filter(Decision.decision_date <= end_date)

    decisions = query.all()

    # Calculate statistics
    total_decisions = db.query(Decision).filter(
        Decision.city_id == city_id,
        Decision.is_deleted == False
    ).count()

    decisions_with_outcomes = len(decisions)

    if decisions_with_outcomes == 0:
        # No outcomes yet
        return DecisionAccuracyReport(
            total_decisions=total_decisions,
            decisions_with_outcomes=0,
            avg_accuracy_percent=0,
            median_accuracy_percent=0,
            accurate_predictions=0,
            inaccurate_predictions=0,
            by_category={},
            insights=["No final outcomes tracked yet. Predictions pending verification."]
        )

    # Calculate accuracy for each decision
    accuracies = []
    accurate_count = 0  # Within 10%
    inaccurate_count = 0  # More than 25% off

    for decision in decisions:
        accuracy = decision.prediction_accuracy_percent
        if accuracy:
            accuracies.append(accuracy)

            # Count accurate/inaccurate
            if 90 <= accuracy <= 110:  # Within 10%
                accurate_count += 1
            elif accuracy < 75 or accuracy > 125:  # More than 25% off
                inaccurate_count += 1

    # Overall statistics
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
    median_accuracy = sorted(accuracies)[len(accuracies) // 2] if accuracies else 0

    # Find best and worst predictions
    best_decision = min(
        decisions,
        key=lambda d: abs(100 - d.prediction_accuracy_percent) if d.prediction_accuracy_percent else float('inf')
    )
    worst_decision = max(
        decisions,
        key=lambda d: abs(100 - d.prediction_accuracy_percent) if d.prediction_accuracy_percent else 0
    )

    # Breakdown by category
    by_category = {}
    for category in DecisionCategory:
        cat_decisions = [d for d in decisions if d.category == category]
        if cat_decisions:
            cat_accuracies = [
                d.prediction_accuracy_percent
                for d in cat_decisions
                if d.prediction_accuracy_percent
            ]
            if cat_accuracies:
                by_category[category.value] = {
                    "count": len(cat_decisions),
                    "avg_accuracy": sum(cat_accuracies) / len(cat_accuracies),
                    "median_accuracy": sorted(cat_accuracies)[len(cat_accuracies) // 2]
                }

    # Generate insights
    insights = []

    if avg_accuracy >= 95:
        insights.append(
            f"Excellent prediction accuracy: {avg_accuracy:.1f}% average across {decisions_with_outcomes} decisions"
        )
    elif avg_accuracy >= 85:
        insights.append(
            f"Good prediction accuracy: {avg_accuracy:.1f}% average across {decisions_with_outcomes} decisions"
        )
    else:
        insights.append(
            f"Prediction accuracy: {avg_accuracy:.1f}% average across {decisions_with_outcomes} decisions. "
            "Methodology improvements recommended."
        )

    if accurate_count > 0:
        insights.append(
            f"{accurate_count} predictions within 10% of actual (highly accurate)"
        )

    if inaccurate_count > 0:
        insights.append(
            f"{inaccurate_count} predictions >25% off from actual. "
            "See variance_explanation fields for analysis."
        )

    # Category-specific insights
    for category, stats in by_category.items():
        if stats["avg_accuracy"] >= 95:
            insights.append(
                f"{category.title()} predictions highly reliable ({stats['avg_accuracy']:.1f}% accuracy)"
            )
        elif stats["avg_accuracy"] < 80:
            insights.append(
                f"{category.title()} predictions need improvement ({stats['avg_accuracy']:.1f}% accuracy)"
            )

    # Add transparency note
    insights.append(
        "Transparent tracking of both successes and failures builds institutional credibility"
    )

    return DecisionAccuracyReport(
        total_decisions=total_decisions,
        decisions_with_outcomes=decisions_with_outcomes,
        avg_accuracy_percent=avg_accuracy,
        median_accuracy_percent=median_accuracy,
        accurate_predictions=accurate_count,
        inaccurate_predictions=inaccurate_count,
        best_prediction=DecisionSummaryResponse.model_validate(best_decision),
        worst_prediction=DecisionSummaryResponse.model_validate(worst_decision),
        by_category=by_category,
        insights=insights
    )
