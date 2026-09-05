from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from config import get_settings
from services.sessions import constant_time_equals

PROTECTED_PATHS = {"/chat", "/voice", "/lead"}


async def require_widget_key(
    request: Request, call_next: Callable[[Request], Awaitable]
):
    if request.method == "OPTIONS" or request.url.path not in PROTECTED_PATHS:
        return await call_next(request)

    settings = get_settings()
    expected = settings.widget_api_secret
    if not expected:
        if settings.app_env == "production":
            return JSONResponse(
                status_code=503,
                content={"detail": "Widget API secret is not configured."},
            )
        return await call_next(request)

    provided = request.headers.get("x-widget-key", "")
    if not constant_time_equals(provided, expected):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized."})
    return await call_next(request)
