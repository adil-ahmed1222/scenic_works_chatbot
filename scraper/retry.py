"""Retry helpers with exponential backoff."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from scraper.config import MAX_RETRIES, RETRY_BACKOFF

T = TypeVar("T")
logger = logging.getLogger("scenicworks.scraper")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    retries: int = MAX_RETRIES,
    backoff: float = RETRY_BACKOFF,
    label: str = "operation",
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001 — crawler must survive transient failures
            last_error = exc
            wait = backoff ** attempt
            logger.warning(
                "%s failed (attempt %s/%s): %s — retrying in %.1fs",
                label,
                attempt,
                retries,
                exc,
                wait,
            )
            await asyncio.sleep(wait)
    assert last_error is not None
    raise last_error
