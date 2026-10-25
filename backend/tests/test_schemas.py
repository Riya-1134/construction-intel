"""Schema enforcement: loose AI output must always coerce into the strict contract."""
from app.ai_service import extract_json
from app.schemas import (
    CrackReport, DailyPlan, ProjectPlan, SafetyReport, ValuationReport, WeatherAdvisory, FEATURE_MODELS,
)


def test_every_feature_model_has_defaults_for_all_keys():
    for feature, model in FEATURE_MODELS.items():
        instance = model()
        data = instance.model_dump()
        assert "meta" in data, feature
        for key, value in data.items():
            assert value is not None, f"{feature}.{key} must never be None"


def test_safety_coerces_messy_ai_output():
    report = SafetyReport.model_validate({
        "summary": None,
        "risk_level": "HIGH risk",
        "risk_score": "87%",
        "hazards": "single hazard string",
        "ppe_missing": [{"item": "helmet", "where": "worker 2"}, None, 42],
        "recommended_ppe": {"a": "boots", "b": "gloves"},
        "unexpected_key": "ignored",
    })
    assert report.summary == ""
    assert report.risk_level == "high"
    assert report.risk_score == 87
    assert report.hazards == ["single hazard string"]
    assert report.ppe_missing == ["helmet - worker 2", "42"]
    assert report.recommended_ppe == ["boots", "gloves"]
    assert report.corrective_actions == []


def test_safety_fallback_has_content():
    fb = SafetyReport.fallback("boom")
    assert fb.recommended_ppe and fb.corrective_actions
    assert fb.meta.notes == ["boom"]
    assert fb.meta.ai_generated is False


def test_crack_coercion_and_bounds():
    report = CrackReport.model_validate({
        "crack_detected": "yes",
        "severity": "Very Severe",
        "estimated_width_mm": "-3 mm",
        "confidence": 250,
        "structural_concern": "false",
    })
    assert report.crack_detected is True
    assert report.severity == "severe"
    assert report.estimated_width_mm == 0.0
    assert report.confidence == 100
    assert report.structural_concern is False
    assert report.crack_type == "unknown"


def test_project_plan_accepts_dict_shaped_lists():
    plan = ProjectPlan.model_validate({
        "materials": {"Cement": {"quantity": "400 bags", "unit": "bags", "estimated_cost_inr": "1,52,000"}},
        "cost_breakdown": [{"category": "Structure", "amount_inr": "₹12,00,000", "percentage": "40%"}],
        "schedule": [{"phase": "Foundation", "start_week": 0, "duration_weeks": "3", "tasks": "Excavation"}],
        "visualization": "not an object",
        "total_estimated_cost_inr": "30 lakh",
    })
    assert plan.materials[0].material == "Cement"
    assert plan.materials[0].quantity == 400
    assert plan.materials[0].estimated_cost_inr == 152000
    assert plan.cost_breakdown[0].amount_inr == 1200000
    assert plan.schedule[0].start_week == 1  # clamped to >= 1
    assert plan.schedule[0].tasks == ["Excavation"]
    assert plan.visualization.svg == ""


def test_valuation_numbers_parse_strings():
    v = ValuationReport.model_validate({"estimated_value_inr": "₹ 85,00,000", "confidence": "high"})
    assert v.estimated_value_inr == 8500000
    assert v.confidence == 50  # unparseable -> default


def test_daily_tasks_accept_plain_strings():
    plan = DailyPlan.model_validate({"tasks": ["Pour slab", {"task": "Cure", "priority": "LOW", "duration_hours": "2h"}, 7]})
    assert [t.task for t in plan.tasks] == ["Pour slab", "Cure"]
    assert plan.tasks[1].priority == "low"
    assert plan.tasks[1].duration_hours == 2


def test_weather_decision_normalisation():
    assert WeatherAdvisory.model_validate({"decision": "no go"}).decision == "NO-GO"
    assert WeatherAdvisory.model_validate({"decision": "Proceed - GO"}).decision == "GO"
    assert WeatherAdvisory.model_validate({"decision": "conditional"}).decision == "CAUTION"
    assert WeatherAdvisory.model_validate({"decision": None}).decision == "CAUTION"


def test_extract_json_handles_fences_and_prose():
    text = 'Sure! Here is the result:\n```json\n{"a": 1, "b": [2]}\n```\nHope this helps.'
    assert extract_json(text) == {"a": 1, "b": [2]}
    assert extract_json('prefix {"x": "y"} suffix') == {"x": "y"}
    assert extract_json('[{"first": true}]') == {"first": True}


def test_extract_json_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        extract_json("no json here")
    with pytest.raises(ValueError):
        extract_json("")


def test_cors_origins_accept_bare_hosts_and_keep_local_dev():
    from app.config import Settings
    s = Settings(cors_origins="construction-intel-web.onrender.com, https://example.com/", _env_file=None)
    origins = s.cors_origin_list
    assert "https://construction-intel-web.onrender.com" in origins
    assert "https://example.com" in origins
    assert "http://localhost:5173" in origins
