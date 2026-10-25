"""Deterministic demo payloads used when the LLM is unavailable (no key, DEMO_MODE,
network failure, or repeated schema failures). They follow the same JSON contracts so the
UI can be demonstrated end-to-end offline. Numeric values use common Indian thumb rules."""
from __future__ import annotations

from typing import Any, Dict, Optional

CITY_RATES_INR_PER_SQFT = {  # indicative construction cost (standard quality)
    "mumbai": 2600, "delhi": 2200, "bengaluru": 2100, "bangalore": 2100, "hyderabad": 1900,
    "chennai": 2000, "pune": 2100, "kolkata": 1800, "ahmedabad": 1700, "jaipur": 1600,
    "lucknow": 1550, "indore": 1500, "bhopal": 1500, "nagpur": 1550, "surat": 1650,
}
CITY_PROPERTY_RATES = {  # indicative resale price per sq ft for mid-segment apartments
    "mumbai": 22000, "delhi": 14000, "gurugram": 11000, "gurgaon": 11000, "noida": 7500,
    "bengaluru": 9000, "bangalore": 9000, "hyderabad": 7000, "chennai": 7500, "pune": 8000,
    "kolkata": 6000, "ahmedabad": 5000, "jaipur": 4500, "lucknow": 4800, "indore": 4200,
    "bhopal": 3800, "nagpur": 4500, "surat": 4300, "kochi": 6000, "chandigarh": 7000,
}
QUALITY_FACTOR = {"basic": 0.8, "standard": 1.0, "premium": 1.35}


def _city_key(city: str) -> str:
    return (city or "").strip().lower()


def build(feature: str, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    builder = _BUILDERS.get(feature)
    return builder(ctx) if builder else None


def _safety(ctx: Dict[str, Any]) -> Dict[str, Any]:
    has_image = bool(ctx.get("has_image"))
    return {
        "summary": ("Demo analysis: the uploaded image was received but AI vision is disabled. "
                    if has_image else "Demo analysis: no image was supplied. ")
                   + "Typical site hazards and PPE requirements are listed for reference.",
        "risk_level": "medium",
        "risk_score": 55,
        "hazards": ["Workers near unguarded slab edge", "Loose debris on walkways",
                    "Scaffold without toe boards", "Exposed rebar ends without caps"],
        "ppe_observed": ["Safety helmets on some workers"],
        "ppe_missing": ["High-visibility vests", "Safety harness at height", "Safety boots"],
        "recommended_ppe": ["Safety helmet (IS 2925)", "High-visibility vest", "Steel-toe boots",
                            "Full-body harness with lanyard", "Gloves", "Safety goggles"],
        "corrective_actions": ["Install edge protection / guardrails before work resumes",
                               "Clear debris and mark walkways", "Fit toe boards and tie scaffold to structure",
                               "Issue and enforce PPE at the gate"],
        "safety_guidelines": ["Daily toolbox talk before shift", "Work-at-height permit above 1.8 m",
                              "Housekeeping inspection every shift", "Display emergency contacts on site"],
        "image_quality": "clear" if has_image else "not provided",
    }


def _crack(ctx: Dict[str, Any]) -> Dict[str, Any]:
    desc = (ctx.get("description") or "").lower()
    diagonal = "diagonal" in desc or "stair" in desc or "step" in desc
    return {
        "crack_detected": True,
        "crack_type": "diagonal (stepped masonry)" if diagonal else "vertical plaster / shrinkage",
        "orientation": "diagonal ~45 degrees" if diagonal else "vertical",
        "severity": "moderate" if diagonal else "minor",
        "estimated_width_mm": 2.5 if diagonal else 0.8,
        "probable_causes": (["Differential foundation settlement", "Load concentration near opening"]
                            if diagonal else ["Plaster shrinkage during curing", "Thermal movement"]),
        "structural_concern": diagonal,
        "potential_risks": (["Progressive widening and masonry displacement", "Water ingress"]
                            if diagonal else ["Moisture ingress and paint failure"]),
        "repair_methods": (["Install tell-tale gauges and monitor 4-6 weeks", "Stitch with helical bars after settlement stabilises",
                            "Repoint and seal with polymer-modified mortar"]
                           if diagonal else ["Open V-groove, fill with polymer crack filler",
                                             "Apply fibre-mesh and re-plaster", "Repaint with elastomeric coating"]),
        "preventive_measures": ["Ensure proper curing of plaster (7 days minimum)", "Maintain drainage away from foundation",
                                "Provide control joints at long wall runs"],
        "inspection_priority": "schedule inspection" if diagonal else "monitor",
        "confidence": 40,
    }


def _planner(ctx: Dict[str, Any]) -> Dict[str, Any]:
    length = float(ctx.get("plot_length_ft") or 30)
    width = float(ctx.get("plot_width_ft") or 40)
    floors = int(ctx.get("floors") or 1)
    quality = str(ctx.get("quality") or "standard")
    city = str(ctx.get("city") or "")
    coverage = 0.75
    bua = round(length * width * coverage * floors)
    rate = round(CITY_RATES_INR_PER_SQFT.get(_city_key(city), 1800) * QUALITY_FACTOR.get(quality, 1.0))
    total = bua * rate
    materials = [
        {"material": "Cement (OPC 53)", "quantity": round(bua * 0.4), "unit": "bags", "estimated_cost_inr": round(bua * 0.4 * 380)},
        {"material": "Sand (river/M-sand)", "quantity": round(bua * 1.3), "unit": "cft", "estimated_cost_inr": round(bua * 1.3 * 55)},
        {"material": "Aggregate (20 mm)", "quantity": round(bua * 1.6), "unit": "cft", "estimated_cost_inr": round(bua * 1.6 * 45)},
        {"material": "Steel (Fe500 TMT)", "quantity": round(bua * 4.0), "unit": "kg", "estimated_cost_inr": round(bua * 4.0 * 68)},
        {"material": "Bricks / AAC blocks", "quantity": round(bua * 9), "unit": "nos", "estimated_cost_inr": round(bua * 9 * 9)},
    ]
    breakdown = [
        ("Structure (RCC + masonry)", 0.42), ("Finishing (plaster, flooring, paint)", 0.25),
        ("Plumbing & sanitary", 0.08), ("Electrical", 0.08), ("Doors & windows", 0.07),
        ("Labour overheads & contingency", 0.10),
    ]
    weeks = max(16, 20 + (floors - 1) * 10 + bua // 400)
    schedule = [
        {"phase": "Site preparation & layout", "start_week": 1, "duration_weeks": 2, "tasks": ["Clearing", "Setting out", "Soil test review"]},
        {"phase": "Foundation & plinth", "start_week": 3, "duration_weeks": 4, "tasks": ["Excavation", "PCC", "Footings", "Plinth beam", "Backfill"]},
        {"phase": "Superstructure", "start_week": 7, "duration_weeks": 5 * floors, "tasks": ["Columns", "Beams & slab", "Masonry", "Lintels"]},
        {"phase": "MEP rough-in", "start_week": 7 + 5 * floors, "duration_weeks": 3, "tasks": ["Conduits", "Plumbing lines", "Water tank"]},
        {"phase": "Finishing", "start_week": 10 + 5 * floors, "duration_weeks": 6, "tasks": ["Plaster", "Flooring", "Doors/windows", "Painting"]},
        {"phase": "Handover", "start_week": 16 + 5 * floors, "duration_weeks": 2, "tasks": ["Snag list", "Cleaning", "Completion certificate"]},
    ]
    return {
        "project_summary": f"Demo estimate for a {floors}-floor {ctx.get('construction_type', 'residential')} building on a "
                           f"{length:g} x {width:g} ft plot in {city or 'an Indian city'} ({quality} quality).",
        "built_up_area_sqft": bua,
        "total_estimated_cost_inr": total,
        "cost_per_sqft_inr": rate,
        "duration_weeks": weeks,
        "materials": materials,
        "cost_breakdown": [{"category": c, "amount_inr": round(total * p), "percentage": round(p * 100)} for c, p in breakdown],
        "schedule": schedule,
        "assumptions": [f"Ground coverage {int(coverage * 100)}% of plot area", "Standard soil bearing capacity",
                        "Rates indicative; verify with local contractors", "Excludes land, approvals and interior furniture"],
        "visualization": {
            "concept_description": f"Compact {floors}-storey massing with a street-facing facade, projecting balconies, "
                                   "parapet-level screen and a shaded entrance porch. Orientation prioritises cross ventilation.",
            "style": "Contemporary Indian residential",
            "floor_plan_notes": ["Living and kitchen on the ground floor front", "Staircase at the centre for stacking",
                                 "Service duct on the rear wall", "Setbacks as per local bye-laws"],
        },
    }


def _valuation(ctx: Dict[str, Any]) -> Dict[str, Any]:
    area = float(ctx.get("area_sqft") or 1000)
    city = str(ctx.get("city") or "")
    age = int(ctx.get("building_age_years") or 0)
    base = CITY_PROPERTY_RATES.get(_city_key(city), 5000)
    rate = round(base * max(0.6, 1 - 0.012 * age))
    if str(ctx.get("property_type", "")).lower() in ("plot", "land"):
        rate = round(rate * 0.7)
    mid = rate * area
    rent_mid = mid * 0.03 / 12
    return {
        "summary": f"Demo valuation for a {area:g} sq ft {ctx.get('property_type', 'property')} in {city or 'the city'}"
                   + (f", {ctx['locality']}" if ctx.get("locality") else "")
                   + f". Indicative rate about INR {rate:,} per sq ft after adjusting for a {age}-year-old building.",
        "estimated_value_min_inr": round(mid * 0.9),
        "estimated_value_max_inr": round(mid * 1.1),
        "estimated_value_inr": round(mid),
        "price_per_sqft_inr": rate,
        "monthly_rent_min_inr": round(rent_mid * 0.85),
        "monthly_rent_max_inr": round(rent_mid * 1.15),
        "rental_yield_percent": 3.0,
        "expected_annual_appreciation_percent": 6.0,
        "five_year_roi_percent": 48.0,
        "investment_outlook": "positive",
        "value_drivers": ["Location tier and connectivity", "Carpet-to-super area efficiency", "Listed amenities"],
        "risk_factors": ["Rates are indicative, not a registered valuation", "Age-related maintenance costs",
                         "Local oversupply can suppress rental growth"],
        "confidence": 35,
    }


def _chat(ctx: Dict[str, Any]) -> Dict[str, Any]:
    q = str(ctx.get("message") or "your question")
    return {
        "answer": f"(Demo mode) I received: \"{q[:200]}\". Connect a GROQ_API_KEY to get a full construction-domain "
                  "answer. In the meantime: for most RCC residential work in India, M20-M25 concrete, Fe500 TMT steel, "
                  "7-day minimum curing and IS 456 detailing are the usual baseline.",
        "key_points": ["Set GROQ_API_KEY in backend/.env to enable live answers",
                       "Follow IS 456 for RCC and NBC 2016 for general building requirements"],
        "references": ["IS 456:2000", "NBC 2016", "IS 3764 (excavation safety)"],
        "follow_up_questions": ["What concrete grade suits my slab span?", "How long should I cure a slab?"],
        "disclaimer": "AI-generated guidance; verify with a qualified engineer and applicable codes.",
    }


def _daily(ctx: Dict[str, Any]) -> Dict[str, Any]:
    stage = str(ctx.get("project_stage") or "construction")
    return {
        "day_summary": f"Demo plan for the {stage} stage based on: {str(ctx.get('planned_activities') or '')[:120]}",
        "tasks": [
            {"task": "Morning toolbox talk and PPE check", "priority": "high", "crew": "All", "duration_hours": 0.5},
            {"task": "Verify formwork alignment and props", "priority": "high", "crew": "Carpenters", "duration_hours": 2},
            {"task": "Rebar placement and cover checks", "priority": "high", "crew": "Bar benders", "duration_hours": 4},
            {"task": "Material receipt and stacking", "priority": "medium", "crew": "Helpers", "duration_hours": 2},
            {"task": "Update daily progress report", "priority": "low", "crew": "Site engineer", "duration_hours": 0.5},
        ],
        "materials_required": ["Cement", "Binding wire", "Cover blocks", "Shuttering oil"],
        "equipment_required": ["Concrete mixer", "Vibrator", "Total station / level", "Bar bending machine"],
        "safety_checks": ["Edge protection in place", "Scaffold tags current", "First-aid kit stocked",
                          "Electrical boards with ELCB"],
        "risk_alerts": ["Heat stress after 12:00 - schedule breaks and water", "Material handling near open shafts"],
        "end_of_day_checklist": ["Cover exposed rebar", "Secure tools and equipment", "Log manpower and consumption",
                                 "Note tomorrow's concrete pour quantity"],
    }


def _weather(ctx: Dict[str, Any]) -> Dict[str, Any]:
    weather = str(ctx.get("weather_conditions") or "").lower()
    rain = ctx.get("rain_probability_percent") or 0
    wind = ctx.get("wind_speed_kmph") or 0
    temp = ctx.get("temperature_c")
    severe = "storm" in weather or "heavy rain" in weather or (rain and rain >= 70) or (wind and wind >= 40) \
        or (temp is not None and temp >= 42)
    moderate = "rain" in weather or "drizzle" in weather or (rain and rain >= 40) or (wind and wind >= 25) \
        or (temp is not None and temp >= 38)
    decision = "NO-GO" if severe else "CAUTION" if moderate else "GO"
    return {
        "decision": decision,
        "confidence": 45,
        "rationale": f"Demo rule-based advisory for '{weather[:80]}'. Live AI reasoning is disabled.",
        "identified_risks": (["Concrete washout and segregation", "Slippery access and fall risk", "Lightning at height"]
                             if decision != "GO" else ["No significant weather risk identified"]),
        "affected_activities": ["Concreting", "Crane lifts", "Work at height"] if decision != "GO" else [],
        "precautions": ["Cover stacked cement and fresh concrete", "Check scaffold ties and anchorage",
                        "Brief crews on heat/rain protocol"],
        "mitigation_steps": (["Postpone pours until rain clears", "Stop crane operations above 38 km/h wind",
                              "Re-sequence to indoor finishing work"] if decision != "GO"
                             else ["Proceed with normal supervision", "Monitor forecast hourly"]),
        "recommended_window": "Re-assess at 10:00 and 14:00" if decision != "GO" else "Full working day",
    }


_BUILDERS = {
    "safety": _safety,
    "crack": _crack,
    "planner": _planner,
    "valuation": _valuation,
    "chat": _chat,
    "daily": _daily,
    "weather": _weather,
}
