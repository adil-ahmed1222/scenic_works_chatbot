"""Generate all-MiniLM-L6-v2 embeddings and upsert them into Supabase pgvector."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from supabase import Client, create_client

KB_DIR = Path(__file__).resolve().parent
ROOT = KB_DIR.parent
load_dotenv(ROOT / ".env")
if str(KB_DIR) not in sys.path:
    sys.path.insert(0, str(KB_DIR))

from knowledge_base_paths import CHUNKS_FILE  # noqa: E402

_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_raw_model = os.getenv("EMBEDDING_MODEL", _DEFAULT_MODEL)
EMBEDDING_MODEL = (
    _DEFAULT_MODEL
    if "bge-m3" in (_raw_model or "").lower()
    else (_raw_model or _DEFAULT_MODEL)
)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
if "minilm" in EMBEDDING_MODEL.lower():
    EMBEDDING_DIM = 384
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "8"))
PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


class Embedder:
    def __init__(self) -> None:
        self.provider = PROVIDER
        self._model = None

    def _load_local(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self.provider == "huggingface":
            return self._encode_hf(texts)
        self._load_local()
        assert self._model is not None
        vectors = self._model.encode(
            list(texts),
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > BATCH_SIZE,
        )
        return [v.tolist() for v in vectors]

    def _encode_hf(self, texts: Sequence[str]) -> list[list[float]]:
        import httpx

        token = os.environ["HF_API_TOKEN"]
        endpoint = os.getenv(
            "HF_EMBEDDING_ENDPOINT",
            f"https://api-inference.huggingface.co/models/{EMBEDDING_MODEL}",
        )
        vectors: list[list[float]] = []
        with httpx.Client(timeout=120) as client:
            for i in range(0, len(texts), BATCH_SIZE):
                batch = list(texts[i : i + BATCH_SIZE])
                response = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"inputs": batch},
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list) and data and isinstance(data[0], list):
                    vectors.extend(data)
                else:
                    raise RuntimeError(f"Unexpected HF embedding payload: {type(data)}")
        return vectors


def upsert_chunks(chunks: list[dict[str, Any]], client: Client | None = None) -> int:
    client = client or get_supabase()
    embedder = Embedder()
    texts = [c["content"] for c in chunks]
    embeddings = embedder.encode(texts)

    rows = []
    source_urls = {c["metadata"].get("source_url") for c in chunks if c.get("metadata")}
    for chunk, vector in zip(chunks, embeddings, strict=True):
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dim {len(vector)} != expected {EMBEDDING_DIM}"
            )
        meta = chunk["metadata"]
        rows.append(
            {
                "id": chunk["chunk_id"],
                "content": chunk["content"],
                "embedding": vector,
                "source_url": meta.get("source_url"),
                "language": meta.get("language"),
                "category": meta.get("category"),
                "title": meta.get("title"),
                "metadata": meta,
            }
        )

    for url in source_urls:
        if url:
            client.table("documents").delete().eq("source_url", url).execute()

    written = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        client.table("documents").upsert(batch).execute()
        written += len(batch)
        print(f"Upserted {written}/{len(rows)} chunks")
    return written


def embed_from_disk() -> int:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError("Run chunker.py first.")
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    return upsert_chunks(chunks)


if __name__ == "__main__":
    embed_from_disk()
