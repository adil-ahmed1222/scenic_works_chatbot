"""Clean, deduplicate, and normalize crawled pages into processed JSON."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from langdetect import DetectorFactory, detect, lang_detect_exception

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW_DIR = Path(__file__).resolve().parent / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent / "processed"

DetectorFactory.seed = 0
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")
MULTI_NL_RE = re.compile(r"\n{3,}")

CATEGORY_MAP = {
    "fitout": "fitout",
    "fitouts": "fitout",
    "facility": "facility",
    "service": "services",
    "services": "services",
    "event": "events",
    "events": "events",
    "exhibition": "exhibitions",
    "exhibitions": "exhibitions",
    "brand": "branding",
    "branding": "branding",
    "contact": "contact",
    "about": "about",
    "display": "instore-display",
}


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = WHITESPACE_RE.sub(" ", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def clean_html(text: str) -> str:
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
    return normalize_whitespace(text)


def detect_language(text: str) -> str:
    sample = text[:4000].strip()
    if not sample:
        return "en"
    arabic_chars = len(ARABIC_RE.findall(sample))
    ratio = arabic_chars / max(len(sample), 1)
    if ratio > 0.15:
        return "ar"
    try:
        lang = detect(sample)
    except lang_detect_exception.LangDetectException:
        return "ar" if arabic_chars > 12 else "en"
    if lang.startswith("ar"):
        return "ar"
    if lang.startswith("en"):
        return "en"
    return lang


def categorize(url: str, title: str) -> str:
    path = urlparse(url).path.lower()
    blob = f"{path} {title.lower()}"
    for key, category in CATEGORY_MAP.items():
        if key in blob:
            return category
    if path in {"", "/"}:
        return "home"
    return "general"


def page_fingerprint(url: str, content: str) -> str:
    return hashlib.sha256(f"{url}\n{content}".encode("utf-8")).hexdigest()


def load_raw_pages() -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    if not RAW_DIR.exists():
        return pages
    for path in sorted(RAW_DIR.glob("*.json")):
        try:
            pages.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return pages


def process_pages(pages: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    pages = pages if pages is not None else load_raw_pages()
    processed: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    seen_urls: set[str] = set()

    for page in pages:
        url = (page.get("url") or "").strip()
        title = (page.get("title") or "").strip()
        content = clean_html(page.get("content") or "")
        if not url or not content or len(content) < 80:
            continue
        if url in seen_urls:
            continue
        digest = page_fingerprint(url, content)
        if digest in seen_hashes:
            continue
        seen_urls.add(url)
        seen_hashes.add(digest)
        language = page.get("language") or detect_language(content)
        if language not in {"en", "ar"}:
            language = detect_language(content)
        category = categorize(url, title)
        processed.append(
            {
                "url": url,
                "title": title,
                "content": content,
                "language": language,
                "metadata": {
                    "source_url": url,
                    "title": title,
                    "language": language,
                    "category": category,
                },
            }
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_file = PROCESSED_DIR / "pages.json"
    out_file.write_text(
        json.dumps(processed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Processed {len(processed)} pages -> {out_file}")
    return processed


if __name__ == "__main__":
    process_pages()
