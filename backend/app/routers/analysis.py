"""Image + text multimodal endpoints: site safety analysis and crack detection."""
from __future__ import annotations

from typing import Optional, Tuple

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..ai_service import run_feature
from ..config import get_settings
from ..schemas import CrackReport, SafetyReport

router = APIRouter(prefix="/api", tags=["multimodal-analysis"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF8": "image/gif",
}


def _sniff(data: bytes) -> str:
    """Detect the real image type from magic bytes; the declared header is not trusted."""
    for magic, mime in MAGIC.items():
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


async def read_image(image: Optional[UploadFile]) -> Tuple[Optional[bytes], str]:
    """Validate and read an optional upload. Returns (bytes | None, content_type)."""
    if image is None or not image.filename:
        return None, ""
    data = await image.read()
    if not data:
        return None, ""  # empty upload is treated as "no image" -> fallback path
    settings = get_settings()
    if len(data) > settings.max_image_bytes:
        raise HTTPException(status_code=413, detail=f"Image exceeds {settings.max_image_bytes // (1024 * 1024)} MB limit")
    content_type = _sniff(data)
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload a JPEG, PNG, WEBP or GIF image.")
    return data, content_type


@router.post("/safety/analyze", response_model=SafetyReport)
async def analyze_safety(
    image: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None, max_length=2000),
    site_type: Optional[str] = Form(None, max_length=120),
) -> SafetyReport:
    data, content_type = await read_image(image)
    if data is None and not (description or "").strip():
        raise HTTPException(status_code=422, detail="Provide a site image, a description, or both.")
    user_text = "Analyse this construction site for safety compliance and hazards."
    if site_type:
        user_text += f"\nSite / work type: {site_type.strip()}"
    if description:
        user_text += f"\nEngineer's description: {description.strip()}"
    if data is None:
        user_text += "\nNo image was provided; reason from the description only and say so in the summary."
    return run_feature(
        "safety", SafetyReport, user_text,
        image_bytes=data, image_content_type=content_type,
        context={"has_image": data is not None, "description": description},
    )


@router.post("/crack/analyze", response_model=CrackReport)
async def analyze_crack(
    image: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None, max_length=2000),
    element: Optional[str] = Form(None, max_length=120),
    building_age_years: Optional[int] = Form(None, ge=0, le=300),
) -> CrackReport:
    data, content_type = await read_image(image)
    if data is None and not (description or "").strip():
        raise HTTPException(status_code=422, detail="Provide a crack image, a description, or both.")
    user_text = "Analyse this crack: classify type, orientation, severity, probable causes and repairs."
    if element:
        user_text += f"\nStructural element: {element.strip()}"
    if building_age_years is not None:
        user_text += f"\nBuilding age: {building_age_years} years"
    if description:
        user_text += f"\nEngineer's description: {description.strip()}"
    if data is None:
        user_text += "\nNo image was provided; reason from the description only and lower confidence."
    return run_feature(
        "crack", CrackReport, user_text,
        image_bytes=data, image_content_type=content_type,
        context={"has_image": data is not None, "description": description},
    )
