from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Sequence

import httpx
from config import get_settings

logger = logging.getLogger("scenicworks.embeddings")


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
        self._model = None

    def _load_local(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s", self.settings.embedding_model)
        offline_keys = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
        previous = {key: os.environ.get(key) for key in offline_keys}
        try:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            self._model = SentenceTransformer(
                self.settings.embedding_model,
                local_files_only=True,
            )
            return
        except Exception as extra:  # noqa: BLE001
            logger.info("Local embedding cache miss (%s); downloading if needed", extra)
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            _reset_hf_http_client()
            self._model = SentenceTransformer(self.settings.embedding_model)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if self.settings.embedding_provider == "huggingface":
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
            batch_size=16,
        )
        return [v.tolist() for v in vectors]

    def _embed_hf(self, texts: Sequence[str]) -> list[list[float]]:
        token = self.settings.hf_api_token
        if not token:
            raise RuntimeError("HF_API_TOKEN is required when EMBEDDING_PROVIDER=huggingface")
        endpoint = self.settings.hf_embedding_endpoint or (
            f"https://api-inference.huggingface.co/models/{self.settings.embedding_model}"
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
