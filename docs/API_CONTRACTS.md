# API Contracts

All responses are JSON. Every key below is **always present** (lists may be empty, numbers may be 0).
Each response ends with:

```json
"meta": { "feature": "safety", "model": "qwen/qwen3.8-27b", "ai_generated": true, "notes": [] }
```

`ai_generated: false` with `model: "demo"` means the deterministic fallback was used; `notes` explains why.

Validation failures: `422 {"detail": "Invalid input", "errors": [{"field": "plot_length_ft", "message": "..."}]}`.
Bad uploads: `415` (not an image), `413` (over 8 MB). Missing both image and text: `422`.

---

## POST /api/safety/analyze  (multipart/form-data)
Request fields: `image` (file, optional), `description` (text, optional, ≤2000), `site_type` (optional).

```json
{
  "summary": "string",
  "risk_level": "low | medium | high | critical",
  "risk_score": 0,
  "hazards": ["string"],
  "ppe_observed": ["string"],
  "ppe_missing": ["string"],
  "recommended_ppe": ["string"],
  "corrective_actions": ["string"],
  "safety_guidelines": ["string"],
  "image_quality": "clear | partially clear | unclear | not provided | ...",
  "meta": {}
}
```

## POST /api/crack/analyze  (multipart/form-data)
Request fields: `image` (optional), `description` (optional), `element` (optional), `building_age_years` (0-300, optional).

```json
{
  "crack_detected": true,
  "crack_type": "string",
  "orientation": "string",
  "severity": "minor | moderate | severe",
  "estimated_width_mm": 0.0,
  "probable_causes": ["string"],
  "structural_concern": false,
  "potential_risks": ["string"],
  "repair_methods": ["string"],
  "preventive_measures": ["string"],
  "inspection_priority": "monitor | schedule inspection | urgent structural assessment",
  "confidence": 0,
  "meta": {}
}
```

## POST /api/planner/generate  (application/json)
```json
{ "plot_length_ft": 30, "plot_width_ft": 40, "floors": 2, "construction_type": "residential",
  "quality": "basic | standard | premium", "city": "Pune", "additional_requirements": null }
```
Response:
```json
{
  "project_summary": "string",
  "built_up_area_sqft": 0.0,
  "total_estimated_cost_inr": 0.0,
  "cost_per_sqft_inr": 0.0,
  "duration_weeks": 0,
  "materials": [{ "material": "string", "quantity": 0.0, "unit": "string", "estimated_cost_inr": 0.0 }],
  "cost_breakdown": [{ "category": "string", "amount_inr": 0.0, "percentage": 0.0 }],
  "schedule": [{ "phase": "string", "start_week": 1, "duration_weeks": 1, "tasks": ["string"] }],
  "assumptions": ["string"],
  "visualization": { "concept_description": "string", "style": "string", "floor_plan_notes": ["string"], "svg": "<svg ...>" },
  "meta": {}
}
```

## POST /api/valuation/estimate  (application/json)
```json
{ "city": "Bengaluru", "locality": "Whitefield", "property_type": "apartment", "area_sqft": 1200,
  "bedrooms": 2, "building_age_years": 5, "floor_number": 4, "furnishing": "semi-furnished",
  "amenities": ["gym"], "nearby_landmarks": "metro 2 km" }
```
Response:
```json
{
  "summary": "string",
  "estimated_value_min_inr": 0.0, "estimated_value_max_inr": 0.0, "estimated_value_inr": 0.0,
  "price_per_sqft_inr": 0.0,
  "monthly_rent_min_inr": 0.0, "monthly_rent_max_inr": 0.0,
  "rental_yield_percent": 0.0, "expected_annual_appreciation_percent": 0.0, "five_year_roi_percent": 0.0,
  "investment_outlook": "strong | positive | neutral | cautious | weak",
  "value_drivers": ["string"], "risk_factors": ["string"],
  "confidence": 0,
  "meta": {}
}
```

## POST /api/chat  (application/json)
```json
{ "message": "string (1-4000)", "history": [{ "role": "user | assistant", "content": "string" }] }
```
Response:
```json
{ "answer": "string", "key_points": ["string"], "references": ["string"],
  "follow_up_questions": ["string"], "disclaimer": "string", "meta": {} }
```

## POST /api/daily/plan  (application/json)
```json
{ "project_stage": "Superstructure", "planned_activities": "string", "workforce": "string",
  "site_conditions": "string", "weather": "string", "date": "2026-10-25" }
```
Response:
```json
{
  "day_summary": "string",
  "tasks": [{ "task": "string", "priority": "high | medium | low", "crew": "string", "duration_hours": 0.0 }],
  "materials_required": ["string"], "equipment_required": ["string"],
  "safety_checks": ["string"], "risk_alerts": ["string"], "end_of_day_checklist": ["string"],
  "meta": {}
}
```

## POST /api/weather/advisory  (application/json)
```json
{ "planned_activities": "string", "weather_conditions": "string", "temperature_c": 34,
  "wind_speed_kmph": 25, "rain_probability_percent": 60, "location": "Mumbai" }
```
Response:
```json
{
  "decision": "GO | CAUTION | NO-GO",
  "confidence": 0,
  "rationale": "string",
  "identified_risks": ["string"], "affected_activities": ["string"],
  "precautions": ["string"], "mitigation_steps": ["string"],
  "recommended_window": "string",
  "meta": {}
}
```

## Coercion rules (backend/app/schemas.py)
- Strings/dicts/mixed lists are normalised into `List[str]`; `null` becomes `[]`.
- Numeric strings such as `"₹12,00,000"` or `"40%"` are parsed; unparseable values default to 0 (or 50 for confidence).
- Enumerations are matched by substring and case-insensitively (`"HIGH risk"` → `high`, `"no go"` → `NO-GO`).
- Unknown keys are ignored; missing keys take defaults.
