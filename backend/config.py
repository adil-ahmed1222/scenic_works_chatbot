from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent
_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", _ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Scenic Works Chatbot"
    log_level: str = "INFO"

    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    allowed_origins: str = (
        "http://localhost:3000,https://adroitiame.com,"
        "https://www.adroitiame.com,https://chat.adroitiame.com"
    )

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 1024

    elevenlabs_api_key: str = ""
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_voice_en: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_voice_ar: str = "onwK4e9ZLuTAKqWW03F9"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "tts-audio"

    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    embedding_provider: Literal["local", "huggingface"] = "local"
    hf_api_token: str = ""
    hf_embedding_endpoint: str = ""

    rag_top_k: int = 5
    rag_min_similarity: float = 0.35
    chat_history_limit: int = 10

    rate_limit_chat: str = "30/minute"
    rate_limit_voice: str = "10/minute"
    rate_limit_lead: str = "8/minute"
    widget_api_secret: str = ""
    session_signing_key: str = ""
    trust_proxy: bool = False

    @field_validator(
        "elevenlabs_api_key",
        "groq_api_key",
        "supabase_service_role_key",
        "widget_api_secret",
        "session_signing_key",
        mode="before",
    )
    @classmethod
    def strip_secret(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
