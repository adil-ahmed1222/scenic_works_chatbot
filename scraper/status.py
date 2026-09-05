"""Persist crawl status for incremental runs and observability."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scraper.config import STATUS_DIR, STATUS_FILE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_status() -> dict[str, Any]:
    if not STATUS_FILE.exists():
        return {
            "last_run_at": None,
            "pages": {},
            "stats": {
                "crawled": 0,
                "skipped": 0,
                "failed": 0,
                "unchanged": 0,
                "updated": 0,
            },
        }
    return json.loads(STATUS_FILE.read_text(encoding="utf-8"))


def save_status(status: dict[str, Any]) -> Path:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return STATUS_FILE


def record_page(
    status: dict[str, Any],
    url: str,
    *,
    content_hash: str,
    title: str,
    language: str,
    changed: bool,
    ok: bool,
    error: str | None = None,
) -> None:
    status.setdefault("pages", {})
    status["pages"][url] = {
        "hash": content_hash,
        "title": title,
        "language": language,
        "ok": ok,
        "changed": changed,
        "error": error,
        "updated_at": _now(),
    }
    stats = status.setdefault(
        "stats",
        {"crawled": 0, "skipped": 0, "failed": 0, "unchanged": 0, "updated": 0},
    )
    if not ok:
        stats["failed"] = stats.get("failed", 0) + 1
    elif changed:
        stats["updated"] = stats.get("updated", 0) + 1
        stats["crawled"] = stats.get("crawled", 0) + 1
    else:
        stats["unchanged"] = stats.get("unchanged", 0) + 1
        stats["skipped"] = stats.get("skipped", 0) + 1


def previous_hash(status: dict[str, Any], url: str) -> str | None:
    page = status.get("pages", {}).get(url) or {}
    return page.get("hash")
