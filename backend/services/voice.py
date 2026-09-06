"""ElevenLabs text-to-speech with English and Arabic voices."""

from __future__ import annotations

import base64
import logging
import uuid

import httpx
from config import get_settings
from services.http_retry import RETRY_STATUSES, call_with_backoff
from services.supabase_client import get_supabase

logger = logging.getLogger("scenicworks.voice")

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def _voice_id(language: str) -> str:
    settings = get_settings()
    return settings.elevenlabs_voice_ar if language == "ar" else settings.elevenlabs_voice_en


def synthesize(text: str, language: str = "en") -> tuple[bytes, str]:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured.")
    cleaned = " ".join((text or "").split())
    if not cleaned:
        raise RuntimeError("Voice text is empty.")
    voice_id = _voice_id(language)
    url = ELEVEN_URL.format(voice_id=voice_id)
    payload = {
        "text": cleaned[:1500],
        "model_id": settings.elevenlabs_model,
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }

    def _request() -> httpx.Response:
        with httpx.Client(timeout=45) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code in RETRY_STATUSES:
            raise httpx.HTTPStatusError(
                f"retryable {response.status_code}",
                request=response.request,
                response=response,
            )
        return response

    response = call_with_backoff(_request, attempts=3, label="elevenlabs.tts")
    if response.status_code == 401:
        logger.error("ElevenLabs rejected ELEVENLABS_API_KEY (401 invalid_api_key).")
        raise RuntimeError(
            "ElevenLabs API key is invalid. Update ELEVENLABS_API_KEY on the API host."
        )
    if response.status_code >= 400:
        logger.error(
            "ElevenLabs TTS failed (%s): %s",
            response.status_code,
            response.text[:300],
        )
        raise RuntimeError("ElevenLabs voice synthesis failed.")
    audio = response.content
    if len(audio) < 64 or not (audio.startswith(b"ID3") or audio.startswith(b"\xff")):
        logger.error("ElevenLabs returned a non-audio payload (%s bytes)", len(audio))
        raise RuntimeError("ElevenLabs voice synthesis failed.")
    logger.info("ElevenLabs synthesized %s bytes voice=%s lang=%s", len(audio), voice_id, language)
    return audio, voice_id


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
        if public and public.startswith("https://"):
            return public.split("?")[0]
        return public
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase audio upload failed, using inline audio: %s", exc)
        return None


def create_audio_url(text: str, language: str = "en") -> tuple[str, str]:
    audio, voice_id = synthesize(text, language)
    filename = f"{uuid.uuid4().hex}.mp3"
    _upload_supabase(audio, filename)
    encoded = base64.b64encode(audio).decode("ascii")
    logger.info("Serving voice as data URL (%s bytes) voice=%s", len(audio), voice_id)
    return f"data:audio/mpeg;base64,{encoded}", voice_id
