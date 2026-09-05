"""Extract page title, content, headings, FAQs, and contact details."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from scraper.config import MAIN_CONTENT_SELECTORS, NOISE_SELECTORS

CONTACT_RE = re.compile(
    r"("
    r"(?:\+?\d[\d\s\-()]{7,}\d)"
    r"|[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}"
    r")",
    re.IGNORECASE,
)

FAQ_QUESTION_RE = re.compile(
    r"^\s*(?:q\s*[:.\-]|faq\s*\d*|[\u061F؟]|.*\?)\s*", re.IGNORECASE
)


def _remove_noise(soup: BeautifulSoup) -> None:
    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()
    for tag in soup.find_all(["script", "style", "noscript", "svg", "canvas"]):
        tag.decompose()


def _main_node(soup: BeautifulSoup) -> Tag:
    for selector in MAIN_CONTENT_SELECTORS:
        node = soup.select_one(selector)
        if node and node.get_text(strip=True):
            return node
    return soup.body or soup


def extract_meta_description(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    return ""


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    heading = soup.find(["h1", "h2"])
    return heading.get_text(strip=True) if heading else ""


def extract_headings(node: Tag) -> list[str]:
    headings: list[str] = []
    for tag in node.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)
        if text:
            headings.append(text)
    return headings


def extract_faqs(node: Tag) -> list[dict[str, str]]:
    faqs: list[dict[str, str]] = []
    for details in node.find_all("details"):
        q = details.find("summary")
        if q:
            faqs.append(
                {
                    "question": q.get_text(" ", strip=True),
                    "answer": details.get_text(" ", strip=True),
                }
            )
    for dt in node.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            faqs.append(
                {
                    "question": dt.get_text(" ", strip=True),
                    "answer": dd.get_text(" ", strip=True),
                }
            )
    return faqs


def extract_contacts(text: str) -> dict[str, list[str]]:
    emails: list[str] = []
    phones: list[str] = []
    for match in CONTACT_RE.findall(text):
        value = re.sub(r"\s+", " ", match).strip()
        if "@" in value:
            emails.append(value.lower())
        else:
            phones.append(value)
    return {
        "emails": sorted(set(emails)),
        "phones": sorted(set(phones)),
    }


def extract_internal_hrefs(soup: BeautifulSoup, page_url: str) -> list[str]:
    from scraper.url_utils import is_internal_url, normalize_url, should_skip

    hrefs: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        try:
            normalized = normalize_url(href, page_url)
        except Exception:  # noqa: BLE001
            continue
        if is_internal_url(normalized) and not should_skip(normalized):
            hrefs.append(normalized)
    return list(dict.fromkeys(hrefs))


def visible_text(node: Tag) -> str:
    parts: list[str] = []
    for descendant in node.descendants:
        if isinstance(descendant, NavigableString):
            parent = descendant.parent
            if parent and parent.name in {"script", "style", "noscript"}:
                continue
            text = str(descendant).strip()
            if text:
                parts.append(text)
    merged = "\n".join(parts)
    merged = re.sub(r"[ \t]+", " ", merged)
    merged = re.sub(r"\n{3,}", "\n\n", merged)
    return merged.strip()


def extract_page(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    _remove_noise(soup)
    main = _main_node(soup)
    title = extract_title(soup)
    meta = extract_meta_description(soup)
    headings = extract_headings(main)
    faqs = extract_faqs(main)
    content = visible_text(main)
    contacts = extract_contacts(f"{content}\n{meta}")
    links = extract_internal_hrefs(soup, url)

    blocks = [title, meta, content]
    if headings:
        blocks.append("Headings:\n" + "\n".join(headings))
    if faqs:
        faq_lines = [
            f"Q: {item['question']}\nA: {item['answer']}" for item in faqs
        ]
        blocks.append("FAQs:\n" + "\n\n".join(faq_lines))
    if contacts["emails"] or contacts["phones"]:
        blocks.append(
            "Contact details:\n"
            + "\n".join(contacts["emails"] + contacts["phones"])
        )

    return {
        "url": url,
        "title": title,
        "meta_description": meta,
        "headings": headings,
        "faqs": faqs,
        "contacts": contacts,
        "links": links,
        "content": "\n\n".join(b for b in blocks if b).strip(),
    }
