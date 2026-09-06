from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services.local_kb import cosine_similarity, rank_lexical, rank_vectors  # noqa: E402


def test_cosine_of_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_rank_vectors_respects_threshold_and_order() -> None:
    rows = [
        ({"id": "low"}, [1.0, 0.0]),
        ({"id": "high"}, [0.0, 1.0]),
    ]
    ranked = rank_vectors(
        [0.0, 1.0],
        rows,
        top_k=2,
        min_similarity=0.5,
    )
    assert [item["id"] for item in ranked] == ["high"]
    assert ranked[0]["similarity"] == 1.0


def test_lexical_rank_prefers_matching_content() -> None:
    items = [
        {"id": "a", "title": "Services", "content": "Exhibition stands and events"},
        {"id": "b", "title": "Other", "content": "Warehouse storage only"},
    ]
    ranked = rank_lexical("exhibition stand designed and built", items, top_k=2)
    assert ranked[0]["id"] == "a"
    assert ranked[0]["similarity"] > 0
