from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Sequence

import httpx
from config import get_settings

logger = logging.getLogger("scenicworks.embeddings")

LIGHTWEIGHT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LIGHTWEIGHT_DIM = 384
HEAVY_MODEL_MARKERS = ("bge-m3", "bge_m3")


def _configure_low_memory_runtime() -> None:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def resolve_embedding_model(name: str | None) -> str:
    raw = (name or "").strip() or LIGHTWEIGHT_MODEL
    lowered = raw.lower()
    if any(marker in lowered for marker in HEAVY_MODEL_MARKERS):
        logger.warning("Replacing heavy embedding model %s with %s", raw, LIGHTWEIGHT_MODEL)
        return LIGHTWEIGHT_MODEL
    if lowered in {"all-minilm-l6-v2", "minilm"}:
        return LIGHTWEIGHT_MODEL
    return raw


def resolve_embedding_dim(model: str, dim: int | None = None) -> int:
    resolved = resolve_embedding_model(model)
    if resolved == LIGHTWEIGHT_MODEL or "minilm" in resolved.lower():
        return LIGHTWEIGHT_DIM
    return int(dim or LIGHTWEIGHT_DIM)


def _reset_hf_http_client() -> None:
    """Uvicorn reload can close Hugging Face's shared httpx client."""
    try:
        import huggingface_hub.utils._http as hf_http

        client = getattr(hf_http, "_GLOBAL_CLIENT", None)
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass
            hf_http._GLOBAL_CLIENT = None
    except Exception:  # noqa: BLE001
        logger.debug("Could not reset Hugging Face HTTP client", exc_info=True)


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = resolve_embedding_model(self.settings.embedding_model)
        self.embedding_dim = resolve_embedding_dim(self.model_name, self.settings.embedding_dim)
        self._model = None

    def _load_local(self) -> None:
        if self._model is not None:
            return
        _configure_low_memory_runtime()
        from sentence_transformers import SentenceTransformer

        try:
            import torch

            torch.set_num_threads(1)
            if hasattr(torch, "set_num_interop_threads"):
                torch.set_num_interop_threads(1)
        except Exception:  # noqa: BLE001
            logger.debug("Could not pin torch to a single thread", exc_info=True)

        logger.info("Lazy-loading embedding model %s on CPU", self.model_name)
        offline_keys = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
        previous = {key: os.environ.get(key) for key in offline_keys}
        try:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            self._model = SentenceTransformer(
                self.model_name,
                device="cpu",
                local_files_only=True,
            )
        except Exception as extra:  # noqa: BLE001
            logger.info("Local embedding cache miss (%s); downloading if needed", extra)
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            _reset_hf_http_client()
            self._model = SentenceTransformer(self.model_name, device="cpu")
        self._model.eval()
        if hasattr(self._model, "max_seq_length"):
            self._model.max_seq_length = min(int(self._model.max_seq_length or 256), 256)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if self.settings.embedding_provider == "huggingface" and self.settings.hf_api_token:
            try:
                return self._embed_hf(texts)
            except Exception as extra:  # noqa: BLE001
                logger.warning("Hugging Face embedding API failed (%s); using local MiniLM", extra)
        try:
            self._load_local()
        except RuntimeError as extra:
            if "client has been closed" not in str(extra).lower():
                raise
            logger.warning("Hugging Face HTTP client was closed; reloading embeddings")
            self._model = None
            get_embedder.cache_clear()
            _reset_hf_http_client()
            replacement = EmbeddingService()
            replacement._load_local()
            self._model = replacement._model
        assert self._model is not None
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            batch_size=1,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    def _embed_hf(self, texts: Sequence[str]) -> list[list[float]]:
        token = self.settings.hf_api_token
        if not token:
            raise RuntimeError("HF_API_TOKEN is required when EMBEDDING_PROVIDER=huggingface")
        endpoint = self.settings.hf_embedding_endpoint or (
            f"https://api-inference.huggingface.co/models/{self.model_name}"
        )
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": list(texts)},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data and isinstance(data[0], float):
            return [data]
        if isinstance(data, list):
            return data
        raise RuntimeError("Unexpected Hugging Face embedding response")


@lru_cache
def get_embedder() -> EmbeddingService:
    return EmbeddingService()
