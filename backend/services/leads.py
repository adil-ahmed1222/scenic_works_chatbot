from __future__ import annotations

import logging
import re

from models.schemas import LeadRequest, LeadResponse
from services.sessions import verified_session_id
from services.supabase_client import get_supabase

logger = logging.getLogger("scenicworks.leads")

EN_INTENT = re.compile(
    r"\b("
    r"quot(?:e|ation)|proposal|pricing|price|cost|budget|rfq|tender|"
    r"exhibition stand|booth|event setup|fit[- ]?out|fitout|"
    r"need (?:a |an )?(?:quote|proposal|stand|booth)|"
    r"get (?:a )?quote|request (?:a )?quote|how much"
    r")\b",
    re.IGNORECASE,
)

AR_INTENT = re.compile(
    r"("
    r"عرض\s*سعر|تسعير|تسعيرة|اقتراح|مقترح|سعر|تكلفة|ميزانية|"
    r"جناح|ستاند|منصة\s*معرض|تنظيم\s*حدث|تجهيز\s*فعالية|"
    r"فيت\s*اوت|تشطيب|طلب\s*عرض"
    r")"
)


def detect_buying_intent(text: str, language: str | None = None) -> bool:
    if not text:
        return False
    return bool(EN_INTENT.search(text) or AR_INTENT.search(text))


def is_honeypot_submission(website: str | None) -> bool:
    return bool(website and str(website).strip())


def save_lead(payload: LeadRequest) -> LeadResponse:
    if is_honeypot_submission(payload.website):
        logger.info("Dropped honeypot lead submission")
        return LeadResponse(id="ignored", status="saved")
    client = get_supabase()
    row = {
        "name": payload.name.strip(),
        "email": str(payload.email).lower(),
        "phone": payload.phone,
        "company": payload.company,
        "requirements": payload.requirements,
        "session_id": verified_session_id(payload.session_id, payload.session_token),
        "language": payload.language,
    }
    result = client.table("leads").insert(row).execute()
    data = (result.data or [{}])[0]
    return LeadResponse(id=str(data.get("id") or ""), status="saved")
