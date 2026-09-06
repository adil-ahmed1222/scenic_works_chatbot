"""Shared retry helper for outbound HTTP calls."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger("scenicworks.retry")

T = TypeVar("T")
RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


def call_with_backoff(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.6,
    label: str,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as extra:  # noqa: BLE001
            last_error = extra
            status = getattr(getattr(extra, "response", None), "status_code", None)
            retryable = status in RETRY_STATUSES or status is None
            logger.warning(
                "%s failed attempt=%s/%s status=%s error=%s",
                label,
                attempt,
                attempts,
                status,
                extra,
            )
            if not retryable or attempt == attempts:
                break
            time.sleep(base_delay * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error
