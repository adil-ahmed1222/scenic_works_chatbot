from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("SESSION_SIGNING_KEY", "unit-test-signing-key")
os.environ.setdefault("WIDGET_API_SECRET", "unit-test-widget-key")

from config import get_settings  # noqa: E402
from services.sessions import (  # noqa: E402
    constant_time_equals,
    issue_session,
    resolve_session,
    sign_session,
    verified_session_id,
)

get_settings.cache_clear()


def test_valid_token_is_reused() -> None:
    session_id, token = issue_session()
    resolved_id, resolved_token = resolve_session(session_id, token)
    assert resolved_id == session_id
    assert resolved_token == token
    assert verified_session_id(session_id, token) == session_id


def test_forged_session_id_is_rejected() -> None:
    _, token = issue_session()
    forged = "00000000-0000-0000-0000-000000000000"
    resolved_id, _resolved_token = resolve_session(forged, token)
    assert resolved_id != forged
    assert verified_session_id(forged, token) is None


def test_missing_or_short_token_issues_new_session() -> None:
    session_id, token = issue_session()
    new_id, new_token = resolve_session(session_id, None)
    assert new_id != session_id
    assert new_token != token
    assert verified_session_id(session_id, "short") is None
    assert sign_session(session_id) == token


def test_malformed_session_id_is_rejected() -> None:
    assert verified_session_id("not-a-uuid", sign_session("not-a-uuid")) is None
    new_id, _token = resolve_session("not-a-uuid", sign_session("not-a-uuid"))
    assert new_id != "not-a-uuid"


def test_constant_time_equals_rejects_length_mismatch() -> None:
    assert constant_time_equals("abcd", "abcd")
    assert not constant_time_equals("ab", "abcd")
    assert not constant_time_equals("", "abcd")
