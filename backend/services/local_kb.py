"""On-disk RAG fallback when Supabase is unreachable."""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import get_settings
from services.embeddings import get_embedder

logger = logging.getLogger("scenicworks.local_kb")

CHUNKS_FILE = (
    Path(__file__).resolve().parents[2] / "knowledge-base" / "chunks" / "chunks.json"
)
VECTOR_FILE = CHUNKS_FILE.with_name("vectors.json")
_TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)
_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "with",
    "is",
    "are",
    "do",
    "does",
    "i",
    "need",
    "want",
    "please",
    "what",
    "how",
    "can",
    "you",
    "your",
    "me",
}


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=False)))


def rank_vectors(
    query: list[float],
    rows: list[tuple[dict[str, Any], list[float]]],
    *,
    top_k: int,
    min_similarity: float,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for item, vector in rows:
        similarity = cosine_similarity(query, vector)
        if similarity >= min_similarity:
            scored.append((similarity, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    results: list[dict[str, Any]] = []
    for similarity, item in scored[:top_k]:
        results.append({**item, "similarity": similarity})
    return results


def _parse_chunks() -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Local knowledge file missing: {CHUNKS_FILE}")
    payload = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    texts: list[str] = []
    ids: list[str] = []
    for row in payload:
        content = (row.get("content") or "").strip()
        if not content:
            continue
        meta = row.get("metadata") or {}
        chunk_id = str(row.get("chunk_id") or len(ids))
        items.append(
            {
                "id": chunk_id,
                "content": content,
                "source_url": meta.get("source_url"),
                "title": meta.get("title"),
                "language": meta.get("language"),
                "category": meta.get("category"),
            }
        )
        texts.append(content)
        ids.append(chunk_id)
    return items, texts, ids


def _load_cached_vectors(model: str, ids: list[str]) -> list[list[float]] | None:
    if not VECTOR_FILE.exists():
        return None
    try:
        cached = json.loads(VECTOR_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if cached.get("model") != model:
        return None
    by_id = {row.get("id"): row.get("vector") for row in cached.get("items") or []}
    if any(not by_id.get(chunk_id) for chunk_id in ids):
        return None
    return [by_id[chunk_id] for chunk_id in ids]


def _save_cached_vectors(model: str, ids: list[str], vectors: list[list[float]]) -> None:
    payload = {
        "model": model,
        "items": [{"id": chunk_id, "vector": vector} for chunk_id, vector in zip(ids, vectors, strict=True)],
    }
    VECTOR_FILE.write_text(json.dumps(payload), encoding="utf-8")


@lru_cache
def _load_index() -> tuple[list[dict[str, Any]], list[list[float]]]:
    settings = get_settings()
    items, texts, ids = _parse_chunks()
    vectors = _load_cached_vectors(settings.embedding_model, ids)
    if vectors is None:
        logger.info("Embedding %s local knowledge chunks", len(texts))
        vectors = get_embedder().embed_texts(texts)
        try:
            _save_cached_vectors(settings.embedding_model, ids, vectors)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not cache local vectors: %s", exc)
    logger.info("Loaded %s local knowledge chunks from %s", len(items), CHUNKS_FILE)
    return items, vectors


def warmup_local_kb() -> None:
    """Optional manual preload. Startup must not call this on 512MB hosts."""
    _load_index()


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text or "")
        if len(token) > 2 and token.lower() not in _STOP
    }


def rank_lexical(
    query: str,
    items: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    needles = _tokens(query)
    if not needles:
        needles = {token.lower() for token in _TOKEN_RE.findall(query or "")}
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in items:
        blob = f"{item.get('title') or ''} {item.get('content') or ''}".lower()
        if not blob.strip():
            continue
        hits = sum(1 for token in needles if token in blob)
        score = hits / max(len(needles), 1)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if not scored and items:
        return [{**item, "similarity": 0.2} for item in items[:top_k]]
    return [{**item, "similarity": score} for score, item in scored[:top_k]]


def retrieve_lexical(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    limit = top_k or settings.rag_top_k
    try:
        from services.supabase_client import get_supabase, remote_enabled

        if remote_enabled():
            rows = (
                get_supabase()
                .table("documents")
                .select("id,content,source_url,title,language,category")
                .execute()
                .data
                or []
            )
            ranked = rank_lexical(query, rows, top_k=limit)
            if ranked:
                logger.info("Lexical remote retrieval returned %s chunks", len(ranked))
                return ranked
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lexical remote retrieval failed: %s", exc)
    try:
        items, _, _ = _parse_chunks()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lexical local retrieval failed: %s", exc)
        return []
    ranked = rank_lexical(query, items, top_k=limit)
    logger.info("Lexical local retrieval returned %s chunks", len(ranked))
    return ranked


def retrieve_local(
    query: str,
    top_k: int | None = None,
    query_vector: list[float] | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    items, vectors = _load_index()
    query_vec = query_vector or get_embedder().embed_query(query)
    ranked = rank_vectors(
        query_vec,
        list(zip(items, vectors, strict=True)),
        top_k=top_k or settings.rag_top_k,
        min_similarity=settings.rag_min_similarity,
    )
    logger.info("Local retrieval returned %s chunks", len(ranked))
    return ranked
