"""AI layer behaviour with a mocked LLM: success, repair-on-retry, and failure fallback."""
import pytest

from app import ai_service
from app.config import Settings
from app.schemas import SafetyReport, WeatherAdvisory


@pytest.fixture
def live_settings(monkeypatch):
    """Pretend a key is configured so run_feature goes through the LLM path."""
    monkeypatch.setattr(ai_service, "get_settings",
                        lambda: Settings(groq_api_key="test-key", demo_mode=False, _env_file=None))


def test_success_path_marks_ai_generated(live_settings, monkeypatch):
    monkeypatch.setattr(ai_service, "call_llm", lambda messages, model: '{"decision": "GO", "confidence": 90, '
                                                                        '"rationale": "clear", "identified_risks": []}')
    out = ai_service.run_feature("weather", WeatherAdvisory, "test")
    assert out.decision == "GO"
    assert out.meta.ai_generated is True
    assert out.meta.model == Settings(_env_file=None).groq_text_model


def test_image_requests_use_vision_model(live_settings, monkeypatch):
    seen = {}

    def fake(messages, model):
        seen["model"] = model
        seen["messages"] = messages
        return '{"summary": "ok"}'

    monkeypatch.setattr(ai_service, "call_llm", fake)
    out = ai_service.run_feature("safety", SafetyReport, "look", image_bytes=b"\xff\xd8\xff", image_content_type="image/jpeg")
    assert seen["model"] == Settings(_env_file=None).groq_vision_model
    user = seen["messages"][-1]["content"]
    assert user[1]["type"] == "image_url"
    assert user[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert out.summary == "ok"
    assert "feature_id=safety" in seen["messages"][0]["content"]


def test_garbage_then_valid_is_repaired_on_retry(live_settings, monkeypatch):
    replies = iter(["I cannot answer in JSON, sorry.", '{"summary": "fixed", "risk_level": "low"}'])
    calls = []

    def fake(messages, model):
        calls.append(messages)
        return next(replies)

    monkeypatch.setattr(ai_service, "call_llm", fake)
    out = ai_service.run_feature("safety", SafetyReport, "test")
    assert out.summary == "fixed"
    assert out.risk_level == "low"
    assert len(calls) == 2


def test_persistent_failure_falls_back_to_demo(live_settings, monkeypatch):
    def boom(messages, model):
        raise RuntimeError("connection reset")

    monkeypatch.setattr(ai_service, "call_llm", boom)
    out = ai_service.run_feature("safety", SafetyReport, "test", context={"has_image": True})
    assert out.meta.ai_generated is False
    assert out.meta.model == "demo"
    assert any("connection reset" in n for n in out.meta.notes)
    assert out.recommended_ppe  # still a useful, fully-populated payload


def test_auth_error_does_not_retry(live_settings, monkeypatch):
    calls = []

    def boom(messages, model):
        calls.append(1)
        raise RuntimeError("Error code: 401 - invalid_api_key")

    monkeypatch.setattr(ai_service, "call_llm", boom)
    ai_service.run_feature("weather", WeatherAdvisory, "test")
    assert len(calls) == 1


def test_disabled_ai_never_calls_llm(monkeypatch):
    monkeypatch.setattr(ai_service, "get_settings", lambda: Settings(groq_api_key="", _env_file=None))

    def boom(messages, model):  # pragma: no cover
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr(ai_service, "call_llm", boom)
    out = ai_service.run_feature("weather", WeatherAdvisory, "test", context={"weather_conditions": "clear"})
    assert out.decision == "GO"
    assert out.meta.model == "demo"
