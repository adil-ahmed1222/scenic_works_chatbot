"""Structured logging for the crawler."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from scraper.config import LOG_DIR


def setup_logging(name: str = "scenicworks.scraper") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        LOG_DIR / f"crawl-{stamp}.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
