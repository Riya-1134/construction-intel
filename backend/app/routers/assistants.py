"""Conversational and advisory endpoints: chatbot, daily site assistant, weather advisory."""
from __future__ import annotations

import json

from fastapi import APIRouter

from ..ai_service import run_feature
from ..schemas import ChatRequest, ChatResponse, DailyPlan, DailyRequest, WeatherAdvisory, WeatherRequest

router = APIRouter(prefix="/api", tags=["assistants"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in body.history[-10:]]
    return run_feature(
        "chat", ChatResponse, body.message.strip(),
        history=history, context={"message": body.message},
    )


@router.post("/daily/plan", response_model=DailyPlan)
def daily_plan(body: DailyRequest) -> DailyPlan:
    payload = body.model_dump()
    user_text = "Create today's site action plan from these inputs:\n" + json.dumps(payload, indent=2)
    return run_feature("daily", DailyPlan, user_text, context=payload)


@router.post("/weather/advisory", response_model=WeatherAdvisory)
def weather_advisory(body: WeatherRequest) -> WeatherAdvisory:
    payload = body.model_dump()
    user_text = "Give a GO / CAUTION / NO-GO advisory for these activities and weather:\n" + json.dumps(payload, indent=2)
    return run_feature("weather", WeatherAdvisory, user_text, context=payload)
