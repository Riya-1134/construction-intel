"""Centralized multimodal AI interaction layer.

All features call `run_feature()`. It:
  1. Builds the feature-specific system prompt (domain context + JSON spec).
  2. Sends text-only or image+text messages to the Groq LLM in JSON mode.
  3. Robustly extracts JSON from the reply (handles fences / stray prose).
  4. Validates and coerces the result into the strict Pydantic contract.
  5. Falls back to safe defaults (or deterministic demo data) on any failure.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .config import get_settings
from .prompts import build_system_prompt
from . import demo

logger = logging.getLogger("construction_ai")

T = TypeVar("T", bound=BaseModel)

_client = None


def _get_client():
    """Lazily construct the Groq client so tests and demo mode never need the SDK key."""
    global _client
    if _client is None:
        from groq import Groq  # imported lazily

        settings = get_settings()
        _client = Groq(api_key=settings.groq_api_key, timeout=settings.ai_timeout_seconds)
    return _client


def reset_client() -> None:
    global _client
    _client = None


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Dict[str, Any]:
    """Return the first JSON object found in `text`, tolerating fences and prose."""
    if not text:
        raise ValueError("empty AI response")
    candidates: List[str] = [text.strip()]
    candidates += [m.strip() for m in _FENCE_RE.findall(text)]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for cand in candidates:
        try:
            data = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    raise ValueError("no JSON object found in AI response")


# ---------------------------------------------------------------------------
# Message construction
# ---------------------------------------------------------------------------
def _image_to_data_url(image_bytes: bytes, content_type: str) -> str:
    mime = content_type if content_type in ("image/jpeg", "image/png", "image/webp", "image/gif") else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def build_messages(
    feature: str,
    user_text: str,
    image_bytes: Optional[bytes] = None,
    image_content_type: str = "image/jpeg",
    history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = [{"role": "system", "content": build_system_prompt(feature)}]
    for turn in history or []:
        messages.append({"role": turn["role"], "content": turn["content"]})
    if image_bytes:
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": _image_to_data_url(image_bytes, image_content_type)}},
        ]
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": user_text})
    return messages


# ---------------------------------------------------------------------------
# Core call
# ---------------------------------------------------------------------------
def call_llm(messages: List[Dict[str, Any]], model: str) -> str:
    client = _get_client()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return completion.choices[0].message.content or ""


def _validate(model_cls: Type[T], data: Dict[str, Any], feature: str, model_name: str) -> T:
    data = dict(data)
    data.pop("meta", None)
    instance = model_cls.model_validate(data)
    instance.meta.feature = feature
    instance.meta.model = model_name
    instance.meta.ai_generated = True
    return instance


def _fallback(model_cls: Type[T], feature: str, reason: str, context: Dict[str, Any]) -> T:
    """Return a safe response: deterministic demo data if available, else schema fallback."""
    logger.warning("feature=%s falling back: %s", feature, reason)
    demo_payload = demo.build(feature, context)
    if demo_payload is not None:
        try:
            instance = model_cls.model_validate(demo_payload)
            instance.meta.feature = feature
            instance.meta.model = "demo"
            instance.meta.ai_generated = False
            instance.meta.notes = [reason]
            return instance
        except ValidationError as exc:  # pragma: no cover - demo data is static
            logger.error("demo payload invalid for %s: %s", feature, exc)
    if hasattr(model_cls, "fallback"):
        return model_cls.fallback(reason)  # type: ignore[attr-defined]
    instance = model_cls()
    instance.meta.feature = feature
    instance.meta.notes = [reason]
    return instance


def run_feature(
    feature: str,
    model_cls: Type[T],
    user_text: str,
    *,
    image_bytes: Optional[bytes] = None,
    image_content_type: str = "image/jpeg",
    history: Optional[List[Dict[str, str]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> T:
    """Run one feature end-to-end and always return a valid `model_cls` instance."""
    settings = get_settings()
    context = context or {}

    if not settings.ai_available:
        return _fallback(model_cls, feature, "AI disabled: no GROQ_API_KEY set or DEMO_MODE=true", context)

    model_name = settings.groq_vision_model if image_bytes else settings.groq_text_model
    messages = build_messages(feature, user_text, image_bytes, image_content_type, history)

    last_error = "unknown error"
    for attempt in range(2):
        try:
            raw = call_llm(messages, model_name)
            data = extract_json(raw)
            return _validate(model_cls, data, feature, model_name)
        except ValidationError as exc:
            last_error = f"schema validation failed: {exc.error_count()} error(s)"
            logger.warning("feature=%s attempt=%s %s", feature, attempt, last_error)
            # Ask the model to fix its output on the retry
            messages = messages + [
                {"role": "assistant", "content": raw if "raw" in locals() else ""},
                {"role": "user", "content": "Your JSON did not match the specification. "
                                            "Return the corrected JSON object only, with every required key."},
            ]
        except Exception as exc:  # network, auth, rate-limit, parsing
            last_error = f"{type(exc).__name__}: {str(exc)[:200]}"
            logger.warning("feature=%s attempt=%s %s", feature, attempt, last_error)
            if "401" in last_error or "invalid_api_key" in last_error.lower():
                break
    return _fallback(model_cls, feature, last_error, context)
