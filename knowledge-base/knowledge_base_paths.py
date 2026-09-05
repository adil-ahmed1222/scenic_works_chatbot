"""Shared paths for the knowledge-base scripts (folder name contains a hyphen)."""

from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
RAW_DIR = KB_DIR / "raw"
PROCESSED_DIR = KB_DIR / "processed"
CHUNKS_DIR = KB_DIR / "chunks"
PROCESSED_FILE = PROCESSED_DIR / "pages.json"
CHUNKS_FILE = CHUNKS_DIR / "chunks.json"
