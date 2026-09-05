"""URL normalization and internal-link filtering."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from scraper.config import ALLOWED_DOMAINS, SKIP_EXTENSIONS, SKIP_PATH_PARTS


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
}


def normalize_url(url: str, base: str | None = None) -> str:
    if base:
        url = urljoin(base, url)
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    query = urlencode(query_pairs)
    return urlunparse((scheme, netloc, path, "", query, ""))


def is_internal_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https", ""}:
        return False
    host = parsed.netloc.lower().lstrip("www.")
    if not host:
        return True
    return host in {d.lstrip("www.") for d in ALLOWED_DOMAINS} or host in ALLOWED_DOMAINS


def should_skip(url: str) -> bool:
    lowered = url.lower()
    parsed = urlparse(lowered)
    path = parsed.path
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True
    return any(part in lowered for part in SKIP_PATH_PARTS)
