from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import get_settings
from logging_config import setup_logging
from rate_limit import limiter
from routers import chat, health, lead, voice
from security import require_widget_key

setup_logging()
logger = logging.getLogger("scenicworks.api")
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parent / "static"
(STATIC_DIR / "audio").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.app_env == "production":
        if not settings.widget_api_secret:
            logger.error("WIDGET_API_SECRET is required in production")
        if not settings.session_signing_key:
            logger.warning("SESSION_SIGNING_KEY is empty; falling back to the widget secret")
    try:
        if settings.embedding_provider == "local":
            from services.embeddings import get_embedder
            from services.local_kb import warmup_local_kb

            get_embedder().embed_query("scenic works")
            logger.info("Embedding model ready")
            warmup_local_kb()
            logger.info("Local knowledge index ready")
        else:
            logger.info("Remote embeddings enabled; skipping local model warmup")
    except Exception:
        logger.exception("Embedding warmup failed; first chat will load the model")
    yield


app = FastAPI(
    title="Scenic Works Chatbot API",
    version="1.0.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded. Please try again shortly."},
))

app.middleware("http")(require_widget_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Widget-Key"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(voice.router, tags=["voice"])
app.include_router(lead.router, tags=["leads"])
