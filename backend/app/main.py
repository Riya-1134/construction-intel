"""FastAPI application entry point for the Construction Intelligence Platform."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import analysis, assistants, planning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()

app = FastAPI(
    title="AI-Powered Multimodal Construction Intelligence Platform",
    version="1.0.0",
    description="Multimodal LLM decision support for construction safety, crack analysis, "
                "planning, valuation and site assistance. All responses follow strict JSON contracts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)
app.include_router(planning.router)
app.include_router(assistants.router)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Flatten validation errors into a stable {detail, errors[]} shape for the UI."""
    errors = [
        {"field": ".".join(str(p) for p in e.get("loc", []) if p not in ("body", "form")), "message": e.get("msg", "")}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Invalid input", "errors": errors})


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    logging.getLogger("construction_ai").exception("unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "errors": []})


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "ai_enabled": settings.ai_available,
        "demo_mode": not settings.ai_available,
        "vision_model": settings.groq_vision_model,
        "text_model": settings.groq_text_model,
    }


@app.get("/")
def root() -> dict:
    return {"message": "Construction Intelligence API. See /docs for the OpenAPI UI."}
