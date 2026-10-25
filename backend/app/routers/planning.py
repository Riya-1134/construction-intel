"""Text / structured-data endpoints: project planner and real-estate valuation."""
from __future__ import annotations

import json

from fastapi import APIRouter

from ..ai_service import run_feature
from ..schemas import PlanRequest, ProjectPlan, ValuationReport, ValuationRequest
from ..visualization import render_concept_svg

router = APIRouter(prefix="/api", tags=["planning-valuation"])


@router.post("/planner/generate", response_model=ProjectPlan)
def generate_plan(body: PlanRequest) -> ProjectPlan:
    payload = body.model_dump()
    user_text = (
        "Generate a complete construction project plan for the following inputs:\n"
        + json.dumps(payload, indent=2)
    )
    plan = run_feature("planner", ProjectPlan, user_text, context=payload)

    # Derived consistency: never show zero area/cost-per-sqft if the AI omitted them.
    if plan.built_up_area_sqft <= 0:
        plan.built_up_area_sqft = round(body.plot_length_ft * body.plot_width_ft * 0.75 * body.floors)
    if plan.cost_per_sqft_inr <= 0 and plan.total_estimated_cost_inr > 0:
        plan.cost_per_sqft_inr = round(plan.total_estimated_cost_inr / plan.built_up_area_sqft)
    if plan.total_estimated_cost_inr <= 0 and plan.cost_per_sqft_inr > 0:
        plan.total_estimated_cost_inr = round(plan.cost_per_sqft_inr * plan.built_up_area_sqft)
    if plan.duration_weeks <= 0 and plan.schedule:
        plan.duration_weeks = max(p.start_week + p.duration_weeks - 1 for p in plan.schedule)

    plan.visualization.svg = render_concept_svg(
        body.plot_length_ft, body.plot_width_ft, body.floors,
        body.construction_type, plan.visualization.style or "contemporary",
    )
    return plan


@router.post("/valuation/estimate", response_model=ValuationReport)
def estimate_value(body: ValuationRequest) -> ValuationReport:
    payload = body.model_dump()
    user_text = (
        "Estimate the indicative market value of this Indian property:\n"
        + json.dumps(payload, indent=2)
    )
    report = run_feature("valuation", ValuationReport, user_text, context=payload)

    # Numeric consistency guards
    lo, hi = report.estimated_value_min_inr, report.estimated_value_max_inr
    if lo > hi > 0:
        report.estimated_value_min_inr, report.estimated_value_max_inr = hi, lo
        lo, hi = hi, lo
    if report.estimated_value_inr <= 0 and hi > 0:
        report.estimated_value_inr = round((lo + hi) / 2)
    if report.estimated_value_inr <= 0 and report.price_per_sqft_inr > 0:
        report.estimated_value_inr = round(report.price_per_sqft_inr * body.area_sqft)
    if lo <= 0 and report.estimated_value_inr > 0:
        report.estimated_value_min_inr = round(report.estimated_value_inr * 0.9)
    if hi <= 0 and report.estimated_value_inr > 0:
        report.estimated_value_max_inr = round(report.estimated_value_inr * 1.1)
    if report.price_per_sqft_inr <= 0 and report.estimated_value_inr > 0:
        report.price_per_sqft_inr = round(report.estimated_value_inr / body.area_sqft)
    if report.rental_yield_percent <= 0 and report.estimated_value_inr > 0 and report.monthly_rent_max_inr > 0:
        avg_rent = (report.monthly_rent_min_inr + report.monthly_rent_max_inr) / 2
        report.rental_yield_percent = round(avg_rent * 12 / report.estimated_value_inr * 100, 2)
    return report
