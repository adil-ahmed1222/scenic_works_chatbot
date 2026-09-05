"""End-to-end knowledge-base pipeline: process → chunk → embed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
if str(KB_DIR) not in sys.path:
    sys.path.insert(0, str(KB_DIR))

from chunker import chunk_pages  # noqa: E402
from embed import embed_from_disk  # noqa: E402
from processor import process_pages  # noqa: E402


def run(skip_embed: bool = False) -> None:
    pages = process_pages()
    chunks = chunk_pages(pages)
    print(f"Pipeline prepared {len(pages)} pages and {len(chunks)} chunks.")
    if skip_embed:
        return
    written = embed_from_disk()
    print(f"Indexed {written} embeddings in Supabase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scenic Works knowledge-base pipeline")
    parser.add_argument(
        "--skip-embed",
        action="store_true",
        help="Stop after chunking (no Supabase writes).",
    )
    args = parser.parse_args()
    run(skip_embed=args.skip_embed)
