"""Live evaluation harness for accuracy, retrieval, hallucination, leads, voice, and latency."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
EN_FILE = ROOT / "questions_en.json"
AR_FILE = ROOT / "questions_ar.json"
REPORT = ROOT / "reports" / "eval.json"

FALLBACK_EN = "I couldn't find that information in Scenic Works' knowledge base"
FALLBACK_AR = "لم أتمكن من العثور على هذه المعلومات في قاعدة معرفة سينيك ووركس"


def load_questions(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_answer(item: dict, answer: str, show_lead: bool) -> dict:
    expect = item.get("expect", "grounded")
    passed = True
    reasons: list[str] = []
    if expect == "fallback":
        if FALLBACK_EN.lower() not in answer.lower() and FALLBACK_AR not in answer:
            passed = False
            reasons.append("expected fallback, got grounded-looking answer")
    elif expect == "grounded":
        if FALLBACK_EN.lower() in answer.lower() or FALLBACK_AR in answer:
            passed = False
            reasons.append("expected grounded answer, got fallback")
        needles = item.get("must_include") or []
        for needle in needles:
            if needle.lower() not in answer.lower():
                passed = False
                reasons.append(f"missing: {needle}")
    if item.get("expect_lead") and not show_lead:
        passed = False
        reasons.append("lead form not triggered")
    return {"passed": passed, "reasons": reasons}


def run(base_url: str, limit: int | None) -> dict:
    questions = load_questions(EN_FILE) + load_questions(AR_FILE)
    if limit:
        questions = questions[:limit]
    results = []
    latencies: list[float] = []
    client = httpx.Client(timeout=60)
    for item in questions:
        started = time.perf_counter()
        try:
            response = client.post(
                f"{base_url.rstrip('/')}/chat",
                json={"message": item["q"], "language": item.get("lang")},
            )
            response.raise_for_status()
            payload = response.json()
            elapsed = time.perf_counter() - started
            latencies.append(elapsed)
            scored = score_answer(
                item, payload.get("answer") or "", payload.get("show_lead_form")
            )
            results.append(
                {
                    "id": item["id"],
                    "q": item["q"],
                    "lang": item.get("lang"),
                    "latency_s": round(elapsed, 3),
                    "answer": payload.get("answer"),
                    "sources": payload.get("sources"),
                    **scored,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "id": item["id"],
                    "q": item["q"],
                    "passed": False,
                    "reasons": [str(exc)],
                }
            )

    passed = sum(1 for r in results if r.get("passed"))
    report = {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "accuracy": round(passed / max(len(results), 1), 4),
        "latency_p50": round(statistics.median(latencies), 3) if latencies else None,
        "latency_p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 3)
        if latencies
        else None,
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Accuracy {report['accuracy']:.1%} "
        f"({passed}/{len(results)}) p50={report['latency_p50']}s p95={report['latency_p95']}s"
    )
    print(f"Wrote {REPORT}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(args.base_url, args.limit)
