"""Crawl4AI domain crawler with sitemap support, retries, and incremental hashing."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.config import (  # noqa: E402
    BASE_URL,
    CONCURRENCY,
    DELAY_SECONDS,
    MAX_DEPTH,
    MAX_PAGES,
    RAW_DIR,
    SEED_URLS,
    TIMEOUT_SECONDS,
    USER_AGENT,
)
from scraper.extractors import extract_page  # noqa: E402
from scraper.logging_setup import setup_logging  # noqa: E402
from scraper.retry import with_retry  # noqa: E402
from scraper.sitemap import discover_sitemap_urls  # noqa: E402
from scraper.status import load_status, previous_hash, record_page, save_status  # noqa: E402
from scraper.url_utils import is_internal_url, normalize_url, should_skip  # noqa: E402

logger = setup_logging()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_language(text: str) -> str:
    try:
        from langdetect import detect

        lang = detect(text[:4000]) if text.strip() else "en"
        return "ar" if lang.startswith("ar") else "en" if lang.startswith("en") else lang
    except Exception:  # noqa: BLE001
        arabic = sum(1 for ch in text if "\u0600" <= ch <= "\u06FF")
        return "ar" if arabic > 20 else "en"


def url_to_filename(url: str) -> str:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()
    return f"{digest}.json"


async def fetch_html(crawler: Any, url: str) -> str:
    from crawl4ai import CrawlerRunConfig

    run_config = CrawlerRunConfig(
        wait_until="domcontentloaded",
        page_timeout=int(TIMEOUT_SECONDS * 1000),
        excluded_tags=["script", "style", "noscript"],
        exclude_external_links=True,
        word_count_threshold=10,
    )

    async def _run() -> str:
        result = await crawler.arun(url=url, config=run_config)
        if not result or not result.success:
            error = getattr(result, "error_message", None) or "unknown crawl error"
            raise RuntimeError(error)
        html = result.cleaned_html or result.html
        if not html:
            raise RuntimeError("empty HTML")
        return html

    return await with_retry(_run, label=f"crawl {url}")


async def crawl_domain(*, incremental: bool = True) -> dict[str, Any]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    status = load_status()
    status["stats"] = {
        "crawled": 0,
        "skipped": 0,
        "failed": 0,
        "unchanged": 0,
        "updated": 0,
    }

    seeds = [normalize_url(u) for u in SEED_URLS]
    try:
        sitemap_urls = await discover_sitemap_urls()
        seeds.extend(sitemap_urls)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sitemap discovery failed: %s", exc)

    queue: deque[tuple[str, int]] = deque()
    seen: set[str] = set()
    for url in seeds:
        if is_internal_url(url) and not should_skip(url) and url not in seen:
            seen.add(url)
            queue.append((url, 0))

    logger.info("Starting crawl of %s with %s seed URLs", BASE_URL, len(queue))

    browser_config = BrowserConfig(
        headless=True,
        user_agent=USER_AGENT,
        verbose=False,
    )
    semaphore = asyncio.Semaphore(CONCURRENCY)
    saved = 0

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and saved < MAX_PAGES:
            url, depth = queue.popleft()
            if depth > MAX_DEPTH:
                continue

            async def _process(current_url: str = url, current_depth: int = depth) -> None:
                nonlocal saved
                async with semaphore:
                    try:
                        html = await fetch_html(crawler, current_url)
                        extracted = extract_page(html, current_url)
                        text = extracted["content"]
                        digest = content_hash(text)
                        language = detect_language(text)
                        prev = previous_hash(status, current_url) if incremental else None
                        changed = digest != prev

                        if incremental and prev and not changed:
                            logger.info("Unchanged: %s", current_url)
                            record_page(
                                status,
                                current_url,
                                content_hash=digest,
                                title=extracted["title"],
                                language=language,
                                changed=False,
                                ok=True,
                            )
                        else:
                            payload = {
                                "url": current_url,
                                "title": extracted["title"],
                                "content": text,
                                "language": language,
                                "meta_description": extracted["meta_description"],
                                "headings": extracted["headings"],
                                "faqs": extracted["faqs"],
                                "contacts": extracted["contacts"],
                                "crawled_at": datetime.now(timezone.utc).isoformat(),
                                "content_hash": digest,
                            }
                            out_path = RAW_DIR / url_to_filename(current_url)
                            out_path.write_text(
                                json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8",
                            )
                            saved += 1
                            logger.info("Saved %s -> %s", current_url, out_path.name)
                            record_page(
                                status,
                                current_url,
                                content_hash=digest,
                                title=extracted["title"],
                                language=language,
                                changed=True,
                                ok=True,
                            )

                        for link in extracted.get("links", []):
                            if (
                                link not in seen
                                and is_internal_url(link)
                                and not should_skip(link)
                            ):
                                seen.add(link)
                                queue.append((link, current_depth + 1))
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Failed %s: %s", current_url, exc)
                        record_page(
                            status,
                            current_url,
                            content_hash="",
                            title="",
                            language="",
                            changed=False,
                            ok=False,
                            error=str(exc),
                        )
                    await asyncio.sleep(DELAY_SECONDS)

            await _process()

    status["last_run_at"] = datetime.now(timezone.utc).isoformat()
    status["seed_count"] = len(seeds)
    status["discovered"] = len(seen)
    save_status(status)
    logger.info("Crawl complete: %s", status["stats"])
    return status


def main() -> None:
    incremental = "--full" not in sys.argv
    asyncio.run(crawl_domain(incremental=incremental))


if __name__ == "__main__":
    main()
