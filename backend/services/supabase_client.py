from __future__ import annotations

import logging
import time
from functools import lru_cache

from supabase import Client, create_client

from config import get_settings

logger = logging.getLogger("scenicworks.supabase")

_SKIP_SECONDS = 90.0
_skip_until = 0.0


def remote_enabled() -> bool:
    return time.monotonic() >= _skip_until


def mark_remote_down(reason: str | None = None) -> None:
    global _skip_until
    _skip_until = time.monotonic() + _SKIP_SECONDS
    logger.warning(
        "Supabase unreachable (%s); skipping remote calls for %.0fs",
        reason or "unknown",
        _SKIP_SECONDS,
    )


def mark_remote_up() -> None:
    global _skip_until
    _skip_until = 0.0


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase service credentials are not configured.")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
