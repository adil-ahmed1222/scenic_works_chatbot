from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from config import get_settings
from models.schemas import VoiceRequest, VoiceResponse
from rate_limit import limiter
from services.voice import create_audio_url

router = APIRouter()


@router.post("/voice", response_model=VoiceResponse)
@limiter.limit(get_settings().rate_limit_voice)
async def voice(request: Request, payload: VoiceRequest) -> VoiceResponse:
    try:
        audio_url, voice_id = create_audio_url(payload.text, payload.language)
        return VoiceResponse(
            audio_url=audio_url, language=payload.language, voice_id=voice_id
        )
    except RuntimeError as exc:
        message = str(exc)
        status = 502 if "API key" in message else 500
        raise HTTPException(status_code=status, detail=message) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Voice synthesis failed.") from exc
