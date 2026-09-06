from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services.language import (  # noqa: E402
    detect_language,
    fallback_message,
    is_closing_message,
    is_knowledge_fallback,
    service_error_message,
    thanks_message,
)


def test_english_detection() -> None:
    assert detect_language("What services does Scenic Works offer?") == "en"


def test_arabic_detection() -> None:
    assert detect_language("ما هي خدمات سينيك ووركس للمعارض؟") == "ar"


def test_fallback_messages() -> None:
    assert "knowledge base" in fallback_message("en").lower()
    assert "قاعدة معرفة" in fallback_message("ar")
    assert is_knowledge_fallback(fallback_message("en"))
    assert "starting up" in service_error_message("en").lower()


def test_closing_messages() -> None:
    assert is_closing_message("ok thank you")
    assert is_closing_message("Thank you!")
    assert is_closing_message("شكرا")
    assert not is_closing_message("What services do you offer?")
    assert "welcome" in thanks_message("en").lower()
