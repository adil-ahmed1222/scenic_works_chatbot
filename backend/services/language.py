from __future__ import annotations

import re

from langdetect import DetectorFactory, detect, lang_detect_exception

DetectorFactory.seed = 0
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

FALLBACK_EN = (
    "I couldn't find that information in Scenic Works' knowledge base. "
    "Please contact Scenic Works directly for assistance."
)
FALLBACK_AR = (
    "لم أتمكن من العثور على هذه المعلومات في قاعدة معرفة سينيك ووركس. "
    "يُرجى التواصل مع سينيك ووركس مباشرة للمساعدة."
)


def detect_language(text: str) -> str:
    sample = (text or "").strip()
    if not sample:
        return "en"
    arabic_count = len(ARABIC_RE.findall(sample))
    if arabic_count / max(len(sample), 1) > 0.12 or arabic_count > 8:
        return "ar"
    try:
        lang = detect(sample)
    except lang_detect_exception.LangDetectException:
        return "ar" if arabic_count else "en"
    if lang.startswith("ar"):
        return "ar"
    return "en"


def fallback_message(language: str) -> str:
    return FALLBACK_AR if language == "ar" else FALLBACK_EN


def service_error_message(language: str) -> str:
    if language == "ar":
        return "المساعد ما زال قيد التحميل. يُرجى إعادة إرسال سؤالك بعد لحظات."
    return "The assistant is still starting up. Please send your question again in a moment."


def is_knowledge_fallback(text: str) -> bool:
    lowered = (text or "").lower()
    return (
        "couldn't find that information in scenic works" in lowered
        or "لم أتمكن من العثور على هذه المعلومات في قاعدة معرفة سينيك ووركس" in (text or "")
    )


def is_rtl(language: str) -> bool:
    return language == "ar"
