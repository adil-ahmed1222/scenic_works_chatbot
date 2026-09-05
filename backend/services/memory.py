from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from config import get_settings
from services.supabase_client import get_supabase, mark_remote_down, remote_enabled

logger = logging.getLogger("scenicworks.memory")

_LOCAL_HISTORY: dict[str, list[dict]] = defaultdict(list)


def _cap(limit: int | None = None) -> int:
    return limit or get_settings().chat_history_limit


def fetch_history(session_id: str, limit: int | None = None) -> list[dict]:
    cap = _cap(limit)
    local = list(_LOCAL_HISTORY.get(session_id, []))[-cap:]
    if not remote_enabled():
        return local
    try:
        client = get_supabase()
        result = (
            client.table("chat_history")
            .select("role, message, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(cap)
            .execute()
        )
        rows = list(reversed(result.data or []))
        return rows or local
    except Exception as exc:  # noqa: BLE001
        mark_remote_down(str(exc))
        logger.warning("Remote history fetch failed: %s", exc)
        return local


def append_message(
    session_id: str, role: str, message: str, language: str | None = None
) -> None:
    row = {
        "session_id": session_id,
        "role": role,
        "message": message,
        "language": language,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _LOCAL_HISTORY[session_id].append(row)
    _LOCAL_HISTORY[session_id] = _LOCAL_HISTORY[session_id][-_cap() * 4 :]
    if not remote_enabled():
        return
    try:
        client = get_supabase()
        client.table("chat_history").insert(
            {
                "session_id": session_id,
                "role": role,
                "message": message,
                "language": language,
            }
        ).execute()
    except Exception as exc:  # noqa: BLE001
        mark_remote_down(str(exc))
        logger.warning("Remote history persist failed; using in-memory store: %s", exc)


def as_openai_messages(history: list[dict]) -> list[dict]:
    messages = []
    for row in history:
        role = row.get("role")
        if role not in {"user", "assistant"}:
            continue
        messages.append({"role": role, "content": row.get("message") or ""})
    return messages[-get_settings().chat_history_limit :]
