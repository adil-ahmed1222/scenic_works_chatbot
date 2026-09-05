"""On-disk RAG fallback when Supabase is unreachable."""

from __future__ import annotations

import json
import logging
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
    _load_index()


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
