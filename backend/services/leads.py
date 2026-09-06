from __future__ import annotations

import logging
import re

from models.schemas import LeadRequest, LeadResponse
from services.http_retry import call_with_backoff
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

CONTACT_RE = re.compile(
    r"("
    r"\bcontact\b|\breach(?:\s+you)?\b|\bphone\b|\bemail\b|\blocation\b|"
    r"\boffice\b|\baddress\b|\bwhatsapp\b|call\s+you|get\s+in\s+touch|talk\s+to|"
    r"ال?تواصل|ال?اتصال|عنوان|مكتب"
    r")",
    re.IGNORECASE,
)


def detect_buying_intent(text: str, language: str | None = None) -> bool:
    if not text:
        return False
    return bool(EN_INTENT.search(text) or AR_INTENT.search(text))


def detect_contact_intent(text: str) -> bool:
    return bool(text and CONTACT_RE.search(text))


def is_honeypot_submission(website: str | None) -> bool:
    return bool(website and str(website).strip())


def save_lead(payload: LeadRequest) -> LeadResponse:
    if is_honeypot_submission(payload.website):
        logger.info("Dropped honeypot lead submission")
        return LeadResponse(id="ignored", status="saved")
    row = {
        "name": payload.name.strip(),
        "email": str(payload.email).lower(),
        "phone": payload.phone,
        "company": payload.company,
        "requirements": payload.requirements,
        "session_id": verified_session_id(payload.session_id, payload.session_token),
        "language": payload.language,
    }

    def _insert():
        return get_supabase().table("leads").insert(row).execute()

    result = call_with_backoff(_insert, attempts=3, label="supabase.leads.insert")
    data = (result.data or [{}])[0]
    lead_id = str(data.get("id") or "")
    if not lead_id:
        raise RuntimeError("Lead insert returned no id.")
    logger.info("Saved lead id=%s email=%s", lead_id, row["email"])
    return LeadResponse(id=lead_id, status="saved")
