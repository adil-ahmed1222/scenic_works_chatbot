"""Daily incremental crawl → process → embed pipeline.

Run at 01:00 UTC via GitHub Actions or a Railway cron service:

    python scheduler/daily_update.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.crawler import crawl_domain  # noqa: E402
from scraper.logging_setup import setup_logging  # noqa: E402

KB = ROOT / "knowledge-base"
if str(KB) not in sys.path:
    sys.path.insert(0, str(KB))

from pipeline import run as run_kb_pipeline  # noqa: E402

logger = setup_logging("scenicworks.scheduler")


def main() -> None:
    logging.getLogger().setLevel(logging.INFO)
    logger.info("Starting daily knowledge-base update")
    status = asyncio.run(crawl_domain(incremental=True))
    stats = status.get("stats") or {}
    logger.info("Crawl stats: %s", stats)
    if stats.get("updated", 0) == 0 and stats.get("failed", 0) == 0:
        logger.info("No page changes detected; skipping embedding refresh.")
        return
    run_kb_pipeline(skip_embed=False)
    logger.info("Daily update complete")


if __name__ == "__main__":
    main()
