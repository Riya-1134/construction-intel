"""Functional + edge-case tests for every endpoint (demo mode, no network)."""
import io

from app.schemas import FEATURE_MODELS


def _assert_contract(payload: dict, feature: str):
    model = FEATURE_MODELS[feature]
    expected_keys = set(model.model_fields.keys())
    assert set(payload.keys()) == expected_keys, f"{feature}: {set(payload) ^ expected_keys}"
    assert payload["meta"]["feature"] == feature
    for key, value in payload.items():
        assert value is not None, f"{feature}.{key} is null"


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


# ---------------- safety ----------------
def test_safety_with_png_image(client, png_bytes):
    r = client.post("/api/safety/analyze",
                    files={"image": ("site.png", io.BytesIO(png_bytes), "image/png")},
                    data={"description": "Workers on 3rd floor slab edge"})
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "safety")
    assert body["risk_level"] in ("low", "medium", "high", "critical")
    assert 0 <= body["risk_score"] <= 100
    assert isinstance(body["hazards"], list)


def test_safety_text_only(client):
    r = client.post("/api/safety/analyze", data={"description": "Open trench 2 m deep, no shoring"})
    assert r.status_code == 200
    _assert_contract(r.json(), "safety")


def test_safety_rejects_empty_request(client):
    r = client.post("/api/safety/analyze", data={})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_safety_empty_file_with_description_falls_back(client):
    r = client.post("/api/safety/analyze",
                    files={"image": ("empty.png", io.BytesIO(b""), "image/png")},
                    data={"description": "partial upload"})
    assert r.status_code == 200
    _assert_contract(r.json(), "safety")


def test_safety_rejects_non_image(client):
    r = client.post("/api/safety/analyze",
                    files={"image": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")})
    assert r.status_code == 415


def test_safety_rejects_spoofed_content_type(client):
    r = client.post("/api/safety/analyze",
                    files={"image": ("x.png", io.BytesIO(b"<html>not an image</html>"), "image/png")})
    assert r.status_code == 415


def test_safety_rejects_oversized_image(client):
    big = b"\xff\xd8\xff" + b"\x00" * (9 * 1024 * 1024)
    r = client.post("/api/safety/analyze", files={"image": ("big.jpg", io.BytesIO(big), "image/jpeg")})
    assert r.status_code == 413


# ---------------- crack ----------------
def test_crack_with_jpeg(client, jpeg_bytes):
    r = client.post("/api/crack/analyze",
                    files={"image": ("crack.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
                    data={"description": "diagonal stepped crack above window", "element": "wall",
                          "building_age_years": "12"})
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "crack")
    assert body["severity"] in ("minor", "moderate", "severe")
    assert isinstance(body["repair_methods"], list)


def test_crack_requires_some_input(client):
    assert client.post("/api/crack/analyze").status_code == 422


def test_crack_invalid_age(client):
    r = client.post("/api/crack/analyze", data={"description": "x", "building_age_years": "-4"})
    assert r.status_code == 422


# ---------------- planner ----------------
def test_planner_full_plan(client):
    r = client.post("/api/planner/generate", json={
        "plot_length_ft": 30, "plot_width_ft": 40, "floors": 2,
        "construction_type": "residential", "quality": "standard", "city": "Pune",
    })
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "planner")
    assert body["built_up_area_sqft"] > 0
    assert body["total_estimated_cost_inr"] > 0
    assert body["cost_per_sqft_inr"] > 0
    assert body["duration_weeks"] > 0
    assert len(body["materials"]) >= 4
    assert len(body["schedule"]) >= 3
    assert body["visualization"]["svg"].startswith("<svg")
    assert abs(sum(c["percentage"] for c in body["cost_breakdown"]) - 100) < 2


def test_planner_validation_errors(client):
    r = client.post("/api/planner/generate", json={"plot_length_ft": -5, "plot_width_ft": 40, "city": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["detail"] == "Invalid input"
    fields = {e["field"] for e in body["errors"]}
    assert "plot_length_ft" in fields and "city" in fields


def test_planner_unknown_city_still_works(client):
    r = client.post("/api/planner/generate", json={"plot_length_ft": 25, "plot_width_ft": 50, "city": "Zzyzx"})
    assert r.status_code == 200
    assert r.json()["total_estimated_cost_inr"] > 0


# ---------------- valuation ----------------
def test_valuation(client):
    r = client.post("/api/valuation/estimate", json={
        "city": "Bengaluru", "locality": "Whitefield", "property_type": "apartment",
        "area_sqft": 1200, "bedrooms": 2, "building_age_years": 5, "amenities": ["gym", "pool"],
    })
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "valuation")
    assert 0 < body["estimated_value_min_inr"] <= body["estimated_value_inr"] <= body["estimated_value_max_inr"]
    assert body["price_per_sqft_inr"] > 0
    assert body["monthly_rent_max_inr"] >= body["monthly_rent_min_inr"] > 0


def test_valuation_partial_inputs(client):
    r = client.post("/api/valuation/estimate", json={"city": "Indore", "area_sqft": 800})
    assert r.status_code == 200
    _assert_contract(r.json(), "valuation")


def test_valuation_rejects_zero_area(client):
    assert client.post("/api/valuation/estimate", json={"city": "Indore", "area_sqft": 0}).status_code == 422


# ---------------- chat ----------------
def test_chat(client):
    r = client.post("/api/chat", json={"message": "What concrete grade for a residential slab?",
                                        "history": [{"role": "user", "content": "hi"},
                                                    {"role": "assistant", "content": "hello"}]})
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "chat")
    assert body["answer"]


def test_chat_rejects_blank(client):
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={}).status_code == 422


# ---------------- daily ----------------
def test_daily(client):
    r = client.post("/api/daily/plan", json={
        "project_stage": "Superstructure", "planned_activities": "Slab casting 2nd floor, brickwork ground floor",
        "workforce": "20 masons, 10 helpers", "site_conditions": "dry", "weather": "sunny 34C",
    })
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "daily")
    assert body["tasks"] and all(t["priority"] in ("high", "medium", "low") for t in body["tasks"])


# ---------------- weather ----------------
def test_weather_no_go_on_storm(client):
    r = client.post("/api/weather/advisory", json={
        "planned_activities": "Roof slab concreting", "weather_conditions": "Thunderstorm with heavy rain",
        "wind_speed_kmph": 55, "rain_probability_percent": 90,
    })
    assert r.status_code == 200
    body = r.json()
    _assert_contract(body, "weather")
    assert body["decision"] == "NO-GO"


def test_weather_go_on_clear(client):
    r = client.post("/api/weather/advisory", json={
        "planned_activities": "Interior painting", "weather_conditions": "Clear sky", "temperature_c": 28,
    })
    assert r.json()["decision"] == "GO"


def test_weather_rejects_out_of_range(client):
    r = client.post("/api/weather/advisory", json={
        "planned_activities": "x", "weather_conditions": "y", "rain_probability_percent": 150})
    assert r.status_code == 422


# ---------------- repeated-request stability ----------------
def test_repeated_requests_are_stable(client):
    payload = {"plot_length_ft": 30, "plot_width_ft": 40, "floors": 1, "city": "Mumbai"}
    results = [client.post("/api/planner/generate", json=payload).json()["total_estimated_cost_inr"] for _ in range(3)]
    assert len(set(results)) == 1
