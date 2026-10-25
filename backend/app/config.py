"""Application settings loaded from environment variables / .env file."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    groq_vision_model: str = "qwen/qwen3.8-27b"
    groq_text_model: str = "openai/gpt-oss-120b"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    demo_mode: bool = False
    max_image_bytes: int = 8 * 1024 * 1024  # 8 MB
    ai_timeout_seconds: float = 60.0

    @property
    def cors_origin_list(self) -> List[str]:
        """Comma-separated origins. Bare hosts (as injected by Render's `fromService`) get https://."""
        origins: List[str] = []
        for raw in self.cors_origins.split(","):
            o = raw.strip().rstrip("/")
            if not o:
                continue
            if not o.startswith(("http://", "https://")):
                o = f"https://{o}"
            origins.append(o)
        # Local dev origins are always allowed so the Vite dev server can talk to a hosted API.
        for local in ("http://localhost:5173", "http://127.0.0.1:5173"):
            if local not in origins:
                origins.append(local)
        return origins

    @property
    def ai_available(self) -> bool:
        return bool(self.groq_api_key) and not self.demo_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
