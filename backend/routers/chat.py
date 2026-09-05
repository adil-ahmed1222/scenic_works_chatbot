from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from config import get_settings
from models.schemas import ChatRequest
from rate_limit import limiter
from services.rag import answer_question, stream_answer

router = APIRouter()


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
@limiter.limit(get_settings().rate_limit_chat)
async def chat(request: Request, payload: ChatRequest):
    accept = (request.headers.get("accept") or "").lower()
    try:
        if "text/event-stream" in accept:
            def events():
                try:
                    for event in stream_answer(
                        payload.message,
                        session_id=payload.session_id,
                        session_token=payload.session_token,
                        language_hint=payload.language,
                    ):
                        yield _sse(event)
                except Exception as exc:  # noqa: BLE001
                    yield _sse({"type": "error", "detail": "Chat failed."})
                    raise exc

            return StreamingResponse(
                events(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-store, no-transform",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                },
            )
        return answer_question(
            payload.message,
            session_id=payload.session_id,
            session_token=payload.session_token,
            language_hint=payload.language,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Chat failed.") from exc
