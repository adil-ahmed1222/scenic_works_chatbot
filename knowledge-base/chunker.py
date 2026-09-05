"""Semantic chunking with 1000-character windows and 200-character overlap."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

KB_DIR = Path(__file__).resolve().parent
if str(KB_DIR) not in sys.path:
    sys.path.insert(0, str(KB_DIR))

from knowledge_base_paths import CHUNKS_DIR, PROCESSED_FILE  # noqa: E402

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", "。", "؟", "?", "!", ".", " ", ""]


def _split_with_separators(text: str, separators: list[str]) -> list[str]:
    if not separators:
        return [text]
    sep, *rest = separators
    if sep == "":
        return list(text)
    parts = text.split(sep)
    rebuilt: list[str] = []
    for i, part in enumerate(parts):
        suffix = sep if i < len(parts) - 1 else ""
        rebuilt.append(part + suffix)
    return rebuilt


def recursive_split(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    for sep in SEPARATORS:
        pieces = _split_with_separators(text, [sep, *SEPARATORS[SEPARATORS.index(sep) + 1 :]])
        if len(pieces) == 1 and pieces[0] == text and sep != "":
            continue
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = buffer + piece
            if len(candidate) <= chunk_size:
                buffer = candidate
                continue
            if buffer.strip():
                chunks.extend(recursive_split(buffer.strip(), chunk_size) if len(buffer) > chunk_size else [buffer.strip()])
            if len(piece) > chunk_size:
                chunks.extend(recursive_split(piece.strip(), chunk_size))
                buffer = ""
            else:
                buffer = piece
        if buffer.strip():
            chunks.append(buffer.strip())
        return [c for c in chunks if c.strip()]
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def apply_overlap(chunks: list[str], overlap: int = CHUNK_OVERLAP) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
            continue
        prev_tail = chunks[i - 1][-overlap:]
        merged = f"{prev_tail} {chunk}".strip()
        overlapped.append(merged[: CHUNK_SIZE + overlap])
    return overlapped


def chunk_id_for(source_url: str, index: int, content: str) -> str:
    digest = hashlib.sha1(f"{source_url}:{index}:{content[:80]}".encode("utf-8")).hexdigest()
    return f"chk_{digest}"


def chunk_pages(pages: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if pages is None:
        if not PROCESSED_FILE.exists():
            raise FileNotFoundError("Run processor.py first.")
        pages = json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))

    records: list[dict[str, Any]] = []
    for page in pages:
        metadata = page.get("metadata") or {
            "source_url": page.get("url"),
            "title": page.get("title"),
            "language": page.get("language"),
            "category": "general",
        }
        title = metadata.get("title") or ""
        body = page.get("content") or ""
        prefixed = f"{title}\n\n{body}".strip() if title else body
        parts = recursive_split(prefixed)
        parts = apply_overlap(parts)
        for index, content in enumerate(parts):
            records.append(
                {
                    "chunk_id": chunk_id_for(metadata.get("source_url") or "", index, content),
                    "content": content,
                    "metadata": {
                        **metadata,
                        "chunk_index": index,
                        "chunk_count": len(parts),
                    },
                }
            )

    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = CHUNKS_DIR / "chunks.json"
    out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} chunks -> {out_file}")
    return records


if __name__ == "__main__":
    chunk_pages()
