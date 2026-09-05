from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services.leads import detect_buying_intent, is_honeypot_submission  # noqa: E402


def test_honeypot_field_is_treated_as_spam() -> None:
    assert is_honeypot_submission("https://spam.example")
    assert not is_honeypot_submission("")
    assert not is_honeypot_submission(None)


def test_english_quote_intent() -> None:
    assert detect_buying_intent("I need a quotation for an exhibition stand")


def test_arabic_quote_intent() -> None:
    assert detect_buying_intent("أريد عرض سعر لجناح معرض")


def test_no_intent_on_general_question() -> None:
    assert not detect_buying_intent("Where are your offices located?")
