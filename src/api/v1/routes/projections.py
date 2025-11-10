"""
Financial projection endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.v1.schemas.projections import (
    FinancialProjectionResponse,
    FiscalCliffAnalysisResponse,
    ProjectionScenarioResponse,
    ScenarioComparisonResponse
)
from src.database.models.core import City, FiscalYear
from src.database.models.projections import (
    FinancialProjection,
    ProjectionScenario,
    FiscalCliffAnalysis
)
from src.analytics.projections.scenario_engine import ScenarioEngine

router = APIRouter(prefix="/projections")


@router.get("/scenarios", response_model=List[ProjectionScenarioResponse])
async def list_scenarios(db: Session = Depends(get_db)):
    """
    List available projection scenarios.
    """
    scenarios = db.query(ProjectionScenario).filter(
        ProjectionScenario.is_active == True
    ).order_by(ProjectionScenario.display_order).all()

    return scenarios


@router.get("/cities/{city_id}/projections", response_model=List[FinancialProjectionResponse])
async def get_city_projections(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    scenario: Optional[str] = Query("base", description="Scenario code"),
    db: Session = Depends(get_db)
):
    """
    Get financial projections for a city.

    Query Parameters:
    - base_year: The fiscal year to project from (required)
    - scenario: Scenario to use (base, optimistic, pessimistic)
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    scenario_obj = db.query(ProjectionScenario).filter(
        ProjectionScenario.scenario_code == scenario
    ).first()

    if not scenario_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")

    projections = db.query(FinancialProjection).filter(
        FinancialProjection.city_id == city_id,
        FinancialProjection.base_fiscal_year_id == base_fy.id,
        FinancialProjection.scenario_id == scenario_obj.id
    ).order_by(FinancialProjection.projection_year).all()

    if not projections:
        raise HTTPException(
            status_code=404,
            detail="No projections found. Run /calculate first."
        )

    return projections


@router.post("/cities/{city_id}/calculate")
async def calculate_projections(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    years_ahead: int = Query(10, ge=1, le=20, description="Years to project"),
    scenario: Optional[str] = Query(None, description="Scenario code (default: all scenarios)"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Calculate financial projections for a city.

    Generates projections for specified scenario or all scenarios if not specified.
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    def calculate():
        engine = ScenarioEngine(db, city_id)

        if scenario:
            # Calculate single scenario
            projections, analysis = engine.run_scenario(
                base_year, years_ahead, scenario
            )
            engine.save_scenario(projections, analysis)
        else:
            # Calculate all scenarios
            all_results = engine.run_all_scenarios(base_year, years_ahead)
            for scenario_code, (projections, analysis) in all_results.items():
                engine.save_scenario(projections, analysis)

    if background_tasks:
        background_tasks.add_task(calculate)
        return {
            "status": "calculating",
            "message": f"Generating projections for {years_ahead} years"
        }
    else:
        calculate()
        return {
            "status": "completed",
            "message": "Projections calculated successfully"
        }


@router.get("/cities/{city_id}/fiscal-cliff", response_model=FiscalCliffAnalysisResponse)
async def get_fiscal_cliff_analysis(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    scenario: str = Query("base", description="Scenario code"),
    db: Session = Depends(get_db)
):
    """
    Get fiscal cliff analysis for a city.

    Shows when/if the city will exhaust reserves.
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    scenario_obj = db.query(ProjectionScenario).filter(
        ProjectionScenario.scenario_code == scenario
    ).first()

    if not scenario_obj:
        raise HTTPException(status_code=404, detail="Scenario not found")

    analysis = db.query(FiscalCliffAnalysis).filter(
        FiscalCliffAnalysis.city_id == city_id,
        FiscalCliffAnalysis.base_fiscal_year_id == base_fy.id,
        FiscalCliffAnalysis.scenario_id == scenario_obj.id
    ).first()

    if not analysis:
        # Calculate it on-demand
        engine = ScenarioEngine(db, city_id)
        projections, analysis = engine.run_scenario(base_year, 10, scenario)
        engine.save_scenario(projections, analysis)

    return analysis


@router.get("/cities/{city_id}/compare-scenarios", response_model=ScenarioComparisonResponse)
async def compare_scenarios(
    city_id: int,
    base_year: int = Query(..., description="Base fiscal year"),
    years_ahead: int = Query(10, ge=1, le=20, description="Years to project"),
    db: Session = Depends(get_db)
):
    """
    Compare outcomes across all scenarios.

    Shows difference between optimistic, base, and pessimistic scenarios.
    """
    base_fy = db.query(FiscalYear).filter(
        FiscalYear.city_id == city_id,
        FiscalYear.year == base_year
    ).first()

    if not base_fy:
        raise HTTPException(status_code=404, detail="Base fiscal year not found")

    # Check if projections exist
    for scenario_code in ["base", "optimistic", "pessimistic"]:
        scenario_obj = db.query(ProjectionScenario).filter(
            ProjectionScenario.scenario_code == scenario_code
        ).first()

        if scenario_obj:
            projections = db.query(FinancialProjection).filter(
                FinancialProjection.city_id == city_id,
                FinancialProjection.base_fiscal_year_id == base_fy.id,
                FinancialProjection.scenario_id == scenario_obj.id
            ).first()

            if not projections:
                raise HTTPException(
                    status_code=404,
                    detail=f"Projections not found for {scenario_code} scenario. Run /calculate first."
                )

    # Run comparison
    engine = ScenarioEngine(db, city_id)
    comparison = engine.compare_scenarios(base_year, years_ahead)

    return comparison
