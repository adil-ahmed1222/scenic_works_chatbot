from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from config import get_settings
from models.schemas import ChatResponse, SourceChunk
from prompts import LANGUAGE_NAMES, LEAD_PROMPT_AR, LEAD_PROMPT_EN, SYSTEM_PROMPT
from services.embeddings import get_embedder
from services.groq_client import complete_stream
from services.language import (
    detect_language,
    fallback_message,
    is_knowledge_fallback,
    service_error_message,
)
from services.leads import detect_buying_intent
from services.local_kb import retrieve_local
from services.memory import append_message, as_openai_messages, fetch_history
from services.sessions import resolve_session
from services.supabase_client import get_supabase, mark_remote_down, remote_enabled

logger = logging.getLogger("scenicworks.rag")


def _is_unreachable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "getaddrinfo",
            "name or service not known",
            "nodename nor servname",
            "name resolution",
            "failed to resolve",
        )
    )


def retrieve(
    query: str,
    top_k: int | None = None,
    language: str | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    started = time.perf_counter()
    if not remote_enabled():
        rows = retrieve_local(query, top_k)
        logger.info(
            "perf stage=rag_local_ms value=%.1f chunks=%s",
            (time.perf_counter() - started) * 1000,
            len(rows),
        )
        return rows

    vector = get_embedder().embed_query(query)
    try:
        client = get_supabase()
        result = client.rpc(
            "match_documents",
            {
                "query_embedding": vector,
                "match_count": top_k or settings.rag_top_k,
                "filter_language": None,
                "min_similarity": settings.rag_min_similarity,
            },
        ).execute()
        rows = result.data or []
        logger.info(
            "perf stage=rag_remote_ms value=%.1f chunks=%s",
            (time.perf_counter() - started) * 1000,
            len(rows),
        )
        return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("Supabase retrieval failed: %s", exc)
        if _is_unreachable(exc):
            mark_remote_down(str(exc))
        get_supabase.cache_clear()
        rows = retrieve_local(query, top_k, query_vector=vector)
        logger.info(
            "perf stage=rag_fallback_ms value=%.1f chunks=%s",
            (time.perf_counter() - started) * 1000,
            len(rows),
        )
        return rows


def _format_context(chunks: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_url") or "unknown"
        title = chunk.get("title") or ""
        blocks.append(
            f"[Source {i}] {title} ({source})\n{chunk.get('content') or ''}"
        )
    return "\n\n".join(blocks)


def _sources(chunks: list[dict[str, Any]]) -> list[SourceChunk]:
    return [
        SourceChunk(
            source_url=chunk.get("source_url"),
            title=chunk.get("title"),
            similarity=chunk.get("similarity"),
        )
        for chunk in chunks
    ]


def stream_answer(
    message: str,
    *,
    session_id: str | None = None,
    session_token: str | None = None,
    language_hint: str | None = None,
) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()

    def perf(stage: str) -> None:
        logger.info(
            "perf stage=%s value=%.1f",
            stage,
            (time.perf_counter() - started) * 1000,
        )

    session, token = resolve_session(session_id, session_token)
    language = language_hint or detect_language(message)
    language_name = LANGUAGE_NAMES.get(language, "English")
    show_lead = detect_buying_intent(message, language)
    lead_prompt = LEAD_PROMPT_AR if language == "ar" else LEAD_PROMPT_EN
    perf("session_ms")

    history: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    retrieval_error = False
    with ThreadPoolExecutor(max_workers=2) as pool:
        hist_future = pool.submit(fetch_history, session)
        ret_future = pool.submit(retrieve, message)
        try:
            history = hist_future.result()
        except Exception as exc:  # noqa: BLE001
            logger.warning("History fetch failed: %s", exc)
        try:
            chunks = ret_future.result()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Retrieval failed: %s", exc)
            retrieval_error = True
            chunks = []
    perf("context_ms")

    if retrieval_error and not chunks:
        answer = service_error_message(language)
        _persist(session, message, answer, language)
        yield {
            "type": "meta",
            "session_id": session,
            "session_token": token,
            "language": language,
            "sources": [],
        }
        yield {"type": "token", "text": answer}
        yield {
            "type": "done",
            "answer": answer,
            "show_lead_form": False,
            "lead_prompt": None,
        }
        return

    if not chunks:
        answer = fallback_message(language)
        _persist(session, message, answer, language)
        yield {
            "type": "meta",
            "session_id": session,
            "session_token": token,
            "language": language,
            "sources": [],
        }
        yield {"type": "token", "text": answer}
        yield {
            "type": "done",
            "answer": answer,
            "show_lead_form": show_lead,
            "lead_prompt": lead_prompt if show_lead else None,
        }
        return

    context = _format_context(chunks)
    system = SYSTEM_PROMPT.format(language_name=language_name)
    messages = [
        {"role": "system", "content": system},
        {"role": "system", "content": f"Website context:\n{context}"},
        *as_openai_messages(history),
        {"role": "user", "content": message},
    ]
    sources = [item.model_dump() for item in _sources(chunks)]
    yield {
        "type": "meta",
        "session_id": session,
        "session_token": token,
        "language": language,
        "sources": sources,
    }
    perf("first_byte_ready_ms")

    parts: list[str] = []
    try:
        for delta in complete_stream(messages):
            parts.append(delta)
            yield {"type": "token", "text": delta}
        answer = "".join(parts).strip()
    except Exception:
        logger.exception("Groq completion failed")
        answer = service_error_message(language)
        if not parts:
            yield {"type": "token", "text": answer}

    if not answer:
        answer = fallback_message(language)
        if not parts:
            yield {"type": "token", "text": answer}

    if is_knowledge_fallback(answer) and chunks:
        logger.warning("Model returned knowledge fallback despite %s retrieved chunks", len(chunks))

    if detect_buying_intent(f"{message}\n{answer}", language):
        show_lead = True

    _persist(session, message, answer, language)
    perf("total_ms")
    yield {
        "type": "done",
        "answer": answer,
        "show_lead_form": show_lead,
        "lead_prompt": lead_prompt if show_lead else None,
        "sources": sources,
    }


def answer_question(
    message: str,
    *,
    session_id: str | None = None,
    session_token: str | None = None,
    language_hint: str | None = None,
) -> ChatResponse:
    session = ""
    token = None
    language = language_hint or "en"
    answer = ""
    sources: list[SourceChunk] = []
    show_lead = False
    lead_prompt = None
    for event in stream_answer(
        message,
        session_id=session_id,
        session_token=session_token,
        language_hint=language_hint,
    ):
        kind = event.get("type")
        if kind == "meta":
            session = event.get("session_id") or session
            token = event.get("session_token")
            language = event.get("language") or language
            sources = [SourceChunk(**item) for item in event.get("sources") or []]
        elif kind == "done":
            answer = event.get("answer") or answer
            show_lead = bool(event.get("show_lead_form"))
            lead_prompt = event.get("lead_prompt")
            if event.get("sources"):
                sources = [SourceChunk(**item) for item in event["sources"]]
    return ChatResponse(
        session_id=session,
        session_token=token,
        answer=answer,
        language=language,
        sources=sources,
        show_lead_form=show_lead,
        lead_prompt=lead_prompt,
    )


def _persist(session_id: str, user_message: str, answer: str, language: str) -> None:
    try:
        append_message(session_id, "user", user_message, language)
        append_message(session_id, "assistant", answer, language)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist chat history: %s", exc)
