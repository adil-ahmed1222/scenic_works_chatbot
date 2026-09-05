from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "knowledge-base"))

from chunker import CHUNK_OVERLAP, CHUNK_SIZE, recursive_split  # noqa: E402
from processor import categorize, clean_html, detect_language  # noqa: E402


def test_clean_html_strips_scripts() -> None:
    html = "<p>Hello</p><script>alert(1)</script>"
    assert "alert" not in clean_html(html)
    assert "Hello" in clean_html(html)


def test_arabic_preserved() -> None:
    text = "سينيك ووركس شركة تصميم أجنحة المعارض"
    assert detect_language(text) == "ar"
    assert "سينيك ووركس" in clean_html(text)


def test_category_from_url() -> None:
    assert categorize("https://adroitiame.com/fitouts.php", "Fitout") == "fitout"
    assert categorize("https://adroitiame.com/", "Home") == "home"


def test_chunk_size_bounds() -> None:
    text = ("Scenic Works exhibition stand design. " * 80).strip()
    chunks = recursive_split(text, CHUNK_SIZE)
    assert chunks
    assert all(len(c) <= CHUNK_SIZE + 20 for c in chunks)
    assert CHUNK_OVERLAP == 200
