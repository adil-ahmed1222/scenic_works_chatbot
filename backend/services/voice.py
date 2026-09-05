"""ElevenLabs text-to-speech with English and Arabic voices."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import httpx
from config import get_settings
from services.supabase_client import get_supabase

logger = logging.getLogger("scenicworks.voice")

AUDIO_DIR = Path(__file__).resolve().parents[1] / "static" / "audio"
ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def _voice_id(language: str) -> str:
    settings = get_settings()
    return settings.elevenlabs_voice_ar if language == "ar" else settings.elevenlabs_voice_en


def synthesize(text: str, language: str = "en") -> tuple[bytes, str]:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured.")
    voice_id = _voice_id(language)
    url = ELEVEN_URL.format(voice_id=voice_id)
    payload = {
        "text": text[:1500],
        "model_id": settings.elevenlabs_model,
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code == 401:
            logger.error(
                "ElevenLabs rejected ELEVENLABS_API_KEY (401 invalid_api_key). "
                "Create a new key at https://elevenlabs.io/app/settings/api-keys "
                "and set it in backend/.env, then restart the API."
            )
            raise RuntimeError(
                "ElevenLabs API key is invalid. Update ELEVENLABS_API_KEY in backend/.env."
            )
        if response.status_code >= 400:
            logger.error(
                "ElevenLabs TTS failed (%s): %s",
                response.status_code,
                response.text[:300],
            )
            raise RuntimeError("ElevenLabs voice synthesis failed.")
        return response.content, voice_id


def _upload_supabase(audio: bytes, filename: str) -> str | None:
    settings = get_settings()
    try:
        client = get_supabase()
        client.storage.from_(settings.supabase_storage_bucket).upload(
            path=filename,
            file=audio,
            file_options={"content-type": "audio/mpeg", "upsert": "true"},
        )
        public = client.storage.from_(settings.supabase_storage_bucket).get_public_url(
            filename
        )
        return public
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase audio upload failed, using local fallback: %s", exc)
        return None


def create_audio_url(text: str, language: str = "en") -> tuple[str, str]:
    audio, voice_id = synthesize(text, language)
    filename = f"{uuid.uuid4().hex}.mp3"
    remote = _upload_supabase(audio, filename)
    if remote:
        return remote, voice_id

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / filename
    path.write_bytes(audio)
    settings = get_settings()
    return f"{settings.backend_url.rstrip('/')}/static/audio/{filename}", voice_id
