"""Signed chat sessions so clients cannot read another visitor's history."""

from __future__ import annotations

import hashlib
import hmac
import re
import uuid

from config import get_settings

_SESSION_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _secret() -> bytes:
    settings = get_settings()
    key = settings.session_signing_key or settings.widget_api_secret or settings.app_name
    return key.encode("utf-8")


def constant_time_equals(left: str, right: str) -> bool:
    if not left or not right or len(left) != len(right):
        return False
    return hmac.compare_digest(left, right)


def sign_session(session_id: str) -> str:
    digest = hmac.new(_secret(), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def issue_session() -> tuple[str, str]:
    session_id = str(uuid.uuid4())
    return session_id, sign_session(session_id)


def verified_session_id(session_id: str | None, session_token: str | None) -> str | None:
    if not session_id or not session_token or not _SESSION_ID.match(session_id):
        return None
    expected = sign_session(session_id)
    if constant_time_equals(expected, session_token):
        return session_id
    return None


def resolve_session(session_id: str | None, session_token: str | None) -> tuple[str, str]:
    verified = verified_session_id(session_id, session_token)
    if verified and session_token:
        return verified, session_token
    return issue_session()
