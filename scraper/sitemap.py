"""Sitemap discovery for seed URL expansion."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import httpx

from scraper.config import BASE_URL, SITEMAP_CANDIDATES, TIMEOUT_SECONDS, USER_AGENT
from scraper.url_utils import is_internal_url, normalize_url

logger = logging.getLogger("scenicworks.scraper")


async def fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url, follow_redirects=True)
        if response.status_code >= 400:
            return None
        return response.text
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to fetch %s: %s", url, exc)
        return None


def parse_sitemap_xml(xml_text: str) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for loc in root.findall(".//sm:loc", ns) or root.findall(".//{*}loc"):
        if loc.text:
            urls.append(loc.text.strip())
    return urls


def parse_robots_sitemaps(robots_text: str) -> list[str]:
    found: list[str] = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            found.append(line.split(":", 1)[1].strip())
    return found


async def discover_sitemap_urls() -> list[str]:
    discovered: list[str] = []
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS, headers=headers, verify=True
    ) as client:
        robots = await fetch_text(client, urljoin(BASE_URL + "/", "robots.txt"))
        sitemap_urls = list(SITEMAP_CANDIDATES)
        if robots:
            sitemap_urls.extend(parse_robots_sitemaps(robots))

        seen_sitemaps: set[str] = set()
        for sitemap_url in sitemap_urls:
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)
            body = await fetch_text(client, sitemap_url)
            if not body:
                continue
            parsed = parse_sitemap_xml(body)
            if not parsed and "sitemap" in body.lower():
                nested = parse_robots_sitemaps(body)
                for nested_url in nested:
                    if nested_url not in seen_sitemaps:
                        sitemap_urls.append(nested_url)
            for raw in parsed:
                if is_internal_url(raw):
                    discovered.append(normalize_url(raw))

    unique = sorted(set(discovered))
    logger.info("Sitemap discovery found %s internal URLs", len(unique))
    return unique
