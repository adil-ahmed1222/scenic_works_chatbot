"""Scraper configuration for the Scenic Works domain crawler."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("CRAWL_BASE_URL", "https://adroitiame.com").rstrip("/")
ALLOWED_DOMAINS = {"adroitiame.com", "www.adroitiame.com"}

SEED_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/services.php",
    f"{BASE_URL}/our-facility.php",
    f"{BASE_URL}/fitouts.php",
    f"{BASE_URL}/about.php",
    f"{BASE_URL}/contact.php",
    f"{BASE_URL}/events.php",
    f"{BASE_URL}/exhibitions.php",
]

SITEMAP_CANDIDATES = [
    f"{BASE_URL}/sitemap.xml",
    f"{BASE_URL}/sitemap_index.xml",
    f"{BASE_URL}/sitemap.php",
    f"{BASE_URL}/robots.txt",
]

MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "500"))
MAX_DEPTH = int(os.getenv("CRAWL_MAX_DEPTH", "6"))
DELAY_SECONDS = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
CONCURRENCY = int(os.getenv("CRAWL_CONCURRENCY", "3"))
TIMEOUT_SECONDS = int(os.getenv("CRAWL_TIMEOUT_SECONDS", "45"))
MAX_RETRIES = int(os.getenv("CRAWL_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("CRAWL_RETRY_BACKOFF", "1.5"))
USER_AGENT = os.getenv(
    "CRAWL_USER_AGENT",
    "ScenicWorksBot/1.0 (+https://adroitiame.com)",
)

RAW_DIR = ROOT / "knowledge-base" / "raw"
STATUS_DIR = Path(__file__).resolve().parent / "data"
LOG_DIR = Path(__file__).resolve().parent / "logs"
STATUS_FILE = STATUS_DIR / "crawl_status.json"

SKIP_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mp3",
    ".zip",
    ".rar",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}

SKIP_PATH_PARTS = {
    "wp-admin",
    "wp-login",
    "cart",
    "checkout",
    "mailto:",
    "tel:",
    "javascript:",
}

NOISE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "script",
    "style",
    "noscript",
    "iframe",
    "form.cookie",
    ".cookie",
    ".cookie-banner",
    "#cookie",
    "#cookie-banner",
    ".cookies",
    ".gdpr",
    ".cc-window",
    ".navbar",
    ".nav-menu",
    ".site-footer",
    ".site-header",
    "#navbar",
    "#footer",
]

MAIN_CONTENT_SELECTORS = [
    "main",
    "article",
    "#content",
    ".content",
    ".page-content",
    ".main-content",
    "section",
    "body",
]
