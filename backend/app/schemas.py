"""Strict JSON data contracts shared by the AI layer and the frontend.

Every response model has a `fallback()` builder so the frontend always receives
every key, with safe types, even when the AI returns partial or malformed data.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Severity = Literal["low", "medium", "high", "critical"]
CrackSeverity = Literal["minor", "moderate", "severe"]


# ---------------------------------------------------------------------------
# Helpers used by validators: coerce loose AI output into the strict contract
# ---------------------------------------------------------------------------
def _as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, (list, tuple, set)):
        out: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, dict):
                text = " - ".join(str(v) for v in item.values() if v not in (None, ""))
            else:
                text = str(item)
            text = text.strip()
            if text:
                out.append(text)
        return out
    return [str(value)]


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
        try:
            return float(cleaned) if cleaned not in ("", "-", ".", "-.") else default
        except ValueError:
            return default
    return default


def _as_int(value: Any, default: int = 0) -> int:
    return int(round(_as_float(value, float(default))))


def _normalise_choice(value: Any, allowed: tuple, default: str) -> str:
    text = str(value or "").strip().lower()
    for option in allowed:
        if option in text:
            return option
    return default


def _s(v: Any, default: str = "") -> str:
    return default if v in (None, "") else str(v)


class Meta(BaseModel):
    feature: str
    model: str = "fallback"
    ai_generated: bool = False
    notes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 1. Safety image analysis
# ---------------------------------------------------------------------------
class SafetyReport(BaseModel):
    summary: str = ""
    risk_level: Severity = "medium"
    risk_score: int = Field(50, ge=0, le=100)
    hazards: List[str] = Field(default_factory=list)
    ppe_observed: List[str] = Field(default_factory=list)
    ppe_missing: List[str] = Field(default_factory=list)
    recommended_ppe: List[str] = Field(default_factory=list)
    corrective_actions: List[str] = Field(default_factory=list)
    safety_guidelines: List[str] = Field(default_factory=list)
    image_quality: str = "unknown"
    meta: Meta = Field(default_factory=lambda: Meta(feature="safety"))

    @field_validator("hazards", "ppe_observed", "ppe_missing", "recommended_ppe",
                     "corrective_actions", "safety_guidelines", mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("risk_level", mode="before")
    @classmethod
    def _risk(cls, v: Any) -> str:
        return _normalise_choice(v, ("critical", "high", "medium", "low"), "medium")

    @field_validator("risk_score", mode="before")
    @classmethod
    def _score(cls, v: Any) -> int:
        return max(0, min(100, _as_int(v, 50)))

    @field_validator("summary", "image_quality", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)

    @classmethod
    def fallback(cls, reason: str) -> "SafetyReport":
        return cls(
            summary="The image could not be fully analysed. A manual site inspection is recommended.",
            risk_level="medium",
            risk_score=50,
            hazards=["Unable to confirm hazards from the provided input"],
            recommended_ppe=["Safety helmet", "High-visibility vest", "Safety boots", "Gloves", "Eye protection"],
            corrective_actions=["Conduct a physical walk-through inspection",
                                "Re-upload a clearer, well-lit photo"],
            safety_guidelines=["Follow IS 3764 and local site safety codes",
                               "Hold a toolbox talk before work starts"],
            image_quality="unclear",
            meta=Meta(feature="safety", notes=[reason]),
        )


# ---------------------------------------------------------------------------
# 2. Crack detection
# ---------------------------------------------------------------------------
class CrackReport(BaseModel):
    crack_detected: bool = True
    crack_type: str = "unknown"
    orientation: str = "unknown"
    severity: CrackSeverity = "moderate"
    estimated_width_mm: float = 0.0
    probable_causes: List[str] = Field(default_factory=list)
    structural_concern: bool = False
    potential_risks: List[str] = Field(default_factory=list)
    repair_methods: List[str] = Field(default_factory=list)
    preventive_measures: List[str] = Field(default_factory=list)
    inspection_priority: str = "schedule inspection"
    confidence: int = Field(50, ge=0, le=100)
    meta: Meta = Field(default_factory=lambda: Meta(feature="crack"))

    @field_validator("probable_causes", "potential_risks", "repair_methods", "preventive_measures",
                     mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("severity", mode="before")
    @classmethod
    def _sev(cls, v: Any) -> str:
        return _normalise_choice(v, ("severe", "moderate", "minor"), "moderate")

    @field_validator("estimated_width_mm", mode="before")
    @classmethod
    def _width(cls, v: Any) -> float:
        return max(0.0, _as_float(v, 0.0))

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: Any) -> int:
        return max(0, min(100, _as_int(v, 50)))

    @field_validator("crack_detected", "structural_concern", mode="before")
    @classmethod
    def _bools(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in ("true", "yes", "1")
        return bool(v)

    @field_validator("crack_type", "orientation", "inspection_priority", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v, "unknown")

    @classmethod
    def fallback(cls, reason: str) -> "CrackReport":
        return cls(
            crack_detected=False,
            crack_type="unknown",
            orientation="unknown",
            severity="moderate",
            probable_causes=["Insufficient visual information to determine cause"],
            potential_risks=["Undetected progression of the crack"],
            repair_methods=["Have a structural engineer inspect the element before repair"],
            preventive_measures=["Monitor with a crack gauge and photograph weekly"],
            inspection_priority="schedule inspection",
            confidence=0,
            meta=Meta(feature="crack", notes=[reason]),
        )


# ---------------------------------------------------------------------------
# 3. Project planner
# ---------------------------------------------------------------------------
class MaterialItem(BaseModel):
    material: str = ""
    quantity: float = 0.0
    unit: str = ""
    estimated_cost_inr: float = 0.0

    @field_validator("quantity", "estimated_cost_inr", mode="before")
    @classmethod
    def _nums(cls, v: Any) -> float:
        return max(0.0, _as_float(v, 0.0))

    @field_validator("material", "unit", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


class CostItem(BaseModel):
    category: str = ""
    amount_inr: float = 0.0
    percentage: float = 0.0

    @field_validator("amount_inr", "percentage", mode="before")
    @classmethod
    def _nums(cls, v: Any) -> float:
        return max(0.0, _as_float(v, 0.0))

    @field_validator("category", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _s(v)


class SchedulePhase(BaseModel):
    phase: str = ""
    start_week: int = 1
    duration_weeks: int = 1
    tasks: List[str] = Field(default_factory=list)

    @field_validator("start_week", "duration_weeks", mode="before")
    @classmethod
    def _ints(cls, v: Any) -> int:
        return max(1, _as_int(v, 1))

    @field_validator("tasks", mode="before")
    @classmethod
    def _tasks(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("phase", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _s(v)


class Visualization(BaseModel):
    concept_description: str = ""
    style: str = ""
    floor_plan_notes: List[str] = Field(default_factory=list)
    svg: str = ""  # conceptual elevation sketch generated server-side

    @field_validator("floor_plan_notes", mode="before")
    @classmethod
    def _notes(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("concept_description", "style", "svg", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


def _dict_to_rows(v: Any) -> List[Any]:
    if isinstance(v, dict):
        out = []
        for key, val in v.items():
            if isinstance(val, dict):
                out.append({"material": key, "category": key, "phase": key, **val})
        return out
    return v if isinstance(v, list) else []


class ProjectPlan(BaseModel):
    project_summary: str = ""
    built_up_area_sqft: float = 0.0
    total_estimated_cost_inr: float = 0.0
    cost_per_sqft_inr: float = 0.0
    duration_weeks: int = 0
    materials: List[MaterialItem] = Field(default_factory=list)
    cost_breakdown: List[CostItem] = Field(default_factory=list)
    schedule: List[SchedulePhase] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    visualization: Visualization = Field(default_factory=Visualization)
    meta: Meta = Field(default_factory=lambda: Meta(feature="planner"))

    @field_validator("built_up_area_sqft", "total_estimated_cost_inr", "cost_per_sqft_inr", mode="before")
    @classmethod
    def _nums(cls, v: Any) -> float:
        return max(0.0, _as_float(v, 0.0))

    @field_validator("duration_weeks", mode="before")
    @classmethod
    def _weeks(cls, v: Any) -> int:
        return max(0, _as_int(v, 0))

    @field_validator("assumptions", mode="before")
    @classmethod
    def _assump(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("materials", "cost_breakdown", "schedule", mode="before")
    @classmethod
    def _rows(cls, v: Any) -> List[Any]:
        return _dict_to_rows(v)

    @field_validator("visualization", mode="before")
    @classmethod
    def _viz(cls, v: Any) -> Any:
        return v if isinstance(v, (dict, Visualization)) else {}

    @field_validator("project_summary", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _s(v)


# ---------------------------------------------------------------------------
# 4. Real estate valuation
# ---------------------------------------------------------------------------
class ValuationReport(BaseModel):
    summary: str = ""
    estimated_value_min_inr: float = 0.0
    estimated_value_max_inr: float = 0.0
    estimated_value_inr: float = 0.0
    price_per_sqft_inr: float = 0.0
    monthly_rent_min_inr: float = 0.0
    monthly_rent_max_inr: float = 0.0
    rental_yield_percent: float = 0.0
    expected_annual_appreciation_percent: float = 0.0
    five_year_roi_percent: float = 0.0
    investment_outlook: str = "neutral"
    value_drivers: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    confidence: int = Field(50, ge=0, le=100)
    meta: Meta = Field(default_factory=lambda: Meta(feature="valuation"))

    @field_validator("estimated_value_min_inr", "estimated_value_max_inr", "estimated_value_inr",
                     "price_per_sqft_inr", "monthly_rent_min_inr", "monthly_rent_max_inr",
                     "rental_yield_percent", "expected_annual_appreciation_percent",
                     "five_year_roi_percent", mode="before")
    @classmethod
    def _nums(cls, v: Any) -> float:
        return _as_float(v, 0.0)

    @field_validator("value_drivers", "risk_factors", mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: Any) -> int:
        return max(0, min(100, _as_int(v, 50)))

    @field_validator("summary", "investment_outlook", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


# ---------------------------------------------------------------------------
# 5. Chatbot
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    answer: str = ""
    key_points: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    disclaimer: str = "AI-generated guidance; verify with a qualified engineer and applicable codes."
    meta: Meta = Field(default_factory=lambda: Meta(feature="chat"))

    @field_validator("key_points", "references", "follow_up_questions", mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("answer", "disclaimer", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


# ---------------------------------------------------------------------------
# 6. Daily site assistant
# ---------------------------------------------------------------------------
class DailyTask(BaseModel):
    task: str = ""
    priority: Literal["high", "medium", "low"] = "medium"
    crew: str = ""
    duration_hours: float = 0.0

    @field_validator("priority", mode="before")
    @classmethod
    def _prio(cls, v: Any) -> str:
        return _normalise_choice(v, ("high", "medium", "low"), "medium")

    @field_validator("duration_hours", mode="before")
    @classmethod
    def _dur(cls, v: Any) -> float:
        return max(0.0, _as_float(v, 0.0))

    @field_validator("task", "crew", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


class DailyPlan(BaseModel):
    day_summary: str = ""
    tasks: List[DailyTask] = Field(default_factory=list)
    materials_required: List[str] = Field(default_factory=list)
    equipment_required: List[str] = Field(default_factory=list)
    safety_checks: List[str] = Field(default_factory=list)
    risk_alerts: List[str] = Field(default_factory=list)
    end_of_day_checklist: List[str] = Field(default_factory=list)
    meta: Meta = Field(default_factory=lambda: Meta(feature="daily"))

    @field_validator("materials_required", "equipment_required", "safety_checks",
                     "risk_alerts", "end_of_day_checklist", mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("tasks", mode="before")
    @classmethod
    def _tasks(cls, v: Any) -> List[Any]:
        if isinstance(v, list):
            return [{"task": t} if isinstance(t, str) else t for t in v if isinstance(t, (str, dict))]
        return []

    @field_validator("day_summary", mode="before")
    @classmethod
    def _str(cls, v: Any) -> str:
        return _s(v)


# ---------------------------------------------------------------------------
# 7. Weather advisory
# ---------------------------------------------------------------------------
class WeatherAdvisory(BaseModel):
    decision: Literal["GO", "CAUTION", "NO-GO"] = "CAUTION"
    confidence: int = Field(50, ge=0, le=100)
    rationale: str = ""
    identified_risks: List[str] = Field(default_factory=list)
    affected_activities: List[str] = Field(default_factory=list)
    precautions: List[str] = Field(default_factory=list)
    mitigation_steps: List[str] = Field(default_factory=list)
    recommended_window: str = ""
    meta: Meta = Field(default_factory=lambda: Meta(feature="weather"))

    @field_validator("decision", mode="before")
    @classmethod
    def _decision(cls, v: Any) -> str:
        text = str(v or "").upper().replace("_", "-").replace(" ", "-")
        if "NO-GO" in text or "NOGO" in text:
            return "NO-GO"
        if "CAUTION" in text or "CONDITIONAL" in text:
            return "CAUTION"
        if "GO" in text:
            return "GO"
        return "CAUTION"

    @field_validator("confidence", mode="before")
    @classmethod
    def _conf(cls, v: Any) -> int:
        return max(0, min(100, _as_int(v, 50)))

    @field_validator("identified_risks", "affected_activities", "precautions", "mitigation_steps",
                     mode="before")
    @classmethod
    def _lists(cls, v: Any) -> List[str]:
        return _as_str_list(v)

    @field_validator("rationale", "recommended_window", mode="before")
    @classmethod
    def _strs(cls, v: Any) -> str:
        return _s(v)


# ---------------------------------------------------------------------------
# Request bodies for text-only features
# ---------------------------------------------------------------------------
class PlanRequest(BaseModel):
    plot_length_ft: float = Field(..., gt=0, le=10000)
    plot_width_ft: float = Field(..., gt=0, le=10000)
    floors: int = Field(1, ge=1, le=50)
    construction_type: str = Field("residential", max_length=80)
    quality: Literal["basic", "standard", "premium"] = "standard"
    city: str = Field(..., min_length=1, max_length=80)
    additional_requirements: Optional[str] = Field(None, max_length=1000)


class ValuationRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=80)
    locality: Optional[str] = Field(None, max_length=120)
    property_type: str = Field("apartment", max_length=60)
    area_sqft: float = Field(..., gt=0, le=1_000_000)
    bedrooms: Optional[int] = Field(None, ge=0, le=50)
    building_age_years: int = Field(0, ge=0, le=200)
    floor_number: Optional[int] = Field(None, ge=-5, le=200)
    furnishing: Optional[str] = Field(None, max_length=40)
    amenities: List[str] = Field(default_factory=list, max_length=40)
    nearby_landmarks: Optional[str] = Field(None, max_length=500)


class DailyRequest(BaseModel):
    project_stage: str = Field(..., min_length=1, max_length=120)
    planned_activities: str = Field(..., min_length=1, max_length=2000)
    workforce: str = Field("", max_length=500)
    site_conditions: str = Field("", max_length=1000)
    weather: str = Field("", max_length=200)
    date: Optional[str] = Field(None, max_length=40)


class WeatherRequest(BaseModel):
    planned_activities: str = Field(..., min_length=1, max_length=2000)
    weather_conditions: str = Field(..., min_length=1, max_length=1000)
    temperature_c: Optional[float] = Field(None, ge=-50, le=70)
    wind_speed_kmph: Optional[float] = Field(None, ge=0, le=400)
    rain_probability_percent: Optional[float] = Field(None, ge=0, le=100)
    location: Optional[str] = Field(None, max_length=120)


FEATURE_MODELS: Dict[str, type] = {
    "safety": SafetyReport,
    "crack": CrackReport,
    "planner": ProjectPlan,
    "valuation": ValuationReport,
    "chat": ChatResponse,
    "daily": DailyPlan,
    "weather": WeatherAdvisory,
}
