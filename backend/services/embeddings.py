from __future__ import annotations

import logging
import math
import os
import time
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

    def _use_remote_api(self) -> bool:
        return self.settings.embedding_provider == "huggingface" or bool(
            os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID")
        )

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if self._use_remote_api():
            return self._embed_hf(texts)
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

    def _hf_endpoints(self) -> list[str]:
        if self.settings.hf_embedding_endpoint:
            return [self.settings.hf_embedding_endpoint]
        model = self.model_name
        return [
            f"https://router.huggingface.co/hf-inference/models/{model}/pipeline/feature-extraction",
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}",
            f"https://api-inference.huggingface.co/models/{model}",
        ]

    def _embed_hf(self, texts: Sequence[str]) -> list[list[float]]:
        token = (self.settings.hf_api_token or "").strip()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        last_error: Exception | None = None
        for endpoint in self._hf_endpoints():
            for attempt in range(4):
                try:
                    response = httpx.post(
                        endpoint,
                        headers=headers,
                        json={"inputs": list(texts), "options": {"wait_for_model": True}},
                        timeout=30,
                    )
                    if response.status_code in {502, 503, 504}:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    response.raise_for_status()
                    vectors = _coerce_vectors(response.json(), len(texts))
                    logger.info("Embedded %s texts via Hugging Face API", len(vectors))
                    return [_normalize(vector) for vector in vectors]
                except Exception as extra:  # noqa: BLE001
                    last_error = extra
                    logger.warning("HF embedding endpoint %s failed: %s", endpoint, extra)
                    break
        raise RuntimeError(
            "Hugging Face embedding API failed. Set HF_API_TOKEN on Render "
            "and do not use EMBEDDING_PROVIDER=local on the Free tier."
        ) from last_error


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _mean_pool(tokens: list[list[float]]) -> list[float]:
    width = len(tokens[0])
    totals = [0.0] * width
    for token in tokens:
        for index, value in enumerate(token):
            totals[index] += float(value)
    count = float(len(tokens))
    return [value / count for value in totals]


def _coerce_vectors(data: object, expected: int) -> list[list[float]]:
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(str(data.get("error")))
    if isinstance(data, list) and data and isinstance(data[0], float):
        return [data]
    if isinstance(data, list) and data and isinstance(data[0], list):
        if data[0] and isinstance(data[0][0], float):
            if expected == 1 and len(data) != 1 and all(isinstance(row[0], float) for row in data):
                return [_mean_pool(data)]  # type: ignore[arg-type]
            return data
        if data[0] and isinstance(data[0][0], list):
            return [_mean_pool(row) for row in data]  # type: ignore[arg-type]
    raise RuntimeError(f"Unexpected Hugging Face embedding response: {type(data)}")


@lru_cache
def get_embedder() -> EmbeddingService:
    return EmbeddingService()
