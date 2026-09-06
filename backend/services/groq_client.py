from __future__ import annotations

import logging
import re
import time

from groq import Groq

from config import get_settings
from services.http_retry import call_with_backoff

logger = logging.getLogger("scenicworks.groq")
_client: Groq | None = None


def get_groq() -> Groq:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        try:
            _client = Groq(
                api_key=settings.groq_api_key,
                timeout=45.0,
                max_retries=2,
            )
        except TypeError:
            _client = Groq(api_key=settings.groq_api_key)
    return _client


def complete(messages: list[dict], *, temperature: float | None = None) -> str:
    return "".join(complete_stream(messages, temperature=temperature)).strip()


def _open_stream(messages: list[dict], temperature: float | None):
    settings = get_settings()
    client = get_groq()
    return client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=settings.groq_temperature if temperature is None else temperature,
        max_tokens=settings.groq_max_tokens,
        stream=True,
    )


def complete_stream(
    messages: list[dict], *, temperature: float | None = None
):
    stream = call_with_backoff(
        lambda: _open_stream(messages, temperature),
        attempts=3,
        label="groq.stream",
    )
    first = True
    started = time.perf_counter()
    for chunk in stream:
        delta = ""
        try:
            delta = chunk.choices[0].delta.content or ""
        except Exception:  # noqa: BLE001
            delta = ""
        if not delta:
            continue
        if first:
            logger.info(
                "perf stage=model_ttft_ms value=%.1f",
                (time.perf_counter() - started) * 1000,
            )
            first = False
        yield delta


def complete_json(messages: list[dict]) -> str:
    settings = get_settings()
    client = get_groq()
    response = call_with_backoff(
        lambda: client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0,
            max_tokens=256,
            response_format={"type": "json_object"},
        ),
        attempts=3,
        label="groq.json",
    )
    return response.choices[0].message.content or "{}"


def strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
